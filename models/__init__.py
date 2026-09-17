"""
Registro y exportación unificada de todos los Modelos de Datos de FashionStore
siguiendo fielmente el Diagrama de Clases UML (29 entidades).
"""
from database import Base

# 1. Seguridad, Personas y Auditoría
from models.seguridad_persona import (
    Persona,
    Empleado,
    Cliente,
    Usuario,
    Rol,
    Permiso,
    Bitacora
)

# 2. Catálogo, Ropa, Parámetros y Promociones
from models.catalogo import (
    Categoria,
    Temporada,
    Proveedor,
    Ropa,
    Talla,
    Color,
    VariantePrenda,
    Promocion,
    PromocionRopa,
    Resena
)

# 3. Sucursales, Inventario y Logística
from models.sucursal import (
    Sucursal,
    InventarioSucursal,
    Traspaso,
    DetalleTraspaso
)

# 4. Carrito de Compras
from models.carrito import (
    CarritoCompra,
    DetalleCarritoCompra
)

# 5. Reservas Web-to-Store
from models.reserva import (
    Reserva,
    DetalleReserva
)

# 6. Ventas, Métodos de Pago y Facturación
from models.venta import (
    MetodoPago,
    TipoVenta,
    Venta,
    DetalleVenta,
    Factura
)

# 7. Innovación, IA y AR
from models.innovacion import RecomendacionIA
from models.ia_alerta import AlertaIAModel
from models.fidelizacion import ConfiguracionFidelizacionModel
from models.notificacion import SuscripcionPushModel

__all__ = [
    "Base",
    "Persona", "Empleado", "Cliente", "Usuario", "Rol", "Permiso", "Bitacora",
    "Categoria", "Temporada", "Proveedor", "Ropa", "Talla", "Color",
    "VariantePrenda", "Promocion", "PromocionRopa", "Resena",
    "Sucursal", "InventarioSucursal", "Traspaso", "DetalleTraspaso",
    "CarritoCompra", "DetalleCarritoCompra",
    "Reserva", "DetalleReserva",
    "MetodoPago", "TipoVenta", "Venta", "DetalleVenta", "Factura",
    "RecomendacionIA", "AlertaIAModel", "ConfiguracionFidelizacionModel", "SuscripcionPushModel"
]
