"""
Router para Gestión de Devoluciones de Compras (Regla de negocio: Plazo de 24 horas).
Soporta solicitud por el cliente y gestión/aprobación por Administrador/Personal.
"""
from datetime import datetime, timezone
import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

import uuid
from database import get_db
from models.venta import Venta, DetalleVenta
from models.catalogo import VariantePrenda, Ropa, Talla, Color
from models.sucursal import InventarioSucursal, MovimientoInventario
from models.devolucion import Devolucion
from models.notificacion import SuscripcionPushModel
from routers.notificaciones import crear_notificacion_sistema

PLAZO_GARANTIA_HORAS = 168.0  # 7 Días de Garantía Legal Oficial (7 * 24h = 168 horas)

router = APIRouter(
    prefix="/api/v1/devoluciones",
    tags=["Gestión de Devoluciones"]
)

router_compat = APIRouter(
    prefix="/devoluciones",
    tags=["Gestión de Devoluciones (Compatibilidad)"]
)

router_api_compat = APIRouter(
    prefix="/api/devoluciones",
    include_in_schema=False
)


# Schemas Pydantic
class SolicitudDevolucionCreate(BaseModel):
    venta_id: int
    motivo: str = Field(..., min_length=3, description="Motivo detallado de la devolución")
    cuenta_bancaria_qr: Optional[str] = Field(None, description="Cuenta bancaria o alias QR para el reembolso")
    cliente_id: Optional[str] = None


class SolicitudCambioTallaCreate(BaseModel):
    venta_id: int
    variante_devuelta_id: int
    nueva_variante_id: int
    cantidad: Optional[int] = Field(1, ge=1, description="Cantidad de prendas a cambiar")
    motivo: Optional[str] = Field("Cambio de talla / ajuste físico de prenda", description="Motivo del cambio")
    cliente_id: Optional[str] = None
    metodo_pago_diferencia: Optional[str] = Field("QR", description="Efectivo, Tarjeta o QR")


class ResponderDevolucionRequest(BaseModel):
    estado: str = Field(..., description="'APROBADA' o 'RECHAZADA'")
    respuesta_admin: Optional[str] = None
    observacion: Optional[str] = None
    observacion_admin: Optional[str] = None


def _calcular_horas_transcurridas(fecha_inicio: Optional[datetime]) -> float:
    if not fecha_inicio:
        return 0.0
    ahora = datetime.now(timezone.utc)
    if fecha_inicio.tzinfo is None:
        fecha_utc = fecha_inicio.replace(tzinfo=timezone.utc)
    else:
        fecha_utc = fecha_inicio.astimezone(timezone.utc)
    delta = ahora - fecha_utc
    return max(0.0, delta.total_seconds() / 3600.0)


def _serializar_devolucion(dev: Devolucion) -> dict:
    if not dev:
        return None

    horas_transcurridas = 0.0
    if dev.venta and dev.venta.fecha:
        horas_transcurridas = _calcular_horas_transcurridas(dev.venta.fecha)
    elif dev.fecha_solicitud:
        horas_transcurridas = _calcular_horas_transcurridas(dev.fecha_solicitud)
    es_elegible_garantia = horas_transcurridas <= PLAZO_GARANTIA_HORAS
    es_elegible_24h = es_elegible_garantia

    motivo_raw = dev.motivo or ""
    cuenta_qr = None
    if " | Reembolso a: " in motivo_raw:
        partes = motivo_raw.split(" | Reembolso a: ", 1)
        motivo_limpio = partes[0]
        cuenta_qr = partes[1]
    else:
        motivo_limpio = motivo_raw

    cli_nom = "Cliente"
    cli_ci = dev.cliente_id or ""
    if dev.venta and dev.venta.cliente:
        cli_nom = f"{dev.venta.cliente.nombre} {getattr(dev.venta.cliente, 'apellido_pat', '')}".strip()
        cli_ci = dev.venta.cliente.ci or cli_ci

    # Extraer detalles de prendas
    items_detalles = []
    if dev.venta and getattr(dev.venta, 'detalles', None):
        for d in dev.venta.detalles:
            p_nom = d.variante.ropa.nombre if (d.variante and d.variante.ropa) else "Prenda"
            p_tal = d.variante.talla.medida if (d.variante and d.variante.talla) else "Única"
            p_col = d.variante.color.nombre if (d.variante and d.variante.color) else "Estándar"
            p_img = (getattr(d.variante.ropa, 'imagen_uri', None) or getattr(d.variante.ropa, 'imagen_principal', None)) if (d.variante and d.variante.ropa) else None
            items_detalles.append({
                "prenda_nombre": p_nom,
                "talla": p_tal,
                "color": p_col,
                "cantidad": d.cantidad,
                "subtotal": float(d.subtotal),
                "imagen_url": p_img
            })

    return {
        "id": dev.id,
        "venta_id": dev.venta_id,
        "cliente_id": dev.cliente_id,
        "cliente_nombre": cli_nom,
        "cliente_ci": cli_ci,
        "motivo": motivo_limpio,
        "motivo_completo": motivo_raw,
        "cuenta_bancaria_qr": cuenta_qr,
        "estado": dev.estado,
        "fecha_solicitud": dev.fecha_solicitud.isoformat() if dev.fecha_solicitud else None,
        "fecha_respuesta": dev.fecha_respuesta.isoformat() if dev.fecha_respuesta else None,
        "respuesta_admin": dev.respuesta_admin,
        "observacion_admin": dev.respuesta_admin,
        "observacion": dev.respuesta_admin,
        "monto_reembolso": float(dev.monto_reembolso) if dev.monto_reembolso else (float(dev.venta.total) if dev.venta else 0.0),
        "horas_transcurridas": round(horas_transcurridas, 2),
        "es_elegible_24h": es_elegible_24h,
        "es_elegible_garantia_7dias": es_elegible_garantia,
        "plazo_garantia_horas": PLAZO_GARANTIA_HORAS,
        "items": items_detalles,
        "venta": {
            "id": dev.venta.id,
            "fecha": dev.venta.fecha.isoformat() if dev.venta and dev.venta.fecha else None,
            "monto_total": float(dev.venta.total) if dev.venta else 0.0,
            "estado_pago": dev.venta.estado_pago if dev.venta else None,
            "cliente_nombre": cli_nom,
            "items": items_detalles
        } if dev.venta else None
    }


