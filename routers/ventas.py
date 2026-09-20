"""
Router para CU14 & CU15: Procesamiento de Ventas Omnicanal (POS & E-commerce) y Facturación.
Alineado fielmente con VENTA, DETALLE_VENTA, FACTURA, METODO_PAGO y TIPO_VENTA del Diagrama UML.
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models.venta import Venta, DetalleVenta, Factura, MetodoPago, TipoVenta
from models.seguridad_persona import Empleado, Cliente, Persona, Usuario
from models.catalogo import VariantePrenda, Ropa, Promocion, PromocionRopa
from models.sucursal import Sucursal, InventarioSucursal
from models.reserva import Reserva
from schemas.venta import (
    VentaPOSCreate,
    VentaEcommerceCreate,
    VentaResponse,
    DetalleVentaResponse,
    FacturaResponse,
    MetodoPagoResponse,
    TipoVentaResponse,
    ItemVentaCreate
)

router = APIRouter(
    prefix="/api/v1/ventas"
)

compat_router = APIRouter(
    prefix="/api/ventas",
    include_in_schema=False
)


def _calcular_precio_unitario_promo(ropa: Optional[Ropa], precio_ajustado: Optional[float] = None) -> tuple[float, float, float]:
    from datetime import date
    hoy = date.today()
    precio_base = float(precio_ajustado or (ropa.precio if (ropa and ropa.precio is not None) else 0.0))
    mejor_descuento = 0.0
    if ropa and getattr(ropa, 'promociones_asociadas', None):
        for pr in ropa.promociones_asociadas:
            if pr.estado and pr.estado.upper() == "ACTIVA" and pr.promocion:
                p = pr.promocion
                if getattr(p, "activo", True):
                    f_ini = p.fecha_inicio.date() if hasattr(p.fecha_inicio, "date") else p.fecha_inicio
                    f_fin = p.fecha_fin.date() if hasattr(p.fecha_fin, "date") else p.fecha_fin
                    if f_ini and f_fin and (f_ini <= hoy <= f_fin):
                        mejor_descuento = max(mejor_descuento, float(p.porcentaje_descuento))
    precio_promo = round(precio_base * (1.0 - (mejor_descuento / 100.0)), 2) if mejor_descuento > 0 else precio_base
    return precio_base, mejor_descuento, precio_promo


def _formatear_venta(venta: Venta) -> VentaResponse:
    detalles_resp = [
        DetalleVentaResponse(
            id=d.id,
            variante_id=d.variante_id,
            cantidad=d.cantidad,
            subtotal=float(d.subtotal),
            precio_unitario=float(d.precio_unitario) if d.precio_unitario is not None else (float(d.variante.ropa.precio) if (d.variante and d.variante.ropa) else 0.0),
            descuento=float(d.descuento) if d.descuento is not None else 0.0,
            cod_barra=d.variante.cod_barra if d.variante else None,
            prenda_nombre=d.variante.ropa.nombre if (d.variante and d.variante.ropa) else None,
            talla=d.variante.talla.medida if (d.variante and d.variante.talla) else "Única",
            color=d.variante.color.nombre if (d.variante and d.variante.color) else "Estándar"
        )
        for d in (venta.detalles or [])
    ]

    factura_resp = None
    if venta.factura:
        factura_resp = FacturaResponse(
            id=venta.factura.id,
            nro_factura=venta.factura.nro_factura,
            nit_cliente=venta.factura.nit_cliente,
            razon_social=venta.factura.razon_social,
            fecha_emision=venta.factura.fecha_emision,
            nro_autorizacion=venta.factura.nro_autorizacion,
            codigo_control=venta.factura.codigo_control,
            total_literal=venta.factura.total_literal
        )

    cli_nom = "Consumidor Final"
    if venta.cliente:
        cli_nom = f"{venta.cliente.nombre} {getattr(venta.cliente, 'apellido_pat', '')}".strip()
    elif venta.factura and venta.factura.razon_social and venta.factura.razon_social != "Sin Nombre":
        cli_nom = venta.factura.razon_social

    emp_nom = None
    if venta.empleado:
        emp_nom = f"{venta.empleado.nombre} {getattr(venta.empleado, 'apellido_pat', '')}".strip()

    return VentaResponse(
        id=venta.id,
        fecha=venta.fecha,
        total=float(venta.total),
        codigo_transaccion=venta.codigo_transaccion,
        estado_pago=venta.estado_pago,
        empleado_id=venta.empleado_ci,
        cliente_id=venta.cliente_id,
        sucursal_id=venta.sucursal_id,
        metodo_pago_id=venta.metodo_pago_id,
        tipo_venta_id=venta.tipo_venta_id,
        sucursal_nombre=venta.sucursal.nombre if venta.sucursal else None,
        empleado_nombre=emp_nom,
        cliente_nombre=cli_nom,
        metodo_pago_nombre=venta.metodo_pago.nombre if venta.metodo_pago else None,
        tipo_venta_nombre=venta.tipo_venta.nombre if venta.tipo_venta else None,
        detalles=detalles_resp,
        factura=factura_resp,
        monto_recibido=float(venta.monto_recibido) if venta.monto_recibido is not None else None,
        cambio_devuelto=float(venta.cambio_devuelto) if venta.cambio_devuelto is not None else None,
        descuento_total=float(venta.descuento_total) if venta.descuento_total is not None else 0.0,
        monto_neto=float(venta.monto_neto) if venta.monto_neto is not None else float(venta.total)
    )


def _ejecutar_venta_pos_core(
    db: Session,
    sucursal_id: int,
    metodo_pago_id: int,
    items: List[ItemVentaCreate],
    empleado_ci: Optional[str] = "1001",
    cliente_ci: Optional[str] = None,
    nit_cliente: Optional[str] = "0",
    razon_social: Optional[str] = "Sin Nombre",
    monto_recibido: Optional[float] = None,
    descuento_total: Optional[float] = 0.0,
    tipo_venta_id: Optional[int] = None
) -> Venta:
    # 1. Validar sucursal
    sucursal = db.query(Sucursal).filter(Sucursal.id == sucursal_id).first()
    if not sucursal:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada.")

    # 2. Validar o asignar empleado cajero
    empleado = None
    if empleado_ci:
        empleado = db.query(Empleado).filter(Empleado.ci == str(empleado_ci)).first()
    if not empleado:
        empleado = db.query(Empleado).first()

    # 3. Validar cliente (o consumidor final)
    cliente = None
    if cliente_ci and cliente_ci not in ["0", "null", "undefined", "anonymous"]:
        cliente = db.query(Cliente).filter(Cliente.ci == str(cliente_ci)).first()
        if not cliente:
            persona = db.query(Persona).filter(Persona.ci == str(cliente_ci)).first()
            if persona:
                cliente = Cliente(
                    ci=persona.ci,
                    nombre=persona.nombre,
                    apellido_pat=persona.apellido_pat,
                    apellido_mat=persona.apellido_mat,
                    correo=persona.correo,
                    telefono=persona.telefono,
                    tipo_persona="CLIENTE"
                )
                db.add(cliente)
                db.flush()

    # 4. Tipo de Venta
    if not tipo_venta_id:
        tipo_pos = db.query(TipoVenta).filter(TipoVenta.nombre.ilike("%POS%")).first()
        tipo_venta_id = tipo_pos.id if tipo_pos else 1

    es_digital = tipo_venta_id == 2 or (db.query(TipoVenta).filter(TipoVenta.id == tipo_venta_id).first() and "Digital" in db.query(TipoVenta).filter(TipoVenta.id == tipo_venta_id).first().nombre)

    # 5. Método de Pago
    metodo = db.query(MetodoPago).filter(MetodoPago.id == metodo_pago_id).first()
    if not metodo:
        metodo = db.query(MetodoPago).first()
        metodo_pago_id = metodo.id if metodo else 1

    # 6. Validar existencias y calcular totales
    total_bruto = 0.0
    ahorro_promos = 0.0
    lineas = []

    for item in items:
        var = db.query(VariantePrenda).options(
            joinedload(VariantePrenda.ropa).joinedload(Ropa.promociones_asociadas).joinedload(PromocionRopa.promocion)
        ).filter(VariantePrenda.id == item.variante_id).first()
        if not var:
            raise HTTPException(status_code=404, detail=f"Variante #{item.variante_id} no encontrada.")

        inv = db.query(InventarioSucursal).filter(
            InventarioSucursal.sucursal_id == sucursal_id,
            InventarioSucursal.variante_id == item.variante_id
        ).with_for_update().first()

        disponible = inv.stock_disponible if inv else 0
        if not inv or disponible < item.cantidad:
            if es_digital:
                # Enrutamiento omnicanal: despachar desde la sucursal con inventario disponible
                inv_alt = db.query(InventarioSucursal).filter(
                    InventarioSucursal.variante_id == item.variante_id,
                    (InventarioSucursal.stock_fisico - InventarioSucursal.stock_reservado) >= item.cantidad
                ).order_by((InventarioSucursal.stock_fisico - InventarioSucursal.stock_reservado).desc()).with_for_update().first()
                if inv_alt:
                    inv = inv_alt
                    disponible = inv.stock_disponible
                    sucursal_id = inv.sucursal_id

            if not inv or disponible < item.cantidad:
                canal = "Digital / E-commerce" if es_digital else "Mostrador POS"
                total_cadena = sum(
                    i.stock_disponible for i in db.query(InventarioSucursal).filter(InventarioSucursal.variante_id == item.variante_id).all()
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Excepción A1 (Stock Insuficiente en {canal}): Solicitadas {item.cantidad} unidades de {var.ropa.nombre if var.ropa else 'Prenda'}, disponibles: {disponible} (Total cadena: {total_cadena})."
                )

        # DESCARGO FÍSICO INMEDIATO DE ALMACÉN
        inv.stock_fisico -= item.cantidad

        p_base, p_desc, p_promo = _calcular_precio_unitario_promo(var.ropa if var else None, float(var.precio_ajustado) if (var and var.precio_ajustado) else None)
        precio_un = float(item.precio_unitario) if (item.precio_unitario is not None and float(item.precio_unitario) > 0) else p_promo
        subt = round(precio_un * item.cantidad, 2)
        total_bruto += subt
        desc_linea = float(item.descuento or 0.0)
        if desc_linea == 0.0 and p_desc > 0:
            desc_linea = round((p_base - p_promo) * item.cantidad, 2)
            ahorro_promos += desc_linea

        lineas.append({
            "variante_id": item.variante_id,
            "cantidad": item.cantidad,
            "precio_unitario": precio_un,
            "subtotal": subt,
            "descuento": desc_linea
        })

    total_bruto = round(total_bruto, 2)
    desc_tot = round(float(descuento_total or 0.0), 2)
    monto_neto = max(0.0, round(total_bruto - desc_tot, 2))

    # Cálculo de cambio devuelto
    cambio = 0.0
    if monto_recibido is not None and monto_recibido > 0:
        if monto_recibido < monto_neto:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Monto recibido (Bs. {monto_recibido}) es inferior al total a pagar (Bs. {monto_neto})."
            )
        cambio = round(monto_recibido - monto_neto, 2)
    else:
        monto_recibido = monto_neto

    # 7. Registrar Venta
    ahora = datetime.now()
    prefijo_trx = "TRX-ECOM" if es_digital else "TRX-POS"
    codigo_trx = f"{prefijo_trx}-{ahora.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    nueva_venta = Venta(
        fecha=ahora,
        total=total_bruto,
        descuento_total=desc_tot,
        monto_neto=monto_neto,
        monto_recibido=monto_recibido,
        cambio_devuelto=cambio,
        codigo_transaccion=codigo_trx,
        estado_pago="COMPLETADA",
        empleado_ci=empleado.ci if empleado else None,
        cliente_id=cliente.ci if cliente else None,
        sucursal_id=sucursal_id,
        metodo_pago_id=metodo_pago_id,
        tipo_venta_id=tipo_venta_id
    )
    db.add(nueva_venta)
    db.flush()

    for l in lineas:
        det = DetalleVenta(
            venta_id=nueva_venta.id,
            variante_id=l["variante_id"],
            cantidad=l["cantidad"],
            precio_unitario=l["precio_unitario"],
            subtotal=l["subtotal"],
            descuento=l["descuento"]
        )
        db.add(det)

    # 8. Emitir Factura Fiscal
    prefijo_fac = "FAC-ECOM" if es_digital else "FAC-POS"
    nro_fac = f"{prefijo_fac}-{ahora.strftime('%Y')}-{uuid.uuid4().hex[:6].upper()}"
    nro_aut = f"AUT-{ahora.strftime('%Y%m')}-{uuid.uuid4().hex[:8].upper()}"
    cod_ctrl = f"{uuid.uuid4().hex[:2].upper()}-{uuid.uuid4().hex[2:4].upper()}-{uuid.uuid4().hex[4:6].upper()}"
    
    db.add(Factura(
        nro_factura=nro_fac,
        nro_autorizacion=nro_aut,
        nit_emisor="1029384025",
        razon_social_emisor="FashionStore Bolivia S.R.L.",
        nit_cliente=nit_cliente or "0",
        razon_social=razon_social or (f"{cliente.nombre} {cliente.apellido_pat}" if cliente else "Sin Nombre"),
        codigo_control=cod_ctrl,
        fecha_emision=ahora,
        fec_limite_emision=ahora + timedelta(days=180),
        total_literal=f"{monto_neto:.2f} BOLIVIANOS",
        estado="VALIDA",
        venta_id=nueva_venta.id
    ))

    db.commit()

    # Emitir notificación para móviles y web
    try:
        from routers.notificaciones import crear_notificacion_sistema
        tipo_nombre = "E-commerce" if tipo_venta_id == 2 else "POS Tienda"
        crear_notificacion_sistema(
            db=db,
            titulo=f"🛍️ Compra Confirmada #{nueva_venta.id}",
            mensaje=f"Tu compra ({tipo_nombre}) por Bs. {nueva_venta.total_final:.2f} ha sido procesada con éxito.",
            tipo="COMPRA"
        )
    except Exception as e:
        print(f"[Ventas] Error al registrar notificación de venta: {e}")

    venta_cargada = db.query(Venta).options(
        joinedload(Venta.sucursal),
        joinedload(Venta.empleado),
        joinedload(Venta.cliente),
        joinedload(Venta.metodo_pago),
        joinedload(Venta.tipo_venta),
        joinedload(Venta.factura),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.ropa),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.talla),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.color)
    ).filter(Venta.id == nueva_venta.id).first()

    return venta_cargada or nueva_venta


# ==============================================================================
# CU14: PROCESAR VENTAS FÍSICAS EN POS
# ==============================================================================

@router.post(
    "/pos",
    response_model=VentaResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["CU14. Procesar ventas físicas en POS"],
    summary="Procesar venta física en POS de sucursal",
    description="Registra la venta en caja, descuenta el stock físico real y emite la Factura fiscal."
)
def procesar_venta_pos(venta_in: VentaPOSCreate, db: Session = Depends(get_db)):
    venta = _ejecutar_venta_pos_core(
        db=db,
        sucursal_id=venta_in.sucursal_id,
        metodo_pago_id=venta_in.metodo_pago_id or 1,
        items=venta_in.items,
        empleado_ci=str(venta_in.empleado_id) if venta_in.empleado_id else "1001",
        cliente_ci=str(venta_in.cliente_id) if venta_in.cliente_id else None,
        nit_cliente=venta_in.nit_cliente,
        razon_social=venta_in.razon_social,
        monto_recibido=venta_in.monto_recibido,
        descuento_total=venta_in.descuento_total
    )
    return _formatear_venta(venta)


# ==============================================================================
# CU15: PROCESAR VENTAS DIGITALES (E-COMMERCE)
# ==============================================================================

@router.post(
    "/ecommerce",
    response_model=VentaResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["CU15. Procesar ventas digitales (E-commerce)"],
    summary="Procesar venta digital en E-commerce Web / Móvil"
)
@router.post("/ecommerce/", response_model=VentaResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def procesar_venta_ecommerce(venta_in: VentaEcommerceCreate, db: Session = Depends(get_db)):
    cliente_str = str(venta_in.cliente_id).strip() if venta_in.cliente_id else "2001"
    cliente = db.query(Cliente).filter(Cliente.ci == cliente_str).first()
    if not cliente:
        persona = db.query(Persona).filter(Persona.ci == cliente_str).first()
        if persona:
            cliente = Cliente(ci=persona.ci, nombre=persona.nombre, apellido_pat=persona.apellido_pat, correo=persona.correo, tipo_persona="CLIENTE")
            db.add(cliente)
            db.flush()
        else:
            cliente = db.query(Cliente).first()
            if not cliente:
                cliente = Cliente(ci=cliente_str, nombre="Cliente", apellido_pat="Tienda", correo="cliente@fashionstore.com", tipo_persona="CLIENTE")
                db.add(cliente)
                db.flush()

    tipo_ecom = db.query(TipoVenta).filter(TipoVenta.nombre.ilike("%Digital%")).first()
    tipo_venta_id = tipo_ecom.id if tipo_ecom else 2

    # Resolver método de pago
    metodo_id = venta_in.metodo_pago_id or 1
    if venta_in.metodo_pago:
        m_str = venta_in.metodo_pago.lower()
        if "qr" in m_str:
            metodo_qr = db.query(MetodoPago).filter(MetodoPago.nombre.ilike("%QR%")).first()
            metodo_id = metodo_qr.id if metodo_qr else 3
        elif "efectivo" in m_str:
            metodo_ef = db.query(MetodoPago).filter(MetodoPago.nombre.ilike("%Efectivo%")).first()
            metodo_id = metodo_ef.id if metodo_ef else 1
        else:
            metodo_tj = db.query(MetodoPago).filter(MetodoPago.nombre.ilike("%Tarjeta%")).first()
            metodo_id = metodo_tj.id if metodo_tj else 2

    # Resolver sucursal
    suc_id = venta_in.sucursal_id or 1
    suc = db.query(Sucursal).filter(Sucursal.id == suc_id).first()
    if not suc:
        suc_first = db.query(Sucursal).first()
        suc_id = suc_first.id if suc_first else 1

    # Obtener items de venta (directos o desde carrito en base de datos)
    items_create: List[ItemVentaCreate] = []
    carrito = None

    if venta_in.items and len(venta_in.items) > 0:
        items_create = [
            ItemVentaCreate(
                variante_id=it.variante_id,
                cantidad=it.cantidad,
                precio_unitario=it.precio_unitario,
                descuento=it.descuento or 0.0
            ) for it in venta_in.items
        ]
    else:
        from models.carrito import CarritoCompra, DetalleCarritoCompra
        carrito = db.query(CarritoCompra).options(
            joinedload(CarritoCompra.detalles).joinedload(DetalleCarritoCompra.variante).joinedload(VariantePrenda.ropa).joinedload(Ropa.promociones_asociadas).joinedload(PromocionRopa.promocion)
        ).filter(CarritoCompra.cliente_id == cliente.ci).first()

        if carrito and carrito.detalles:
            items_create = [
                ItemVentaCreate(
                    variante_id=d.variante_id,
                    cantidad=d.cantidad,
                    precio_unitario=_calcular_precio_unitario_promo(d.variante.ropa if d.variante else None, float(d.variante.precio_ajustado) if (d.variante and d.variante.precio_ajustado) else None)[2]
                )
                for d in carrito.detalles
            ]

    if not items_create:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se encontraron prendas en el carrito para procesar el pago."
        )

    # Excepción A1: Simulación de fallo de pasarela externa
    if venta_in.token_pasarela and ("rechazad" in venta_in.token_pasarela.lower() or "fallid" in venta_in.token_pasarela.lower()):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Pago rechazado por la pasarela de pagos externa (fondos insuficientes o tarjeta inválida)."
        )

    venta = _ejecutar_venta_pos_core(
        db=db,
        sucursal_id=suc_id,
        metodo_pago_id=metodo_id,
        items=items_create,
        empleado_ci="1001",
        cliente_ci=cliente.ci,
        nit_cliente=venta_in.nit_cliente or "0",
        razon_social=venta_in.razon_social or f"{cliente.nombre} {cliente.apellido_pat}",
        monto_recibido=None,
        descuento_total=0.0,
        tipo_venta_id=tipo_venta_id
    )

    # Vaciar carrito de base de datos si existía
    if carrito:
        from models.carrito import DetalleCarritoCompra
        db.query(DetalleCarritoCompra).filter(DetalleCarritoCompra.carrito_id == carrito.id).delete()
        db.commit()

    return _formatear_venta(venta)


# ==============================================================================
# CONSULTAS GENERALES
# ==============================================================================

@router.get(
    "/metodos-pago",
    response_model=List[MetodoPagoResponse],
    summary="Listar métodos de pago disponibles"
)
def listar_metodos_pago(db: Session = Depends(get_db)):
    return db.query(MetodoPago).all()


@router.get(
    "/tipos-venta",
    response_model=List[TipoVentaResponse],
    summary="Listar tipos de venta"
)
def listar_tipos_venta(db: Session = Depends(get_db)):
    return db.query(TipoVenta).all()


@router.get(
    "/",
    response_model=List[VentaResponse],
    summary="Historial general de ventas"
)
def listar_ventas(
    sucursal_id: Optional[int] = Query(None, description="Filtrar por ID de sucursal física"),
    db: Session = Depends(get_db)
):
    query = db.query(Venta).options(
        joinedload(Venta.sucursal),
        joinedload(Venta.empleado),
        joinedload(Venta.cliente),
        joinedload(Venta.metodo_pago),
        joinedload(Venta.tipo_venta),
        joinedload(Venta.factura),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.ropa),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.talla),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.color)
    )

    if isinstance(sucursal_id, (int, float)) or (isinstance(sucursal_id, str) and sucursal_id.isdigit()):
        query = query.filter(Venta.sucursal_id == int(sucursal_id))

    ventas = query.order_by(Venta.id.desc()).all()
    return [_formatear_venta(v) for v in ventas]


@router.get(
    "/{venta_id}",
    response_model=VentaResponse,
    summary="Consultar venta y factura fiscal por ID"
)
def obtener_venta(venta_id: int, db: Session = Depends(get_db)):
    venta = db.query(Venta).options(
        joinedload(Venta.sucursal),
        joinedload(Venta.empleado),
        joinedload(Venta.cliente),
        joinedload(Venta.metodo_pago),
        joinedload(Venta.tipo_venta),
        joinedload(Venta.factura),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.ropa),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.talla),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.color)
    ).filter(Venta.id == venta_id).first()

    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada.")

    return _formatear_venta(venta)


# ==============================================================================
# COMPATIBILIDAD CON FRONTEND ANGULAR (/api/ventas)
# ==============================================================================

class VentaFrontendCreateDto(BaseModel):
    tipo: Optional[str] = "presencial"
    estado: Optional[str] = "completado"
    precio_total: Optional[float] = None
    descuento_total: Optional[float] = 0.0
    usuario_id: Optional[Union[str, int]] = "1001"
    sucursal_id: Optional[int] = 1
    metodo_pago_id: Optional[int] = 1
    metodo: Optional[str] = "efectivo"
    nit_cliente: Optional[str] = "0"
    razon_social: Optional[str] = "Sin Nombre"
    monto_recibido: Optional[float] = None
    detalles: List[dict] = []


@compat_router.post("/")
def crear_venta_compat_frontend(body: VentaFrontendCreateDto, db: Session = Depends(get_db)):
    # Mapear método de pago de string a ID
    metodo_id = body.metodo_pago_id or 1
    if body.metodo:
        m_str = body.metodo.lower()
        if "tarjeta" in m_str:
            metodo_id = 2
        elif "qr" in m_str:
            metodo_id = 3
        else:
            metodo_id = 1

    items_create = [
        ItemVentaCreate(
            variante_id=int(d.get("variante_producto_id") or d.get("variante_id") or d.get("variante")),
            cantidad=int(d.get("cantidad", 1)),
            precio_unitario=float(d.get("precio_unitario", 0.0)) if d.get("precio_unitario") else None
        )
        for d in body.detalles
    ]

    es_digital = body.tipo and "digital" in body.tipo.lower()
    tipo_id = 2 if es_digital else 1

    suc_id = body.sucursal_id or 1

    # Determinar cliente y empleado
    if es_digital:
        # En venta digital E-commerce, el cliente es la cuenta compradora
        c_raw = str(body.usuario_id or "admin")
        target_cliente = "admin" if c_raw in ["1", "1001", "admin"] else c_raw
        # Asegurar que exista como Cliente
        cli_obj = db.query(Cliente).filter(Cliente.ci == target_cliente).first()
        if not cli_obj:
            cli_obj = db.query(Cliente).first()
            target_cliente = cli_obj.ci if cli_obj else "admin"
        target_empleado = "1001"
    else:
        target_empleado = str(body.usuario_id) if body.usuario_id else "1001"
        target_cliente = str(body.usuario_id) if str(body.usuario_id) not in ["1001", "1002"] else None

    venta = _ejecutar_venta_pos_core(
        db=db,
        sucursal_id=suc_id,
        metodo_pago_id=metodo_id,
        items=items_create,
        empleado_ci=target_empleado,
        cliente_ci=target_cliente,
        nit_cliente=body.nit_cliente,
        razon_social=body.razon_social,
        monto_recibido=body.monto_recibido,
        descuento_total=body.descuento_total or 0.0,
        tipo_venta_id=tipo_id
    )

    resp = _formatear_venta(venta)
    return {
        "id": resp.id,
        "tipo": "Presencial" if resp.tipo_venta_id == 1 else "Digital",
        "estado": "Completada",
        "precio_total": f"{resp.monto_neto:.2f}",
        "descuento_total": f"{resp.descuento_total:.2f}",
        "fecha": resp.fecha.isoformat() if resp.fecha else "",
        "nro_comprobante": resp.codigo_transaccion,
        "nro_factura": resp.factura.nro_factura if resp.factura else "",
        "nit_cliente": resp.factura.nit_cliente if resp.factura else "0",
        "razon_social": resp.factura.razon_social if resp.factura else "Sin Nombre",
        "cambio_devuelto": resp.cambio_devuelto
    }


class CheckoutFrontendDto(BaseModel):
    cliente_id: Optional[Union[str, int]] = None
    usuario_id: Optional[Union[str, int]] = None
    sucursal_id: Optional[int] = 1
    metodo_pago_id: Optional[int] = 1
    metodo: Optional[str] = "tarjeta"
    nit_cliente: Optional[str] = "0"
    razon_social: Optional[str] = "Sin Nombre"
    direccion_envio: Optional[str] = None


@compat_router.post("/checkout")
@compat_router.post("/checkout/")
@compat_router.post("/ecommerce")
@compat_router.post("/ecommerce/")
def checkout_ecommerce_compat(body: CheckoutFrontendDto, db: Session = Depends(get_db)):
    c_id = body.cliente_id or body.usuario_id or "2001"
    
    metodo_id = body.metodo_pago_id or 1
    if body.metodo:
        m_str = body.metodo.lower()
        if "qr" in m_str:
            metodo_id = 3
        elif "efectivo" in m_str:
            metodo_id = 1
        else:
            metodo_id = 2  # Tarjeta / Pasarela
            
    v_ecom = VentaEcommerceCreate(
        cliente_id=str(c_id),
        sucursal_id=body.sucursal_id or 1,
        metodo_pago_id=metodo_id,
        nit_cliente=body.nit_cliente or "0",
        razon_social=body.razon_social or "Sin Nombre",
        direccion_envio=body.direccion_envio
    )
    
    resp = procesar_venta_ecommerce(v_ecom, db)
    return {
        "success": True,
        "id": resp.id,
        "tipo": "Digital / E-commerce",
        "estado": "Completada",
        "precio_total": f"{resp.total:.2f}",
        "nro_comprobante": resp.codigo_transaccion,
        "nro_factura": resp.factura.nro_factura if resp.factura else "",
        "nit_cliente": resp.factura.nit_cliente if resp.factura else "0",
        "razon_social": resp.factura.razon_social if resp.factura else "Sin Nombre",
        "mensaje": "¡Pago procesado y compra E-commerce registrada exitosamente con Factura Fiscal!"
    }


@router.get("/historial-cliente")
@router.get("/historial-cliente/")
@compat_router.get("/historial-cliente")
@compat_router.get("/historial-cliente/")
def listar_historial_cliente(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    estado: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Venta).options(
        joinedload(Venta.tipo_venta),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.ropa)
    )

    if estado:
        est_l = estado.strip().lower()
        if "complet" in est_l or "pagad" in est_l:
            query = query.filter(Venta.estado_pago.in_(["COMPLETADA", "PAGADA"]))
        elif "cancel" in est_l or "anul" in est_l or "fall" in est_l:
            query = query.filter(Venta.estado_pago.in_(["ANULADA", "FALLIDA"]))
        elif "pend" in est_l:
            query = query.filter(Venta.estado_pago == "PENDIENTE")

    if fecha_desde:
        try:
            fd = datetime.fromisoformat(fecha_desde.replace("Z", "+00:00"))
            query = query.filter(Venta.fecha >= fd)
        except Exception:
            pass

    if fecha_hasta:
        try:
            fh = datetime.fromisoformat(fecha_hasta.replace("Z", "+00:00"))
            query = query.filter(Venta.fecha <= fh)
        except Exception:
            pass

    total = query.count()
    offset = (page - 1) * page_size
    ventas = query.order_by(Venta.fecha.desc()).offset(offset).limit(page_size).all()

    results = []
    for v in ventas:
        estado_out = "completado" if v.estado_pago in ["COMPLETADA", "PAGADA"] else ("cancelado" if v.estado_pago in ["ANULADA", "FALLIDA"] else "pendiente")
        prods = [
            {
                "id": d.id,
                "producto_id": d.variante.ropa_id if (d.variante and d.variante.ropa_id) else d.variante_id,
                "producto_nombre": d.variante.ropa.nombre if (d.variante and d.variante.ropa) else f"Prenda #{d.variante_id}",
                "variante_id": d.variante_id,
                "variante_sku": d.variante.sku if (d.variante and d.variante.sku) else f"SKU-{d.variante_id}",
                "cantidad": d.cantidad,
                "precio_unitario": float(d.precio_unitario if d.precio_unitario is not None else (d.variante.ropa.precio if (d.variante and d.variante.ropa) else 0.0)),
                "precio_subtotal": float(d.subtotal)
            }
            for d in (v.detalles or [])
        ]
        results.append({
            "compra_id": v.id,
            "fecha": v.fecha.isoformat() if v.fecha else "",
            "total": float(v.monto_neto if v.monto_neto is not None else v.total),
            "estado": estado_out,
            "tipo": v.tipo_venta.nombre if v.tipo_venta else "Digital E-commerce Web",
            "cantidad_productos": sum(d.cantidad for d in (v.detalles or [])),
            "productos": prods,
            "descuento_fidelizacion": float(v.descuento_total or 0.0)
        })

    return {
        "count": total,
        "next": f"?page={page+1}&page_size={page_size}" if (offset + page_size) < total else None,
        "previous": f"?page={page-1}&page_size={page_size}" if page > 1 else None,
        "results": results
    }


@compat_router.get("/")
def listar_ventas_paginadas_frontend(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    db: Session = Depends(get_db)
):
    query = db.query(Venta).options(
        joinedload(Venta.sucursal),
        joinedload(Venta.empleado),
        joinedload(Venta.cliente),
        joinedload(Venta.tipo_venta),
        joinedload(Venta.factura),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.ropa),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.talla),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.color)
    ).order_by(Venta.id.desc())

    total = query.count()
    offset = (page - 1) * page_size
    ventas = query.offset(offset).limit(page_size).all()

    results = []
    for v in ventas:
        tipo_nom = v.tipo_venta.nombre if v.tipo_venta else "Presencial"
        tipo_str = "Presencial" if "POS" in tipo_nom or "Presencial" in tipo_nom else "Digital"
        estado_str = "Completada" if v.estado_pago == "PAGADA" else v.estado_pago
        fecha_str = v.fecha.isoformat() if v.fecha else ""
        total_str = f"{float(v.total):.2f}"
        usuario_nom = v.cliente.nombre if v.cliente else (v.empleado.nombre if v.empleado else "Consumidor Final")

        results.append({
            "id": v.id,
            "tipo": tipo_str,
            "estado": estado_str,
            "fecha": fecha_str,
            "precio_total": total_str,
            "usuario": v.empleado_ci or 1,
            "usuario_username": usuario_nom,
            "nro_comprobante": v.codigo_transaccion,
            "detalles": [
                {
                    "id": d.id,
                    "cantidad": d.cantidad,
                    "precio_unitario": str(d.precio_unitario if d.precio_unitario is not None else (d.variante.ropa.precio if (d.variante and d.variante.ropa) else 0)),
                    "subtotal": str(d.subtotal),
                    "variante": d.variante_id,
                    "variante_nombre": d.variante.ropa.nombre if (d.variante and d.variante.ropa) else f"Variante #{d.variante_id}",
                    "talla": d.variante.talla.medida if (d.variante and d.variante.talla) else "Única",
                    "color": d.variante.color.nombre if (d.variante and d.variante.color) else ""
                }
                for d in v.detalles
            ]
        })

    return {
        "count": total,
        "next": f"?page={page+1}&page_size={page_size}" if (offset + page_size) < total else None,
        "previous": f"?page={page-1}&page_size={page_size}" if page > 1 else None,
        "results": results
    }


@compat_router.get("/{venta_id}/")
def obtener_venta_frontend(venta_id: int, db: Session = Depends(get_db)):
    venta = db.query(Venta).options(
        joinedload(Venta.sucursal),
        joinedload(Venta.empleado),
        joinedload(Venta.cliente),
        joinedload(Venta.tipo_venta),
        joinedload(Venta.factura),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.ropa),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.talla),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.color)
    ).filter(Venta.id == venta_id).first()

    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")

    tipo_nom = venta.tipo_venta.nombre if venta.tipo_venta else "Presencial"
    tipo_str = "Presencial" if "POS" in tipo_nom or "Presencial" in tipo_nom else "Digital"
    estado_str = "Completada" if venta.estado_pago == "PAGADA" else venta.estado_pago
    fecha_str = venta.fecha.isoformat() if venta.fecha else ""
    total_num = float(venta.monto_neto if venta.monto_neto is not None else venta.total)
    total_str = f"{total_num:.2f}"
    usuario_nom = venta.cliente.nombre if venta.cliente else (venta.empleado.nombre if venta.empleado else "Consumidor Final")

    return {
        "id": venta.id,
        "tipo": tipo_str,
        "estado": estado_str,
        "fecha": fecha_str,
        "precio_total": total_str,
        "subtotal": f"{float(venta.total):.2f}",
        "descuento_total": f"{float(venta.descuento_total or 0.0):.2f}",
        "monto_neto": f"{float(venta.monto_neto or venta.total):.2f}",
        "usuario": venta.empleado_ci or 1,
        "usuario_username": usuario_nom,
        "nro_comprobante": venta.codigo_transaccion,
        "nro_factura": venta.factura.nro_factura if venta.factura else "",
        "nit_cliente": venta.factura.nit_cliente if venta.factura else "0",
        "razon_social": venta.factura.razon_social if venta.factura else "Sin Nombre",
        "monto_recibido": float(venta.monto_recibido) if venta.monto_recibido is not None else None,
        "cambio_devuelto": float(venta.cambio_devuelto) if venta.cambio_devuelto is not None else None,
        "detalles": [
            {
                "id": d.id,
                "cantidad": d.cantidad,
                "precio_unitario": str(d.precio_unitario if d.precio_unitario is not None else (d.variante.ropa.precio if (d.variante and d.variante.ropa) else 0)),
                "subtotal": str(d.subtotal),
                "variante": d.variante_id,
                "variante_producto": d.variante_id,
                "variante_producto_id": d.variante_id,
                "variante_nombre": d.variante.ropa.nombre if (d.variante and d.variante.ropa) else f"Variante #{d.variante_id}",
                "variante_producto_nombre": f"{d.variante.ropa.nombre} ({d.variante.talla.medida if (d.variante and d.variante.talla) else 'Única'})" if (d.variante and d.variante.ropa) else f"Variante #{d.variante_id}",
                "talla": d.variante.talla.medida if (d.variante and d.variante.talla) else "Única",
                "color": d.variante.color.nombre if (d.variante and d.variante.color) else ""
            }
            for d in venta.detalles
        ]
    }


@compat_router.patch("/{venta_id}/")
@compat_router.patch("/{venta_id}")
def actualizar_estado_venta_compat(venta_id: int, payload: dict, db: Session = Depends(get_db)):
    venta = db.query(Venta).filter(Venta.id == venta_id).first()
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    
    nuevo_estado = payload.get("estado", "")
    if nuevo_estado:
        est_str = nuevo_estado.lower()
        if "completad" in est_str or "pagad" in est_str:
            venta.estado_pago = "COMPLETADA"
        elif "cancelad" in est_str or "anulad" in est_str:
            venta.estado_pago = "ANULADA"
        elif "fallid" in est_str or "rechazad" in est_str:
            venta.estado_pago = "FALLIDA"
        else:
            venta.estado_pago = "PENDIENTE"
    
    db.commit()
    return {"message": "Venta actualizada exitosamente", "id": venta.id, "estado": venta.estado_pago}


@compat_router.put("/{venta_id}/")
@compat_router.put("/{venta_id}")
def actualizar_venta_completa_compat(venta_id: int, payload: dict, db: Session = Depends(get_db)):
    venta = db.query(Venta).options(
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.ropa)
    ).filter(Venta.id == venta_id).first()
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    
    nuevo_estado = payload.get("estado", "")
    if nuevo_estado:
        est_str = nuevo_estado.lower()
        if "completad" in est_str or "pagad" in est_str:
            venta.estado_pago = "COMPLETADA"
        elif "cancelad" in est_str or "anulad" in est_str:
            venta.estado_pago = "ANULADA"
        elif "fallid" in est_str or "rechazad" in est_str:
            venta.estado_pago = "FALLIDA"
        else:
            venta.estado_pago = "PENDIENTE"
    
    if "detalles" in payload and isinstance(payload["detalles"], list):
        for item in payload["detalles"]:
            det_id = item.get("id")
            nueva_cant = item.get("cantidad")
            if det_id and nueva_cant is not None:
                det = db.query(DetalleVenta).filter(DetalleVenta.id == det_id, DetalleVenta.venta_id == venta.id).first()
                if det:
                    det.cantidad = int(nueva_cant)
                    p_unit = float(det.precio_unitario) if det.precio_unitario is not None else 0.0
                    det.subtotal = round(p_unit * int(nueva_cant), 2)
        
        db.flush()
        total_nuevo = sum(float(d.subtotal) for d in venta.detalles)
        venta.total = total_nuevo
        venta.monto_neto = max(0.0, total_nuevo - float(venta.descuento_total or 0.0))
    
    db.commit()
    return {"message": "Venta guardada exitosamente", "id": venta.id, "estado": venta.estado_pago}


@compat_router.delete("/{venta_id}/")
@compat_router.delete("/{venta_id}")
def eliminar_venta_compat(venta_id: int, db: Session = Depends(get_db)):
    venta = db.query(Venta).filter(Venta.id == venta_id).first()
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    db.delete(venta)
    db.commit()
    return {"message": "Venta eliminada exitosamente", "id": venta_id}

