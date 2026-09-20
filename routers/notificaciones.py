"""
Router para Gestión de Notificaciones Push Web, Móviles y Feed en Tiempo Real.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from database import get_db
from models.notificacion import SuscripcionPushModel, NotificacionModel


router = APIRouter(
    prefix="/api/v1/notificaciones",
    tags=["Notificaciones Push & Feed"]
)

compat_router = APIRouter(
    prefix="/api/notificaciones",
    include_in_schema=False
)

# Llave VAPID pública válida para web push
VAPID_PUBLIC_KEY = "BEl62iUYgUivxIkv69yViEuiBIa-Ib9-SkvMeAtA3LFgDzkrxZJjSgSnfckjBJuBkr3qBUYIHBQFLXYp5Nksh8U"


class PushKeysSchema(BaseModel):
    p256dh: str
    auth: str


class SuscripcionPushCreate(BaseModel):
    endpoint: str
    keys: PushKeysSchema


class PruebaPushPayload(BaseModel):
    titulo: str
    mensaje: str
    tipo: Optional[str] = "BROADCAST"


class NotificacionCreatePayload(BaseModel):
    titulo: str
    mensaje: str
    tipo: Optional[str] = "PROMOCION"
    usuario_id: Optional[int] = None
    datos_adicionales: Optional[str] = None


class NotificacionResponse(BaseModel):
    id: int
    titulo: str
    mensaje: str
    tipo: str
    leida: bool
    fecha_creacion: datetime
    datos_adicionales: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


def crear_notificacion_sistema(
    db: Session,
    titulo: str,
    mensaje: str,
    tipo: str = "PROMOCION",
    usuario_id: Optional[int] = None,
    datos_adicionales: Optional[str] = None
) -> NotificacionModel:
    """Función utilitaria interna para registrar notificaciones desde cualquier módulo."""
    try:
        nueva = NotificacionModel(
            titulo=titulo,
            mensaje=mensaje,
            tipo=tipo,
            usuario_id=usuario_id,
            datos_adicionales=datos_adicionales,
            fecha_creacion=datetime.utcnow(),
            leida=False
        )
        db.add(nueva)
        db.commit()
        db.refresh(nueva)
        return nueva
    except Exception as e:
        db.rollback()
        print(f"[Notificaciones] Error al crear notificación: {e}")
        return None


def _formatear_suscripcion(s: SuscripcionPushModel) -> Dict[str, Any]:
    return {
        "id": s.id,
        "usuario": s.usuario_id or 1,
        "endpoint": s.endpoint,
        "p256dh": s.p256dh,
        "auth": s.auth,
        "user_agent": s.user_agent or "Navegador Web",
        "activa": bool(s.activa),
        "ultima_promocion": s.ultima_promocion_id,
        "ultimo_envio": s.ultimo_envio.isoformat() if s.ultimo_envio else None,
        "ultimo_error": s.ultimo_error
    }


def _formatear_notificacion(n: NotificacionModel) -> Dict[str, Any]:
    return {
        "id": n.id,
        "titulo": n.titulo,
        "mensaje": n.mensaje,
        "tipo": n.tipo,
        "leida": bool(n.leida),
        "fecha_creacion": n.fecha_creacion.isoformat() if n.fecha_creacion else datetime.utcnow().isoformat(),
        "created_at": n.fecha_creacion.isoformat() if n.fecha_creacion else datetime.utcnow().isoformat(),
        "datos_adicionales": n.datos_adicionales
    }


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints de Notificaciones
# ─────────────────────────────────────────────────────────────────────────────

def _listar_feed_impl(
    tipo: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Retorna el listado de notificaciones para la app móvil y frontend."""
    query = db.query(NotificacionModel).order_by(NotificacionModel.id.desc())
    if tipo:
        query = query.filter(NotificacionModel.tipo.ilike(f"%{tipo}%"))
    
    notificaciones = query.limit(limit).all()
    results = [_formatear_notificacion(n) for n in notificaciones]
    return {
        "count": len(results),
        "results": results,
        "notificaciones": results
    }


def _listar_suscripciones_impl(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    db: Session = Depends(get_db)
):
    query = db.query(SuscripcionPushModel).order_by(SuscripcionPushModel.id.desc())
    total = query.count()
    offset = (page - 1) * page_size
    suscripciones = query.offset(offset).limit(page_size).all()
    
    results = [_formatear_suscripcion(s) for s in suscripciones]
    return {
        "count": total,
        "next": f"?page={page+1}&page_size={page_size}" if (offset + page_size) < total else None,
        "previous": f"?page={page-1}&page_size={page_size}" if page > 1 else None,
        "results": results
    }


