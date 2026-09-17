"""
Exportación de Esquemas Pydantic unificados para FashionStore.
"""
from schemas.talla import TallaBase, TallaCreate, TallaResponse
from schemas.sucursal import SucursalCreate, SucursalResponse, InventarioSucursalResponse, TraspasoCreate, TraspasoResponse
from schemas.catalogo import RopaCreate, RopaResponse, CategoriaResponse, TemporadaResponse, ProveedorResponse, VariantePrendaResponse, ResenaCreate, ResenaResponse
from schemas.promocion import PromocionCreate, PromocionResponse
from schemas.catalogo_disponibilidad import (
    StockSucursalResponse,
    VarianteConStockResponse,
    PrendaCatalogoDisponibilidadResponse,
    SucursalStockDetalleResponse,
)
from schemas.reserva import ReservaCreate, ReservaResponse, DetalleReservaCreate, DetalleReservaResponse
from schemas.carrito import DetalleCarritoCreate, DetalleCarritoResponse, CarritoCompraResponse
from schemas.venta import (
    ItemVentaCreate,
    VentaPOSCreate,
    VentaEcommerceCreate,
    VentaResponse,
    DetalleVentaResponse,
    FacturaResponse,
    MetodoPagoResponse,
    TipoVentaResponse
)
from schemas.innovacion import (
    MetadatosARResponse,
    ValidarAjusteCorporalRequest,
    AjusteCorporalResponse,
    GenerarOutfitRequest,
    OutfitRecomendadoResponse,
    FeedbackRecomendacionRequest,
    ComandoVozTextoRequest,
    ReporteVozResponse,
    ResenaCreateRequest,
    ResenaItemResponse,
    ResumenCalificacionesRopaResponse
)

__all__ = [
    "TallaBase", "TallaCreate", "TallaResponse",
    "SucursalCreate", "SucursalResponse", "InventarioSucursalResponse", "TraspasoCreate", "TraspasoResponse",
    "RopaCreate", "RopaResponse", "CategoriaResponse", "TemporadaResponse", "ProveedorResponse", "VariantePrendaResponse", "ResenaCreate", "ResenaResponse",
    "PromocionCreate", "PromocionResponse",
    "StockSucursalResponse", "VarianteConStockResponse", "PrendaCatalogoDisponibilidadResponse",
    "SucursalStockDetalleResponse",
    "ReservaCreate", "ReservaResponse", "DetalleReservaCreate", "DetalleReservaResponse",
    "DetalleCarritoCreate", "DetalleCarritoResponse", "CarritoCompraResponse",
    "ItemVentaCreate", "VentaPOSCreate", "VentaEcommerceCreate",
    "VentaResponse", "DetalleVentaResponse", "FacturaResponse", "MetodoPagoResponse", "TipoVentaResponse",
    "MetadatosARResponse", "ValidarAjusteCorporalRequest", "AjusteCorporalResponse",
    "GenerarOutfitRequest", "OutfitRecomendadoResponse", "FeedbackRecomendacionRequest",
    "ComandoVozTextoRequest", "ReporteVozResponse",
    "ResenaCreateRequest", "ResenaItemResponse", "ResumenCalificacionesRopaResponse"
]

