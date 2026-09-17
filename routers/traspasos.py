"""
Router para CU10: Gestión de Traspasos entre Sucursales.
Alineado con TRASPASO, DETALLE_TRASPASO, SUCURSAL e INVENTARIO_SUCURSAL del Diagrama UML.
Permite registrar el envío de mercadería desde una tienda de origen y confirmar su recepción en una tienda de destino para equilibrar el stock.
"""
from datetime import datetime, timezone
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_

from database import get_db
from models.catalogo import Ropa, VariantePrenda, Talla, Color
from models.sucursal import Sucursal, InventarioSucursal, Traspaso, DetalleTraspaso, MovimientoInventario
from pydantic import BaseModel, Field, ConfigDict


class DetalleTraspasoItemResponse(BaseModel):
    id: int
    variante_id: int
    ropa_nombre: str
    sku: str
    talla: str
    color: str
    imagen_uri: Optional[str] = None
    cantidad: int

    model_config = ConfigDict(from_attributes=True)


class TraspasoResponse(BaseModel):
    id: int
    sucursal_origen_id: int
    sucursal_origen_nombre: str
    sucursal_origen_ciudad: str
    sucursal_destino_id: int
    sucursal_destino_nombre: str
    sucursal_destino_ciudad: str
    estado: str  # 'SOLICITADO', 'EN_TRANSITO', 'RECIBIDO', 'CANCELADO'
    observacion: Optional[str] = None
    fecha_solicitud: Optional[datetime] = None
    fecha_recepcion: Optional[datetime] = None
    solicitado_por_ci: Optional[str] = None
    total_unidades: int = 0
    detalles: List[DetalleTraspasoItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class DetalleTraspasoCreate(BaseModel):
    variante_id: int = Field(..., gt=0)
    cantidad: int = Field(..., gt=0, description="Cantidad física a traspasar (mayor a 0)")


class TraspasoCreate(BaseModel):
    sucursal_origen_id: int = Field(..., gt=0)
    sucursal_destino_id: int = Field(..., gt=0)
    observacion: Optional[str] = Field(None, max_length=500)
    solicitado_por_ci: Optional[str] = None
    despachar_inmediato: Optional[bool] = True
    detalles: List[DetalleTraspasoCreate] = Field(..., min_length=1)


router = APIRouter(
    prefix="/api/v1/traspasos",
    tags=["CU10. Gestionar traspasos entre sucursales"]
)

router_compat = APIRouter(
    prefix="/api/traspasos",
    tags=["CU10. Gestionar traspasos entre sucursales (Compat)"]
)


def _map_traspaso_to_response(t: Traspaso) -> TraspasoResponse:
    detalles_resp = []
    total_cant = 0
    for d in (t.detalles or []):
        v = d.variante
        r = v.ropa if v else None
        total_cant += d.cantidad
        detalles_resp.append(
            DetalleTraspasoItemResponse(
                id=d.id,
                variante_id=d.variante_id,
                ropa_nombre=r.nombre if r else "Prenda",
                sku=v.sku if v else f"SKU-{d.variante_id}",
                talla=v.talla.nombre if v and v.talla else "M",
                color=v.color.nombre if v and v.color else "Normal",
                imagen_uri=r.imagen_uri if r else None,
                cantidad=d.cantidad
            )
        )

    return TraspasoResponse(
        id=t.id,
        sucursal_origen_id=t.sucursal_origen_id,
        sucursal_origen_nombre=t.sucursal_origen.nombre if t.sucursal_origen else "Origen",
        sucursal_origen_ciudad=t.sucursal_origen.ciudad if t.sucursal_origen else "",
        sucursal_destino_id=t.sucursal_destino_id,
        sucursal_destino_nombre=t.sucursal_destino.nombre if t.sucursal_destino else "Destino",
        sucursal_destino_ciudad=t.sucursal_destino.ciudad if t.sucursal_destino else "",
        estado=t.estado,
        observacion=t.observacion,
        fecha_solicitud=t.fecha,
        fecha_recepcion=t.fecha_recepcion,
        solicitado_por_ci=t.empleado_id,
        total_unidades=total_cant,
        detalles=detalles_resp
    )


def _listar_traspasos_impl(
    estado: Optional[str] = None,
    sucursal_id: Optional[int] = None,
    db: Session = Depends(get_db)
) -> List[TraspasoResponse]:
    query = (
        db.query(Traspaso)
        .options(
            joinedload(Traspaso.sucursal_origen),
            joinedload(Traspaso.sucursal_destino),
            joinedload(Traspaso.detalles).joinedload(DetalleTraspaso.variante).joinedload(VariantePrenda.ropa),
            joinedload(Traspaso.detalles).joinedload(DetalleTraspaso.variante).joinedload(VariantePrenda.talla),
            joinedload(Traspaso.detalles).joinedload(DetalleTraspaso.variante).joinedload(VariantePrenda.color)
        )
        .order_by(Traspaso.id.desc())
    )

    if estado and estado != "TODOS":
        query = query.filter(Traspaso.estado == estado.upper())

    if sucursal_id:
        query = query.filter(
            or_(
                Traspaso.sucursal_origen_id == sucursal_id,
                Traspaso.sucursal_destino_id == sucursal_id
            )
        )

    traspasos = query.all()
    return [_map_traspaso_to_response(t) for t in traspasos]


def _obtener_traspaso_impl(traspaso_id: int, db: Session = Depends(get_db)) -> TraspasoResponse:
    t = (
        db.query(Traspaso)
        .options(
            joinedload(Traspaso.sucursal_origen),
            joinedload(Traspaso.sucursal_destino),
            joinedload(Traspaso.detalles).joinedload(DetalleTraspaso.variante).joinedload(VariantePrenda.ropa),
            joinedload(Traspaso.detalles).joinedload(DetalleTraspaso.variante).joinedload(VariantePrenda.talla),
            joinedload(Traspaso.detalles).joinedload(DetalleTraspaso.variante).joinedload(VariantePrenda.color)
        )
        .filter(Traspaso.id == traspaso_id)
        .first()
    )
    if not t:
        raise HTTPException(status_code=404, detail="Traspaso no encontrado.")
    return _map_traspaso_to_response(t)


def _crear_traspaso_impl(req: TraspasoCreate, db: Session = Depends(get_db)) -> TraspasoResponse:
    if req.sucursal_origen_id == req.sucursal_destino_id:
        raise HTTPException(
            status_code=400,
            detail="La sucursal de origen no puede ser la misma sucursal de destino."
        )

    orig = db.query(Sucursal).filter(Sucursal.id == req.sucursal_origen_id).first()
    dest = db.query(Sucursal).filter(Sucursal.id == req.sucursal_destino_id).first()
    if not orig or not dest:
        raise HTTPException(status_code=404, detail="Sucursal de origen o destino no encontrada.")

    # Validar existencias físicas en origen
    for item in req.detalles:
        inv = db.query(InventarioSucursal).filter(
            InventarioSucursal.sucursal_id == req.sucursal_origen_id,
            InventarioSucursal.variante_id == item.variante_id
        ).first()

        disponible = (inv.stock_fisico or 0) - (inv.stock_reservado or 0) if inv else 0
        if not inv or disponible < item.cantidad:
            var = db.query(VariantePrenda).filter(VariantePrenda.id == item.variante_id).first()
            var_nombre = f"{var.ropa.nombre} ({var.sku})" if var and var.ropa else f"Variante #{item.variante_id}"
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente en {orig.nombre} para '{var_nombre}'. Disponible: {disponible}, Solicitado: {item.cantidad}."
            )

    estado_inicial = "EN_TRANSITO" if req.despachar_inmediato else "SOLICITADO"

    nuevo_traspaso = Traspaso(
        sucursal_origen_id=req.sucursal_origen_id,
        sucursal_destino_id=req.sucursal_destino_id,
        empleado_id=req.solicitado_por_ci,
        observacion=req.observacion,
        estado=estado_inicial,
        fecha=datetime.now(timezone.utc)
    )
    db.add(nuevo_traspaso)
    db.flush()

    for item in req.detalles:
        db.add(DetalleTraspaso(
            traspaso_id=nuevo_traspaso.id,
            variante_id=item.variante_id,
            cantidad=item.cantidad
        ))

        # Si se despacha de inmediato, descontar de origen
        if req.despachar_inmediato:
            inv_orig = db.query(InventarioSucursal).filter(
                InventarioSucursal.sucursal_id == req.sucursal_origen_id,
                InventarioSucursal.variante_id == item.variante_id
            ).first()
            stock_ant = inv_orig.stock_fisico
            inv_orig.stock_fisico -= item.cantidad
            inv_orig.fec_actualizacion = datetime.now(timezone.utc)

            # Registrar movimiento Kardex
            db.add(MovimientoInventario(
                sucursal_id=req.sucursal_origen_id,
                variante_id=item.variante_id,
                tipo_movimiento="TRASPASO_SALIDA",
                cantidad=-item.cantidad,
                stock_anterior=stock_ant,
                stock_nuevo=inv_orig.stock_fisico,
                motivo=f"Despacho por Traspaso #{nuevo_traspaso.id} hacia {dest.nombre}",
                usuario_ci=req.solicitado_por_ci
            ))

    db.commit()
    db.refresh(nuevo_traspaso)
    return _obtener_traspaso_impl(nuevo_traspaso.id, db)


