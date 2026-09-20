"""
CU03: Bitácora de Auditoría Inmutable.
- Zona horaria Bolivia (America/La_Paz = UTC-4)
- Paginación compatible con el frontend Angular
- Acciones: INSERT/CREATE, UPDATE, DELETE, LOGIN, LOGOUT
- Registra IP del cliente en cada operación
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
import pytz

from database import get_db
from models.seguridad_persona import Bitacora, Usuario

router = APIRouter(
    prefix="/api/v1/bitacora",
    tags=["CU03. Gestionar bitácora de auditoría inmutable"]
)

# ─── Zona horaria Bolivia ─────────────────────────────────────────────────────
TZ_BOLIVIA = pytz.timezone('America/La_Paz')
try:
    import pytz
    TZ_BOLIVIA = pytz.timezone('America/La_Paz')
    def now_bolivia() -> datetime:
        return datetime.now(TZ_BOLIVIA)
except ImportError:
    from datetime import timezone, timedelta
    TZ_BOLIVIA = timezone(timedelta(hours=-4))
    def now_bolivia() -> datetime:
        return datetime.now(TZ_BOLIVIA)

def now_bolivia() -> datetime:
    """Hora actual en Bolivia (UTC-4)."""
    return datetime.now(TZ_BOLIVIA)

# ─── Función pública para registrar desde cualquier router ───────────────────
def obtener_usuario_e_ip(request: Request) -> tuple[Optional[int], str]:
    ip = "127.0.0.1"
    if request.client and request.client.host:
        ip = request.client.host
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip = forwarded.split(",")[0].strip()

    usuario_id = None
    user_header = request.headers.get("x-user-id")
    if user_header and user_header.isdigit():
        usuario_id = int(user_header)

    return usuario_id, ip

def registrar_bitacora(
    db: Session,
    accion: str,
    tabla: str,
    registro_id: str,
    detalles: str,
    usuario_id: Optional[int] = None,
    ip_origen: Optional[str] = None,
    request: Optional[Request] = None
):
    """
    Registra un evento inmutable en la bitácora.
    Normaliza acciones a: INSERT, UPDATE, DELETE, LOGIN, LOGOUT
    """
    if request:
        req_user_id, req_ip = obtener_usuario_e_ip(request)
        if usuario_id is None:
            usuario_id = req_user_id
        if not ip_origen:
            ip_origen = req_ip

    # Si usuario_id sigue siendo None, buscar el admin por defecto para que no quede NULL
    if usuario_id is None:
        admin_usr = db.query(Usuario).filter(Usuario.nombre_usuario == 'admin').first()
        if admin_usr:
            usuario_id = admin_usr.id
        else:
            primer_usr = db.query(Usuario).first()
            if primer_usr:
                usuario_id = primer_usr.id
            else:
                usuario_id = 1

    if not ip_origen:
        ip_origen = "127.0.0.1"

    # Normalizar alias de acciones
    accion_norm = accion.upper().strip()
    alias = {
        "CREATE": "INSERT",
        "ADD":    "INSERT",
        "EDIT":   "UPDATE",
        "REMOVE": "DELETE",
    }
    accion_norm = alias.get(accion_norm, accion_norm)

    try:
        nueva = Bitacora(
            accion=accion_norm,
            tabla_afectada=tabla,
            registro_id=str(registro_id),
            detalles=detalles,
            usuario_id=usuario_id,
            ip_origen=ip_origen,
            fecha_hora=now_bolivia()
        )
        db.add(nueva)
        db.commit()
    except Exception as e:
        print("Error al registrar bitacora:", e)
        db.rollback()

# ─── GET /api/v1/bitacora/ ────────────────────────────────────────────────────
@router.get("/")
def listar_bitacora(
    accion:       Optional[str] = Query(None, description="Filtrar por acción: INSERT, UPDATE, DELETE, LOGIN, LOGOUT"),
    metodo:       Optional[str] = Query(None, description="Alias de método HTTP (GET/POST/PUT/DELETE)"),
    usuario_id:   Optional[int] = Query(None),
    fecha_inicio: Optional[datetime] = Query(None),
    fecha_fin:    Optional[datetime] = Query(None),
    page:         int = Query(1, ge=1),
    page_size:    int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lista la bitácora de auditoría con paginación y filtros."""
    query = db.query(Bitacora)

    # Filtros
    if accion:
        accion_norm = accion.upper()
        mapa = {"CREATE": "INSERT", "UPDATE": "UPDATE", "DELETE": "DELETE",
                "LOGIN": "LOGIN", "LOGOUT": "LOGOUT"}
        query = query.filter(Bitacora.accion == mapa.get(accion_norm, accion_norm))
    if usuario_id:
        query = query.filter(Bitacora.usuario_id == usuario_id)
    if fecha_inicio:
        query = query.filter(Bitacora.fecha_hora >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Bitacora.fecha_hora <= fecha_fin)
    
    total = query.count()
    registros = (
        query.order_by(Bitacora.fecha_hora.desc())
             .offset((page - 1) * page_size)
             .limit(page_size)
             .all()
    )

    base = "/api/v1/bitacora/"
    results = []
    for r in registros:
        fecha_str = None
        hora_str = None
        fecha_hora_str = None
        if r.fecha_hora:
            fecha_str = r.fecha_hora.strftime("%Y-%m-%d")
            hora_str = r.fecha_hora.strftime("%H:%M:%S")
            fecha_hora_str = f"{fecha_str}T{hora_str}-04:00"

        username_val = r.usuario.nombre_usuario if r.usuario else ("admin" if r.usuario_id == 1 else f"Usuario #{r.usuario_id or '?'}")
        entidad_val = (r.tabla_afectada or "seguridad").capitalize()

        metodo_val = "POST"
        if r.accion == "UPDATE":
            metodo_val = "PUT"
        elif r.accion == "DELETE":
            metodo_val = "DELETE"
        elif r.accion in ["LOGIN", "LOGOUT"]:
            metodo_val = "POST"

        results.append({
            "id":              r.id,
            "id_bitacora":     r.id,
            "fecha":           fecha_str,
            "hora":            hora_str,
            "fecha_hora":      fecha_hora_str,
            "created_at":      fecha_hora_str,
            "accion":          r.accion,
            "action":          r.accion,
            "tabla_afectada":  r.tabla_afectada,
            "entidad":         entidad_val,
            "registro_id":     r.registro_id,
            "detalles":        r.detalles,
            "descripcion":     r.detalles,
            "ip_origen":       r.ip_origen,
            "ip_cliente":      r.ip_origen or "127.0.0.1",
            "usuario_id":      r.usuario_id,
            "usuarios_id":     r.usuario_id,
            "usuario_username": username_val,
            "username":        username_val,
            "metodo":          metodo_val,
            "ruta":            f"/api/{r.tabla_afectada or 'seguridad'}/",
            "estado_http":     200,
        })

    return {
        "count":    total,
        "next":     f"{base}?page={page+1}&page_size={page_size}" if page * page_size < total else None,
        "previous": f"{base}?page={page-1}&page_size={page_size}" if page > 1 else None,
        "results":  results
    }

# ─── GET /api/bitacora/ ── alias sin versión (para compatibilidad frontend) ──
router_compat = APIRouter(
    prefix="/api/bitacora",
    tags=["CU03. Gestionar bitácora de auditoría inmutable"]
)

@router_compat.get("/")
def listar_bitacora_compat(
    accion:       Optional[str] = Query(None),
    metodo:       Optional[str] = Query(None),
    usuario_id:   Optional[int] = Query(None),
    fecha_inicio: Optional[datetime] = Query(None),
    fecha_fin:    Optional[datetime] = Query(None),
    page:         int = Query(1, ge=1),
    page_size:    int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Alias /api/bitacora/ -> /api/v1/bitacora/ para compatibilidad con el frontend."""
    return listar_bitacora(
        accion=accion, metodo=metodo, usuario_id=usuario_id,
        fecha_inicio=fecha_inicio, fecha_fin=fecha_fin,
        page=page, page_size=page_size, db=db
    )
