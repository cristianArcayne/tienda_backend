from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

class TallaBase(BaseModel):
    """Atributos comunes para la entidad Talla"""
    medida: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Identificador o código de la talla (ej. XS, S, M, L, XL, 38, 40)"
    )
    tipo: str = Field(
        default="Textil",
        max_length=30,
        description="Clasificación de la talla: 'Textil', 'Calzado' o 'Accesorio'"
    )
    guia_medida: Optional[str] = Field(
        default=None,
        max_length=150,
        description="Medida física en centímetros o guía orientativa (ej. Busto 92-98 cm)"
    )


class TallaCreate(TallaBase):
    """Esquema para la creación de una nueva Talla (Entrada POST)"""

    @field_validator("medida")
    @classmethod
    def validar_medida_no_vacia(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("La medida de la talla es obligatoria y no puede consistir únicamente en espacios.")
        return v.strip().upper()


class TallaResponse(TallaBase):
    """Esquema de respuesta serializada para Talla (Salida de la API)"""
    id: int

    model_config = ConfigDict(from_attributes=True)
