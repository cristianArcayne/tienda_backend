"""
Router para CU09: Gestión de Inventario Físico Local.
Alineado con INVENTARIO_SUCURSAL, VARIANTE_PRENDA, ROPA y SUCURSAL del Diagrama UML de FashionStore.
Permite registrar entrada de nueva mercadería, control de existencias reales (físico, reservado, disponible) y ajustes por mermas o daños.
"""
from datetime import datetime, timezone
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_

from database import get_db
from models.catalogo import Ropa, Categoria, VariantePrenda, Talla, Color
from models.sucursal import Sucursal, InventarioSucursal, MovimientoInventario
from pydantic import BaseModel, Field, ConfigDict


class VarianteStockItem(BaseModel):
    id: int
    variante_id: int
    ropa_id: int
    ropa_nombre: str
    categoria_nombre: str
    sku: str
    cod_barra: str
    talla: str
    color: str
    color_hex: str
    imagen_uri: Optional[str] = None
    precio_base: float
    stock_fisico: int
    stock_reservado: int
    stock_disponible: int
    stock_minimo: int
    estado_stock: str  # 'DISPONIBLE', 'BAJO_STOCK', 'AGOTADO'
    fec_actualizacion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ResumenInventarioSucursal(BaseModel):
    sucursal_id: int
    sucursal_nombre: str
    ciudad: str
    total_skus: int
    total_unidades_fisicas: int
    total_unidades_reservadas: int
    total_unidades_disponibles: int
    total_alertas_bajo_stock: int
    items: List[VarianteStockItem]


class EntradaMercaderiaRequest(BaseModel):
    sucursal_id: int = Field(..., gt=0)
    variante_id: int = Field(..., gt=0)
    cantidad: int = Field(..., gt=0, description="Cantidad física a ingresar (mayor a 0)")
    motivo: Optional[str] = Field("Ingreso por recepción de mercadería / compra", max_length=255)
    costo_unitario: Optional[float] = Field(None, ge=0)
    nro_documento: Optional[str] = Field(None, max_length=100)
    usuario_ci: Optional[str] = None


class AjusteInventarioRequest(BaseModel):
    sucursal_id: int = Field(..., gt=0)
    variante_id: int = Field(..., gt=0)
    tipo_ajuste: str = Field(..., description="MERMA, DANIO, CONTEO_FISICO, CORRECCION")
    cantidad_ajuste: int = Field(..., description="Cantidad a sumar (+) o restar (-)")
    motivo: str = Field(..., min_length=3, max_length=255, description="Justificación del ajuste")
    usuario_ci: Optional[str] = None


class MovimientoKardexResponse(BaseModel):
    id: int
    sucursal_id: int
    variante_id: int
    ropa_nombre: str
    sku: str
    talla: str
    color: str
    tipo_movimiento: str
    cantidad: int
    stock_anterior: int
    stock_nuevo: int
    motivo: Optional[str] = None
    fecha: datetime
    usuario_ci: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


router = APIRouter(
    prefix="/api/v1/inventario",
    tags=["CU09. Gestionar inventario físico local"]
)

router_compat = APIRouter(
    prefix="/api/inventario",
    tags=["CU09. Gestionar inventario físico local (Compat)"]
)


def _garantizar_inventario_sucursal(db: Session, sucursal_id: int):
    """Garantiza que todas las ropas tengan variantes y que todas las variantes tengan un registro en la sucursal"""
    # 1. Asegurar que toda Ropa activa tenga al menos una variante
    ropas = db.query(Ropa).filter(Ropa.activo == True).all()
    talla_def = db.query(Talla).filter(Talla.medida == "M").first() or db.query(Talla).first()
    color_def = db.query(Color).first()

    for r in ropas:
        cnt_vars = db.query(VariantePrenda).filter(VariantePrenda.ropa_id == r.id).count()
        if cnt_vars == 0:
            sku_prefix = "".join([c for c in r.nombre if c.isalnum()][:4]).upper() or "ROP"
            nueva_var = VariantePrenda(
                ropa_id=r.id,
                talla_id=talla_def.id if talla_def else 1,
                color_id=color_def.id if color_def else 1,
                sku=f"{sku_prefix}-{r.id}-M-STD",
                cod_barra=f"BAR-{r.id}-{sku_prefix}",
                activo=True
            )
            db.add(nueva_var)
            db.flush()

    variantes = db.query(VariantePrenda).filter(VariantePrenda.activo == True).all()
    existentes = {
        inv.variante_id for inv in db.query(InventarioSucursal).filter(InventarioSucursal.sucursal_id == sucursal_id).all()
    }
    nuevos = []
    for var in variantes:
        if var.id not in existentes:
            nuevos.append(
                InventarioSucursal(
                    sucursal_id=sucursal_id,
                    variante_id=var.id,
                    stock_fisico=0,
                    stock_reservado=0,
                    stock_minimo=5
                )
            )
    if nuevos:
        db.add_all(nuevos)
    db.commit()


