"""
Router para Suscripciones de Empresa, Planes y Tenants SaaS.
Gestiona el catálogo de planes, la suscripción activa por empresa
y la auditoría de cambios de plan.
"""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models.empresa_suscripcion import Empresa, PlanSuscripcion, SuscripcionEmpresa, HistorialCambioPlan
from schemas.empresa_suscripcion import (
    PlanResponse,
    EmpresaResponse,
    EmpresaCreate,
    SuscripcionResponse,
    CambiarPlanRequest,
    HistorialCambioPlanResponse
)

router = APIRouter(tags=["SaaS - Suscripciones y Planes Multitenant"])


def _formatear_suscripcion(s: SuscripcionEmpresa) -> SuscripcionResponse:
    plan = s.plan
    precio = float(plan.precio_anual if s.ciclo == "anual" else plan.precio_mensual) if plan else 0.0
    return SuscripcionResponse(
        id=s.id,
        empresa=s.empresa_id,
        plan=s.plan_id,
        plan_nombre=plan.nombre if plan else "Plan Desconocido",
        plan_codigo=plan.codigo if plan else "UNKNOWN",
        plan_precio=precio,
        estado=s.estado,
        ciclo=s.ciclo,
        fecha_inicio=s.fecha_inicio,
        fecha_fin=s.fecha_fin,
        auto_renovar=s.auto_renovar,
        ultima_renovacion=s.ultima_renovacion,
        limite_sucursales=plan.limite_sucursales if plan else 2,
        soporta_ia=plan.soporta_ia if plan else False,
        soporta_ar=plan.soporta_ar if plan else True,
        soporta_offline=plan.soporta_offline if plan else True,
    )


# ==============================================================================
# 1. PLANES DE SUSCRIPCIÓN
# ==============================================================================
@router.get("/api/planes/", response_model=None)
@router.get("/api/v1/planes/", response_model=None)
def listar_planes(
    page: Optional[int] = None,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    """Lista todos los planes de suscripción configurados en el SaaS."""
    query = db.query(PlanSuscripcion).filter(PlanSuscripcion.activo == True).order_by(PlanSuscripcion.id.asc())
    planes = query.all()

    items = [
        {
            "id": p.id,
            "codigo": p.codigo,
            "nombre": p.nombre,
            "descripcion": p.descripcion,
            "precio_mensual": float(p.precio_mensual),
            "precio_anual": float(p.precio_anual),
            "limite_sucursales": p.limite_sucursales,
            "limite_usuarios": p.limite_usuarios,
            "soporta_ar": p.soporta_ar,
            "soporta_ia": p.soporta_ia,
            "soporta_offline": p.soporta_offline,
            "activo": p.activo,
        }
        for p in planes
    ]

    if page is not None:
        return {
            "count": len(items),
            "next": None,
            "previous": None,
            "results": items
        }
    return items


# ==============================================================================
# 2. SUSCRIPCIONES
# ==============================================================================
@router.get("/api/suscripciones/", response_model=None)
@router.get("/api/v1/suscripciones/", response_model=None)
def obtener_suscripciones(
    empresa_id: Optional[int] = Query(None, description="Filtrar por empresa ID"),
    page: Optional[int] = None,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    """Retorna las suscripciones registradas (por empresa o globales)."""
    query = db.query(SuscripcionEmpresa).options(
        joinedload(SuscripcionEmpresa.plan),
        joinedload(SuscripcionEmpresa.empresa)
    )
    if empresa_id:
        query = query.filter(SuscripcionEmpresa.empresa_id == empresa_id)

    suscripciones = query.order_by(SuscripcionEmpresa.id.desc()).all()
    results = [_formatear_suscripcion(s).model_dump() for s in suscripciones]

    if page is not None:
        return {
            "count": len(results),
            "next": None,
            "previous": None,
            "results": results
        }
    return results


@router.get("/api/v1/suscripciones/mi-suscripcion", response_model=SuscripcionResponse)
def mi_suscripcion(
    empresa_id: int = Query(1, description="ID de la empresa del usuario actual"),
    db: Session = Depends(get_db)
):
    """Retorna la suscripción activa de la empresa del usuario."""
    suscripcion = db.query(SuscripcionEmpresa).options(
        joinedload(SuscripcionEmpresa.plan),
        joinedload(SuscripcionEmpresa.empresa)
    ).filter(
        SuscripcionEmpresa.empresa_id == empresa_id
    ).order_by(SuscripcionEmpresa.id.desc()).first()

    if not suscripcion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró suscripción activa para la empresa ID {empresa_id}"
        )
    return _formatear_suscripcion(suscripcion)


@router.post("/api/v1/suscripciones/cambiar-plan", response_model=SuscripcionResponse)
@router.post("/api/v1/suscripciones/{suscripcion_id}/cambiar-plan", response_model=SuscripcionResponse)
def cambiar_plan(
    req: CambiarPlanRequest,
    suscripcion_id: Optional[int] = None,
    empresa_id: int = Query(1, description="ID de la empresa si no se envía suscripcion_id"),
    db: Session = Depends(get_db)
):
    """
    Permite a la empresa actualizar o cambiar su plan de suscripción
    (ej: upgrade de Básico a Profesional) registrando la auditoría.
    """
    if suscripcion_id:
        suscripcion = db.query(SuscripcionEmpresa).filter(SuscripcionEmpresa.id == suscripcion_id).first()
    else:
        suscripcion = db.query(SuscripcionEmpresa).filter(SuscripcionEmpresa.empresa_id == empresa_id).first()

    if not suscripcion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suscripción no encontrada."
        )

    nuevo_plan = db.query(PlanSuscripcion).filter(PlanSuscripcion.id == req.plan_id).first()
    if not nuevo_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan ID {req.plan_id} no encontrado en el catálogo."
        )

    plan_anterior_id = suscripcion.plan_id
    suscripcion.plan_id = nuevo_plan.id
    suscripcion.ciclo = req.ciclo or suscripcion.ciclo
    suscripcion.ultima_renovacion = datetime.utcnow()
    suscripcion.fecha_fin = datetime.utcnow() + timedelta(days=nuevo_plan.duracion_dias)

    # Registrar historial de cambio
    cambio = HistorialCambioPlan(
        suscripcion_id=suscripcion.id,
        plan_anterior_id=plan_anterior_id,
        plan_nuevo_id=nuevo_plan.id,
        cambiado_en=datetime.utcnow(),
        motivo=req.motivo or f"Cambio de plan a {nuevo_plan.nombre}"
    )
    db.add(cambio)
    db.commit()
    db.refresh(suscripcion)

    return _formatear_suscripcion(suscripcion)


