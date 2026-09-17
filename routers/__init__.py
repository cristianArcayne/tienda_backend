from routers.tallas import router as tallas_router
from routers.sucursales import router as sucursales_router
from routers.catalogo import router as catalogo_router
from routers.promociones import router as promociones_router
from routers.carrito import router as carrito_router
from routers.ventas import router as ventas_router
from routers.catalogo_disponibilidad import router as catalogo_disponibilidad_router
from routers.reservas import router as reservas_router
from routers.carrito_persistente import router as carrito_persistente_router
from routers.personal import router as personal_router
from routers.bitacora import router as bitacora_router
from routers.parametros_catalogo import router as parametros_router

__all__ = [
    "tallas_router",
    "sucursales_router",
    "catalogo_router",
    "promociones_router",
    "carrito_router",
    "ventas_router",
    "catalogo_disponibilidad_router",
    "reservas_router",
    "carrito_persistente_router",
    "personal_router",
    "bitacora_router",
    "parametros_router"
]