def _obtener_inventario_sucursal_impl(
    sucursal_id: int,
    search: Optional[str] = None,
    categoria_id: Optional[int] = None,
    solo_alertas: Optional[bool] = False,
    db: Session = Depends(get_db)
) -> ResumenInventarioSucursal:
    sucursal = db.query(Sucursal).filter(Sucursal.id == sucursal_id).first()
    if not sucursal:
        raise HTTPException(status_code=404, detail=f"Sucursal #{sucursal_id} no encontrada.")

    _garantizar_inventario_sucursal(db, sucursal_id)

    query = (
        db.query(InventarioSucursal)
        .join(VariantePrenda, InventarioSucursal.variante_id == VariantePrenda.id)
        .join(Ropa, VariantePrenda.ropa_id == Ropa.id)
        .options(
            joinedload(InventarioSucursal.variante).joinedload(VariantePrenda.ropa).joinedload(Ropa.categoria),
            joinedload(InventarioSucursal.variante).joinedload(VariantePrenda.talla),
            joinedload(InventarioSucursal.variante).joinedload(VariantePrenda.color)
        )
        .filter(InventarioSucursal.sucursal_id == sucursal_id)
        .order_by(Ropa.nombre.asc(), VariantePrenda.sku.asc())
    )

    if categoria_id:
        query = query.filter(Ropa.categoria_id == categoria_id)

    if search:
        s = f"%{search}%"
        query = query.filter(
            or_(
                Ropa.nombre.ilike(s),
                VariantePrenda.sku.ilike(s),
                VariantePrenda.cod_barra.ilike(s)
            )
        )

    inventarios = query.all()

    items = []
    total_fisico = 0
    total_reservado = 0
    total_disponible = 0
    alertas_count = 0

    for inv in inventarios:
        v = inv.variante
        if not v or not v.ropa:
            continue

        r = v.ropa
        fisico = inv.stock_fisico or 0
        reservado = inv.stock_reservado or 0
        disponible = max(0, fisico - reservado)
        minimo = inv.stock_minimo if inv.stock_minimo is not None else 5

        if disponible <= 0:
            estado = "AGOTADO"
        elif disponible <= minimo:
            estado = "BAJO_STOCK"
        else:
            estado = "DISPONIBLE"

        if solo_alertas and estado == "DISPONIBLE":
            continue

        if estado in ["BAJO_STOCK", "AGOTADO"]:
            alertas_count += 1

        total_fisico += fisico
        total_reservado += reservado
        total_disponible += disponible

        talla_nombre = v.talla.nombre if v.talla else "M"
        color_nombre = v.color.nombre if v.color else "Normal"
        color_hex = v.color.codigo_hex if v.color else "#000000"
        cat_nombre = r.categoria.nombre if r.categoria else "General"

        items.append(
            VarianteStockItem(
                id=inv.id,
                variante_id=v.id,
                ropa_id=r.id,
                ropa_nombre=r.nombre,
                categoria_nombre=cat_nombre,
                sku=v.sku or f"SKU-{v.id}",
                cod_barra=v.cod_barra or f"BAR-{v.id}",
                talla=talla_nombre,
                color=color_nombre,
                color_hex=color_hex,
                imagen_uri=r.imagen_uri,
                precio_base=float(r.precio or 0.0),
                stock_fisico=fisico,
                stock_reservado=reservado,
                stock_disponible=disponible,
                stock_minimo=minimo,
                estado_stock=estado,
                fec_actualizacion=inv.fec_actualizacion or datetime.now(timezone.utc)
            )
        )

    return ResumenInventarioSucursal(
        sucursal_id=sucursal.id,
        sucursal_nombre=sucursal.nombre,
        ciudad=sucursal.ciudad,
        total_skus=len(items),
        total_unidades_fisicas=total_fisico,
        total_unidades_reservadas=total_reservado,
        total_unidades_disponibles=total_disponible,
        total_alertas_bajo_stock=alertas_count,
        items=items
    )


