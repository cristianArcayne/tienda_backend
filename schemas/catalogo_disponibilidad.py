"""
Esquemas Pydantic para Consulta de Catálogo y Disponibilidad en Tiempo Real (CU11).
Alineados con ROPA, VARIANTE_PRENDA, INVENTARIO_SUCURSAL y SUCURSAL del Diagrama UML.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class StockSucursalResponse(BaseModel):
    sucursal_id: int
    sucursal_nombre: str
    ciudad: str
    stock_fisico: int
    stock_reservado: int
    stock_disponible: int
    estado_stock: str

    model_config = ConfigDict(from_attributes=True)


class VarianteConStockResponse(BaseModel):
    variante_id: int
    sku: str
    talla: str
    color: str
    codigo_hex: Optional[str] = None
    precio_especifico: float
    stock_fisico_total: int
    stock_disponible_total: int
    estado_disponibilidad: str
    disponibilidad_sucursales: List[StockSucursalResponse] = []

    model_config = ConfigDict(from_attributes=True)


class PrendaCatalogoDisponibilidadResponse(BaseModel):
    id: int
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    precio_base: float
    precio_promocional: Optional[float] = None
    descuento_aplicado_pct: Optional[float] = None
    id_categoria: int
    categoria_nombre: str
    imagen_principal: Optional[str] = None
    modelo_3d_uri: Optional[str] = None
    tiene_modelo_ar: bool = False
    recursos_multimedia: List[str] = []
    variantes: List[VarianteConStockResponse] = []
    stock_fisico_cadena: int = 0
    stock_disponible_cadena: int = 0
    disponible_en_cadena: bool = False

    model_config = ConfigDict(from_attributes=True)


class SucursalStockDetalleResponse(BaseModel):
    prenda_id: int
    prenda_nombre: str
    sucursales: List[StockSucursalResponse] = []

    model_config = ConfigDict(from_attributes=True)
