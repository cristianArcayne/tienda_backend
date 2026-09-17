"""
Router para Suscripciones de Empresa y Planes (SaaS/Multisucursal).
Proporciona datos operativos para el panel de suscripción en Angular.
"""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db

router = APIRouter(tags=["Empresa - Suscripciones y Planes"])

# Mock dataset dinámico de suscripción activa de la empresa
MOCK_PLANES = [
    {
        "id": 1,
        "nombre": "Plan Starter",
        "descripcion": "Ideal para tiendas individuales con probador AR básico.",
        "precio_mensual": 49.0,
        "precio_anual": 490.0,
        "limite_sucursales": 1,
        "limite_usuarios": 3,
        "soporta_ar": True,
        "soporta_ia": False,
        "activo": True
    },
    {
        "id": 2,
        "nombre": "Plan Pro Enterprise (FashionStore)",
        "descripcion": "Plan Multisucursal Omnicanal con probador AR 3D y analítica IA Gemini.",
        "precio_mensual": 149.0,
        "precio_anual": 1490.0,
        "limite_sucursales": 10,
        "limite_usuarios": 25,
        "soporta_ar": True,
        "soporta_ia": True,
        "activo": True
    }
]

MOCK_SUSCRIPCION = {
    "id": 1,
    "empresa": 1,
    "plan": 2,
    "estado": "activa",
    "ciclo": "mensual",
    "fecha_inicio": "2026-01-01T00:00:00Z",
    "fecha_fin": "2026-12-31T23:59:59Z",
    "auto_renovar": True,
    "ultima_renovacion": "2026-09-01T10:00:00Z",
    "cancelada_en": None,
    "cancelada_por": "",
    "fecha_creacion": "2026-01-01T00:00:00Z"
}

MOCK_CAMBIOS = [
    {
        "id": 1,
        "suscripcion": 1,
        "plan_anterior": 1,
        "plan_nuevo": 2,
        "cambiado_en": "2026-03-15T14:30:00Z",
        "motivo": "Actualización a multisucursal y recomendador IA para el parcial SI2"
    }
]


# === PLANES ===
@router.get("/api/planes/")
@router.get("/api/v1/planes/")
def listar_planes():
    return MOCK_PLANES


# === SUSCRIPCIONES ===
@router.get("/api/suscripciones/")
@router.get("/api/v1/suscripciones/")
def obtener_suscripciones(page: Optional[int] = None, page_size: int = 10):
    if page is not None:
        return {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [MOCK_SUSCRIPCION]
        }
    return [MOCK_SUSCRIPCION]


@router.get("/api/suscripcion-cambios/")
@router.get("/api/v1/suscripcion-cambios/")
def obtener_cambios_suscripcion(page: Optional[int] = None, page_size: int = 10):
    if page is not None:
        return {
            "count": len(MOCK_CAMBIOS),
            "next": None,
            "previous": None,
            "results": MOCK_CAMBIOS
        }
    return MOCK_CAMBIOS