def _registrar_entrada_impl(
    req: EntradaMercaderiaRequest,
    db: Session = Depends(get_db)
) -> VarianteStockItem:
    sucursal = db.query(Sucursal).filter(Sucursal.id == req.sucursal_id).first()
    if not sucursal:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada.")

    variante = db.query(VariantePrenda).filter(VariantePrenda.id == req.variante_id).first()
    if not variante:
        raise HTTPException(status_code=404, detail="Variante de prenda no encontrada.")

    inv = db.query(InventarioSucursal).filter(
        InventarioSucursal.sucursal_id == req.sucursal_id,
        InventarioSucursal.variante_id == req.variante_id
    ).first()

    if not inv:
        inv = InventarioSucursal(
            sucursal_id=req.sucursal_id,
            variante_id=req.variante_id,
            stock_fisico=0,
            stock_reservado=0,
            stock_minimo=5
        )
        db.add(inv)
        db.flush()

    stock_ant = inv.stock_fisico
    inv.stock_fisico += req.cantidad
    inv.fec_actualizacion = datetime.now(timezone.utc)

    # Registrar en Kardex
    mov = MovimientoInventario(
        sucursal_id=req.sucursal_id,
        variante_id=req.variante_id,
        tipo_movimiento="ENTRADA",
        cantidad=req.cantidad,
        stock_anterior=stock_ant,
        stock_nuevo=inv.stock_fisico,
        motivo=req.motivo or "Ingreso por recepción de mercadería",
        usuario_ci=req.usuario_ci
    )
    db.add(mov)
    db.commit()
    db.refresh(inv)

    r = variante.ropa
    disponible = max(0, inv.stock_fisico - inv.stock_reservado)
    estado = "AGOTADO" if disponible <= 0 else ("BAJO_STOCK" if disponible <= inv.stock_minimo else "DISPONIBLE")

    return VarianteStockItem(
        id=inv.id,
        variante_id=variante.id,
        ropa_id=r.id if r else 0,
        ropa_nombre=r.nombre if r else "Prenda",
        categoria_nombre=r.categoria.nombre if r and r.categoria else "General",
        sku=variante.sku or f"SKU-{variante.id}",
        cod_barra=variante.cod_barra or f"BAR-{variante.id}",
        talla=variante.talla.nombre if variante.talla else "M",
        color=variante.color.nombre if variante.color else "Normal",
        color_hex=variante.color.codigo_hex if variante.color else "#000000",
        imagen_uri=r.imagen_uri if r else None,
        precio_base=float(r.precio or 0.0) if r else 0.0,
        stock_fisico=inv.stock_fisico,
        stock_reservado=inv.stock_reservado,
        stock_disponible=disponible,
        stock_minimo=inv.stock_minimo,
        estado_stock=estado,
        fec_actualizacion=inv.fec_actualizacion
    )


