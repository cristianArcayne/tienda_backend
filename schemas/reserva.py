"""
Esquemas Pydantic para Reservas Web-to-Store y Detalle de Reserva.
Alineados fielmente con el Diagrama de Clases UML de FashionStore.
"""
from typing import List, Optional, Union
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict


class DetalleReservaCreate(BaseModel):
    variante_id: int
    cantidad: int = Field(..., gt=0)


class DetalleReservaResponse(BaseModel):
    id: int
    variante_id: int
    cantidad: int
    cod_barra: Optional[str] = None
    prenda_nombre: Optional[str] = None
    imagen_url: Optional[str] = None
    talla: Optional[str] = None
    color: Optional[str] = None
    precio_unitario: Optional[float] = None
    subtotal: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class ReservaCreate(BaseModel):
    cliente_id: Optional[Union[str, int]] = "admin"
    cliente_nombre: Optional[str] = None
    sucursal_id: int
    hora_estimada: Optional[str] = "18:00"
    detalles: Optional[List[DetalleReservaCreate]] = None
    items: Optional[List[DetalleReservaCreate]] = None


class ReservaResponse(BaseModel):
    id: int
    fecha: Optional[Union[datetime, date]] = None
    fecha_limite: Optional[Union[datetime, date]] = None
    hora_estimada: Optional[str] = None
    estado: str
    cliente_id: Union[str, int]
    sucursal_id: int
    sucursal_nombre: Optional[str] = None
    cliente_nombre: Optional[str] = None
    detalles: List[DetalleReservaResponse] = []
    total_estimado: float = 0.0

    model_config = ConfigDict(from_attributes=True)