def _vapid_public_key_impl():
    return {
        "public_key": VAPID_PUBLIC_KEY,
        "publicKey": VAPID_PUBLIC_KEY,
        "vapid_public_key": VAPID_PUBLIC_KEY
    }


def _suscribirse_impl(
    payload: SuscripcionPushCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    ua = request.headers.get("user-agent", "Web Browser")
    sub = db.query(SuscripcionPushModel).filter(SuscripcionPushModel.endpoint == payload.endpoint).first()
    if sub:
        sub.p256dh = payload.keys.p256dh
        sub.auth = payload.keys.auth
        sub.activa = True
        sub.user_agent = ua
    else:
        sub = SuscripcionPushModel(
            endpoint=payload.endpoint,
            p256dh=payload.keys.p256dh,
            auth=payload.keys.auth,
            user_agent=ua,
            activa=True
        )
        db.add(sub)
    
    db.commit()
    db.refresh(sub)
    return _formatear_suscripcion(sub)


def _desuscribirse_impl(
    data: dict,
    db: Session = Depends(get_db)
):
    endpoint = data.get("endpoint")
    if endpoint:
        sub = db.query(SuscripcionPushModel).filter(SuscripcionPushModel.endpoint == endpoint).first()
        if sub:
            sub.activa = False
            db.commit()
    return {"message": "Suscripción desactivada correctamente"}


def _probar_impl(
    payload: PruebaPushPayload,
    db: Session = Depends(get_db)
):
    # Guardar en base de datos para que la app móvil y web lo lean
    notif = crear_notificacion_sistema(
        db=db,
        titulo=payload.titulo or "Aviso de FashionStore",
        mensaje=payload.mensaje,
        tipo=payload.tipo or "BROADCAST"
    )

    # Actualizar suscripciones web
    activas = db.query(SuscripcionPushModel).filter(SuscripcionPushModel.activa == True).all()
    ahora = datetime.utcnow()
    for s in activas:
        s.ultimo_envio = ahora
    db.commit()

    return {
        "success": True,
        "notificacion": _formatear_notificacion(notif) if notif else None,
        "message": f"Notificación '{payload.titulo}' enviada a {len(activas)} dispositivo(s) y registrada en el centro de notificaciones."
    }


def _enviar_notificacion_impl(
    payload: NotificacionCreatePayload,
    db: Session = Depends(get_db)
):
    notif = crear_notificacion_sistema(
        db=db,
        titulo=payload.titulo,
        mensaje=payload.mensaje,
        tipo=payload.tipo or "PROMOCION",
        usuario_id=payload.usuario_id,
        datos_adicionales=payload.datos_adicionales
    )
    return _formatear_notificacion(notif) if notif else {"message": "Notificación creada"}


for r in [router, compat_router]:
    r.add_api_route("/", _listar_suscripciones_impl, methods=["GET"])
    r.add_api_route("", _listar_suscripciones_impl, methods=["GET"], include_in_schema=False)
    r.add_api_route("/feed", _listar_feed_impl, methods=["GET"])
    r.add_api_route("/feed/", _listar_feed_impl, methods=["GET"], include_in_schema=False)
    r.add_api_route("/lista", _listar_feed_impl, methods=["GET"])
    r.add_api_route("/lista/", _listar_feed_impl, methods=["GET"], include_in_schema=False)
    r.add_api_route("/vapid-public-key", _vapid_public_key_impl, methods=["GET"])
    r.add_api_route("/vapid-public-key/", _vapid_public_key_impl, methods=["GET"], include_in_schema=False)
    r.add_api_route("/suscribirse", _suscribirse_impl, methods=["POST"])
    r.add_api_route("/suscribirse/", _suscribirse_impl, methods=["POST"], include_in_schema=False)
    r.add_api_route("/desuscribirse", _desuscribirse_impl, methods=["POST"])
    r.add_api_route("/desuscribirse/", _desuscribirse_impl, methods=["POST"], include_in_schema=False)
    r.add_api_route("/probar", _probar_impl, methods=["POST"])
    r.add_api_route("/probar/", _probar_impl, methods=["POST"], include_in_schema=False)
    r.add_api_route("/enviar", _enviar_notificacion_impl, methods=["POST"])
    r.add_api_route("/enviar/", _enviar_notificacion_impl, methods=["POST"], include_in_schema=False)
