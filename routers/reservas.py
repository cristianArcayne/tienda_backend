"""
Router para CU12: Gestionar Reservas Web-to-Store.
Alineado fielmente con RESERVA, DETALLE_RESERVA, CLIENTE y SUCURSAL del Diagrama UML.
"""
from datetime import date, datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
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

    return ReservaResponse(
        id=reserva.id,
        fecha=reserva.fecha,
        fecha_limite=reserva.fecha_limite,
        hora_estimada=reserva.hora_estimada,
        estado=reserva.estado,
        cliente_id=reserva.cliente_id,
        sucursal_id=reserva.sucursal_id,
        sucursal_nombre=reserva.sucursal.nombre if reserva.sucursal else None,
        cliente_nombre=f"{reserva.cliente.nombre} {reserva.cliente.apellido_pat}".strip() if (reserva.cliente and hasattr(reserva.cliente, 'apellido_pat')) else (reserva.cliente.nombre if reserva.cliente else None),
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

    # 1. Validar sucursal y cliente
    sucursal = db.query(Sucursal).filter(Sucursal.id == reserva_in.sucursal_id).first()
    if not sucursal:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada.")

    cliente_ci = str(reserva_in.cliente_id).strip() if reserva_in.cliente_id else "admin"

    # Buscar primero si el cliente ya existe con ese código directamente (ej: 'admin', '2001')
    cliente = db.query(Cliente).filter(Cliente.ci == cliente_ci).first()

    if not cliente:
        # Buscar usuario correspondiente
        u = db.query(Usuario).filter(Usuario.nombre_usuario == cliente_ci).first()
        if not u and cliente_ci.isdigit():
            u = db.query(Usuario).filter(Usuario.id == int(cliente_ci)).first()

        if u and u.persona_ci:
            cliente = db.query(Cliente).filter(Cliente.ci == u.persona_ci).first()
            if not cliente:
                # Si la persona existe pero falta en la tabla clientes, enlazarla
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
            cliente = Cliente(
                ci=cliente_ci,
                nombre=cliente_ci.capitalize(),
                apellido_pat="Web",
                correo=f"cliente_{cliente_ci}@fashionstore.com",
                telefono="+591 70000000",
                tipo_persona="CLIENTE"
            )
            db.add(cliente)
            db.flush()

    # 2. Validar existencias y congelar stock
    for item in detalles_list:
        inv = db.query(InventarioSucursal).filter(
            InventarioSucursal.sucursal_id == reserva_in.sucursal_id,
            InventarioSucursal.variante_id == item.variante_id
        ).with_for_update().first()

        disponible = inv.stock_disponible if inv else 0
        if not inv or disponible < item.cantidad:
            # Buscar sucursales alternativas
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

    # 3. Crear Reserva
    ahora = datetime.now()
    nueva_reserva = Reserva(
        fecha=ahora,
        fecha_limite=ahora + timedelta(hours=48),
        hora_estimada=reserva_in.hora_estimada or "18:00",
        estado="PENDIENTE",
        cliente_id=cliente.ci,
        sucursal_id=reserva_in.sucursal_id
    )
    db.add(nueva_reserva)
    db.flush()

    for item in reserva_in.detalles:
        var = db.query(VariantePrenda).options(joinedload(VariantePrenda.ropa)).filter(VariantePrenda.id == item.variante_id).first()
        precio_un = float(var.ropa.precio) if (var and var.ropa) else 0.0
        det = DetalleReserva(
            reserva_id=nueva_reserva.id,
            variante_id=item.variante_id,
            cantidad=item.cantidad,
            precio_unitario=precio_un
        )
    db.commit()

    try:
        from routers.notificaciones import crear_notificacion_sistema
        crear_notificacion_sistema(
            db=db,
            titulo=f"📦 Reserva Creada #{nueva_reserva.id}",
            mensaje=f"Tu reserva en {sucursal.nombre} ha sido confirmada. Tienes 48 horas para retirarla.",
            tipo="RESERVA"
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
def listar_mis_reservas(cliente_ci: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Reserva).options(
        joinedload(Reserva.detalles).joinedload(DetalleReserva.variante).joinedload(VariantePrenda.ropa),
        joinedload(Reserva.detalles).joinedload(DetalleReserva.variante).joinedload(VariantePrenda.talla),
        joinedload(Reserva.detalles).joinedload(DetalleReserva.variante).joinedload(VariantePrenda.color),
        joinedload(Reserva.sucursal),
        joinedload(Reserva.cliente)
    )
    if cliente_ci:
        u = db.query(Usuario).filter(Usuario.nombre_usuario == cliente_ci).first()
        if not u and cliente_ci.isdigit():
            u = db.query(Usuario).filter(Usuario.id == int(cliente_ci)).first()
        ci_target = u.persona_ci if (u and u.persona_ci) else cliente_ci
        query = query.filter((Reserva.cliente_id == ci_target) | (Reserva.cliente_id == cliente_ci))
    reservas = query.order_by(Reserva.id.desc()).all()
    return [_formatear_reserva(r) for r in reservas]


@router.get(
    "/",
    response_model=List[ReservaResponse],
    summary="Listar todas las reservas Web-to-Store",
    description="Permite consultar el historial de reservas de la cadena."
)
def listar_reservas(db: Session = Depends(get_db)):
    reservas = db.query(Reserva).options(
        joinedload(Reserva.detalles).joinedload(DetalleReserva.variante).joinedload(VariantePrenda.ropa),
        joinedload(Reserva.detalles).joinedload(DetalleReserva.variante).joinedload(VariantePrenda.talla),
        joinedload(Reserva.detalles).joinedload(DetalleReserva.variante).joinedload(VariantePrenda.color),
        joinedload(Reserva.sucursal),
        joinedload(Reserva.cliente)
    ).order_by(Reserva.id.desc()).all()

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