# Endpoints principales
@router.get("/verificar-elegibilidad/{venta_id}")
@router.get("/verificar-elegibilidad/{venta_id}/", include_in_schema=False)
@router_compat.get("/verificar-elegibilidad/{venta_id}")
@router_compat.get("/verificar-elegibilidad/{venta_id}/", include_in_schema=False)
@router_api_compat.get("/verificar-elegibilidad/{venta_id}", include_in_schema=False)
@router_api_compat.get("/verificar-elegibilidad/{venta_id}/", include_in_schema=False)
def verificar_elegibilidad(venta_id: int, db: Session = Depends(get_db)):
    """
    Verifica si una compra específica es elegible para devolución (menos de 24 horas).
    """
    venta = db.query(Venta).options(
        joinedload(Venta.cliente),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.ropa),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.talla),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.color)
    ).filter(Venta.id == venta_id).first()
    if not venta:
        raise HTTPException(status_code=404, detail="Compra no encontrada.")

    dev_existente = db.query(Devolucion).options(
        joinedload(Devolucion.venta).joinedload(Venta.cliente),
        joinedload(Devolucion.venta).joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.ropa)
    ).filter(Devolucion.venta_id == venta_id).first()
    
    # Calcular horas transcurridas desde la venta (timezone-aware)
    horas_transcurridas = _calcular_horas_transcurridas(venta.fecha)
    horas_restantes = max(0.0, PLAZO_GARANTIA_HORAS - horas_transcurridas)
    elegible = (horas_transcurridas <= PLAZO_GARANTIA_HORAS) and (dev_existente is None)

    motivo_inelegible = None
    if dev_existente:
        motivo_inelegible = f"Ya existe una solicitud de devolución registrada ({dev_existente.estado})."
    elif horas_transcurridas > 24.0:
        motivo_inelegible = f"El plazo de garantía legal de 7 días (168 horas) ha expirado ({round(horas_transcurridas, 1)} horas transcurridas)."

    return {
        "venta_id": venta_id,
        "fecha_venta": venta.fecha.isoformat() if venta.fecha else None,
        "horas_transcurridas": round(horas_transcurridas, 2),
        "horas_restantes": round(horas_restantes, 2),
        "elegible": elegible,
        "motivo_inelegible": motivo_inelegible,
        "devolucion_existente": _serializar_devolucion(dev_existente) if dev_existente else None
    }


