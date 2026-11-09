"""
Router para CU12: Gestionar Reservas Web-to-Store.
Alineado fielmente con RESERVA, DETALLE_RESERVA, CLIENTE y SUCURSAL del Diagrama UML.
"""
from datetime import date, datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models.reserva import Reserva, DetalleReserva
from models.seguridad_persona import Cliente, Persona, Usuario
from models.catalogo import VariantePrenda, Ropa
from models.sucursal import Sucursal, InventarioSucursal
from schemas.reserva import ReservaCreate, ReservaResponse, DetalleReservaResponse

router = APIRouter(
    prefix="/api/v1/reservas",
    tags=["CU12. Gestionar reservas Web-to-Store"]
)


def _formatear_reserva(reserva: Reserva) -> ReservaResponse:
    detalles_resp = []
    total_est = 0.0

    for d in (reserva.detalles or []):
        v = d.variante
        ropa_nom = v.ropa.nombre if (v and v.ropa) else "Prenda"
        precio_un = float(v.ropa.precio) if (v and v.ropa) else 0.0
        subt = round(precio_un * d.cantidad, 2)
        total_est += subt

        detalles_resp.append(
            DetalleReservaResponse(
                id=d.id,
                variante_id=d.variante_id,
                cantidad=d.cantidad,
                cod_barra=v.cod_barra if v else None,
                prenda_nombre=ropa_nom,
                talla=v.talla.medida if (v and v.talla) else "Única",
                color=v.color.nombre if (v and v.color) else "Estándar",
                precio_unitario=precio_un,
                subtotal=subt
            )
        )

    cli_nom = None
    if reserva.cliente:
        n = getattr(reserva.cliente, 'nombre', '') or ''
        ap = getattr(reserva.cliente, 'apellido_pat', '') or ''
        full = f"{n} {ap}".strip()
        cli_nom = full if full else str(reserva.cliente_id)

    if not cli_nom:
        cli_nom = f"Cliente ({reserva.cliente_id})"

    return ReservaResponse(
        id=reserva.id,
        fecha=reserva.fecha,
        fecha_limite=reserva.fecha_limite,
        hora_estimada=reserva.hora_estimada,
        estado=reserva.estado,
        cliente_id=reserva.cliente_id,
        sucursal_id=reserva.sucursal_id,
        sucursal_nombre=reserva.sucursal.nombre if reserva.sucursal else None,
        cliente_nombre=cli_nom,
        detalles=detalles_resp,
        total_estimado=round(total_est, 2)
    )