def _despachar_traspaso_impl(traspaso_id: int, db: Session = Depends(get_db)) -> TraspasoResponse:
    t = db.query(Traspaso).filter(Traspaso.id == traspaso_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Traspaso no encontrado.")

    if t.estado != "SOLICITADO":
        raise HTTPException(status_code=400, detail=f"No se puede despachar un traspaso en estado '{t.estado}'.")

    dest = db.query(Sucursal).filter(Sucursal.id == t.sucursal_destino_id).first()
    dest_nombre = dest.nombre if dest else "Destino"

    for d in t.detalles:
        inv_orig = db.query(InventarioSucursal).filter(
            InventarioSucursal.sucursal_id == t.sucursal_origen_id,
            InventarioSucursal.variante_id == d.variante_id
        ).first()

        if not inv_orig or inv_orig.stock_fisico < d.cantidad:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente en origen para despachar la variante #{d.variante_id}."
            )

        stock_ant = inv_orig.stock_fisico
        inv_orig.stock_fisico -= d.cantidad
        inv_orig.fec_actualizacion = datetime.now(timezone.utc)

        db.add(MovimientoInventario(
            sucursal_id=t.sucursal_origen_id,
            variante_id=d.variante_id,
            tipo_movimiento="TRASPASO_SALIDA",
            cantidad=-d.cantidad,
            stock_anterior=stock_ant,
            stock_nuevo=inv_orig.stock_fisico,
            motivo=f"Despacho por Traspaso #{t.id} hacia {dest_nombre}",
            usuario_ci=t.empleado_id
        ))

    t.estado = "EN_TRANSITO"
    db.commit()
    db.refresh(t)
    return _obtener_traspaso_impl(t.id, db)


