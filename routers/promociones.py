"""
Router para CU08: Gestión de Promociones y Descuentos.
Alineado fielmente con PROMOCION y PROMOCION_ROPA del Diagrama UML de FashionStore.
Permite configurar y aplicar reducciones de precio temporales o porcentuales a prendas y categorías específicas del catálogo.
"""
from datetime import datetime, date, timezone
from typing import List, Optional, Any, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from database import get_db
from models.catalogo import Ropa, Categoria, Promocion, PromocionRopa
from pydantic import BaseModel, Field, ConfigDict


class PrendaAsociadaInfo(BaseModel):
    id: int
    nombre: str
    precio_base: float
    precio_promocional: float
    imagen_uri: Optional[str] = None
    categoria_nombre: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PromocionCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=150)
    descripcion: Optional[str] = None
    porcentaje_descuento: float = Field(..., gt=0, le=100)
    fecha_inicio: datetime
    fecha_fin: datetime
    activo: Optional[bool] = True
    ropas_ids: Optional[List[int]] = []
    categoria_id: Optional[int] = None


class PromocionUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=150)
    descripcion: Optional[str] = None
    porcentaje_descuento: Optional[float] = Field(None, gt=0, le=100)
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    activo: Optional[bool] = None
    ropas_ids: Optional[List[int]] = None


class PromocionResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    porcentaje_descuento: float
    fecha_inicio: datetime
    fecha_fin: datetime
    activo: bool = True
    esta_vigente: bool = False
    estado_calculado: str = "ACTIVA"  # ACTIVA, EXPIRADA, PROGRAMADA, INACTIVA
    total_prendas_asociadas: int = 0
    prendas: List[PrendaAsociadaInfo] = []

    model_config = ConfigDict(from_attributes=True)


class PaginatedPromocionesResponse(BaseModel):
    count: int
    next: Optional[str] = None
    previous: Optional[str] = None
    results: List[PromocionResponse]


class AsociarPrendasRequest(BaseModel):
    ropas_ids: List[int]


class AplicarCategoriaRequest(BaseModel):
    categoria_id: int


def calcular_estado_promocion(p: Promocion) -> tuple[bool, str]:
    ahora = datetime.now(timezone.utc)
    
    # Normalizar fechas a aware si son naive
    inicio = p.fecha_inicio
    fin = p.fecha_fin
    if inicio.tzinfo is None:
        inicio = inicio.replace(tzinfo=timezone.utc)
    if fin.tzinfo is None:
        fin = fin.replace(tzinfo=timezone.utc)

    if not p.activo:
        return False, "INACTIVA"
    if ahora < inicio:
        return False, "PROGRAMADA"
    if ahora > fin:
        return False, "EXPIRADA"
    return True, "ACTIVA"


def map_promocion_to_response(p: Promocion) -> PromocionResponse:
    vigente, estado = calcular_estado_promocion(p)
    desc_pct = float(p.porcentaje_descuento)
    factor_descuento = max(0.0, 1.0 - (desc_pct / 100.0))

    prendas_info = []
    for assoc in p.ropas_asociadas:
        r = assoc.ropa
        if r:
            precio_base = float(r.precio) if r.precio is not None else 0.0
            precio_promo = round(precio_base * factor_descuento, 2)
            cat_nombre = r.categoria.nombre if r.categoria else "Sin categoría"
            prendas_info.append(
                PrendaAsociadaInfo(
                    id=r.id,
                    nombre=r.nombre,
                    precio_base=precio_base,
                    precio_promocional=precio_promo,
                    imagen_uri=r.imagen_uri,
                    categoria_nombre=cat_nombre
                )
            )

    return PromocionResponse(
        id=p.id,
        nombre=p.nombre,
        descripcion=p.descripcion,
        porcentaje_descuento=desc_pct,
        fecha_inicio=p.fecha_inicio,
        fecha_fin=p.fecha_fin,
        activo=p.activo,
        esta_vigente=vigente,
        estado_calculado=estado,
        total_prendas_asociadas=len(prendas_info),
        prendas=prendas_info
    )


router = APIRouter(
    prefix="/api/v1/promociones",
    tags=["CU08. Gestionar promociones y descuentos"]
)

router_compat = APIRouter(
    prefix="/api/promociones",
    tags=["CU08. Gestionar promociones y descuentos (Compat)"]
)


