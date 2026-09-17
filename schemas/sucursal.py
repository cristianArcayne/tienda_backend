"""
Esquemas Pydantic para Sucursales, Inventario y Traspasos entre Tiendas.
Alineados fielmente con el Diagrama de Clases UML de FashionStore.
"""
from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field, ConfigDict


class SucursalCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    direccion: str = Field(..., min_length=3, max_length=200)
    ciudad: str = Field(default="Santa Cruz", max_length=50)
    telefono: Optional[str] = Field(None, max_length=30)


class SucursalResponse(BaseModel):
    id: int
    nombre: str
    direccion: str
    ciudad: str
    telefono: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class InventarioSucursalResponse(BaseModel):
    id: int
    sucursal_id: int
    variante_id: int
    stock_fisico: int
    stock_reservado: int
    stock_disponible: int
    sucursal_nombre: Optional[str] = None
    prenda_nombre: Optional[str] = None
    talla: Optional[str] = None
    color: Optional[str] = None
    cod_barra: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DetalleTraspasoCreate(BaseModel):
    variante_id: int
    cantidad: int = Field(..., gt=0)


class DetalleTraspasoResponse(BaseModel):
    id: int
    variante_id: int
    cantidad: int

    model_config = ConfigDict(from_attributes=True)


class TraspasoCreate(BaseModel):
    empleado_id: int
    sucursal_origen_id: int
    sucursal_destino_id: int
    detalles: List[DetalleTraspasoCreate]


class TraspasoResponse(BaseModel):
    id: int
    fecha: date
    estado: str
    empleado_id: int
    sucursal_origen_id: int
    sucursal_destino_id: int
    detalles: List[DetalleTraspasoResponse] = []

    model_config = ConfigDict(from_attributes=True)
