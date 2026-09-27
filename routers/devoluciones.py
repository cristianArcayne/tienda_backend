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

from database import get_db
from models.venta import Venta, DetalleVenta
from models.catalogo import VariantePrenda, Ropa, Talla, Color
from models.devolucion import Devolucion
from models.notificacion import SuscripcionPushModel
from routers.notificaciones import crear_notificacion_sistema

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
    es_elegible_24h = horas_transcurridas <= 24.0

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
    horas_restantes = max(0.0, 24.0 - horas_transcurridas)
    elegible = (horas_transcurridas <= 24.0) and (dev_existente is None)

    motivo_inelegible = None
    if dev_existente:
        motivo_inelegible = f"Ya existe una solicitud de devolución registrada ({dev_existente.estado})."
    elif horas_transcurridas > 24.0:
        motivo_inelegible = f"El plazo de 24 horas ha expirado ({round(horas_transcurridas, 1)} horas transcurridas)."

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
    if horas_transcurridas > 24.0:
        raise HTTPException(
            status_code=400,
            detail=f"El plazo límite de 24 horas para solicitar una devolución ha expirado. (Tiempo transcurrido: {round(horas_transcurridas, 1)} horas)."
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
        elif nuevo_estado == "RECHAZADA":
            dev.venta.estado_pago = "COMPLETADA"

    db.commit()
    db.refresh(dev)

    # Notificar al cliente
    try:
        icono = "✅" if nuevo_estado == "APROBADA" else "❌"
        crear_notificacion_sistema(
            db=db,
            titulo=f"{icono} Devolución {nuevo_estado} Pedido #{dev.venta_id}",
            mensaje=f"Tu solicitud de devolución para el pedido #{dev.venta_id} ha sido {nuevo_estado.lower()}." +
                    (f" Nota: {body.respuesta_admin}" if body.respuesta_admin else ""),
            tipo="DEVOLUCION"
        )
    except Exception as e:
        print(f"[Devoluciones] Error enviando notificación: {e}")

    return {
        "message": f"Devolución #{devolucion_id} fue {nuevo_estado} exitosamente.",
        "devolucion": _serializar_devolucion(dev)
    }

