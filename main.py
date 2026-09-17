from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from database import engine, Base
import models  # Registra todos los modelos (parametros, sucursal, catalogo, promocion, carrito, venta)
from routers.tallas import router as tallas_router, router_compat as tallas_compat_router
from routers.sucursales import router as sucursales_router, router_compat as sucursales_compat_router
from routers.catalogo import (
    router as catalogo_router,
    router_catalogo_compat,
    router_productos_compat,
    router_productos_v1,
    router_productos_detalle_compat,
    router_marcas_compat,
    router_multimedios_compat,
    router_variantes_compat
)
from routers.promociones import router as promociones_router, router_compat as promociones_compat_router
from routers.inventario_local import router as inventario_local_router, router_compat as inventario_local_compat_router
from routers.traspasos import router as traspasos_router, router_compat as traspasos_compat_router
from routers.carrito import router as carrito_router, router_compat as carrito_compat_router
from routers.ventas import router as ventas_router, compat_router as ventas_compat_router
from routers.catalogo_disponibilidad import router as catalogo_disponibilidad_router, router_compat as catalogo_disponibilidad_compat_router
from routers.reservas import router as reservas_router, router_compat as reservas_compat_router
from routers.carrito_persistente import router as carrito_persistente_router
from routers.ar_vestidor import router as ar_vestidor_router
from routers.recomendador_ia import router as recomendador_ia_router, compat_router as recomendador_ia_compat_router
from routers.reportes_voz import router as reportes_voz_router
from routers.reportes_tabulares import router as reportes_tabulares_router, compat_router as reportes_tabulares_compat_router
from routers.resenas_calificaciones import router as resenas_calificaciones_router, compat_router as resenas_compat_router
from routers.parametros_catalogo import (
    router as parametros_catalogo_router,
    router_proveedores_compat,
    router_proveedores_v1_compat,
    router_categorias_compat,
    router_temporadas_compat,
    router_colores_compat
)
from routers.seguridad import router as seguridad_router
from routers.personal import router as personal_router
from routers.bitacora import router as bitacora_router, router_compat as bitacora_compat_router
from routers.cu02_personal import router as cu02_personal_router
from routers.fidelizacion import (
    router_config as fidelizacion_config_router,
    router_config_compat as fidelizacion_config_compat_router,
    router_beneficio as fidelizacion_beneficio_router,
    router_beneficio_compat as fidelizacion_beneficio_compat_router
)
from routers.ia_alertas import router as ia_alertas_router, compat_router as ia_alertas_compat_router
from routers.notificaciones import router as notificaciones_router, compat_router as notificaciones_compat_router
from routers.suscripciones import router as suscripciones_router
from routers.sugerencias_compra import router as sugerencias_compra_router

