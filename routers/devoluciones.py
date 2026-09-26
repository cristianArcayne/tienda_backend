"""
Router para Gestión de Devoluciones de Compras (Regla de negocio: Plazo de 24 horas).
Soporta solicitud por el cliente y gestión/aprobación por Administrador/Personal.
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models.venta import Venta
from models.devolucion import Devolucion
from routers.notificaciones import crear_notificacion_sistema

router = APIRouter(
    prefix="/api/v1/devoluciones",
    tags=["Gestión de Devoluciones"]
)

router_compat = APIRouter(
    prefix="/devoluciones",
    tags=["Gestión de Devoluciones (Compatibilidad)"]
)


# Schemas Pydantic
class SolicitudDevolucionCreate(BaseModel):
    venta_id: int
    motivo: str = Field(..., min_length=5, description="Motivo detallado de la devolución")
    cuenta_bancaria_qr: Optional[str] = None


class ResponderDevolucionRequest(BaseModel):
    estado: str = Field(..., description="'APROBADA' o 'RECHAZADA'")
    respuesta_admin: Optional[str] = None


def _serializar_devolucion(dev: Devolucion) -> dict:
    horas_transcurridas = 0.0
    es_elegible_24h = False
    if dev.venta and dev.venta.fecha:
        delta = datetime.utcnow() - dev.venta.fecha
        horas_transcurridas = round(delta.total_seconds() / 3600.0, 2)
        es_elegible_24h = horas_transcurridas <= 24.0

    return {
        "id": dev.id,
        "venta_id": dev.venta_id,
        "cliente_id": dev.cliente_id,
        "motivo": dev.motivo,
        "estado": dev.estado,
        "fecha_solicitud": dev.fecha_solicitud.isoformat() if dev.fecha_solicitud else None,
        "fecha_respuesta": dev.fecha_respuesta.isoformat() if dev.fecha_respuesta else None,
        "respuesta_admin": dev.respuesta_admin,
        "monto_reembolso": float(dev.monto_reembolso) if dev.monto_reembolso else (float(dev.venta.total) if dev.venta else 0.0),
        "horas_transcurridas": horas_transcurridas,
        "es_elegible_24h": es_elegible_24h,
        "venta": {
            "id": dev.venta.id,
            "fecha": dev.venta.fecha.isoformat() if dev.venta and dev.venta.fecha else None,
            "monto_total": float(dev.venta.total) if dev.venta else 0.0,
            "estado_pago": dev.venta.estado_pago if dev.venta else None,
            "cliente_nombre": dev.venta.cliente.nombre if (dev.venta and dev.venta.cliente) else "Cliente"
        } if dev.venta else None
    }


# Endpoints principales
@router.get("/verificar-elegibilidad/{venta_id}")
@router_compat.get("/verificar-elegibilidad/{venta_id}")
def verificar_elegibilidad(venta_id: int, db: Session = Depends(get_db)):
    """
    Verifica si una compra específica es elegible para devolución (menos de 24 horas).
    """
    venta = db.query(Venta).filter(Venta.id == venta_id).first()
    if not venta:
        raise HTTPException(status_code=404, detail="Compra no encontrada.")

    dev_existente = db.query(Devolucion).filter(Devolucion.venta_id == venta_id).first()
    
    # Calcular horas transcurridas desde la venta
    fecha_venta = venta.fecha or datetime.utcnow()
    horas_transcurridas = (datetime.utcnow() - fecha_venta).total_seconds() / 3600.0
    horas_restantes = max(0.0, 24.0 - horas_transcurridas)
    elegible = (horas_transcurridas <= 24.0) and (dev_existente is None)

    motivo_inelegible = None
    if dev_existente:
        motivo_inelegible = f"Ya existe una solicitud de devolución registrada ({dev_existente.estado})."
    elif horas_transcurridas > 24.0:
        motivo_inelegible = f"El plazo de 24 horas ha expirado ({round(horas_transcurridas, 1)} horas transcurridas)."

    return {
        "venta_id": venta_id,
        "fecha_venta": fecha_venta.isoformat(),
        "horas_transcurridas": round(horas_transcurridas, 2),
        "horas_restantes": round(horas_restantes, 2),
        "elegible": elegible,
        "motivo_inelegible": motivo_inelegible,
        "devolucion_existente": _serializar_devolucion(dev_existente) if dev_existente else None
    }


@router.post("/solicitar")
@router_compat.post("/solicitar")
def solicitar_devolucion(body: SolicitudDevolucionCreate, db: Session = Depends(get_db)):
    """
    Registra la solicitud de devolución por parte del cliente dentro de las 24 horas.
    """
    venta = db.query(Venta).filter(Venta.id == body.venta_id).first()
    if not venta:
        raise HTTPException(status_code=404, detail="La compra especificada no existe.")

    # Regla de negocio: 24 horas
    fecha_venta = venta.fecha or datetime.utcnow()
    horas_transcurridas = (datetime.utcnow() - fecha_venta).total_seconds() / 3600.0
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

    # Crear la solicitud
    motivo_texto = body.motivo.strip()
    if body.cuenta_bancaria_qr and body.cuenta_bancaria_qr.strip():
        motivo_texto += f" | Cuenta/QR: {body.cuenta_bancaria_qr.strip()}"

    nueva_dev = Devolucion(
        venta_id=venta.id,
        cliente_id=venta.cliente_id,
        motivo=motivo_texto,
        estado="SOLICITADA",
        fecha_solicitud=datetime.utcnow(),
        monto_reembolso=venta.total
    )
    db.add(nueva_dev)

    # Actualizar estado de la venta
    venta.estado_pago = "EN_DEVOLUCION"
    db.commit()
    db.refresh(nueva_dev)

    # Notificación
    try:
        crear_notificacion_sistema(
            db=db,
            titulo=f"🔄 Solicitud de Devolución Pedido #{venta.id}",
            mensaje=f"Tu solicitud de devolución para el pedido #{venta.id} por Bs. {float(venta.total):.2f} ha sido recibida y está en revisión.",
            tipo="DEVOLUCION"
        )
    except Exception as e:
        print(f"[Devoluciones] Error enviando notificación: {e}")

    return {
        "message": "Solicitud de devolución registrada exitosamente dentro del plazo legal de 24 horas.",
        "devolucion": _serializar_devolucion(nueva_dev)
    }


@router.get("/mis-devoluciones")
@router_compat.get("/mis-devoluciones")
def listar_mis_devoluciones(cliente_ci: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Lista las solicitudes de devolución enviadas por los clientes.
    """
    query = db.query(Devolucion).options(
        joinedload(Devolucion.venta).joinedload(Venta.cliente)
    )
    if cliente_ci:
        query = query.filter(Devolucion.cliente_id == cliente_ci)

    devoluciones = query.order_by(Devolucion.fecha_solicitud.desc()).all()
    return [_serializar_devolucion(d) for d in devoluciones]


@router.get("/admin/listar")
@router_compat.get("/admin/listar")
def listar_devoluciones_admin(estado: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Lista general para el módulo de Administración y Gestión de Devoluciones (Web Dashboard).
    """
    query = db.query(Devolucion).options(
        joinedload(Devolucion.venta).joinedload(Venta.cliente)
    )

    if estado:
        query = query.filter(Devolucion.estado == estado.upper())

    devoluciones = query.order_by(Devolucion.fecha_solicitud.desc()).all()
    return {
        "total": len(devoluciones),
        "results": [_serializar_devolucion(d) for d in devoluciones]
    }


@router.put("/admin/{devolucion_id}/responder")
@router_compat.put("/admin/{devolucion_id}/responder")
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
    dev.respuesta_admin = body.respuesta_admin.strip() if body.respuesta_admin else None

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