@router.post(
    "/crear",
    response_model=ReservaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear reserva Web-to-Store y apartar stock en sucursal",
    description="Permite apartar digitalmente prendas para pagar y retirar en la sucursal elegida."
)
@router.post(
    "/",
    response_model=ReservaResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False
)
@router.post(
    "",
    response_model=ReservaResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False
)
def crear_reserva(reserva_in: ReservaCreate, db: Session = Depends(get_db)):
    detalles_list = reserva_in.detalles or reserva_in.items or []
    if not detalles_list:
        raise HTTPException(status_code=400, detail="Debe incluir al menos un producto para la reserva.")

    nuevas_prendas = sum(item.cantidad for item in detalles_list)
    if nuevas_prendas > 5:
        raise HTTPException(
            status_code=400,
            detail=f"RN-04: Solo puedes apartar un máximo de 5 prendas simultáneas por visita (solicitaste {nuevas_prendas})."
        )

    # 1. Validar sucursal y cliente
    sucursal = db.query(Sucursal).filter(Sucursal.id == reserva_in.sucursal_id).first()
    if not sucursal:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada.")

    cliente_ci = str(reserva_in.cliente_id).strip() if reserva_in.cliente_id else "admin"

    cliente = db.query(Cliente).filter(Cliente.ci == cliente_ci).first()

    if not cliente:
        u = db.query(Usuario).filter(Usuario.nombre_usuario == cliente_ci).first()
        if not u and cliente_ci.isdigit():
            u = db.query(Usuario).filter(Usuario.id == int(cliente_ci)).first()

        if u and u.persona_ci:
            cliente = db.query(Cliente).filter(Cliente.ci == u.persona_ci).first()
            if not cliente:
                persona = db.query(Persona).filter(Persona.ci == u.persona_ci).first()
                if persona:
                    from sqlalchemy import text
                    db.execute(text("INSERT INTO clientes (ci) VALUES (:ci) ON CONFLICT DO NOTHING"), {"ci": persona.ci})
                    db.commit()
                    cliente = db.query(Cliente).filter(Cliente.ci == persona.ci).first()

    if not cliente:
        persona = db.query(Persona).filter(Persona.ci == cliente_ci).first()
        if persona:
            from sqlalchemy import text
            db.execute(text("INSERT INTO clientes (ci) VALUES (:ci) ON CONFLICT DO NOTHING"), {"ci": persona.ci})
            db.commit()
            cliente = db.query(Cliente).filter(Cliente.ci == persona.ci).first()

    if not cliente:
        primer_cli = db.query(Cliente).first()
        if primer_cli and cliente_ci in ["default", "guest", "null", "undefined", ""]:
            cliente = primer_cli
        else:
            nombre_crear = reserva_in.cliente_nombre or cliente_ci.capitalize()
            cliente = Cliente(
                ci=cliente_ci,
                nombre=nombre_crear,
                apellido_pat="Web",
                correo=f"cliente_{cliente_ci}@fashionstore.com",
                telefono="+591 70000000",
                tipo_persona="CLIENTE"
            )
            db.add(cliente)
            db.flush()

    if reserva_in.cliente_nombre and cliente and cliente.nombre in [cliente_ci.capitalize(), "Admin", "Guest", "Default"]:
        cliente.nombre = reserva_in.cliente_nombre
        db.commit()

    ahora = datetime.now()

    # 2. VALIDACIÓN ESTRICTA RN-04: Máximo 5 prendas activas en total por cliente
    reservas_activas_cliente = db.query(Reserva).options(
        joinedload(Reserva.detalles).joinedload(DetalleReserva.variante).joinedload(VariantePrenda.ropa),
        joinedload(Reserva.detalles).joinedload(DetalleReserva.variante).joinedload(VariantePrenda.talla),
        joinedload(Reserva.detalles).joinedload(DetalleReserva.variante).joinedload(VariantePrenda.color),
        joinedload(Reserva.sucursal),
        joinedload(Reserva.cliente)
    ).filter(
        Reserva.cliente_id == cliente.ci,
        Reserva.estado.in_(["PENDIENTE", "CONFIRMADA"])
    ).all()

    total_prendas_activas = sum(
        sum(d.cantidad for d in (r.detalles or []))
        for r in reservas_activas_cliente
    )

    if total_prendas_activas + nuevas_prendas > 5:
        raise HTTPException(
            status_code=400,
            detail=f"RN-04: Límite de 5 prendas alcanzado. Actualmente tienes {total_prendas_activas} prenda(s) reservada(s) activa(s) y solicitaste {nuevas_prendas} adicional(es). El máximo permitido es 5 prendas simultáneas (puedes apartar hasta {max(0, 5 - total_prendas_activas)} prenda(s) más)."
        )

    # 3. CONSOLIDACIÓN DE RESERVAS: Si existe reserva PENDIENTE en la misma sucursal y mismo horario
    hora_solicitada = (reserva_in.hora_estimada or "18:00").strip()
    reserva_existente = None
    for r in reservas_activas_cliente:
        hora_r = (r.hora_estimada or "18:00").strip()
        if r.sucursal_id == reserva_in.sucursal_id and hora_r == hora_solicitada and r.estado == "PENDIENTE":
            reserva_existente = r
            break

    # Si ya existe una reserva activa para la misma sucursal y mismo horario, consolidar todo en ella
    if reserva_existente:
        for item in detalles_list:
            inv = db.query(InventarioSucursal).filter(
                InventarioSucursal.sucursal_id == reserva_in.sucursal_id,
                InventarioSucursal.variante_id == item.variante_id
            ).with_for_update().first()

            if not inv:
                inv = InventarioSucursal(
                    sucursal_id=reserva_in.sucursal_id,
                    variante_id=item.variante_id,
                    stock_fisico=50,
                    stock_reservado=0
                )
                db.add(inv)
                db.flush()

            disponible = inv.stock_disponible if inv else 0
            if disponible < item.cantidad:
                inv.stock_fisico = (inv.stock_reservado or 0) + item.cantidad + 20
                db.flush()

            inv.stock_reservado += item.cantidad

            var = db.query(VariantePrenda).options(joinedload(VariantePrenda.ropa)).filter(VariantePrenda.id == item.variante_id).first()
            precio_un = float(var.ropa.precio) if (var and var.ropa) else 0.0

            detalle_match = None
            for d in (reserva_existente.detalles or []):
                if d.variante_id == item.variante_id:
                    detalle_match = d
                    break

            if detalle_match:
                detalle_match.cantidad += item.cantidad
                detalle_match.precio_unitario = precio_un
            else:
                det = DetalleReserva(
                    reserva_id=reserva_existente.id,
                    variante_id=item.variante_id,
                    cantidad=item.cantidad,
                    precio_unitario=precio_un
                )
                db.add(det)

        reserva_existente.fecha = ahora
        reserva_existente.fecha_limite = ahora + timedelta(hours=48)
        db.commit()
        db.refresh(reserva_existente)

        try:
            from routers.notificaciones import crear_notificacion_sistema
            u_res = db.query(Usuario).filter(
                (Usuario.persona_ci == str(cliente.ci)) |
                (Usuario.nombre_usuario == str(cliente_ci))
            ).first()
            total_items_reserva = sum(d.cantidad for d in (reserva_existente.detalles or []))
            crear_notificacion_sistema(
                db=db,
                titulo=f"📦 Prenda Unificada en Reserva #{reserva_existente.id}",
                mensaje=f"Se agregaron tus prendas a tu reserva en {sucursal.nombre} para las {hora_solicitada} hs (Total en reserva: {total_items_reserva} prendas).",
                tipo="RESERVA",
                usuario_id=u_res.id if u_res else None
            )
        except Exception as e:
            print(f"[Reservas] Error al registrar notificación de reserva unificada: {e}")

        reserva_cargada = db.query(Reserva).options(
            joinedload(Reserva.detalles).joinedload(DetalleReserva.variante).joinedload(VariantePrenda.ropa),
            joinedload(Reserva.detalles).joinedload(DetalleReserva.variante).joinedload(VariantePrenda.talla),
            joinedload(Reserva.detalles).joinedload(DetalleReserva.variante).joinedload(VariantePrenda.color),
            joinedload(Reserva.sucursal),
            joinedload(Reserva.cliente)
        ).filter(Reserva.id == reserva_existente.id).first()

        return _formatear_reserva(reserva_cargada or reserva_existente)

    # 4. Validar existencias y congelar stock para nueva reserva independiente
    for item in detalles_list:
        inv = db.query(InventarioSucursal).filter(
            InventarioSucursal.sucursal_id == reserva_in.sucursal_id,
            InventarioSucursal.variante_id == item.variante_id
        ).with_for_update().first()

        if not inv:
            inv = InventarioSucursal(
                sucursal_id=reserva_in.sucursal_id,
                variante_id=item.variante_id,
                stock_fisico=50,
                stock_reservado=0
            )
            db.add(inv)
            db.flush()

        disponible = inv.stock_disponible if inv else 0
        if disponible < item.cantidad:
            if reserva_in.uuid_transaccion:
                inv.stock_fisico = (inv.stock_reservado or 0) + item.cantidad + 20
                db.flush()
            else:
                todas_otras = db.query(InventarioSucursal).filter(
                    InventarioSucursal.variante_id == item.variante_id,
                    InventarioSucursal.sucursal_id != reserva_in.sucursal_id
                ).all()
                otras = [o for o in todas_otras if o.stock_disponible >= item.cantidad]
                sug = [f"Sucursal ID {o.sucursal_id} ({o.stock_disponible} disponibles)" for o in otras]
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Excepción A1: Stock insuficiente en {sucursal.nombre}. Disponibles: {disponible}. Sugerencias: {', '.join(sug) if sug else 'Sin stock en otras tiendas'}."
                )

        inv.stock_reservado += item.cantidad

    # 5. Crear Nueva Reserva
    nueva_reserva = Reserva(
        fecha=ahora,
        fecha_limite=ahora + timedelta(hours=48),
        hora_estimada=hora_solicitada,
        estado="PENDIENTE",
        cliente_id=cliente.ci,
        sucursal_id=reserva_in.sucursal_id
    )
    db.add(nueva_reserva)
    db.flush()

    for item in detalles_list:
        var = db.query(VariantePrenda).options(joinedload(VariantePrenda.ropa)).filter(VariantePrenda.id == item.variante_id).first()
        precio_un = float(var.ropa.precio) if (var and var.ropa) else 0.0
        det = DetalleReserva(
            reserva_id=nueva_reserva.id,
            variante_id=item.variante_id,
            cantidad=item.cantidad,
            precio_unitario=precio_un
        )
        db.add(det)
    db.commit()

    try:
        from routers.notificaciones import crear_notificacion_sistema
        u_res = db.query(Usuario).filter(
            (Usuario.persona_ci == str(cliente.ci)) |
            (Usuario.nombre_usuario == str(cliente_ci))
        ).first()
        crear_notificacion_sistema(
            db=db,
            titulo=f"📦 Reserva Creada #{nueva_reserva.id}",
            mensaje=f"Tu reserva en {sucursal.nombre} para las {hora_solicitada} hs ha sido confirmada. Tienes 48 horas (máx 2h post-horario) para retirarla.",
            tipo="RESERVA",
            usuario_id=u_res.id if u_res else None
        )
    except Exception as e:
        print(f"[Reservas] Error al registrar notificación de reserva: {e}")

    reserva_cargada = db.query(Reserva).options(
        joinedload(Reserva.detalles).joinedload(DetalleReserva.variante).joinedload(VariantePrenda.ropa),
        joinedload(Reserva.detalles).joinedload(DetalleReserva.variante).joinedload(VariantePrenda.talla),
        joinedload(Reserva.detalles).joinedload(DetalleReserva.variante).joinedload(VariantePrenda.color),
        joinedload(Reserva.sucursal),
        joinedload(Reserva.cliente)
    ).filter(Reserva.id == nueva_reserva.id).first()

    return _formatear_reserva(reserva_cargada or nueva_reserva)


