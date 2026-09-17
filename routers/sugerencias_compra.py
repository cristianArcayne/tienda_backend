"""
Router para Sugerencias de Compra Inteligentes (IA Reabastecimiento).
Integrado con el backend de inventarios y proveedores de FashionStore.
"""
from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models.catalogo import Ropa, VariantePrenda, Proveedor
from models.sucursal import InventarioSucursal

router = APIRouter(tags=["IA - Sugerencias de Compra"])

# Sugerencias calculadas a partir de stock crítico y reabastecimiento inteligente
@router.get("/api/ia/sugerencias-compra/")
@router.get("/api/v1/ia/sugerencias-compra/")
def listar_sugerencias_compra(
    estado: Optional[str] = None,
    page: Optional[int] = None,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    # Generar sugerencias dinámicas basadas en prendas con bajo inventario
    items_criticos = (
        db.query(InventarioSucursal)
        .join(VariantePrenda)
        .join(Ropa)
        .outerjoin(Proveedor)
        .filter((InventarioSucursal.stock_fisico - InventarioSucursal.stock_reservado) <= 5)
        .all()
    )

    detalles_mock = []
    total_estimado = 0.0

    for idx, inv in enumerate(items_criticos, start=1):
        variante = inv.variante
        ropa = variante.ropa if variante else None
        precio = ropa.precio if ropa else 120.0
        cant_sugerida = 15 - (inv.stock_fisico - inv.stock_reservado)
        if cant_sugerida < 5: cant_sugerida = 10
        costo_est = round(precio * 0.6, 2)
        total_estimado += cant_sugerida * costo_est

        detalles_mock.append({
            "id": idx,
            "sugerencia": 1,
            "variante": variante.id if variante else idx,
            "sku": variante.sku if variante else f"VAR-{idx}",
            "producto_nombre": ropa.nombre if ropa else f"Prenda {idx}",
            "cantidad_sugerida": cant_sugerida,
            "costo_unitario_estimado": costo_est,
            "alerta_origen": inv.id
        })

    sugerencia_principal = {
        "id": 1,
        "proveedor": 1,
        "proveedor_nombre": "Textiles & Confecciones Bolivia S.R.L.",
        "estado": estado or "pendiente",
        "fecha_creacion": datetime.now().isoformat(),
        "fecha_resolucion": None,
        "compra_generada": None,
        "detalles": detalles_mock,
        "total_estimado": round(total_estimado, 2)
    }

    sugerencias = [sugerencia_principal] if detalles_mock else []

    if page is not None:
        return {
            "count": len(sugerencias),
            "next": None,
            "previous": None,
            "results": sugerencias
        }
    return sugerencias
