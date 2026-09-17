"""
Router para CU13: Gestionar Carrito de Compras Persistente y Sincronización Cross-Device.
Alineado con CARRITO_COMPRA y DETALLE_CARRITO_COMPRA del Diagrama UML.
"""
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models.carrito import CarritoCompra, DetalleCarritoCompra
from models.seguridad_persona import Cliente
from models.catalogo import VariantePrenda, Ropa
from models.sucursal import InventarioSucursal
from schemas.carrito import DetalleCarritoCreate, DetalleCarritoResponse, CarritoCompraResponse

router = APIRouter(
    prefix="/api/v1/carrito-persistente",
    tags=["CU13. Gestionar Carrito de Compras Persistente"]
)


def _formatear_carrito(carrito: CarritoCompra) -> CarritoCompraResponse:
    detalles_resp = []
    total_cant = 0
    monto_total = 0.0

    for d in (carrito.detalles or []):
        v = d.variante
        ropa_nom = v.ropa.nombre if (v and v.ropa) else "Prenda"
        precio_un = float(v.ropa.precio) if (v and v.ropa) else 0.0
        subt = round(precio_un * d.cantidad, 2)

        total_cant += d.cantidad
        monto_total += subt

        detalles_resp.append(
            DetalleCarritoResponse(
                id=d.id,
                variante_id=d.variante_id,
                cantidad=d.cantidad,
                cod_barra=v.cod_barra if v else None,
                prenda_nombre=ropa_nom,
                precio_unitario=precio_un,
                subtotal=subt,
                talla=v.talla.medida if (v and v.talla) else "Única",
                color=v.color.nombre if (v and v.color) else "Estándar"
            )
        )

    return CarritoCompraResponse(
        id=carrito.id,
        fecha_creacion=carrito.fecha_creacion,
        cliente_id=carrito.cliente_id,
        detalles=detalles_resp,
        total_articulos=total_cant,
        monto_total=round(monto_total, 2)
    )


@router.get(
    "/{cliente_id}",
    response_model=CarritoCompraResponse,
    summary="Recuperar carrito sincronizado en PostgreSQL",
    description="Sincroniza y retorna el carrito persistente del cliente para Web Angular y App Móvil Flutter."
)
def obtener_carrito_persistente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.ci == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    carrito = db.query(CarritoCompra).options(
        joinedload(CarritoCompra.detalles).joinedload(DetalleCarritoCompra.variante).joinedload(VariantePrenda.ropa),
        joinedload(CarritoCompra.detalles).joinedload(DetalleCarritoCompra.variante).joinedload(VariantePrenda.talla),
        joinedload(CarritoCompra.detalles).joinedload(DetalleCarritoCompra.variante).joinedload(VariantePrenda.color)
    ).filter(CarritoCompra.cliente_id == cliente_id).first()

    if not carrito:
        carrito = CarritoCompra(fecha_creacion=date.today(), cliente_id=cliente_id)
        db.add(carrito)
        db.commit()
        db.refresh(carrito)

    return _formatear_carrito(carrito)