def _listar_promociones_impl(
    search: Optional[str] = None,
    categoria_id: Optional[int] = None,
    estado: Optional[str] = None,
    page: Optional[int] = Query(None, ge=1),
    page_size: Optional[int] = Query(None, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Any:
    query = db.query(Promocion).order_by(Promocion.id.desc())

    if search:
        query = query.filter(
            or_(
                Promocion.nombre.ilike(f"%{search}%"),
                Promocion.descripcion.ilike(f"%{search}%")
            )
        )

    promociones_all = query.all()
    
    # Filtrado en memoria si hay filtros de estado o categoría
    items = []
    for p in promociones_all:
        resp = map_promocion_to_response(p)
        
        if estado:
            if resp.estado_calculado.upper() != estado.upper():
                continue
                
        if categoria_id:
            has_cat = any(
                assoc.ropa and assoc.ropa.categoria_id == categoria_id
                for assoc in p.ropas_asociadas
            )
            if not has_cat:
                continue

        items.append(resp)

    total = len(items)

    if page is not None and page_size is not None:
        start = (page - 1) * page_size
        end = start + page_size
        paginated_items = items[start:end]
        return {
            "count": total,
            "next": None,
            "previous": None,
            "results": paginated_items
        }

    return items


def _obtener_promocion_impl(promo_id: int, db: Session = Depends(get_db)) -> PromocionResponse:
    promo = db.query(Promocion).filter(Promocion.id == promo_id).first()
    if not promo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Promoción #{promo_id} no encontrada."
        )
    return map_promocion_to_response(promo)


def _crear_promocion_impl(promo_in: PromocionCreate, db: Session = Depends(get_db)) -> PromocionResponse:
    if promo_in.fecha_fin < promo_in.fecha_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Excepción A1: La fecha de finalización no puede ser anterior a la fecha de inicio."
        )

    nueva_promo = Promocion(
        nombre=promo_in.nombre.strip(),
        descripcion=promo_in.descripcion.strip() if promo_in.descripcion else None,
        porcentaje_descuento=promo_in.porcentaje_descuento,
        fecha_inicio=promo_in.fecha_inicio,
        fecha_fin=promo_in.fecha_fin,
        activo=promo_in.activo if promo_in.activo is not None else True
    )
    db.add(nueva_promo)
    db.flush()

    ropas_set = set(promo_in.ropas_ids or [])

    # Si se especificó una categoría, agregar todas las prendas de esa categoría
    if promo_in.categoria_id:
        ropas_cat = db.query(Ropa.id).filter(Ropa.categoria_id == promo_in.categoria_id).all()
        for (r_id,) in ropas_cat:
            ropas_set.add(r_id)

    for r_id in ropas_set:
        ropa = db.query(Ropa).filter(Ropa.id == r_id).first()
        if ropa:
            db.add(PromocionRopa(promocion_id=nueva_promo.id, ropa_id=r_id, estado="ACTIVA"))

    db.commit()
    db.refresh(nueva_promo)

    return map_promocion_to_response(nueva_promo)


def _actualizar_promocion_impl(
    promo_id: int,
    promo_in: PromocionUpdate,
    db: Session = Depends(get_db)
) -> PromocionResponse:
    promo = db.query(Promocion).filter(Promocion.id == promo_id).first()
    if not promo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Promoción #{promo_id} no encontrada."
        )

    if promo_in.nombre is not None:
        promo.nombre = promo_in.nombre.strip()
    if promo_in.descripcion is not None:
        promo.descripcion = promo_in.descripcion.strip() if promo_in.descripcion else None
    if promo_in.porcentaje_descuento is not None:
        promo.porcentaje_descuento = promo_in.porcentaje_descuento
    if promo_in.fecha_inicio is not None:
        promo.fecha_inicio = promo_in.fecha_inicio
    if promo_in.fecha_fin is not None:
        promo.fecha_fin = promo_in.fecha_fin
    if promo_in.activo is not None:
        promo.activo = promo_in.activo

    if promo.fecha_fin < promo.fecha_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de finalización no puede ser anterior a la fecha de inicio."
        )

    # Actualizar prendas asociadas si se envió la lista
    if promo_in.ropas_ids is not None:
        db.query(PromocionRopa).filter(PromocionRopa.promocion_id == promo_id).delete()
        for r_id in promo_in.ropas_ids:
            ropa = db.query(Ropa).filter(Ropa.id == r_id).first()
            if ropa:
                db.add(PromocionRopa(promocion_id=promo.id, ropa_id=r_id, estado="ACTIVA"))

    db.commit()
    db.refresh(promo)
    return map_promocion_to_response(promo)


def _eliminar_promocion_impl(promo_id: int, db: Session = Depends(get_db)):
    promo = db.query(Promocion).filter(Promocion.id == promo_id).first()
    if not promo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Promoción #{promo_id} no encontrada."
        )
    db.delete(promo)
    db.commit()
    return None


def _toggle_estado_impl(promo_id: int, db: Session = Depends(get_db)) -> PromocionResponse:
    promo = db.query(Promocion).filter(Promocion.id == promo_id).first()
    if not promo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Promoción #{promo_id} no encontrada."
        )
    promo.activo = not promo.activo
    db.commit()
    db.refresh(promo)
    return map_promocion_to_response(promo)


