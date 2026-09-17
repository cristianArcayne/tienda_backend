"""
Router para CU11: Consultar Catálogo y Disponibilidad en Tiempo Real.
Alineado fielmente con ROPA, VARIANTE_PRENDA, INVENTARIO_SUCURSAL y SUCURSAL del Diagrama UML.
"""
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import or_

from database import get_db
from models.catalogo import Ropa, Categoria, VariantePrenda, Talla, Color, PromocionRopa, Promocion
from models.sucursal import Sucursal, InventarioSucursal
from schemas.catalogo_disponibilidad import (
    StockSucursalResponse,
    VarianteConStockResponse,
    PrendaCatalogoDisponibilidadResponse,
    SucursalStockDetalleResponse,
)

router = APIRouter(
    prefix="/api/v1/catalogo-disponibilidad",
    tags=["CU11. Consultar catálogo y disponibilidad en tiempo real"]
)


def _calcular_estado_stock(disponible: int) -> str:
    if disponible > 5:
        return "DISPONIBLE"
    elif disponible > 0:
        return "ULTIMAS_UNIDADES"
    return "AGOTADO"


@router.get(
    "/",
    response_model=List[PrendaCatalogoDisponibilidadResponse],
    summary="Consultar catálogo con stock omnicanal en tiempo real",
    description="Consulta optimizada con Eager Loading desglosando existencias exactas (Stock_Fisico, Stock_Reservado, Stock_Disponible) por tienda."
)
def consultar_catalogo_con_disponibilidad(
    id_categoria: Optional[int] = Query(None, description="Filtrar por ID de categoría"),
    talla: Optional[str] = Query(None, description="Filtrar por medida de talla (ej. S, M, L, XL, 38, 40)"),
    color: Optional[str] = Query(None, description="Filtrar por nombre de color (ej. Azul Denim, Negro Clásico)"),
    sucursal_id: Optional[int] = Query(None, description="Consultar disponibilidad en una sucursal específica"),
    solo_con_stock: Optional[bool] = Query(False, description="Mostrar solo prendas con existencias disponibles"),
    solo_ar: Optional[bool] = Query(False, description="Filtrar solo prendas con modelo 3D para AR"),
    buscar: Optional[str] = Query(None, description="Búsqueda predictiva por nombre o descripción"),
    db: Session = Depends(get_db)
):
    id_categoria = id_categoria if isinstance(id_categoria, int) else None
    talla = talla if isinstance(talla, str) else None
    color = color if isinstance(color, str) else None
    sucursal_id = sucursal_id if isinstance(sucursal_id, int) else None
    solo_con_stock = solo_con_stock if isinstance(solo_con_stock, bool) else False
    solo_ar = solo_ar if isinstance(solo_ar, bool) else False
    buscar = buscar if isinstance(buscar, str) else None

    hoy = date.today()

    query = db.query(Ropa).options(
        joinedload(Ropa.categoria),
        selectinload(Ropa.variantes).joinedload(VariantePrenda.talla),
        selectinload(Ropa.variantes).joinedload(VariantePrenda.color),
        selectinload(Ropa.variantes).selectinload(VariantePrenda.inventarios_sucursal).joinedload(InventarioSucursal.sucursal),
        selectinload(Ropa.promociones_asociadas).joinedload(PromocionRopa.promocion)
    )

    if id_categoria:
        query = query.filter(Ropa.categoria_id == id_categoria)

    if buscar:
        termino = f"%{buscar.strip()}%"
        query = query.filter(
            or_(
                Ropa.nombre.ilike(termino),
                Ropa.descripcion.ilike(termino)
            )
        )

    ropas = query.order_by(Ropa.id.asc()).all()
    todas_sucursales = db.query(Sucursal).all()
    resultado = []

    for r in ropas:
        tiene_ar = bool(r.modelo_3d_uri and (".glb" in r.modelo_3d_uri or ".gltf" in r.modelo_3d_uri or "3d" in r.modelo_3d_uri.lower()))
        if solo_ar and not tiene_ar:
            continue

        # Descuentos
        mejor_descuento: Optional[float] = None
        if r.promociones_asociadas:
            descuentos = []
            for pr in r.promociones_asociadas:
                if pr.estado == "ACTIVA" and pr.promocion and pr.promocion.activo:
                    f_ini = pr.promocion.fecha_inicio.date() if hasattr(pr.promocion.fecha_inicio, "date") else pr.promocion.fecha_inicio
                    f_fin = pr.promocion.fecha_fin.date() if hasattr(pr.promocion.fecha_fin, "date") else pr.promocion.fecha_fin
                    if f_ini and f_fin and f_ini <= hoy <= f_fin:
                        descuentos.append(float(pr.promocion.porcentaje_descuento))
            if descuentos:
                mejor_descuento = max(descuentos)

        precio_flt = float(r.precio)
        precio_promo = round(precio_flt * (1.0 - (mejor_descuento / 100.0)), 2) if mejor_descuento is not None else None

        variantes_procesadas = []
        stock_total_fisico_prod = 0
        stock_total_disponible_prod = 0

        for v in r.variantes:
            if talla and v.talla and v.talla.medida.upper() != talla.strip().upper():
                continue
            if color and v.color and color.strip().lower() not in v.color.nombre.lower():
                continue

            stocks_por_sucursal = []
            stock_fisico_var = 0
            stock_disponible_var = 0

            inv_map = {inv.sucursal_id: inv for inv in v.inventarios_sucursal}

            for suc in todas_sucursales:
                inv = inv_map.get(suc.id)
                sf = inv.stock_fisico if inv else 0
                sr = inv.stock_reservado if inv else 0
                sd = inv.stock_disponible if inv else max(0, sf - sr)

                if sucursal_id and suc.id != sucursal_id:
                    continue

                stock_fisico_var += sf
                stock_disponible_var += sd

                stocks_por_sucursal.append(
                    StockSucursalResponse(
                        sucursal_id=suc.id,
                        sucursal_nombre=suc.nombre,
                        ciudad=suc.ciudad,
                        stock_fisico=sf,
                        stock_reservado=sr,
                        stock_disponible=sd,
                        estado_stock=_calcular_estado_stock(sd)
                    )
                )

            if solo_con_stock and stock_disponible_var <= 0:
                continue

            stock_total_fisico_prod += stock_fisico_var
            stock_total_disponible_prod += stock_disponible_var

            variantes_procesadas.append(
                VarianteConStockResponse(
                    variante_id=v.id,
                    sku=v.cod_barra,
                    talla=v.talla.medida if v.talla else "Única",
                    color=v.color.nombre if v.color else "Estándar",
                    codigo_hex=v.color.codigo_hex if v.color else None,
                    precio_especifico=precio_flt,
                    stock_fisico_total=stock_fisico_var,
                    stock_disponible_total=stock_disponible_var,
                    estado_disponibilidad=_calcular_estado_stock(stock_disponible_var),
                    disponibilidad_sucursales=stocks_por_sucursal
                )
            )

        if (talla or color or solo_con_stock) and not variantes_procesadas:
            continue

        resultado.append(
            PrendaCatalogoDisponibilidadResponse(
                id=r.id,
                codigo=f"ROPA-{r.id:04d}",
                nombre=r.nombre,
                descripcion=r.descripcion,
                precio_base=precio_flt,
                precio_promocional=precio_promo,
                descuento_aplicado_pct=mejor_descuento,
                id_categoria=r.categoria_id or 1,
                categoria_nombre=r.categoria.nombre if r.categoria else "General",
                imagen_principal=r.imagen_uri,
                modelo_3d_uri=r.modelo_3d_uri,
                tiene_modelo_ar=tiene_ar,
                recursos_multimedia=[r.imagen_uri] if r.imagen_uri else [],
                variantes=variantes_procesadas,
                stock_fisico_cadena=stock_total_fisico_prod,
                stock_disponible_cadena=stock_total_disponible_prod,
                disponible_en_cadena=stock_total_disponible_prod > 0
            )
        )

    return resultado


