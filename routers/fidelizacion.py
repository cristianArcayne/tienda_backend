"""
Router para Fidelización de Clientes y Configuración de Fidelización.
Soporta:
- Configuración global del programa de fidelización
- Consulta de beneficios acumulados por el cliente actual
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from database import get_db
from models.fidelizacion import ConfiguracionFidelizacionModel
from models.venta import Venta
from models.seguridad_persona import Cliente, Usuario


router_config = APIRouter(
    prefix="/api/v1/configuracion-fidelizacion",
    tags=["Fidelización de Clientes"]
)

router_config_compat = APIRouter(
    prefix="/api/configuracion-fidelizacion",
    include_in_schema=False
)

router_beneficio = APIRouter(
    prefix="/api/v1/ventas",
    tags=["Fidelización - Mis Beneficios"]
)

router_beneficio_compat = APIRouter(
    prefix="/api/ventas",
    include_in_schema=False
)


class ConfiguracionFidelizacionSchema(BaseModel):
    monto_minimo_acumulado: float
    monto_descuento: float
    activo: bool
    fecha_actualizacion: Optional[datetime] = None


class ConfiguracionFidelizacionUpdate(BaseModel):
    monto_minimo_acumulado: Optional[float] = None
    monto_descuento: Optional[float] = None
    activo: Optional[bool] = None


class BeneficioFidelizacionResponse(BaseModel):
    acumulado: float
    monto_minimo: float
    monto_descuento: float
    activo: bool
    usado: bool
    elegible: bool


def _obtener_configuracion(db: Session) -> ConfiguracionFidelizacionModel:
    config = db.query(ConfiguracionFidelizacionModel).first()
    if not config:
        config = ConfiguracionFidelizacionModel(
            monto_minimo_acumulado=100.0,
            monto_descuento=15.0,
            activo=True
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints de Configuración
# ─────────────────────────────────────────────────────────────────────────────

def _get_config_impl(db: Session = Depends(get_db)):
    config = _obtener_configuracion(db)
    return {
        "monto_minimo_acumulado": float(config.monto_minimo_acumulado),
        "monto_descuento": float(config.monto_descuento),
        "activo": bool(config.activo),
        "fecha_actualizacion": config.fecha_actualizacion.isoformat() if config.fecha_actualizacion else datetime.utcnow().isoformat()
    }


def _update_config_impl(data: ConfiguracionFidelizacionUpdate, db: Session = Depends(get_db)):
    config = _obtener_configuracion(db)
    if data.monto_minimo_acumulado is not None:
        config.monto_minimo_acumulado = data.monto_minimo_acumulado
    if data.monto_descuento is not None:
        config.monto_descuento = data.monto_descuento
    if data.activo is not None:
        config.activo = data.activo
    config.fecha_actualizacion = datetime.utcnow()
    db.commit()
    db.refresh(config)
    return {
        "monto_minimo_acumulado": float(config.monto_minimo_acumulado),
        "monto_descuento": float(config.monto_descuento),
        "activo": bool(config.activo),
        "fecha_actualizacion": config.fecha_actualizacion.isoformat()
    }


for r in [router_config, router_config_compat]:
    r.add_api_route("/", _get_config_impl, methods=["GET"])
    r.add_api_route("", _get_config_impl, methods=["GET"], include_in_schema=False)
    r.add_api_route("/", _update_config_impl, methods=["PUT", "PATCH"])
    r.add_api_route("", _update_config_impl, methods=["PUT", "PATCH"], include_in_schema=False)


# ─────────────────────────────────────────────────────────────────────────────
# Endpoint: Mi Beneficio (/api/v1/ventas/mi-beneficio-fidelizacion/)
# ─────────────────────────────────────────────────────────────────────────────

def _mi_beneficio_impl(
    request: Request,
    cliente_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    config = _obtener_configuracion(db)
    hoy = datetime.utcnow()
    
    # Buscar cliente: si se pasa parámetro, o por defecto buscar ventas del mes actual
    # Si no se especifica cliente, calculamos el acumulado de compras completadas en el mes
    query = db.query(func.coalesce(func.sum(Venta.total), 0.0)).filter(
        Venta.estado_pago == "COMPLETADA",
        extract("year", Venta.fecha) == hoy.year,
        extract("month", Venta.fecha) == hoy.month
    )

    if cliente_id:
        query = query.filter(Venta.cliente_id == str(cliente_id).strip())

    acumulado_total = float(query.scalar() or 0.0)
    monto_min = float(config.monto_minimo_acumulado)
    monto_desc = float(config.monto_descuento)
    activo = bool(config.activo)

    elegible = activo and (acumulado_total >= monto_min) and (monto_min > 0)

    return {
        "acumulado": round(acumulado_total, 2),
        "monto_minimo": monto_min,
        "monto_descuento": monto_desc,
        "activo": activo,
        "usado": False,
        "elegible": elegible
    }


for r in [router_beneficio, router_beneficio_compat]:
    r.add_api_route("/mi-beneficio-fidelizacion/", _mi_beneficio_impl, methods=["GET"])
    r.add_api_route("/mi-beneficio-fidelizacion", _mi_beneficio_impl, methods=["GET"], include_in_schema=False)