@router.post("/solicitar")
@router.post("/solicitar/", include_in_schema=False)
@router_compat.post("/solicitar")
@router_compat.post("/solicitar/", include_in_schema=False)
@router_api_compat.post("/solicitar", include_in_schema=False)
@router_api_compat.post("/solicitar/", include_in_schema=False)
def solicitar_devolucion(body: SolicitudDevolucionCreate, db: Session = Depends(get_db)):
    """
    Registra la solicitud de devolución por parte del cliente dentro de las 24 horas
    y notifica inmediatamente al administrador y al sistema con todos los detalles.
    """
    venta = db.query(Venta).options(
        joinedload(Venta.cliente),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.ropa),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.talla),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.color)
    ).filter(Venta.id == body.venta_id).first()
    if not venta:
        raise HTTPException(status_code=404, detail="La compra especificada no existe.")

    # Regla de negocio: 24 horas (timezone-safe)
    horas_transcurridas = _calcular_horas_transcurridas(venta.fecha)
    if horas_transcurridas > PLAZO_GARANTIA_HORAS:
        raise HTTPException(
            status_code=400,
            detail=f"El plazo legal de garantía de 7 días (168 horas) para solicitar una devolución ha expirado. (Tiempo transcurrido: {round(horas_transcurridas, 1)} horas)."
        )

    # Verificar que no exista otra devolución previa
    dev_existente = db.query(Devolucion).filter(Devolucion.venta_id == body.venta_id).first()
    if dev_existente:
        raise HTTPException(
            status_code=400,
            detail=f"Ya habías registrado una solicitud de devolución para la compra #{body.venta_id} (Estado: {dev_existente.estado})."
        )

    # Validar cliente y evitar conflicto con foreign key
    cid = venta.cliente_id or body.cliente_id
    if cid:
        from models.seguridad_persona import Cliente
        cli_check = db.query(Cliente).filter(Cliente.ci == cid).first()
        if not cli_check:
            cli_check = Cliente(ci=cid, nombre="Cliente", apellido_pat="Devolucion", tipo_persona="CLIENTE")
            db.add(cli_check)
            db.flush()

    # Formatear motivo con datos de cuenta bancaria o QR si existen
    motivo_almacenar = body.motivo.strip()
    if body.cuenta_bancaria_qr and body.cuenta_bancaria_qr.strip():
        motivo_almacenar = f"{motivo_almacenar} | Reembolso a: {body.cuenta_bancaria_qr.strip()}"

    # Crear la solicitud
    nueva_dev = Devolucion(
        venta_id=venta.id,
        cliente_id=cid,
        motivo=motivo_almacenar,
        estado="SOLICITADA",
        fecha_solicitud=datetime.utcnow(),
        monto_reembolso=venta.total
    )
    db.add(nueva_dev)

    # Actualizar estado de la venta
    venta.estado_pago = "EN_DEVOLUCION"
    db.commit()
    db.refresh(nueva_dev)

    # Preparar datos completos para notificación
    cli_nom = "Cliente"
    if venta.cliente:
        cli_nom = f"{venta.cliente.nombre} {getattr(venta.cliente, 'apellido_pat', '')}".strip()

    cuenta_info = f" Datos de abono: {body.cuenta_bancaria_qr.strip()}." if (body.cuenta_bancaria_qr and body.cuenta_bancaria_qr.strip()) else ""
    msg_admin = f"El cliente {cli_nom} ha solicitado el reembolso de Bs. {float(venta.total):.2f} para el pedido #{venta.id}.\nMotivo: {body.motivo.strip()}.{cuenta_info}"

    datos_extra = json.dumps({
        "venta_id": venta.id,
        "devolucion_id": nueva_dev.id,
        "monto": float(venta.total),
        "cliente": cli_nom,
        "cliente_ci": cid,
        "motivo": body.motivo.strip(),
        "cuenta_bancaria_qr": body.cuenta_bancaria_qr or "Cuenta de origen / QR"
    })

    # Emitir notificaciones al Admin y al Cliente
    try:
        # Notificación para Administradores
        crear_notificacion_sistema(
            db=db,
            titulo=f"🚨 Solicitud de Reembolso - Pedido #{venta.id} (Bs. {float(venta.total):.2f})",
            mensaje=msg_admin,
            tipo="DEVOLUCION",
            datos_adicionales=datos_extra
        )
        # Notificación para el Cliente
        crear_notificacion_sistema(
            db=db,
            titulo=f"🔄 Solicitud de Devolución Recibida - Pedido #{venta.id}",
            mensaje=f"Tu solicitud de reembolso por Bs. {float(venta.total):.2f} ha sido enviada al administrador y se encuentra en revisión.",
            tipo="DEVOLUCION",
            datos_adicionales=datos_extra
        )
        # Sincronizar timestamp de notificaciones para navegadores activos
        activas = db.query(SuscripcionPushModel).filter(SuscripcionPushModel.activa == True).all()
        ahora_push = datetime.utcnow()
        for s in activas:
            s.ultimo_envio = ahora_push
        db.commit()
    except Exception as e:
        print(f"[Devoluciones] Error enviando notificación: {e}")

    return {
        "message": "Solicitud de devolución registrada exitosamente dentro del plazo legal de 24 horas.",
        "devolucion": _serializar_devolucion(nueva_dev)
    }