# ==============================================================================
# 3. HISTORIAL DE CAMBIOS DE PLAN
# ==============================================================================
@router.get("/api/suscripcion-cambios/", response_model=None)
@router.get("/api/v1/suscripcion-cambios/", response_model=None)
def obtener_cambios_suscripcion(
    suscripcion_id: Optional[int] = Query(None),
    page: Optional[int] = None,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    query = db.query(HistorialCambioPlan).options(
        joinedload(HistorialCambioPlan.plan_anterior),
        joinedload(HistorialCambioPlan.plan_nuevo)
    )
    if suscripcion_id:
        query = query.filter(HistorialCambioPlan.suscripcion_id == suscripcion_id)

    cambios = query.order_by(HistorialCambioPlan.cambiado_en.desc()).all()
    results = [
        {
            "id": c.id,
            "suscripcion": c.suscripcion_id,
            "plan_anterior": c.plan_anterior_id,
            "plan_anterior_nombre": c.plan_anterior.nombre if c.plan_anterior else None,
            "plan_nuevo": c.plan_nuevo_id,
            "plan_nuevo_nombre": c.plan_nuevo.nombre if c.plan_nuevo else "Plan",
            "cambiado_en": c.cambiado_en.isoformat(),
            "motivo": c.motivo,
        }
        for c in cambios
    ]

    if page is not None:
        return {
            "count": len(results),
            "next": None,
            "previous": None,
            "results": results
        }
    return results


# ==============================================================================
# 4. ADMINISTRACIÓN DE EMPRESAS (TENANTS)
# ==============================================================================
@router.get("/api/v1/empresas/", response_model=List[EmpresaResponse])
def listar_empresas(db: Session = Depends(get_db)):
    """Lista todas las empresas registradas en la plataforma SaaS."""
    empresas = db.query(Empresa).options(
        joinedload(Empresa.suscripciones).joinedload(SuscripcionEmpresa.plan)
    ).all()

    resp = []
    for e in empresas:
        activa = e.suscripcion_activa
        susc_dict = _formatear_suscripcion(activa).model_dump() if activa else None
        resp.append(
            EmpresaResponse(
                id=e.id,
                razon_social=e.razon_social,
                nit=e.nit,
                slug=e.slug,
                logo_url=e.logo_url,
                color_marca=e.color_marca,
                descripcion=e.descripcion,
                direccion=e.direccion,
                ciudad=e.ciudad,
                telefono=e.telefono,
                correo_contacto=e.correo_contacto,
                estado=e.estado,
                creada_en=e.creada_en,
                plan_nombre=activa.plan.nombre if (activa and activa.plan) else "Sin Plan",
                suscripcion_actual=susc_dict
            )
        )
    return resp