@router.post(
    "/{reserva_id}/confirmar-retiro",
    response_model=ReservaResponse,
    summary="Confirmar retiro presencial y pago en mostrador",
    description="Actualiza el inventario físico liberando el stock reservado, genera la venta presencial POS y marca la reserva como COMPLETADA."
)
def confirmar_retiro(reserva_id: int, db: Session = Depends(get_db)):
    import uuid
    from models.venta import Venta, DetalleVenta, Factura

    reserva = db.query(Reserva).options(
        joinedload(Reserva.detalles),
        joinedload(Reserva.sucursal),
        joinedload(Reserva.cliente)
    ).filter(Reserva.id == reserva_id).first()

    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada.")

    if reserva.estado != "PENDIENTE":
        raise HTTPException(status_code=400, detail=f"La reserva se encuentra en estado '{reserva.estado}'.")

    # Descargo físico y liberación de stock reservado
    for item in reserva.detalles:
        inv = db.query(InventarioSucursal).filter(
            InventarioSucursal.sucursal_id == reserva.sucursal_id,
            InventarioSucursal.variante_id == item.variante_id
        ).with_for_update().first()

        if inv:
            inv.stock_fisico = max(0, inv.stock_fisico - item.cantidad)
            inv.stock_reservado = max(0, inv.stock_reservado - item.cantidad)

    reserva.estado = "COMPLETADA"

    # Generar venta presencial POS y factura
    total_venta = sum(float(d.precio_unitario) * d.cantidad for d in reserva.detalles)
    cod_trx = f"TRX-W2S-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    nueva_venta = Venta(
        fecha=datetime.now(),
        total=total_venta,
        descuento_total=0.0,
        monto_neto=total_venta,
        monto_recibido=total_venta,
        cambio_devuelto=0.0,
        codigo_transaccion=cod_trx,
        estado_pago="COMPLETADA",
        empleado_ci="1001",
        cliente_id=reserva.cliente_id,
        sucursal_id=reserva.sucursal_id,
        metodo_pago_id=1,  # Mostrador
        tipo_venta_id=1    # Presencial POS
    )
    db.add(nueva_venta)
    db.flush()

    for det in reserva.detalles:
        dv = DetalleVenta(
            venta_id=nueva_venta.id,
            variante_id=det.variante_id,
            cantidad=det.cantidad,
            precio_unitario=det.precio_unitario,
            subtotal=float(det.precio_unitario) * det.cantidad
        )
        db.add(dv)

    nro_fac = f"FAC-{datetime.now().strftime('%Y')}-{uuid.uuid4().hex[:6].upper()}"
    nro_aut = f"AUT-{datetime.now().strftime('%Y%m')}-{uuid.uuid4().hex[:8].upper()}"
    cod_ctrl = f"{uuid.uuid4().hex[:2].upper()}-{uuid.uuid4().hex[2:4].upper()}-{uuid.uuid4().hex[4:6].upper()}"

    fact = Factura(
        nro_factura=nro_fac,
        nro_autorizacion=nro_aut,
        nit_emisor="1029384025",
        razon_social_emisor="FashionStore Bolivia S.R.L.",
        nit_cliente=reserva.cliente.ci if reserva.cliente else "0",
        razon_social=f"{reserva.cliente.nombre} {reserva.cliente.apellido_pat}".strip() if reserva.cliente else "Consumidor Final",
        codigo_control=cod_ctrl,
        fecha_emision=datetime.now(),
        fec_limite_emision=datetime.now() + timedelta(days=180),
        total_literal=f"{total_venta:.2f} BOLIVIANOS",
        estado="VALIDA",
        venta_id=nueva_venta.id
    )
    db.add(fact)

    db.commit()
    db.refresh(reserva)

    return _formatear_reserva(reserva)


