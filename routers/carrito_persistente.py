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
    "/",
    response_model=CarritoCompraResponse,
    summary="Recuperar carrito persistente activo",
    include_in_schema=False
)
@router.get(
    "",
    response_model=CarritoCompraResponse,
    summary="Recuperar carrito persistente activo"
)
def obtener_carrito_activo(db: Session = Depends(get_db)):
    cliente = db.query(Cliente).first()
    cliente_ci = cliente.ci if cliente else "admin"

    carrito = db.query(CarritoCompra).options(
        joinedload(CarritoCompra.detalles).joinedload(DetalleCarritoCompra.variante).joinedload(VariantePrenda.ropa),
        joinedload(CarritoCompra.detalles).joinedload(DetalleCarritoCompra.variante).joinedload(VariantePrenda.talla),
        joinedload(CarritoCompra.detalles).joinedload(DetalleCarritoCompra.variante).joinedload(VariantePrenda.color)
    ).first()

    if not carrito:
        carrito = CarritoCompra(fecha_creacion=date.today(), cliente_id=cliente_ci)
        db.add(carrito)
        db.commit()
        db.refresh(carrito)

    return _formatear_carrito(carrito)


@router.get(
    "/{cliente_id}",
    response_model=CarritoCompraResponse,
    summary="Recuperar carrito sincronizado en PostgreSQL",
    description="Sincroniza y retorna el carrito persistente del cliente para Web Angular y App Móvil Flutter."
)
def obtener_carrito_persistente(cliente_id: str, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.ci == str(cliente_id)).first()
    if not cliente:
        cliente = db.query(Cliente).first()
    cliente_ci = cliente.ci if cliente else str(cliente_id)

    carrito = db.query(CarritoCompra).options(
        joinedload(CarritoCompra.detalles).joinedload(DetalleCarritoCompra.variante).joinedload(VariantePrenda.ropa),
        joinedload(CarritoCompra.detalles).joinedload(DetalleCarritoCompra.variante).joinedload(VariantePrenda.talla),
        joinedload(CarritoCompra.detalles).joinedload(DetalleCarritoCompra.variante).joinedload(VariantePrenda.color)
    ).filter(CarritoCompra.cliente_id == cliente_ci).first()

    if not carrito:
        carrito = CarritoCompra(fecha_creacion=date.today(), cliente_id=cliente_ci)
        db.add(carrito)
        db.commit()
        db.refresh(carrito)

    return _formatear_carrito(carrito)


@router.post(
    "/items",
    summary="Agregar item al carrito persistente"
)
@router.post(
    "/items/",
    summary="Agregar item al carrito persistente",
    include_in_schema=False
)
def agregar_item_persistente(item_in: dict, db: Session = Depends(get_db)):
    variante_id = item_in.get("variante_id")
    cantidad = item_in.get("cantidad", 1)

    if not variante_id:
        raise HTTPException(status_code=400, detail="variante_id es requerido")

    carrito = db.query(CarritoCompra).first()
    if not carrito:
        cliente = db.query(Cliente).first()
        cliente_ci = cliente.ci if cliente else "admin"
        carrito = CarritoCompra(fecha_creacion=date.today(), cliente_id=cliente_ci)
        db.add(carrito)
        db.commit()
        db.refresh(carrito)

    detalle = db.query(DetalleCarritoCompra).filter(
        DetalleCarritoCompra.carrito_id == carrito.id,
        DetalleCarritoCompra.variante_id == variante_id
    ).first()

    if detalle:
        detalle.cantidad += cantidad
    else:
        nuevo_detalle = DetalleCarritoCompra(
            carrito_id=carrito.id,
            variante_id=variante_id,
            cantidad=cantidad
        )
        db.add(nuevo_detalle)

    db.commit()
    return {"success": True, "mensaje": "Producto añadido al carrito correctamente"}


@router.delete(
    "/vaciar",
    summary="Vaciar carrito persistente activo"
)
@router.delete(
    "",
    summary="Vaciar carrito persistente activo",
    include_in_schema=False
)
@router.delete(
    "/",
    summary="Vaciar carrito persistente activo",
    include_in_schema=False
)
def vaciar_carrito_persistente(db: Session = Depends(get_db)):
    carrito = db.query(CarritoCompra).first()
    if carrito:
        db.query(DetalleCarritoCompra).filter(
            DetalleCarritoCompra.carrito_id == carrito.id
        ).delete()
        db.commit()
    return {"success": True, "mensaje": "Carrito vaciado correctamente"}


@router.delete(
    "/items/{variante_id}",
    summary="Eliminar item de carrito persistente"
)
def eliminar_item_persistente(variante_id: int, db: Session = Depends(get_db)):
    carrito = db.query(CarritoCompra).first()
    if carrito:
        db.query(DetalleCarritoCompra).filter(
            DetalleCarritoCompra.carrito_id == carrito.id,
            DetalleCarritoCompra.variante_id == variante_id
        ).delete()
        db.commit()
    return {"success": True, "mensaje": "Item eliminado correctamente"}

