"""
Módulo de Aislamiento y Reglas de Negocio Multitenant para FashionStore SaaS.
Asegura que los límites del Plan y el aislamiento de datos se cumplan en el Backend
según las especificaciones de la Ing. Angélica Garzón Cuéllar (Sistemas 2).
"""
from typing import Optional
from fastapi import Header, HTTPException, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from models.empresa_suscripcion import Empresa, PlanSuscripcion, SuscripcionEmpresa
from models.sucursal import Sucursal


def obtener_tenant_id(
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID", description="ID o Slug del Tenant/Empresa"),
    db: Session = Depends(get_db)
) -> int:
    """
    Resuelve el ID de la empresa a partir del Header HTTP 'X-Tenant-ID' o por defecto empresa ID 1 (FashionStore).
    """
    if not x_tenant_id:
        return 1  # Tenant por defecto: FashionStore S.A.

    if str(x_tenant_id).isdigit():
        empresa = db.query(Empresa).filter(Empresa.id == int(x_tenant_id)).first()
        if empresa:
            return empresa.id

    empresa = db.query(Empresa).filter(Empresa.slug == str(x_tenant_id).strip().lower()).first()
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
    empresa: Empresa = Depends(obtener_empresa_actual)
):
    """
    Regla RNF: Bloquea el uso de IA si el plan de la empresa no lo incluye.
    El Plan Básico NO soporta IA. Solo el Plan Profesional.
    """
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

    cantidad_actual = db.query(Sucursal).filter(
        Sucursal.empresa_id == empresa_id,
        Sucursal.activo == True
    ).count()

    if cantidad_actual >= limite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Límite de sucursales alcanzado: Su plan '{suscripcion.plan.nombre if suscripcion and suscripcion.plan else 'Básico'}' "
                f"permite un máximo de {limite} sucursales activas. "
                f"Actualmente ya tiene {cantidad_actual} registradas. Actualice al Plan Profesional para registrar más sucursales."
            )
        )
    return True