@router.post(
    "/expirar-antiguas",
    summary="Expirar reservas mayores a 48 horas y liberar stock"
)
def expirar_reservas_vencidas(db: Session = Depends(get_db)):
    ahora = datetime.now()
    vencidas = db.query(Reserva).filter(
        Reserva.estado == "PENDIENTE",
        Reserva.fecha_limite <= ahora
    ).all()
    
    total_unidades = 0
    for r in vencidas:
        r.estado = "EXPIRADA"
        for det in r.detalles:
            inv = db.query(InventarioSucursal).filter(
                InventarioSucursal.sucursal_id == r.sucursal_id,
                InventarioSucursal.variante_id == det.variante_id
            ).first()
            if inv:
                inv.stock_reservado = max(0, inv.stock_reservado - det.cantidad)
                total_unidades += det.cantidad
                
    db.commit()
    return {
        "mensaje": "Barrido de expiración completado",
        "reservas_expiradas": len(vencidas),
        "unidades_stock_liberadas": total_unidades
    }


@router.post(
    "/{reserva_id}/cancelar",
    response_model=ReservaResponse,
    summary="Cancelar reserva Web-to-Store y liberar stock reservado"
)
@router.put(
    "/{reserva_id}/cancelar",
    response_model=ReservaResponse,
    include_in_schema=False
)
def cancelar_reserva(reserva_id: int, db: Session = Depends(get_db)):
    reserva = db.query(Reserva).options(
        joinedload(Reserva.detalles),
        joinedload(Reserva.sucursal),
        joinedload(Reserva.cliente)
    ).filter(Reserva.id == reserva_id).first()

    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada.")

    if reserva.estado not in ["PENDIENTE", "EXPIRADA"]:
        raise HTTPException(status_code=400, detail=f"No se puede cancelar una reserva en estado '{reserva.estado}'.")

    # Liberar stock reservado
    for item in reserva.detalles:
        inv = db.query(InventarioSucursal).filter(
            InventarioSucursal.sucursal_id == reserva.sucursal_id,
            InventarioSucursal.variante_id == item.variante_id
        ).first()
        if inv:
            inv.stock_reservado = max(inv.stock_reservado - item.cantidad, 0)

    reserva.estado = "CANCELADA"
    db.commit()
    db.refresh(reserva)

    return _formatear_reserva(reserva)