def _confirmar_recepcion_impl(traspaso_id: int, db: Session = Depends(get_db)) -> TraspasoResponse:
    t = db.query(Traspaso).filter(Traspaso.id == traspaso_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Traspaso no encontrado.")

    if t.estado != "EN_TRANSITO":
        raise HTTPException(
            status_code=400,
            detail=f"Solo se puede confirmar la recepción de traspasos en estado 'EN_TRANSITO' (estado actual: '{t.estado}')."
        )

    orig = db.query(Sucursal).filter(Sucursal.id == t.sucursal_origen_id).first()
    orig_nombre = orig.nombre if orig else "Origen"

    for d in t.detalles:
        inv_dest = db.query(InventarioSucursal).filter(
            InventarioSucursal.sucursal_id == t.sucursal_destino_id,
            InventarioSucursal.variante_id == d.variante_id
        ).first()

        if not inv_dest:
            inv_dest = InventarioSucursal(
                sucursal_id=t.sucursal_destino_id,
                variante_id=d.variante_id,
                stock_fisico=0,
                stock_reservado=0,
                stock_minimo=5
            )
            db.add(inv_dest)
            db.flush()

        stock_ant = inv_dest.stock_fisico
        inv_dest.stock_fisico += d.cantidad
        inv_dest.fec_actualizacion = datetime.now(timezone.utc)

        # Registrar movimiento Kardex de entrada
        db.add(MovimientoInventario(
            sucursal_id=t.sucursal_destino_id,
            variante_id=d.variante_id,
            tipo_movimiento="TRASPASO_ENTRADA",
            cantidad=d.cantidad,
            stock_anterior=stock_ant,
            stock_nuevo=inv_dest.stock_fisico,
            motivo=f"Recepción de mercadería por Traspaso #{t.id} desde {orig_nombre}",
            usuario_ci=t.empleado_id
        ))

    t.estado = "RECIBIDO"
    t.fecha_recepcion = datetime.now(timezone.utc)
    db.commit()
    db.refresh(t)
    return _obtener_traspaso_impl(t.id, db)


def _cancelar_traspaso_impl(traspaso_id: int, db: Session = Depends(get_db)) -> TraspasoResponse:
    t = db.query(Traspaso).filter(Traspaso.id == traspaso_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Traspaso no encontrado.")

    if t.estado == "RECIBIDO":
        raise HTTPException(status_code=400, detail="No se puede cancelar un traspaso que ya ha sido recibido en destino.")

    # Si estaba en tránsito, restituir el stock al origen
    if t.estado == "EN_TRANSITO":
        for d in t.detalles:
            inv_orig = db.query(InventarioSucursal).filter(
                InventarioSucursal.sucursal_id == t.sucursal_origen_id,
                InventarioSucursal.variante_id == d.variante_id
            ).first()
            if inv_orig:
                stock_ant = inv_orig.stock_fisico
                inv_orig.stock_fisico += d.cantidad
                inv_orig.fec_actualizacion = datetime.now(timezone.utc)

                db.add(MovimientoInventario(
                    sucursal_id=t.sucursal_origen_id,
                    variante_id=d.variante_id,
                    tipo_movimiento="AJUSTE",
                    cantidad=d.cantidad,
                    stock_anterior=stock_ant,
                    stock_nuevo=inv_orig.stock_fisico,
                    motivo=f"Cancelación y restitución de Traspaso #{t.id}"
                ))

    t.estado = "CANCELADO"
    db.commit()
    db.refresh(t)
    return _obtener_traspaso_impl(t.id, db)


# Registrar endpoints
for r in [router, router_compat]:
    r.add_api_route(
        "/",
        _listar_traspasos_impl,
        methods=["GET"],
        response_model=List[TraspasoResponse],
        summary="Listar traspasos entre sucursales"
    )
    r.add_api_route(
        "/",
        _crear_traspaso_impl,
        methods=["POST"],
        response_model=TraspasoResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Registrar envío o solicitud de traspaso entre tiendas"
    )
    r.add_api_route(
        "/{traspaso_id}",
        _obtener_traspaso_impl,
        methods=["GET"],
        response_model=TraspasoResponse,
        summary="Detalle del traspaso con desglose de prendas"
    )
    r.add_api_route(
        "/{traspaso_id}/despachar",
        _despachar_traspaso_impl,
        methods=["POST"],
        response_model=TraspasoResponse,
        summary="Despachar mercadería (pasar a EN_TRANSITO)"
    )
    r.add_api_route(
        "/{traspaso_id}/confirmar_recepcion",
        _confirmar_recepcion_impl,
        methods=["POST"],
        response_model=TraspasoResponse,
        summary="Confirmar recepción en destino (sumar al inventario local)"
    )
    r.add_api_route(
        "/{traspaso_id}/cancelar",
        _cancelar_traspaso_impl,
        methods=["POST"],
        response_model=TraspasoResponse,
        summary="Cancelar traspaso y restituir existencias"
    )

