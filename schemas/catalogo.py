"""
Esquemas Pydantic para el Catálogo de Prendas, Variantes, Categorías, Colores, Tallas, Proveedores y Temporadas.
Alineados fielmente con el Diagrama de Clases UML de FashionStore.
"""
from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field, field_validator, ConfigDict


class CategoriaCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)

class CategoriaResponse(BaseModel):
    id: int
    nombre: str

    model_config = ConfigDict(from_attributes=True)


class TemporadaCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=50)

class TemporadaResponse(BaseModel):
    id: int
    nombre: str

    model_config = ConfigDict(from_attributes=True)


class ProveedorCreate(BaseModel):
    razon_social: Optional[str] = Field(None, max_length=150)
    nombre: Optional[str] = Field(None, max_length=150)
    nit: Optional[str] = Field(None, max_length=50)
    correo: Optional[str] = Field(None, max_length=150)
    direccion: Optional[str] = Field(None, max_length=255)
    telefono: Optional[str] = Field(None, max_length=30)
    contacto: Optional[str] = Field(None, max_length=100)

class ProveedorResponse(BaseModel):
    id: int
    razon_social: str
    nombre: Optional[str] = None
    nit: Optional[str] = None
    correo: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    contacto: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TallaResponse(BaseModel):
    id: int
    medida: str

    model_config = ConfigDict(from_attributes=True)


class ColorCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=50)
    codigo_hex: Optional[str] = Field(None, max_length=10)

class ColorResponse(BaseModel):
    id: int
    nombre: str
    codigo_hex: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)



class VariantePrendaCreate(BaseModel):
    talla_id: int
    color_id: int
    sku: str = Field(..., max_length=50)
    cod_barra: str = Field(..., max_length=50)
    precio_ajustado: Optional[float] = None

class VariantePrendaResponse(BaseModel):
    id: int
    sku: Optional[str] = None
    cod_barra: str
    precio_ajustado: Optional[float] = None
    ropa_id: int
    talla_id: int
    color_id: int
    talla: Optional[TallaResponse] = None
    color: Optional[ColorResponse] = None

    model_config = ConfigDict(from_attributes=True)


class RopaCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    descripcion: Optional[str] = Field(None, max_length=500)
    precio: float = Field(..., gt=0)
    imagen_uri: Optional[str] = Field(None, max_length=255)
    modelo_3d_uri: Optional[str] = Field(None, max_length=255)  # URL de modelo .glb para AR
    categoria_id: Optional[int] = None
    temporada_id: Optional[int] = None
    proveedor_id: Optional[int] = None


class RopaResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    imagen_uri: Optional[str] = None
    modelo_3d_uri: Optional[str] = None
    categoria_id: Optional[int] = None
    temporada_id: Optional[int] = None
    proveedor_id: Optional[int] = None

    categoria: Optional[CategoriaResponse] = None
    temporada: Optional[TemporadaResponse] = None
    proveedor: Optional[ProveedorResponse] = None
    variantes: Optional[List[VariantePrendaResponse]] = []

    precio_promocional: Optional[float] = None
    tiene_modelo_ar: bool = False

    model_config = ConfigDict(from_attributes=True)


class ResenaCreate(BaseModel):
    puntuacion_estrellas: int = Field(..., ge=1, le=5)
    comentario: Optional[str] = None
    cliente_id: int
    ropa_id: int


class ResenaResponse(BaseModel):
    id: int
    puntuacion_estrellas: int
    comentario: Optional[str] = None
    fecha: date
    cliente_id: int
    ropa_id: int

    model_config = ConfigDict(from_attributes=True)