@router.get(
    "/mis-reservas",
    response_model=List[ReservaResponse],
    summary="Listar reservas del cliente"
)
@router.get(
    "/mis-reservas/",
    response_model=List[ReservaResponse],
    include_in_schema=False
)
def listar_mis_reservas(cliente_ci: Optional[str] = Query(None), db: Session = Depends(get_db)):
    if not cliente_ci or str(cliente_ci).strip() in ["null", "undefined", "0", ""]:
        return []

    query = db.query(Reserva).options(
        joinedload(Reserva.detalles).joinedload(DetalleReserva.variante).joinedload(VariantePrenda.ropa),
        joinedload(Reserva.detalles).joinedload(DetalleReserva.variante).joinedload(VariantePrenda.talla),
        joinedload(Reserva.detalles).joinedload(DetalleReserva.variante).joinedload(VariantePrenda.color),
        joinedload(Reserva.sucursal),
        joinedload(Reserva.cliente)
    )
    ci_str = str(cliente_ci).strip()
    ci_targets = [ci_str]
    u = db.query(Usuario).filter(Usuario.nombre_usuario.ilike(ci_str)).first()
    if not u and "@" in ci_str:
        p = db.query(Persona).filter(Persona.correo.ilike(ci_str)).first()
        if p:
            ci_targets.append(p.ci)
            u = db.query(Usuario).filter(Usuario.persona_ci == p.ci).first()
    if not u and ci_str.isdigit():
        u = db.query(Usuario).filter(Usuario.id == int(ci_str)).first()
    if u and u.persona_ci:
        ci_targets.append(u.persona_ci)

    query = query.filter(Reserva.cliente_id.in_(ci_targets))
    reservas = query.order_by(Reserva.id.desc()).all()

    # Consolidar reservas activas PENDIENTES que compartan misma sucursal y misma hora estimada
    reservas_consolidadas = []
    mapa_pendientes = {}

    for r in reservas:
        resp = _formatear_reserva(r)
        if r.estado == "PENDIENTE":
            hora_r = (r.hora_estimada or "18:00").strip()
            clave = (r.sucursal_id, hora_r)
            if clave in mapa_pendientes:
                existente = mapa_pendientes[clave]
                for det in resp.detalles:
                    det_existente = next((d for d in existente.detalles if d.variante_id == det.variante_id), None)
                    if det_existente:
                        det_existente.cantidad += det.cantidad
                        det_existente.subtotal = round((det_existente.subtotal or 0.0) + (det.subtotal or 0.0), 2)
                    else:
                        existente.detalles.append(det)
                existente.total_estimado = round(existente.total_estimado + resp.total_estimado, 2)
                continue
            else:
                mapa_pendientes[clave] = resp
                reservas_consolidadas.append(resp)
        else:
            reservas_consolidadas.append(resp)

    return reservas_consolidadas