# Crear tablas en base de datos si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FashionStore API - Backend de Comercio Electrónico Omnicanal",
    description=(
        "API REST desarrollada con **Python + FastAPI**, **SQLAlchemy ORM** y **PostgreSQL** "
        "para la plataforma FashionStore (Tienda de ropa con vestidores virtuales AR e IA).\n\n"
        "### Módulos Implementados:\n"
        "- **CU05: Parámetros de Moda (Tallas)**: Control de duplicados e integridad relacional.\n"
        "- **CU06: Sucursales de la Cadena y Traspasos**: Gestión de sucursales físicas y logística inter-tiendas.\n"
        "- **CU07: Catálogo de Prendas y Recursos 3D**: Prenda base, fotos y modelos 3D (.glb).\n"
        "- **CU08: Promociones y Descuentos**: Campañas con validación temporal y cálculo dinámico.\n"
        "- **CU09 / CU13: Carrito de Compras Persistente**: Persistencia omnicanal y bloqueo de stock.\n"
        "- **CU11: Disponibilidad en Tiempo Real**: Desglose exacto de existencias por sucursal.\n"
        "- **CU12: Reservas Web-to-Store**: Apartado de 48h para retiro/pago presencial.\n"
        "- **CU14: Ventas Físicas en POS**: Venta con cajero, control de vuelto y Facturación Fiscal.\n"
        "- **CU15: Ventas Digitales E-commerce**: Pasarelas de pago y rollback de stock ante rechazos.\n"
        "- **CU16: Vestidor Virtual (AR)**: Endpoints de metadatos 3D y texturas para Flutter / ARCore.\n"
        "- **CU17: Recomendador Inteligente (IA)**: Generador de outfits y combinaciones de venta cruzada.\n"
        "- **CU18: Reportes mediante Comandos de Voz**: Transcripción y analítica de datos para gráficos gerenciales.\n"
        "- **CU19: Gestionar Reseñas y Calificaciones**: Registro de feedback, satisfacción e histograma de estrellas."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuración de CORS para permitir peticiones desde cualquier origen y puerto
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar carpeta de archivos estáticos (fotografías y modelos 3D .glb)
os.makedirs(os.path.join("static", "uploads"), exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Inclusión de Routers modulares por Caso de Uso
app.include_router(tallas_router)
app.include_router(tallas_compat_router)
app.include_router(sucursales_router)
app.include_router(sucursales_compat_router)
app.include_router(catalogo_router)
app.include_router(router_catalogo_compat)
app.include_router(router_productos_compat)
app.include_router(router_productos_v1)
app.include_router(router_productos_detalle_compat)
app.include_router(router_marcas_compat)
app.include_router(router_multimedios_compat)
app.include_router(router_variantes_compat)
app.include_router(promociones_router)
app.include_router(promociones_compat_router)
app.include_router(inventario_local_router)
app.include_router(inventario_local_compat_router)
app.include_router(traspasos_router)
app.include_router(traspasos_compat_router)
app.include_router(carrito_router)
app.include_router(carrito_compat_router)
app.include_router(ventas_router)
app.include_router(ventas_compat_router)
app.include_router(fidelizacion_beneficio_router)
app.include_router(fidelizacion_beneficio_compat_router)
app.include_router(fidelizacion_config_router)
app.include_router(fidelizacion_config_compat_router)
app.include_router(ia_alertas_router)
app.include_router(ia_alertas_compat_router)
app.include_router(notificaciones_router)
app.include_router(notificaciones_compat_router)
app.include_router(catalogo_disponibilidad_router)
app.include_router(catalogo_disponibilidad_compat_router)
app.include_router(reservas_router)
app.include_router(reservas_compat_router)
app.include_router(carrito_persistente_router)
app.include_router(ar_vestidor_router)
app.include_router(recomendador_ia_router)
app.include_router(recomendador_ia_compat_router)
app.include_router(reportes_voz_router)
app.include_router(reportes_tabulares_router)
app.include_router(reportes_tabulares_compat_router)
app.include_router(resenas_calificaciones_router)
app.include_router(resenas_compat_router)
app.include_router(parametros_catalogo_router)
app.include_router(router_proveedores_compat)
app.include_router(router_proveedores_v1_compat)
app.include_router(router_categorias_compat)
app.include_router(router_temporadas_compat)
app.include_router(router_colores_compat)
app.include_router(seguridad_router)
app.include_router(personal_router)
app.include_router(bitacora_router)
app.include_router(bitacora_compat_router)
app.include_router(cu02_personal_router)
app.include_router(suscripciones_router)
app.include_router(sugerencias_compra_router)

@app.get("/", tags=["Estado del Sistema"])
def raiz():
    return {
        "proyecto": "FashionStore - Smart E-Commerce",
        "materia": "Sistemas de Información 2 - MSc. Ing. Angélica Garzón Cuéllar",
        "estado": "Operativo",
        "framework": "FastAPI + SQLAlchemy + PostgreSQL",
        "modulos_activos": [
            "CU05 (Tallas)",
            "CU06 (Sucursales)",
            "CU07 (Catálogo & 3D)",
            "CU08 (Promociones)",
            "CU09/CU13 (Carrito Persistente)",
            "CU11 (Disponibilidad en Tiempo Real)",
            "CU12 (Reservas Web-to-Store)",
            "CU14 (Ventas Físicas en POS)",
            "CU15 (Ventas Digitales E-commerce)",
            "CU16 (Vestidor Virtual AR)",
            "CU17 (Recomendador Inteligente IA)",
            "CU18 (Reportes por Comandos de Voz)",
            "CU19 (Reseñas y Calificaciones)"
        ],
        "documentacion_interactiva": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