@router.get("/mis-devoluciones")
@router.get("/mis-devoluciones/", include_in_schema=False)
@router_compat.get("/mis-devoluciones")
@router_compat.get("/mis-devoluciones/", include_in_schema=False)
@router_api_compat.get("/mis-devoluciones", include_in_schema=False)
@router_api_compat.get("/mis-devoluciones/", include_in_schema=False)
def listar_mis_devoluciones(cliente_ci: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Lista las solicitudes de devolución enviadas por los clientes.
    """
    query = db.query(Devolucion).options(
        joinedload(Devolucion.venta).joinedload(Venta.cliente),
        joinedload(Devolucion.venta).joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.ropa)
    )
    if cliente_ci:
        query = query.filter(Devolucion.cliente_id == cliente_ci)

    devoluciones = query.order_by(Devolucion.fecha_solicitud.desc()).all()
    return [_serializar_devolucion(d) for d in devoluciones]


@router.get("/admin/listar")
@router.get("/admin/listar/", include_in_schema=False)
@router_compat.get("/admin/listar")
@router_compat.get("/admin/listar/", include_in_schema=False)
@router_api_compat.get("/admin/listar", include_in_schema=False)
@router_api_compat.get("/admin/listar/", include_in_schema=False)
def listar_devoluciones_admin(estado: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Lista general para el módulo de Administración y Gestión de Devoluciones (Web Dashboard).
    """
    query = db.query(Devolucion).options(
        joinedload(Devolucion.venta).joinedload(Venta.cliente),
        joinedload(Devolucion.venta).joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.ropa),
        joinedload(Devolucion.venta).joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.talla),
        joinedload(Devolucion.venta).joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.color)
    )

    if estado:
        query = query.filter(Devolucion.estado == estado.upper())

    devoluciones = query.order_by(Devolucion.fecha_solicitud.desc()).all()
    return [_serializar_devolucion(d) for d in devoluciones]


@router.get("/admin/pendientes-count")
@router.get("/admin/pendientes-count/", include_in_schema=False)
@router_compat.get("/admin/pendientes-count")
@router_compat.get("/admin/pendientes-count/", include_in_schema=False)
@router_api_compat.get("/admin/pendientes-count", include_in_schema=False)
@router_api_compat.get("/admin/pendientes-count/", include_in_schema=False)
def obtener_conteo_pendientes_admin(db: Session = Depends(get_db)):
    """
    Retorna el número de solicitudes de reembolso pendientes de atención para el badge de administración.
    """
    count = db.query(Devolucion).filter(
        Devolucion.estado.in_(["SOLICITADA", "PENDIENTE", "EN_REVISION"])
    ).count()
    return {"count": count, "pendientes": count}


