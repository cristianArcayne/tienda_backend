"""
Esquemas Pydantic para Carrito de Compras y Detalle de Carrito.
Alineados fielmente con el Diagrama de Clases UML de FashionStore.
"""
from typing import List, Optional, Union
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict


class DetalleCarritoCreate(BaseModel):
    variante_id: int
    cantidad: int = Field(..., gt=0)
    sucursal_id: Optional[int] = 1  # Tienda física desde la que se aparta el stock


class DetalleCarritoResponse(BaseModel):
    id: int
    variante_id: int
    cantidad: int
    cod_barra: Optional[str] = None
    prenda_nombre: Optional[str] = None
    precio_unitario: Optional[float] = None
    subtotal: Optional[float] = None
    talla: Optional[str] = None
    color: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CarritoCompraResponse(BaseModel):
    id: int
    fecha_creacion: Optional[Union[datetime, date]] = None
    cliente_id: Union[str, int]
    detalles: List[DetalleCarritoResponse] = []
    total_articulos: int = 0
    monto_total: float = 0.0

    model_config = ConfigDict(from_attributes=True)
