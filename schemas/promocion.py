from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

class PromocionBase(BaseModel):
    """Atributos base de una campaña promocional"""
    nombre: str = Field(
        ...,
        min_length=3,
        max_length=120,
        description="Nombre de la campaña (ej. Rebajas de Primavera, Cyber Week 20%)"
    )
    descuento_pct: float = Field(
        ...,
        gt=0,
        le=100,
        description="Porcentaje de descuento aplicable (debe ser mayor a 0 y menor o igual a 100)"
    )
    fecha_inicio: datetime = Field(
        ...,
        description="Fecha y hora de inicio de la vigencia de la promoción"
    )
    fecha_fin: datetime = Field(
        ...,
        description="Fecha y hora de finalización de la vigencia de la promoción"
    )

    @field_validator("nombre")
    @classmethod
    def validar_nombre_no_vacio(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("El nombre de la promoción es obligatorio.")
        return v.strip()


class PromocionCreate(PromocionBase):
    """
    Esquema para crear una nueva promoción y asociarla a prendas (Entrada POST - CU08).
    Implementa la Excepción A1: Valida que la fecha de fin no sea anterior a la de inicio.
    """
    productos_ids: List[int] = Field(
        default=[],
        description="Lista de IDs de productos del catálogo que recibirán la rebaja de precio"
    )

    @model_validator(mode="after")
    def validar_rango_fechas(self):
        # Excepción A1: Validación de consistencia temporal
        if self.fecha_fin <= self.fecha_inicio:
            raise ValueError(
                "Excepción A1: La fecha de finalización de la campaña no puede ser anterior "
                "ni igual a la fecha de inicio."
            )
        return self


class PromocionResponse(PromocionBase):
    """Esquema de salida de campaña promocional"""
    id: int
    activo: bool
    esta_vigente: bool
    total_productos_afectados: int
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)


class CalculoPrecioResponse(BaseModel):
    """
    Respuesta para el cálculo dinámico de precio con descuento
    utilizado por el E-commerce y el Punto de Venta (POS).
    """
    producto_id: int
    codigo_prenda: str
    nombre_prenda: str
    precio_base: float
    descuento_pct: float
    monto_descuento: float
    precio_final: float
    aplica_descuento: bool
    nombre_promocion: Optional[str] = None
