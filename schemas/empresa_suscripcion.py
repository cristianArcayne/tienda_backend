"""
Schemas Pydantic para el Módulo SaaS Multitenant y Planes de Suscripción.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


# === PLANES ===
class PlanBase(BaseModel):
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    precio_mensual: float = 0.0
    precio_anual: float = 0.0
    duracion_dias: int = 30
    limite_sucursales: int = 2
    limite_usuarios: int = 5
    soporta_ar: bool = True
    soporta_ia: bool = False
    soporta_offline: bool = True
    activo: bool = True


class PlanCreate(PlanBase):
    pass


class PlanResponse(PlanBase):
    id: int
    creado_en: Optional[datetime] = None

    class Config:
        from_attributes = True


# === EMPRESAS (TENANTS) ===
class EmpresaBase(BaseModel):
    razon_social: str
    nit: str
    slug: str
    logo_url: Optional[str] = None
    color_marca: Optional[str] = "#1e293b"
    descripcion: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = "Santa Cruz"
    telefono: Optional[str] = None
    correo_contacto: Optional[str] = None


class EmpresaCreate(EmpresaBase):
    plan_id: Optional[int] = 1


class EmpresaResponse(EmpresaBase):
    id: int
    estado: str
    creada_en: datetime
    plan_nombre: Optional[str] = None
    suscripcion_actual: Optional[dict] = None

    class Config:
        from_attributes = True


# === SUSCRIPCIONES ===
class SuscripcionBase(BaseModel):
    empresa_id: int
    plan_id: int
    estado: str = "ACTIVA"
    ciclo: str = "mensual"
    auto_renovar: bool = True


class CambiarPlanRequest(BaseModel):
    plan_id: int
    ciclo: Optional[str] = "mensual"
    motivo: Optional[str] = "Actualización administrativa de plan"


class SuscripcionResponse(BaseModel):
    id: int
    empresa: int
    plan: int
    plan_nombre: str
    plan_codigo: str
    plan_precio: float
    estado: str
    ciclo: str
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    auto_renovar: bool
    ultima_renovacion: Optional[datetime] = None
    limite_sucursales: int
    soporta_ia: bool
    soporta_ar: bool
    soporta_offline: bool

    class Config:
        from_attributes = True


class HistorialCambioPlanResponse(BaseModel):
    id: int
    suscripcion_id: int
    plan_anterior_id: Optional[int] = None
    plan_anterior_nombre: Optional[str] = None
    plan_nuevo_id: int
    plan_nuevo_nombre: str
    cambiado_en: datetime
    motivo: Optional[str] = None

    class Config:
        from_attributes = True