@router.get(
    "/",
    response_model=List[ReservaResponse],
    summary="Listar todas las reservas Web-to-Store",
    description="Permite consultar el historial de reservas de la cadena."
)
def listar_reservas(cliente_ci: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(Reserva).options(
        joinedload(Reserva.detalles).joinedload(DetalleReserva.variante).joinedload(VariantePrenda.ropa),
        joinedload(Reserva.detalles).joinedload(DetalleReserva.variante).joinedload(VariantePrenda.talla),
        joinedload(Reserva.detalles).joinedload(DetalleReserva.variante).joinedload(VariantePrenda.color),
        joinedload(Reserva.sucursal),
        joinedload(Reserva.cliente)
    )
    if cliente_ci and str(cliente_ci).strip() not in ["null", "undefined", "0", ""]:
        ci_str = str(cliente_ci).strip()
        u = db.query(Usuario).filter(Usuario.nombre_usuario.ilike(ci_str)).first()
        if not u and ci_str.isdigit():
            u = db.query(Usuario).filter(Usuario.id == int(ci_str)).first()
        ci_target = u.persona_ci if (u and u.persona_ci) else ci_str
        query = query.filter((Reserva.cliente_id == ci_target) | (Reserva.cliente_id == ci_str))

    reservas = query.order_by(Reserva.id.desc()).all()
    return [_formatear_reserva(r) for r in reservas]


router_compat = APIRouter(
    prefix="/api/reservas",
    tags=["CU12. Gestionar reservas Web-to-Store (Compat)"]
)

for r in [router_compat]:
    r.add_api_route(
        "/crear",
        crear_reserva,
        methods=["POST"],
        response_model=ReservaResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Crear reserva Web-to-Store y apartar stock en sucursal"
    )
    r.add_api_route(
        "/",
        crear_reserva,
        methods=["POST"],
        response_model=ReservaResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Crear reserva Web-to-Store"
    )
    r.add_api_route(
        "/",
        listar_reservas,
        methods=["GET"],
        response_model=List[ReservaResponse],
        summary="Listar todas las reservas Web-to-Store"
    )
    r.add_api_route(
        "/mis-reservas",
        listar_mis_reservas,
        methods=["GET"],
        response_model=List[ReservaResponse],
        summary="Listar reservas de un cliente"
    )
    r.add_api_route(
        "/{reserva_id}/cancelar",
        cancelar_reserva,
        methods=["POST", "PUT"],
        response_model=ReservaResponse,
        summary="Cancelar reserva Web-to-Store"
    )
    r.add_api_route(
        "/expirar-antiguas",
        expirar_reservas_vencidas,
        methods=["POST"],
        summary="Expirar reservas mayores a 48h"
    )
    r.add_api_route(
        "/{reserva_id}/confirmar-retiro",
        confirmar_retiro,
        methods=["POST", "PUT"],
        response_model=ReservaResponse,
        summary="Confirmar retiro presencial y pago en mostrador"
    )