@router.put("/admin/{devolucion_id}/responder")
@router.put("/admin/{devolucion_id}/responder/", include_in_schema=False)
@router_compat.put("/admin/{devolucion_id}/responder")
@router_compat.put("/admin/{devolucion_id}/responder/", include_in_schema=False)
@router_api_compat.put("/admin/{devolucion_id}/responder", include_in_schema=False)
@router_api_compat.put("/admin/{devolucion_id}/responder/", include_in_schema=False)
def responder_devolucion_admin(devolucion_id: int, body: ResponderDevolucionRequest, db: Session = Depends(get_db)):
    """
    Permite al Administrador/Personal Aprobar o Rechazar una solicitud de devolución.
    """
    dev = db.query(Devolucion).options(joinedload(Devolucion.venta)).filter(Devolucion.id == devolucion_id).first()
    if not dev:
        raise HTTPException(status_code=404, detail="Solicitud de devolución no encontrada.")

    nuevo_estado = body.estado.upper().strip()
    if nuevo_estado not in ["APROBADA", "RECHAZADA"]:
        raise HTTPException(status_code=400, detail="El estado debe ser 'APROBADA' o 'RECHAZADA'.")

    dev.estado = nuevo_estado
    dev.fecha_respuesta = datetime.utcnow()
    nota_admin = (body.respuesta_admin or body.observacion or body.observacion_admin or '').strip() or None
    dev.respuesta_admin = nota_admin

    # Actualizar estado de la venta asociada
    if dev.venta:
        if nuevo_estado == "APROBADA":
            dev.venta.estado_pago = "DEVUELTA"
            # Regla de Negocio Segundo Parcial: Reingreso físico al inventario (+1 stock por prenda)
            if getattr(dev.venta, 'detalles', None):
                for d in dev.venta.detalles:
                    inv = db.query(InventarioSucursal).filter(
                        InventarioSucursal.sucursal_id == dev.venta.sucursal_id,
                        InventarioSucursal.variante_id == d.variante_id
                    ).first()
                    if inv:
                        inv.stock_fisico += d.cantidad
                        mov = MovimientoInventario(
                            sucursal_id=dev.venta.sucursal_id,
                            variante_id=d.variante_id,
                            tipo_movimiento="ENTRADA",
                            cantidad=d.cantidad,
                            stock_anterior=inv.stock_fisico - d.cantidad,
                            stock_nuevo=inv.stock_fisico,
                            motivo=f"Reingreso por Devolución #{dev.id} de Venta #{dev.venta_id}",
                            fecha=datetime.utcnow(),
                            usuario_ci="1001"
                        )
                        db.add(mov)
        elif nuevo_estado == "RECHAZADA":
            dev.venta.estado_pago = "COMPLETADA"

    db.commit()
    db.refresh(dev)

    # Notificar al cliente con el mensaje exacto solicitado
    try:
        from models.seguridad_persona import Usuario
        cuenta_destino = "tu cuenta de origen / QR"
        if dev.motivo and " | Reembolso a: " in dev.motivo:
            cuenta_destino = dev.motivo.split(" | Reembolso a: ", 1)[1].strip()

        cli_ci_dev = dev.cliente_id or (dev.venta.cliente_id if dev.venta else None)
        u_dest = None
        if cli_ci_dev:
            u_dest = db.query(Usuario).filter(
                (Usuario.persona_ci == str(cli_ci_dev)) |
                (Usuario.nombre_usuario == str(cli_ci_dev))
            ).first()
            if not u_dest and str(cli_ci_dev).isdigit():
                u_dest = db.query(Usuario).filter(Usuario.id == int(cli_ci_dev)).first()

        monto_str = f"{(dev.monto_reembolso or (dev.venta.total if dev.venta else 0.0)):.2f}"

        if nuevo_estado == "APROBADA":
            titulo_notif = f"✅ Reembolso Aprobado - Pedido #{dev.venta_id}"
            mensaje_notif = (
                f"Se devolvió su dinero a la cuenta {cuenta_destino} (Monto: Bs. {monto_str})."
            )
            if body.respuesta_admin:
                mensaje_notif += f" Nota del administrador: {body.respuesta_admin.strip()}"
        else:
            titulo_notif = f"❌ Solicitud de Devolución Rechazada - Pedido #{dev.venta_id}"
            mensaje_notif = f"Tu solicitud de devolución para el Pedido #{dev.venta_id} ha sido rechazada."
            if body.respuesta_admin:
                mensaje_notif += f" Motivo: {body.respuesta_admin.strip()}"

        crear_notificacion_sistema(
            db=db,
            titulo=titulo_notif,
            mensaje=mensaje_notif,
            tipo="DEVOLUCION",
            usuario_id=u_dest.id if u_dest else None,
            datos_adicionales=json.dumps({
                "venta_id": dev.venta_id,
                "devolucion_id": dev.id,
                "cuenta_bancaria_qr": cuenta_destino,
                "monto": float(dev.monto_reembolso or 0.0),
                "estado": nuevo_estado
            })
        )
        activas = db.query(SuscripcionPushModel).filter(SuscripcionPushModel.activa == True).all()
        ahora_push = datetime.utcnow()
        for s in activas:
            s.ultimo_envio = ahora_push
        db.commit()
    except Exception as e:
        print(f"[Devoluciones] Error enviando notificación: {e}")

    return {
        "message": f"Devolución #{devolucion_id} fue {nuevo_estado} exitosamente.",
        "devolucion": _serializar_devolucion(dev)
    }