def _aplicar_categoria_impl(
    promo_id: int,
    req: AplicarCategoriaRequest,
    db: Session = Depends(get_db)
) -> PromocionResponse:
    promo = db.query(Promocion).filter(Promocion.id == promo_id).first()
    if not promo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Promoción #{promo_id} no encontrada."
        )

    ropas_cat = db.query(Ropa).filter(Ropa.categoria_id == req.categoria_id).all()
    existentes = {assoc.ropa_id for assoc in promo.ropas_asociadas}

    for r in ropas_cat:
        if r.id not in existentes:
            db.add(PromocionRopa(promocion_id=promo.id, ropa_id=r.id, estado="ACTIVA"))

    db.commit()
    db.refresh(promo)
    return map_promocion_to_response(promo)


def _asociar_prenda_impl(
    promo_id: int,
    ropa_id: int,
    db: Session = Depends(get_db)
) -> PromocionResponse:
    promo = db.query(Promocion).filter(Promocion.id == promo_id).first()
    if not promo:
        raise HTTPException(status_code=404, detail="Promoción no encontrada.")
    ropa = db.query(Ropa).filter(Ropa.id == ropa_id).first()
    if not ropa:
        raise HTTPException(status_code=404, detail="Prenda no encontrada.")

    ya_asoc = db.query(PromocionRopa).filter(
        PromocionRopa.promocion_id == promo_id,
        PromocionRopa.ropa_id == ropa_id
    ).first()

    if not ya_asoc:
        db.add(PromocionRopa(promocion_id=promo_id, ropa_id=ropa_id, estado="ACTIVA"))
        db.commit()
        db.refresh(promo)

    return map_promocion_to_response(promo)


def _desasociar_prenda_impl(
    promo_id: int,
    ropa_id: int,
    db: Session = Depends(get_db)
) -> PromocionResponse:
    promo = db.query(Promocion).filter(Promocion.id == promo_id).first()
    if not promo:
        raise HTTPException(status_code=404, detail="Promoción no encontrada.")

    db.query(PromocionRopa).filter(
        PromocionRopa.promocion_id == promo_id,
        PromocionRopa.ropa_id == ropa_id
    ).delete()
    db.commit()
    db.refresh(promo)

    return map_promocion_to_response(promo)


# Registrar endpoints en ambos routers
for r in [router, router_compat]:
    r.add_api_route(
        "/",
        _listar_promociones_impl,
        methods=["GET"],
        summary="Listar campañas promocionales",
        description="Recupera todas las promociones con prendas asignadas, estado y vigencia."
    )
    r.add_api_route(
        "/",
        _crear_promocion_impl,
        methods=["POST"],
        status_code=status.HTTP_201_CREATED,
        summary="Crear campaña promocional y aplicarla a prendas o categorías"
    )
    r.add_api_route(
        "/{promo_id}",
        _obtener_promocion_impl,
        methods=["GET"],
        response_model=PromocionResponse,
        summary="Detalle de promoción con prendas asociadas"
    )
    r.add_api_route(
        "/{promo_id}",
        _actualizar_promocion_impl,
        methods=["PUT", "PATCH"],
        response_model=PromocionResponse,
        summary="Actualizar promoción y prendas asignadas"
    )
    r.add_api_route(
        "/{promo_id}",
        _eliminar_promocion_impl,
        methods=["DELETE"],
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Eliminar promoción"
    )
    r.add_api_route(
        "/{promo_id}/toggle_estado",
        _toggle_estado_impl,
        methods=["POST", "PATCH"],
        response_model=PromocionResponse,
        summary="Activar o pausar promoción"
    )
    r.add_api_route(
        "/{promo_id}/publicar/",
        _toggle_estado_impl,
        methods=["POST"],
        response_model=PromocionResponse,
        summary="Publicar promoción (compatibilidad notificaciones)"
    )
    r.add_api_route(
        "/{promo_id}/aplicar_categoria",
        _aplicar_categoria_impl,
        methods=["POST"],
        response_model=PromocionResponse,
        summary="Aplicar promoción a todas las prendas de una categoría"
    )
    r.add_api_route(
        "/{promo_id}/prendas/{ropa_id}",
        _asociar_prenda_impl,
        methods=["POST"],
        response_model=PromocionResponse,
        summary="Asociar prenda a la promoción"
    )
    r.add_api_route(
        "/{promo_id}/prendas/{ropa_id}",
        _desasociar_prenda_impl,
        methods=["DELETE"],
        response_model=PromocionResponse,
        summary="Desasociar prenda de la promoción"
    )