def _registrar_ajuste_impl(
    req: AjusteInventarioRequest,
    db: Session = Depends(get_db)
) -> VarianteStockItem:
    sucursal = db.query(Sucursal).filter(Sucursal.id == req.sucursal_id).first()
    if not sucursal:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada.")

    inv = db.query(InventarioSucursal).filter(
        InventarioSucursal.sucursal_id == req.sucursal_id,
        InventarioSucursal.variante_id == req.variante_id
    ).first()

    if not inv:
        raise HTTPException(status_code=404, detail="No existe registro de inventario para esta variante en la sucursal.")

    stock_ant = inv.stock_fisico
    nuevo_stock = stock_ant + req.cantidad_ajuste

    if nuevo_stock < 0:
        raise HTTPException(
            status_code=400,
            detail=f"El ajuste resultaría en stock negativo ({nuevo_stock}). Stock físico actual: {stock_ant}."
        )

    inv.stock_fisico = nuevo_stock
    inv.fec_actualizacion = datetime.now(timezone.utc)

    mov = MovimientoInventario(
        sucursal_id=req.sucursal_id,
        variante_id=req.variante_id,
        tipo_movimiento=req.tipo_ajuste.upper(),
        cantidad=req.cantidad_ajuste,
        stock_anterior=stock_ant,
        stock_nuevo=nuevo_stock,
        motivo=req.motivo,
        usuario_ci=req.usuario_ci
    )
    db.add(mov)
    db.commit()
    db.refresh(inv)

    v = inv.variante
    r = v.ropa if v else None
    disponible = max(0, inv.stock_fisico - inv.stock_reservado)
    estado = "AGOTADO" if disponible <= 0 else ("BAJO_STOCK" if disponible <= inv.stock_minimo else "DISPONIBLE")

    return VarianteStockItem(
        id=inv.id,
        variante_id=v.id if v else 0,
        ropa_id=r.id if r else 0,
        ropa_nombre=r.nombre if r else "Prenda",
        categoria_nombre=r.categoria.nombre if r and r.categoria else "General",
        sku=v.sku if v else "SKU",
        cod_barra=v.cod_barra if v else "BAR",
        talla=v.talla.nombre if v and v.talla else "M",
        color=v.color.nombre if v and v.color else "Normal",
        color_hex=v.color.codigo_hex if v and v.color else "#000000",
        imagen_uri=r.imagen_uri if r else None,
        precio_base=float(r.precio or 0.0) if r else 0.0,
        stock_fisico=inv.stock_fisico,
        stock_reservado=inv.stock_reservado,
        stock_disponible=disponible,
        stock_minimo=inv.stock_minimo,
        estado_stock=estado,
        fec_actualizacion=inv.fec_actualizacion
    )


def _listar_movimientos_impl(
    sucursal_id: int,
    variante_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
) -> List[MovimientoKardexResponse]:
    query = (
        db.query(MovimientoInventario)
        .options(
            joinedload(MovimientoInventario.variante).joinedload(VariantePrenda.ropa),
            joinedload(MovimientoInventario.variante).joinedload(VariantePrenda.talla),
            joinedload(MovimientoInventario.variante).joinedload(VariantePrenda.color)
        )
        .filter(MovimientoInventario.sucursal_id == sucursal_id)
        .order_by(MovimientoInventario.fecha.desc(), MovimientoInventario.id.desc())
    )

    if variante_id:
        query = query.filter(MovimientoInventario.variante_id == variante_id)

    limit_val = limit if isinstance(limit, int) else 50
    movs = query.limit(limit_val).all()

    res = []
    for m in movs:
        v = m.variante
        r = v.ropa if v else None
        res.append(
            MovimientoKardexResponse(
                id=m.id,
                sucursal_id=m.sucursal_id,
                variante_id=m.variante_id,
                ropa_nombre=r.nombre if r else "Prenda",
                sku=v.sku if v else "SKU",
                talla=v.talla.nombre if v and v.talla else "M",
                color=v.color.nombre if v and v.color else "Normal",
                tipo_movimiento=m.tipo_movimiento,
                cantidad=m.cantidad,
                stock_anterior=m.stock_anterior,
                stock_nuevo=m.stock_nuevo,
                motivo=m.motivo,
                fecha=m.fecha,
                usuario_ci=m.usuario_ci
            )
        )
    return res


# Registrar endpoints en ambos routers
for r in [router, router_compat]:
    for p in ["/sucursal/{sucursal_id}", "/sucursal/{sucursal_id}/"]:
        r.add_api_route(
            p,
            _obtener_inventario_sucursal_impl,
            methods=["GET"],
            response_model=ResumenInventarioSucursal,
            summary="Consultar existencias de inventario físico local por sucursal"
        )
    for p in ["/entrada", "/entrada/", "/entrada-mercaderia", "/entrada-mercaderia/"]:
        r.add_api_route(
            p,
            _registrar_entrada_impl,
            methods=["POST"],
            response_model=VarianteStockItem,
            status_code=status.HTTP_201_CREATED,
            summary="Registrar entrada de mercadería a la sucursal"
        )
    for p in ["/ajuste", "/ajuste/"]:
        r.add_api_route(
            p,
            _registrar_ajuste_impl,
            methods=["POST"],
            response_model=VarianteStockItem,
            summary="Registrar ajuste por merma, daño o conteo físico"
        )
    for p in ["/movimientos/{sucursal_id}", "/movimientos/{sucursal_id}/"]:
        r.add_api_route(
            p,
            _listar_movimientos_impl,
            methods=["GET"],
            response_model=List[MovimientoKardexResponse],
            summary="Consultar historial de movimientos (Kardex) de la sucursal"
        )