@router.get(
    "/prendas/{prenda_id}/disponibilidad-sucursales",
    response_model=SucursalStockDetalleResponse,
    summary="Mapa de disponibilidad física exacta de una prenda por sucursal",
    description="Permite al cliente ver las existencias exactas en cada tienda antes de visitar o reservar."
)
def obtener_disponibilidad_prenda(prenda_id: int, db: Session = Depends(get_db)):
    prenda = db.query(Ropa).options(
        selectinload(Ropa.variantes).joinedload(VariantePrenda.talla),
        selectinload(Ropa.variantes).joinedload(VariantePrenda.color),
        selectinload(Ropa.variantes).selectinload(VariantePrenda.inventarios_sucursal).joinedload(InventarioSucursal.sucursal)
    ).filter(Ropa.id == prenda_id).first()

    if not prenda:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prenda con ID {prenda_id} no encontrada."
        )

    todas_sucursales = db.query(Sucursal).all()
    lista_sucursales_resp = []

    for suc in todas_sucursales:
        total_f = 0
        total_r = 0
        total_d = 0
        desglose = []

        for v in prenda.variantes:
            inv = next((i for i in v.inventarios_sucursal if i.sucursal_id == suc.id), None)
            sf = inv.stock_fisico if inv else 0
            sr = inv.stock_reservado if inv else 0
            sd = inv.stock_disponible if inv else max(0, sf - sr)

            total_f += sf
            total_r += sr
            total_d += sd

            desglose.append({
                "variante_id": v.id,
                "sku": v.cod_barra,
                "talla": v.talla.medida if v.talla else "Única",
                "color": v.color.nombre if v.color else "Estándar",
                "stock_disponible": sd
            })

        lista_sucursales_resp.append(
            StockSucursalResponse(
                sucursal_id=suc.id,
                sucursal_nombre=suc.nombre,
                ciudad=suc.ciudad,
                stock_fisico=total_f,
                stock_reservado=total_r,
                stock_disponible=total_d,
                estado_stock=_calcular_estado_stock(total_d)
            )
        )

    return SucursalStockDetalleResponse(
        prenda_id=prenda.id,
        prenda_nombre=prenda.nombre,
        sucursales=lista_sucursales_resp
    )


router_compat = APIRouter(
    prefix="/api/catalogo-disponibilidad",
    tags=["CU11. Consultar catálogo y disponibilidad en tiempo real (Compat)"]
)

for r in [router_compat]:
    r.add_api_route(
        "/",
        consultar_catalogo_con_disponibilidad,
        methods=["GET"],
        response_model=List[PrendaCatalogoDisponibilidadResponse],
        summary="Consultar catálogo con stock omnicanal en tiempo real"
    )
    r.add_api_route(
        "/prendas/{prenda_id}/disponibilidad-sucursales",
        obtener_disponibilidad_prenda,
        methods=["GET"],
        response_model=SucursalStockDetalleResponse,
        summary="Mapa de disponibilidad física exacta de una prenda por sucursal"
    )