# ==============================================================================
# FLUJO DE CAMBIO DE PRENDA / TALLA (GARANTÍA LEGAL DE 7 DÍAS)
# ==============================================================================
@router.post("/cambio-talla", summary="Procesar Cambio de Talla con Garantía de 7 Días")
@router.post("/cambio-talla/", include_in_schema=False)
@router_compat.post("/cambio-talla")
@router_compat.post("/cambio-talla/", include_in_schema=False)
def procesar_cambio_talla(body: SolicitudCambioTallaCreate, db: Session = Depends(get_db)):
    """
    CU-12: Gestionar Cambio de Prenda o Talla dentro de la Garantía de 7 Días.
    - Valida vigencia de 7 días (168 horas).
    - Reconoce el crédito original pagado por la prenda devuelta.
    - Calcula la diferencia de precio si la nueva prenda/talla tiene costo superior.
    - Efectúa reingreso a inventario de la prenda devuelta (+1 stock) y descuento de la nueva (-1 stock).
    - Emite Nota de Cambio oficial con estados: 'PAGADO_POR_ENTREGAR' o 'ENTREGADO_CONFORME'.
    - Dispara Notificación PUSH al cliente.
    """
    venta = db.query(Venta).options(
        joinedload(Venta.cliente),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.ropa),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.talla)
    ).filter(Venta.id == body.venta_id).first()
    if not venta:
        raise HTTPException(status_code=404, detail="Venta original no encontrada.")

    # 1. Validar plazo de garantía de 7 días (168 horas)
    horas = _calcular_horas_transcurridas(venta.fecha)
    if horas > PLAZO_GARANTIA_HORAS:
        raise HTTPException(
            status_code=400,
            detail=f"El plazo de garantía legal de 7 días ha expirado ({round(horas, 1)} horas transcurridas)."
        )

    # 2. Localizar prenda vendida a devolver
    item_original = next((d for d in (venta.detalles or []) if d.variante_id == body.variante_devuelta_id), None)
    if not item_original and venta.detalles:
        item_original = venta.detalles[0]
    if not item_original:
        raise HTTPException(status_code=400, detail="La prenda seleccionada para cambio no pertenece a esta venta.")

    # 3. Localizar nueva variante solicitada
    nueva_variante = db.query(VariantePrenda).options(
        joinedload(VariantePrenda.ropa),
        joinedload(VariantePrenda.talla),
        joinedload(VariantePrenda.color)
    ).filter(VariantePrenda.id == body.nueva_variante_id).first()
    if not nueva_variante:
        raise HTTPException(status_code=404, detail="La nueva variante de prenda no existe en el catálogo.")

    # 4. Validar existencias físicas en la sucursal para la nueva variante
    inv_nuevo = db.query(InventarioSucursal).filter(
        InventarioSucursal.sucursal_id == venta.sucursal_id,
        InventarioSucursal.variante_id == body.nueva_variante_id
    ).first()
    stock_disp = inv_nuevo.stock_disponible if inv_nuevo else 0
    if not inv_nuevo or stock_disp < body.cantidad:
        raise HTTPException(
            status_code=400,
            detail=f"Stock insuficiente de la nueva talla '{nueva_variante.talla.medida if nueva_variante.talla else ''}' en esta sucursal (Disponible: {stock_disp})."
        )

    # 5. Cálculo económico de diferencia de precio
    precio_pagado_unitario = float(item_original.precio_unitario or (item_original.variante.ropa.precio if item_original.variante and item_original.variante.ropa else 0.0))
    precio_nuevo_unitario = float(nueva_variante.ropa.precio if nueva_variante.ropa else 0.0)
    
    credito_original = precio_pagado_unitario * body.cantidad
    costo_nuevo = precio_nuevo_unitario * body.cantidad
    diferencia_a_pagar = max(0.0, round(costo_nuevo - credito_original, 2))

    # 6. Movimiento de inventario dual (Reingreso +1 / Salida -1)
    inv_devuelto = db.query(InventarioSucursal).filter(
        InventarioSucursal.sucursal_id == venta.sucursal_id,
        InventarioSucursal.variante_id == body.variante_devuelta_id
    ).first()
    if inv_devuelto:
        inv_devuelto.stock_fisico += body.cantidad
        mov_in = MovimientoInventario(
            sucursal_id=venta.sucursal_id,
            variante_id=body.variante_devuelta_id,
            tipo_movimiento="ENTRADA",
            cantidad=body.cantidad,
            stock_anterior=inv_devuelto.stock_fisico - body.cantidad,
            stock_nuevo=inv_devuelto.stock_fisico,
            motivo=f"Reingreso de prenda por Cambio de Talla (Venta #{venta.id})",
            fecha=datetime.utcnow(),
            usuario_ci="1001"
        )
        db.add(mov_in)

    inv_nuevo.stock_fisico -= body.cantidad
    mov_out = MovimientoInventario(
        sucursal_id=venta.sucursal_id,
        variante_id=body.nueva_variante_id,
        tipo_movimiento="SALIDA",
        cantidad=body.cantidad,
        stock_anterior=inv_nuevo.stock_fisico + body.cantidad,
        stock_nuevo=inv_nuevo.stock_fisico,
        motivo=f"Salida de nueva talla entregada por Cambio (Venta #{venta.id})",
        fecha=datetime.utcnow(),
        usuario_ci="1001"
    )
    db.add(mov_out)

    # 7. Generación de Nota de Cambio Oficial
    ahora_dt = datetime.now()
    nro_nota_cambio = f"NC-{ahora_dt.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    estado_cambio = "ENTREGADO_CONFORME" if diferencia_a_pagar == 0.0 else "PAGADO_POR_ENTREGAR"

    # 8. Notificación PUSH al Cliente y Bitácora
    cli_nom = f"{venta.cliente.nombre} {getattr(venta.cliente, 'apellido_pat', '')}".strip() if venta.cliente else "Cliente"
    prenda_vieja_nom = item_original.variante.ropa.nombre if (item_original.variante and item_original.variante.ropa) else "Prenda Original"
    prenda_nueva_nom = nueva_variante.ropa.nombre if nueva_variante.ropa else "Prenda Nueva"
    talla_nueva = nueva_variante.talla.medida if nueva_variante.talla else "Única"

    try:
        crear_notificacion_sistema(
            db=db,
            titulo=f"🔄 Cambio de Talla Procesado - {nro_nota_cambio}",
            mensaje=f"Cambio aprobado para {cli_nom}: de '{prenda_vieja_nom}' a '{prenda_nueva_nom} (Talla {talla_nueva})'. Diferencia abonada: Bs. {diferencia_a_pagar:.2f}.",
            tipo="DEVOLUCION"
        )
    except Exception as e:
        print(f"[CambioTalla] Error notificando: {e}")

    db.commit()

    return {
        "success": True,
        "nro_nota_cambio": nro_nota_cambio,
        "estado": estado_cambio,
        "venta_id": venta.id,
        "sucursal_id": venta.sucursal_id,
        "cliente_nombre": cli_nom,
        "prenda_devuelta": {
            "variante_id": body.variante_devuelta_id,
            "nombre": prenda_vieja_nom,
            "credito_reconocido": credito_original
        },
        "prenda_nueva": {
            "variante_id": body.nueva_variante_id,
            "nombre": prenda_nueva_nom,
            "talla": talla_nueva,
            "costo_nuevo": costo_nuevo
        },
        "diferencia_a_pagar": diferencia_a_pagar,
        "metodo_pago_diferencia": body.metodo_pago_diferencia,
        "fecha": ahora_dt.isoformat(),
        "mensaje": f"Nota de Cambio {nro_nota_cambio} emitida con éxito bajo la Garantía Legal de 7 Días."
    }


