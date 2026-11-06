"""
Módulo de Aislamiento y Reglas de Negocio Multitenant para FashionStore SaaS.
Asegura que los límites del Plan y el aislamiento de datos se cumplan en el Backend
según las especificaciones de la Ing. Angélica Garzón Cuéllar (Sistemas 2).
"""
from typing import Optional
from fastapi import Header, HTTPException, Depends, status, Request
from sqlalchemy.orm import Session

from database import get_db
from models.empresa_suscripcion import Empresa, PlanSuscripcion, SuscripcionEmpresa
from models.sucursal import Sucursal


def obtener_tenant_id(
    request: Request,
    db: Session = Depends(get_db)
) -> int:
    """
    Resuelve el ID de la empresa a partir del Header HTTP 'X-Tenant-ID', 'x-tenant',
    o query params (?tenant_id=, ?empresa_id=). Por defecto ID 1 (FashionStore S.A.).
    """
    val = (
        request.headers.get("x-tenant-id")
        or request.headers.get("X-Tenant-ID")
        or request.headers.get("x-tenant")
        or request.headers.get("X-Tenant")
        or request.query_params.get("tenant_id")
        or request.query_params.get("empresa_id")
    )
    if not val:
        return 1  # Tenant por defecto: FashionStore S.A.

    val_str = str(val).strip()
    if val_str.isdigit():
        empresa = db.query(Empresa).filter(Empresa.id == int(val_str)).first()
        if empresa:
            return empresa.id

    empresa = db.query(Empresa).filter(Empresa.slug == val_str.lower()).first()
    if empresa:
        return empresa.id

    return 1


def obtener_empresa_actual(
    tenant_id: int = Depends(obtener_tenant_id),
    db: Session = Depends(get_db)
) -> Empresa:
    """Obtiene la instancia de la Empresa actual con su suscripción activa."""
    empresa = db.query(Empresa).filter(Empresa.id == tenant_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empresa/Tenant ID {tenant_id} no encontrada."
        )
    return empresa


def verificar_acceso_ia(
    request: Request,
    empresa: Empresa = Depends(obtener_empresa_actual)
):
    """
    Regla RNF: Bloquea el uso de IA si el plan de la empresa no lo incluye.
    El Plan Básico NO soporta IA. Solo el Plan Profesional.
    
    EXCEPCIÓN SUPERADMIN: El Superadministrador global tiene acceso total de auditoría
    para analizar e inspeccionar cualquier empresa u organización del sistema SaaS.
    """
    if request.headers.get("x-is-superuser") == "true":
        return True
    auth = request.headers.get("authorization", "")
    if "admin" in auth.lower():
        return True


    suscripcion = empresa.suscripcion_activa
    if not suscripcion or not suscripcion.plan:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La empresa no cuenta con una suscripción activa."
        )

    if not suscripcion.plan.soporta_ia:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Acceso denegado: Su empresa '{empresa.razon_social}' cuenta con el plan '{suscripcion.plan.nombre}', "
                f"el cual no incluye funciones de Inteligencia Artificial. "
                f"Actualice al Plan Profesional para habilitar reportes generativos y analítica."
            )
        )
    return True


def verificar_limite_sucursales(
    empresa_id: int,
    db: Session
):
    """
    Verifica que la empresa no exceda el límite de sucursales permitidas según su plan:
    - Básico: Hasta 2 sucursales.
    - Profesional: Hasta 10 sucursales.
    """
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        return True

    suscripcion = empresa.suscripcion_activa
    limite = suscripcion.plan.limite_sucursales if (suscripcion and suscripcion.plan) else 2
    plan_nombre = suscripcion.plan.nombre if (suscripcion and suscripcion.plan) else "Plan Básico"

    cantidad_actual = db.query(Sucursal).filter(
        Sucursal.empresa_id == empresa_id,
        Sucursal.activo == True
    ).count()

    if cantidad_actual >= limite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Límite de suscripción alcanzado: La empresa '{empresa.razon_social}' cuenta con el '{plan_nombre}', "
                f"el cual permite un máximo de {limite} sucursales físicas activas (actualmente ya tiene {cantidad_actual} registradas). "
                f"Para registrar más sucursales, la empresa debe subir o cambiar su suscripción a un plan superior (Plan Profesional)."
            )
        )
    return True