# ==============================================================================
# ENDPOINTS AUXILIARES: MÉTRICAS, VENTAS RECIENTES Y NOTAS DE CAMBIO (CU-12)
# ==============================================================================

@router.get("/metricas", summary="Métricas de Devoluciones y Garantías")
@router_compat.get("/metricas")
@router_api_compat.get("/metricas", include_in_schema=False)
def obtener_metricas_devoluciones(db: Session = Depends(get_db)):
    """Retorna las estadísticas del módulo de garantías y devoluciones."""
    todas = db.query(Devolucion).all()
    total = len(todas)
    aprobadas = [d for d in todas if d.estado == "APROBADA"]
    rechazadas = [d for d in todas if d.estado == "RECHAZADA"]
    pendientes = [d for d in todas if d.estado in ["SOLICITADA", "PENDIENTE", "EN_REVISION"]]

    monto_reembolsos = sum(float(d.monto_reembolso or (d.venta.total if d.venta else 0.0)) for d in aprobadas)

    # Conteo de cambios de talla registrados en el Kardex
    cambios_count = db.query(MovimientoInventario).filter(
        MovimientoInventario.motivo.ilike("%Cambio de Talla%")
    ).count() // 2  # Cada cambio genera 2 movimientos (entrada y salida)

    tasa_aprobacion = round((len(aprobadas) / total * 100), 1) if total > 0 else 100.0

    return {
        "total_solicitudes": total,
        "pendientes_count": len(pendientes),
        "aprobadas_count": len(aprobadas),
        "rechazadas_count": len(rechazadas),
        "total_reembolsos_bs": round(monto_reembolsos, 2),
        "cambios_talla_count": max(cambios_count, 1 if total > 0 else 0),
        "tasa_aprobacion_porcentaje": tasa_aprobacion,
        "plazo_garantia_dias": 7,
        "plazo_garantia_horas": 168.0
    }


@router.get("/ventas-recientes", summary="Listar ventas recientes para verificación rápida de garantía")
@router_compat.get("/ventas-recientes")
@router_api_compat.get("/ventas-recientes", include_in_schema=False)
def listar_ventas_recientes_garantia(db: Session = Depends(get_db)):
    """Retorna las ventas más recientes con cálculo de horas de garantía y estado de elegibilidad."""
    ventas = db.query(Venta).options(
        joinedload(Venta.cliente),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.ropa),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.talla),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.color)
    ).order_by(Venta.fecha.desc()).limit(20).all()

    resultado = []
    for v in ventas:
        horas = _calcular_horas_transcurridas(v.fecha)
        horas_rest = max(0.0, PLAZO_GARANTIA_HORAS - horas)
        elegible = horas <= PLAZO_GARANTIA_HORAS

        items = []
        for d in (v.detalles or []):
            p_nom = d.variante.ropa.nombre if (d.variante and d.variante.ropa) else "Prenda FashionStore"
            p_tal = d.variante.talla.medida if (d.variante and d.variante.talla) else "M"
            p_col = d.variante.color.nombre if (d.variante and d.variante.color) else "Normal"
            p_img = getattr(d.variante.ropa, 'imagen_principal', None) or getattr(d.variante.ropa, 'imagen_uri', None) if (d.variante and d.variante.ropa) else None

            items.append({
                "detalle_id": d.id,
                "variante_id": d.variante_id,
                "ropa_id": d.variante.ropa_id if d.variante else None,
                "prenda_nombre": p_nom,
                "talla": p_tal,
                "color": p_col,
                "cantidad": d.cantidad,
                "precio_unitario": float(d.precio_unitario or 0.0),
                "subtotal": float(d.subtotal or 0.0),
                "imagen_url": p_img
            })

        cli_nom = "Consumidor Final"
        cli_ci = "0"
        if v.cliente and hasattr(v.cliente, 'persona') and v.cliente.persona:
            cli_nom = f"{v.cliente.persona.nombre} {v.cliente.persona.apellido}".strip()
            cli_ci = v.cliente.ci or "0"
        elif v.cliente and hasattr(v.cliente, 'nombre'):
            cli_nom = f"{v.cliente.nombre} {getattr(v.cliente, 'apellido_pat', '')}".strip()
            cli_ci = v.cliente.ci or "0"

        resultado.append({
            "venta_id": v.id,
            "fecha": v.fecha.isoformat() if v.fecha else None,
            "monto_total": float(v.total or 0.0),
            "estado_pago": v.estado_pago,
            "cliente_nombre": cli_nom,
            "cliente_ci": cli_ci,
            "horas_transcurridas": round(horas, 1),
            "horas_restantes": round(horas_rest, 1),
            "dias_restantes": round(horas_rest / 24.0, 1),
            "elegible": elegible,
            "items_count": len(items),
            "items": items
        })

    return resultado


@router.get("/variantes-disponibles", summary="Listar variantes disponibles para cambio de talla")
@router_compat.get("/variantes-disponibles")
@router_api_compat.get("/variantes-disponibles", include_in_schema=False)
def listar_variantes_disponibles(
    sucursal_id: int = 1,
    ropa_id: Optional[int] = None,
    variante_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Retorna las variantes únicas por talla disponibles para realizar el cambio de talla (RN-02)."""
    # Si viene variante_id y no ropa_id, resolver la prenda a la que pertenece
    if not ropa_id and variante_id:
        v_ref = db.query(VariantePrenda).filter(VariantePrenda.id == variante_id).first()
        if v_ref:
            ropa_id = v_ref.ropa_id

    query = db.query(VariantePrenda).options(
        joinedload(VariantePrenda.ropa),
        joinedload(VariantePrenda.talla),
        joinedload(VariantePrenda.color)
    )

    if ropa_id:
        query = query.filter(VariantePrenda.ropa_id == ropa_id)

    variantes = query.all()

    # Deduplicar estrictamente por talla para no mostrar tallas repetidas
    vistas_tallas = set()
    resultado = []
    for var in variantes:
        talla_str = var.talla.medida if var.talla else "M"
        if talla_str in vistas_tallas:
            continue
        vistas_tallas.add(talla_str)

        inv = db.query(InventarioSucursal).filter(
            InventarioSucursal.sucursal_id == sucursal_id,
            InventarioSucursal.variante_id == var.id
        ).first()

        stock_fis = inv.stock_fisico if inv else 10
        precio = float(var.ropa.precio if var.ropa else 100.0)

        resultado.append({
            "variante_id": var.id,
            "ropa_id": var.ropa_id,
            "prenda_nombre": var.ropa.nombre if var.ropa else "Prenda",
            "talla": talla_str,
            "color": var.color.nombre if var.color else "Estándar",
            "precio": precio,
            "stock_disponible": max(0, stock_fis)
        })

    return resultado

