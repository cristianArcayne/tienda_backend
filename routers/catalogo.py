"""
Router para CU07: Catálogo de Prendas y Recursos 3D.
Alineado fielmente con la entidad ROPA y el Diagrama de Clases UML de FashionStore.
Soporta gestión completa de prendas, imágenes, modelos 3D (.glb/.gltf para Realidad Aumentada) y variantes.
"""
import os
import uuid
from datetime import date
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, or_

from database import get_db
from models.catalogo import (
    Categoria,
    Temporada,
    Proveedor,
    Ropa,
    Talla,
    Color,
    VariantePrenda,
    Promocion,
    PromocionRopa,
    Resena
)
from models.sucursal import InventarioSucursal, Sucursal
from schemas.catalogo import (
    RopaCreate,
    RopaResponse,
    CategoriaResponse,
    TemporadaResponse,
    ProveedorResponse,
    VariantePrendaResponse,
    ResenaCreate,
    ResenaResponse,
    VariantePrendaCreate
)

router = APIRouter(
    prefix="/api/v1/prendas",
    tags=["CU07. Gestionar catálogo de prendas y recursos 3D"]
)


def _formatear_ropa(ropa: Ropa) -> RopaResponse:
    """Calcula promociones activas y recursos AR para la respuesta estructurada UML"""
    hoy = date.today()
    
    # 1. Detectar si posee modelo 3D para probador virtual AR
    tiene_ar = bool(ropa.modelo_3d_uri and (
        ropa.modelo_3d_uri.endswith(".glb") or 
        ropa.modelo_3d_uri.endswith(".gltf") or 
        "3d" in ropa.modelo_3d_uri.lower() or 
        "readyplayer" in ropa.modelo_3d_uri.lower()
    ))

    # 2. Calcular precio promocional vigente
    mejor_descuento: Optional[float] = None
    if ropa.promociones_asociadas:
        descuentos_activos = []
        for pr in ropa.promociones_asociadas:
            if pr.estado == "ACTIVA" and pr.promocion:
                f_ini = pr.promocion.fecha_inicio.date() if hasattr(pr.promocion.fecha_inicio, 'date') else pr.promocion.fecha_inicio
                f_fin = pr.promocion.fecha_fin.date() if hasattr(pr.promocion.fecha_fin, 'date') else pr.promocion.fecha_fin
                if f_ini and f_fin and (f_ini <= hoy <= f_fin):
                    descuentos_activos.append(float(pr.promocion.porcentaje_descuento))
        if descuentos_activos:
            mejor_descuento = max(descuentos_activos)

    precio_flt = float(ropa.precio) if ropa.precio is not None else 0.0
    precio_promo = round(precio_flt * (1.0 - (mejor_descuento / 100.0)), 2) if mejor_descuento is not None else None

    variantes_resp = [
        VariantePrendaResponse(
            id=v.id,
            cod_barra=v.cod_barra,
            ropa_id=v.ropa_id,
            talla_id=v.talla_id,
            color_id=v.color_id,
            talla=v.talla,
            color=v.color
        )
        for v in (ropa.variantes or [])
    ]

    return RopaResponse(
        id=ropa.id,
        nombre=ropa.nombre,
        descripcion=ropa.descripcion,
        precio=precio_flt,
        imagen_uri=ropa.imagen_uri,
        modelo_3d_uri=ropa.modelo_3d_uri,
        categoria_id=ropa.categoria_id,
        temporada_id=ropa.temporada_id,
        proveedor_id=ropa.proveedor_id,
        categoria=ropa.categoria,
        temporada=ropa.temporada,
        proveedor=ropa.proveedor,
        variantes=variantes_resp,
        precio_promocional=precio_promo,
        tiene_modelo_ar=tiene_ar
    )


def _normalizar_media_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    if url.startswith("/static/"):
        return f"http://localhost:8000{url}"
    return url


def _formatear_producto_angular(ropa: Ropa, db: Session = None, sucursal_id: Optional[int] = None) -> dict:
    """Formato compatible al 100% con Angular Producto / Multimedia / Variantes"""
    img_url = _normalizar_media_url(ropa.imagen_uri)
    m3d_url = _normalizar_media_url(ropa.modelo_3d_uri)

    imagenes = []
    if img_url:
        imagenes.append({
            "id": 1,
            "archivo_url": img_url,
            "tipo": "imagen",
            "es_principal": True,
            "orden": 0
        })
    
    modelos_3d = []
    if m3d_url:
        modelos_3d.append({
            "id": 2,
            "archivo_url": m3d_url,
            "tipo": "realidad_aumentada",
            "es_principal": True,
            "orden": 1
        })
    
    hoy = date.today()
    mejor_descuento: Optional[float] = None
    if ropa.promociones_asociadas:
        descuentos_activos = []
        for pr in ropa.promociones_asociadas:
            if pr.estado == "ACTIVA" and pr.promocion:
                p_act = getattr(pr.promocion, 'activo', True)
                if p_act:
                    f_ini = pr.promocion.fecha_inicio.date() if hasattr(pr.promocion.fecha_inicio, 'date') else pr.promocion.fecha_inicio
                    f_fin = pr.promocion.fecha_fin.date() if hasattr(pr.promocion.fecha_fin, 'date') else pr.promocion.fecha_fin
                    if f_ini and f_fin and (f_ini <= hoy <= f_fin):
                        descuentos_activos.append(float(pr.promocion.porcentaje_descuento))
        if descuentos_activos:
            mejor_descuento = max(descuentos_activos)

    cat_nombre = ropa.categoria.nombre if ropa.categoria else "General"
    marca_nombre = ropa.proveedor.razon_social if ropa.proveedor else (ropa.categoria.nombre if ropa.categoria else "FashionStore")
    precio_flt = float(ropa.precio) if ropa.precio is not None else 0.0
    precio_promo = round(precio_flt * (1.0 - (mejor_descuento / 100.0)), 2) if mejor_descuento is not None else None
    en_oferta = mejor_descuento is not None and mejor_descuento > 0
    
    variantes_list = []
    for v in (ropa.variantes or []):
        talla_nombre = v.talla.nombre if v.talla else "M"
        color_nombre = v.color.nombre if v.color else "Normal"
        color_hex = v.color.codigo_hex if v.color else "#000000"
        
        stock_total = 0
        if v.inventarios_sucursal:
            if sucursal_id:
                stock_total = sum(inv.stock_disponible or inv.stock_fisico or 0 for inv in v.inventarios_sucursal if inv.sucursal_id == sucursal_id)
            else:
                stock_total = sum(inv.stock_disponible or inv.stock_fisico or 0 for inv in v.inventarios_sucursal)
        elif db:
            if sucursal_id:
                invs = db.query(InventarioSucursal).filter(InventarioSucursal.variante_id == v.id, InventarioSucursal.sucursal_id == sucursal_id).all()
            else:
                invs = db.query(InventarioSucursal).filter(InventarioSucursal.variante_id == v.id).all()
            stock_total = sum(inv.stock_disponible or inv.stock_fisico or 0 for inv in invs)
        
        variantes_list.append({
            "id": v.id,
            "sku": v.sku or f"SKU-{v.id}",
            "cod_barra": v.cod_barra or f"BAR-{v.id}",
            "precio": float(v.precio_ajustado or precio_flt),
            "precio_ajustado": float(v.precio_ajustado or precio_flt),
            "cantidad": stock_total,
            "stock": stock_total,
            "limite_cantidad": 50,
            "costo_ponderado": float(ropa.costo_estandar or 0.0),
            "producto_id": ropa.id,
            "talla_id": v.talla_id,
            "talla_nombre": talla_nombre,
            "color_id": v.color_id,
            "color_nombre": color_nombre,
            "color_hex": color_hex,
            "talla": {"id": v.talla.id, "nombre": v.talla.nombre} if v.talla else None,
            "color": {"id": v.color.id, "nombre": v.color.nombre, "codigo_hex": color_hex} if v.color else None
        })

    stock_total_producto = sum(v["stock"] for v in variantes_list)

    # Calcular reseñas y calificación promedio
    total_resenas = 0
    calificacion_promedio = None
    resenas_list = getattr(ropa, 'resenas', None)
    if resenas_list is None and db is not None:
        resenas_list = db.query(Resena).filter(Resena.ropa_id == ropa.id).all()
    if resenas_list:
        total_resenas = len(resenas_list)
        califs = [r.puntuacion_estrellas for r in resenas_list if r.puntuacion_estrellas is not None]
        if califs:
            calificacion_promedio = round(sum(califs) / len(califs), 1)

    return {
        "id": ropa.id,
        "nombre": ropa.nombre,
        "descripcion": ropa.descripcion or "",
        "activo": ropa.activo if ropa.activo is not None else True,
        "categoria": ropa.categoria_id,
        "categoria_id": ropa.categoria_id,
        "categoria_nombre": cat_nombre,
        "marca": ropa.proveedor_id or 1,
        "marca_id": ropa.proveedor_id or 1,
        "marca_nombre": marca_nombre,
        "precio": precio_flt,
        "precio_base": precio_flt,
        "precio_minimo": precio_promo if en_oferta else precio_flt,
        "precio_promocional": precio_promo,
        "porcentaje_descuento": mejor_descuento or 0.0,
        "en_oferta": en_oferta,
        "costo_estandar": float(ropa.costo_estandar or 0.0),
        "calificacion_promedio": calificacion_promedio,
        "total_resenas": total_resenas,
        "imagen_uri": img_url,
        "imagen_principal": img_url,
        "modelo_3d_uri": m3d_url,
        "imagenes": imagenes,
        "modelos_3d": modelos_3d,
        "variantes": variantes_list,
        "stock_total": stock_total_producto,
        "disponible_en_sucursal": stock_total_producto > 0,
        "sucursal_filtrada": sucursal_id,
        "tiene_modelo_ar": bool(ropa.modelo_3d_uri)
    }


# ==============================================================================
# ENDPOINTS REST CU07 (PRENDAS / ROPA / RECURSOS 3D)
# ==============================================================================

@router.get(
    "/",
    response_model=List[RopaResponse],
    summary="Listar catálogo con fotos, modelos 3D y precios promocionales",
    description="Consulta el catálogo completo de ropa con modelos 3D para Realidad Aumentada y descuentos estacionales."
)
@router.get("", response_model=List[RopaResponse])
def listar_prendas(
    categoria_id: Optional[int] = Query(None, description="Filtrar por ID de categoría"),
    temporada_id: Optional[int] = Query(None, description="Filtrar por ID de temporada"),
    solo_ar: Optional[bool] = Query(None, description="Filtrar solo prendas con modelo 3D para AR"),
    db: Session = Depends(get_db)
):
    query = db.query(Ropa).options(
        joinedload(Ropa.categoria),
        joinedload(Ropa.temporada),
        joinedload(Ropa.proveedor),
        joinedload(Ropa.variantes).joinedload(VariantePrenda.talla),
        joinedload(Ropa.variantes).joinedload(VariantePrenda.color),
        joinedload(Ropa.promociones_asociadas).joinedload(PromocionRopa.promocion)
    )

    if categoria_id:
        query = query.filter(Ropa.categoria_id == categoria_id)
    if temporada_id:
        query = query.filter(Ropa.temporada_id == temporada_id)

    ropas = query.order_by(Ropa.id.asc()).all()
    respuestas = [_formatear_ropa(r) for r in ropas]

    if solo_ar:
        respuestas = [r for r in respuestas if r.tiene_modelo_ar]

    return respuestas


@router.get(
    "/{ropa_id}",
    response_model=RopaResponse,
    summary="Detalle de prenda con recursos 3D",
    description="Obtiene la información técnica, modelos 3D y variantes de una prenda específica."
)
@router.get("/{ropa_id}/", response_model=RopaResponse)
def obtener_prenda(ropa_id: int, db: Session = Depends(get_db)):
    ropa = db.query(Ropa).options(
        joinedload(Ropa.categoria),
        joinedload(Ropa.temporada),
        joinedload(Ropa.proveedor),
        joinedload(Ropa.variantes).joinedload(VariantePrenda.talla),
        joinedload(Ropa.variantes).joinedload(VariantePrenda.color),
        joinedload(Ropa.promociones_asociadas).joinedload(PromocionRopa.promocion)
    ).filter(Ropa.id == ropa_id).first()

    if not ropa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prenda con ID {ropa_id} no encontrada en el catálogo."
        )

    return _formatear_ropa(ropa)


@router.post(
    "/",
    response_model=RopaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nueva prenda y vincular modelo 3D para AR",
    description="Registra una prenda en el catálogo validando que no existan duplicados de nombre comercial (Excepción A1)."
)
@router.post("", response_model=RopaResponse, status_code=status.HTTP_201_CREATED)
def crear_prenda(prenda_in: RopaCreate, db: Session = Depends(get_db)):
    duplicado = db.query(
        exists().where(Ropa.nombre == prenda_in.nombre)
    ).scalar()

    if duplicado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Excepción A1: Ya existe una prenda registrada con el nombre '{prenda_in.nombre}'."
        )

    nueva_ropa = Ropa(
        nombre=prenda_in.nombre,
        descripcion=prenda_in.descripcion,
        precio=prenda_in.precio,
        imagen_uri=prenda_in.imagen_uri,
        modelo_3d_uri=prenda_in.modelo_3d_uri,
        categoria_id=prenda_in.categoria_id,
        temporada_id=prenda_in.temporada_id,
        proveedor_id=prenda_in.proveedor_id,
        activo=True
    )
    db.add(nueva_ropa)
    db.commit()
    db.refresh(nueva_ropa)

    # Crear variante base y existencias en sucursales para que aparezca en inventario físico y ventas
    talla_def = db.query(Talla).filter(Talla.medida == "M").first() or db.query(Talla).first()
    color_def = db.query(Color).first()
    sku_prefix = "".join([c for c in nueva_ropa.nombre if c.isalnum()][:4]).upper() or "ROP"
    def_var = VariantePrenda(
        ropa_id=nueva_ropa.id,
        talla_id=talla_def.id if talla_def else 1,
        color_id=color_def.id if color_def else 1,
        sku=f"{sku_prefix}-{nueva_ropa.id}-M-STD",
        cod_barra=f"BAR-{nueva_ropa.id}-{sku_prefix}",
        activo=True
    )
    db.add(def_var)
    db.commit()
    db.refresh(def_var)

    sucursales = db.query(Sucursal).all()
    for suc in sucursales:
        db.add(InventarioSucursal(
            sucursal_id=suc.id,
            variante_id=def_var.id,
            stock_fisico=0,
            stock_reservado=0,
            stock_minimo=5
        ))
    db.commit()

    return _formatear_ropa(nueva_ropa)


@router.put("/{ropa_id}", response_model=RopaResponse)
@router.put("/{ropa_id}/", response_model=RopaResponse)
def actualizar_prenda(ropa_id: int, prenda_in: RopaCreate, db: Session = Depends(get_db)):
    ropa = db.query(Ropa).filter(Ropa.id == ropa_id).first()
    if not ropa:
        raise HTTPException(status_code=404, detail="Prenda no encontrada")
    ropa.nombre = prenda_in.nombre
    ropa.descripcion = prenda_in.descripcion
    ropa.precio = prenda_in.precio
    if prenda_in.imagen_uri:
        ropa.imagen_uri = prenda_in.imagen_uri
    if prenda_in.modelo_3d_uri:
        ropa.modelo_3d_uri = prenda_in.modelo_3d_uri
    if prenda_in.categoria_id:
        ropa.categoria_id = prenda_in.categoria_id
    if prenda_in.temporada_id:
        ropa.temporada_id = prenda_in.temporada_id
    if prenda_in.proveedor_id:
        ropa.proveedor_id = prenda_in.proveedor_id
    db.commit()
    db.refresh(ropa)
    return _formatear_ropa(ropa)


@router.delete("/{ropa_id}")
@router.delete("/{ropa_id}/")
def eliminar_prenda(ropa_id: int, db: Session = Depends(get_db)):
    ropa = db.query(Ropa).filter(Ropa.id == ropa_id).first()
    if not ropa:
        raise HTTPException(status_code=404, detail="Prenda no encontrada")
    db.query(VariantePrenda).filter(VariantePrenda.ropa_id == ropa_id).delete()
    db.delete(ropa)
    db.commit()
    return {"message": "Prenda eliminada exitosamente"}


@router.post("/{ropa_id}/upload-foto")
async def upload_foto_prenda(ropa_id: int, archivo: UploadFile = File(...), db: Session = Depends(get_db)):
    """Sube un archivo de fotografía para la prenda y actualiza imagen_uri"""
    ropa = db.query(Ropa).filter(Ropa.id == ropa_id).first()
    if not ropa:
        raise HTTPException(status_code=404, detail="Prenda no encontrada")
    
    os.makedirs(os.path.join("static", "uploads"), exist_ok=True)
    ext = os.path.splitext(archivo.filename)[1] or ".jpg"
    filename = f"prenda_{ropa_id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join("static", "uploads", filename)
    
    with open(filepath, "wb") as f:
        f.write(await archivo.read())
    
    ropa.imagen_uri = f"/static/uploads/{filename}"
    db.commit()
    db.refresh(ropa)
    return {"message": "Fotografía subida exitosamente", "imagen_uri": ropa.imagen_uri}


@router.post("/{ropa_id}/upload-3d")
async def upload_modelo_3d_prenda(ropa_id: int, archivo: UploadFile = File(...), db: Session = Depends(get_db)):
    """Sube un archivo de modelo tridimensional (.glb / .gltf) para el vestidor virtual AR"""
    ropa = db.query(Ropa).filter(Ropa.id == ropa_id).first()
    if not ropa:
        raise HTTPException(status_code=404, detail="Prenda no encontrada")
    
    ext = os.path.splitext(archivo.filename)[1].lower()
    if ext not in [".glb", ".gltf", ".obj", ".fbx"]:
        raise HTTPException(status_code=400, detail="Formato 3D no válido. Debe ser .glb o .gltf")
    
    os.makedirs(os.path.join("static", "uploads"), exist_ok=True)
    filename = f"modelo3d_{ropa_id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join("static", "uploads", filename)
    
    with open(filepath, "wb") as f:
        f.write(await archivo.read())
    
    ropa.modelo_3d_uri = f"/static/uploads/{filename}"
    db.commit()
    db.refresh(ropa)
    return {"message": "Modelo 3D para Realidad Aumentada subido exitosamente", "modelo_3d_uri": ropa.modelo_3d_uri}


@router.post("/{ropa_id}/variantes", response_model=VariantePrendaResponse, status_code=status.HTTP_201_CREATED)
def agregar_variante(ropa_id: int, var_in: VariantePrendaCreate, db: Session = Depends(get_db)):
    if db.query(exists().where(VariantePrenda.cod_barra == var_in.cod_barra)).scalar():
        raise HTTPException(status_code=400, detail="Código de barras ya registrado")
    
    if db.query(exists().where(
        (VariantePrenda.ropa_id == ropa_id) & 
        (VariantePrenda.talla_id == var_in.talla_id) & 
        (VariantePrenda.color_id == var_in.color_id)
    )).scalar():
        raise HTTPException(status_code=400, detail="La variante (talla, color) ya existe para esta prenda")
    
    nueva = VariantePrenda(
        ropa_id=ropa_id,
        talla_id=var_in.talla_id,
        color_id=var_in.color_id,
        sku=var_in.sku,
        cod_barra=var_in.cod_barra,
        precio_ajustado=var_in.precio_ajustado
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


# ==============================================================================
# ALIAS Y COMPATIBILIDAD FRONTEND ANGULAR (/api/catalogo, /api/productos, /api/marcas, etc.)
# ==============================================================================

router_catalogo_compat = APIRouter(
    prefix="/api/catalogo",
    tags=["CU07. Catálogo Web"]
)

@router_catalogo_compat.get("/")
@router_catalogo_compat.get("")
def listar_catalogo_compat(
    categoria: Optional[int] = None,
    categoria_id: Optional[int] = None,
    sucursal_id: Optional[int] = None,
    search: Optional[str] = None,
    page: Optional[int] = None,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    cat_filtro = categoria or categoria_id
    query = db.query(Ropa).options(
        joinedload(Ropa.categoria),
        joinedload(Ropa.temporada),
        joinedload(Ropa.proveedor),
        joinedload(Ropa.variantes).joinedload(VariantePrenda.talla),
        joinedload(Ropa.variantes).joinedload(VariantePrenda.color),
        joinedload(Ropa.promociones_asociadas).joinedload(PromocionRopa.promocion),
        joinedload(Ropa.resenas)
    )
    if cat_filtro:
        query = query.filter(Ropa.categoria_id == cat_filtro)
    if search:
        query = query.filter(Ropa.nombre.ilike(f"%{search}%"))

    total = query.count()
    if page is not None:
        ropas = query.order_by(Ropa.id.asc()).offset((page - 1) * page_size).limit(page_size).all()
        res = [_formatear_producto_angular(r, db=db, sucursal_id=sucursal_id) for r in ropas]
        base = "/api/catalogo/"
        return {
            "count": total,
            "next": f"{base}?page={page+1}&page_size={page_size}" if page * page_size < total else None,
            "previous": f"{base}?page={page-1}&page_size={page_size}" if page > 1 else None,
            "results": res
        }
    else:
        ropas = query.order_by(Ropa.id.asc()).all()
        return [_formatear_producto_angular(r, db=db, sucursal_id=sucursal_id) for r in ropas]

@router_catalogo_compat.get("/{ropa_id}")
@router_catalogo_compat.get("/{ropa_id}/")
def obtener_catalogo_compat(ropa_id: int, db: Session = Depends(get_db)):
    ropa = db.query(Ropa).filter(Ropa.id == ropa_id).first()
    if not ropa:
        raise HTTPException(status_code=404, detail="Prenda no encontrada")
    return _formatear_producto_angular(ropa, db=db)


@router_catalogo_compat.get("/ropas")
@router_catalogo_compat.get("/ropas/")
def listar_catalogo_ropas_compat(db: Session = Depends(get_db)):
    return listar_catalogo_compat(page=None, db=db)


router_catalogo_v1 = APIRouter(
    prefix="/api/v1/catalogo",
    tags=["CU07. Catálogo Web v1"]
)

@router_catalogo_v1.get("/")
@router_catalogo_v1.get("")
@router_catalogo_v1.get("/ropas")
@router_catalogo_v1.get("/ropas/")
def listar_catalogo_v1(
    categoria: Optional[int] = None,
    categoria_id: Optional[int] = None,
    sucursal_id: Optional[int] = None,
    search: Optional[str] = None,
    page: Optional[int] = None,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    return listar_catalogo_compat(
        categoria=categoria,
        categoria_id=categoria_id,
        sucursal_id=sucursal_id,
        search=search,
        page=page,
        page_size=page_size,
        db=db
    )

@router_catalogo_v1.get("/{ropa_id}")
@router_catalogo_v1.get("/{ropa_id}/")
def obtener_catalogo_v1(ropa_id: int, db: Session = Depends(get_db)):
    return obtener_catalogo_compat(ropa_id=ropa_id, db=db)


router_productos_compat = APIRouter(
    prefix="/api/productos",
    tags=["CU07. Productos Web"]
)

router_productos_v1 = APIRouter(
    prefix="/api/v1/productos",
    tags=["CU07. Productos Web v1"]
)

def _listar_productos_impl(
    page: Optional[int] = None,
    page_size: int = 10,
    search: Optional[str] = None,
    categoria: Optional[int] = None,
    categoria_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    return listar_catalogo_compat(
        categoria=categoria,
        categoria_id=categoria_id,
        search=search,
        page=page,
        page_size=page_size,
        db=db
    )

def _obtener_producto_impl(ropa_id: int, db: Session = Depends(get_db)):
    ropa = db.query(Ropa).filter(Ropa.id == ropa_id).first()
    if not ropa:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return _formatear_producto_angular(ropa, db=db)

def _crear_producto_impl(data: dict, db: Session = Depends(get_db)):
    nombre = data.get("nombre")
    if not nombre:
        raise HTTPException(status_code=400, detail="El nombre del producto es obligatorio")
    
    if db.query(exists().where(Ropa.nombre == nombre)).scalar():
        raise HTTPException(status_code=400, detail="Ya existe una prenda registrada con este nombre")
    
    categoria_id = data.get("categoria_id") or data.get("categoria") or 1
    proveedor_id = data.get("marca_id") or data.get("proveedor_id") or 1
    
    nueva = Ropa(
        nombre=nombre,
        descripcion=data.get("descripcion", ""),
        precio=data.get("precio", 150.0),
        imagen_uri=data.get("imagen_uri", "https://images.unsplash.com/photo-1523381210434-271e8be1f52b"),
        modelo_3d_uri=data.get("modelo_3d_uri"),
        categoria_id=categoria_id,
        temporada_id=data.get("temporada_id") or 1,
        proveedor_id=proveedor_id,
        activo=data.get("activo", True)
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return _formatear_producto_angular(nueva, db=db)

for r_prod in [router_productos_compat, router_productos_v1]:
    r_prod.add_api_route("/", _listar_productos_impl, methods=["GET"])
    r_prod.add_api_route("", _listar_productos_impl, methods=["GET"], include_in_schema=False)
    r_prod.add_api_route("/{ropa_id}", _obtener_producto_impl, methods=["GET"])
    r_prod.add_api_route("/{ropa_id}/", _obtener_producto_impl, methods=["GET"], include_in_schema=False)
    r_prod.add_api_route("/", _crear_producto_impl, methods=["POST"])
    r_prod.add_api_route("", _crear_producto_impl, methods=["POST"], include_in_schema=False)

@router_productos_compat.put("/{ropa_id}")
@router_productos_compat.put("/{ropa_id}/")
def actualizar_producto_compat(ropa_id: int, data: dict, db: Session = Depends(get_db)):
    ropa = db.query(Ropa).filter(Ropa.id == ropa_id).first()
    if not ropa:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    if "nombre" in data and data["nombre"]:
        ropa.nombre = data["nombre"]
    if "descripcion" in data:
        ropa.descripcion = data["descripcion"]
    if "precio" in data and data["precio"] is not None:
        ropa.precio = data["precio"]
    if "categoria_id" in data and data["categoria_id"]:
        ropa.categoria_id = data["categoria_id"]
    if "marca_id" in data and data["marca_id"]:
        ropa.proveedor_id = data["marca_id"]
    if "activo" in data:
        ropa.activo = data["activo"]
    if "imagen_uri" in data and data["imagen_uri"]:
        ropa.imagen_uri = data["imagen_uri"]
    if "modelo_3d_uri" in data:
        ropa.modelo_3d_uri = data["modelo_3d_uri"]
        
    db.commit()
    db.refresh(ropa)
    return _formatear_producto_angular(ropa, db=db)

@router_productos_compat.delete("/{ropa_id}")
@router_productos_compat.delete("/{ropa_id}/")
def eliminar_producto_compat(ropa_id: int, db: Session = Depends(get_db)):
    ropa = db.query(Ropa).filter(Ropa.id == ropa_id).first()
    if not ropa:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    db.query(VariantePrenda).filter(VariantePrenda.ropa_id == ropa_id).delete()
    db.delete(ropa)
    db.commit()
    return {"message": "Producto eliminado exitosamente"}

@router_productos_compat.get("/{ropa_id}/recomendados")
@router_productos_compat.get("/{ropa_id}/recomendados/")
def recomendados_compat(ropa_id: int, db: Session = Depends(get_db)):
    ropa = db.query(Ropa).filter(Ropa.id == ropa_id).first()
    query = db.query(Ropa).filter(Ropa.id != ropa_id)
    if ropa and ropa.categoria_id:
        query = query.filter(Ropa.categoria_id == ropa.categoria_id)
    recomendados = query.limit(4).all()
    return [_formatear_producto_angular(r, db=db) for r in recomendados]


# ─── Endpoint para Detalle de Producto (/api/productos-detalle) ─────────────
router_productos_detalle_compat = APIRouter(
    prefix="/api/productos-detalle",
    tags=["CU07. Detalle de Producto"]
)

@router_productos_detalle_compat.get("/{ropa_id}")
@router_productos_detalle_compat.get("/{ropa_id}/")
def obtener_producto_detalle_compat(ropa_id: int, db: Session = Depends(get_db)):
    ropa = db.query(Ropa).options(
        joinedload(Ropa.categoria),
        joinedload(Ropa.temporada),
        joinedload(Ropa.proveedor),
        joinedload(Ropa.variantes).joinedload(VariantePrenda.talla),
        joinedload(Ropa.variantes).joinedload(VariantePrenda.color),
        joinedload(Ropa.promociones_asociadas).joinedload(PromocionRopa.promocion)
    ).filter(Ropa.id == ropa_id).first()
    if not ropa:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return _formatear_producto_angular(ropa, db=db)


# ─── Endpoint para Marcas (/api/marcas) ──────────────────────────────────────
router_marcas_compat = APIRouter(
    prefix="/api/marcas",
    tags=["CU07. Marcas"]
)

@router_marcas_compat.get("/")
@router_marcas_compat.get("")
def listar_marcas_compat(
    page: Optional[int] = None,
    page_size: int = 100,
    db: Session = Depends(get_db)
):
    provs = db.query(Proveedor).order_by(Proveedor.id.asc()).all()
    results = [{"id": p.id, "nombre": p.razon_social, "descripcion": f"Proveedor {p.razon_social}"} for p in provs]
    if page is not None:
        return {
            "count": len(results),
            "next": None,
            "previous": None,
            "results": results
        }
    return results


@router_marcas_compat.post("/")
@router_marcas_compat.post("")
def crear_marca_compat(data: dict, db: Session = Depends(get_db)):
    nombre = (data.get("nombre") or "").strip()
    if not nombre:
        raise HTTPException(status_code=400, detail="El nombre de la marca es obligatorio.")
    if db.query(exists().where(Proveedor.razon_social == nombre)).scalar():
        raise HTTPException(status_code=400, detail=f"La marca '{nombre}' ya existe.")
    nuevo = Proveedor(razon_social=nombre)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return {"id": nuevo.id, "nombre": nuevo.razon_social, "descripcion": f"Proveedor {nuevo.razon_social}"}


@router_marcas_compat.put("/{marca_id}")
@router_marcas_compat.put("/{marca_id}/")
def actualizar_marca_compat(marca_id: int, data: dict, db: Session = Depends(get_db)):
    p = db.query(Proveedor).filter(Proveedor.id == marca_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Marca no encontrada.")
    nombre = (data.get("nombre") or "").strip()
    if not nombre:
        raise HTTPException(status_code=400, detail="El nombre de la marca es obligatorio.")
    p.razon_social = nombre
    db.commit()
    db.refresh(p)
    return {"id": p.id, "nombre": p.razon_social, "descripcion": f"Proveedor {p.razon_social}"}


@router_marcas_compat.delete("/{marca_id}")
@router_marcas_compat.delete("/{marca_id}/")
def eliminar_marca_compat(marca_id: int, db: Session = Depends(get_db)):
    p = db.query(Proveedor).filter(Proveedor.id == marca_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Marca no encontrada.")
    if db.query(exists().where(Ropa.proveedor_id == marca_id)).scalar():
        raise HTTPException(status_code=400, detail="Restricción: La marca tiene prendas asociadas en el catálogo.")
    db.delete(p)
    db.commit()
    return {"message": "Marca eliminada exitosamente", "id": marca_id}


# ─── Endpoint para Subida de Multimedia / Modelos 3D (/api/multimedios) ──────
router_multimedios_compat = APIRouter(
    prefix="/api/multimedios",
    tags=["CU07. Multimedios y Modelos 3D"]
)

@router_multimedios_compat.post("/")
@router_multimedios_compat.post("")
async def upload_multimedia_compat(
    archivo: UploadFile = File(...),
    producto_id: int = Form(...),
    tipo: str = Form("imagen"),
    es_principal: bool = Form(False),
    orden: int = Form(0),
    db: Session = Depends(get_db)
):
    ropa = db.query(Ropa).filter(Ropa.id == producto_id).first()
    if not ropa:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    os.makedirs(os.path.join("static", "uploads"), exist_ok=True)
    ext = os.path.splitext(archivo.filename)[1].lower()
    filename = f"media_{producto_id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join("static", "uploads", filename)
    
    with open(filepath, "wb") as f:
        f.write(await archivo.read())
    
    url_guardada = f"/static/uploads/{filename}"
    if tipo == "realidad_aumentada" or ext in [".glb", ".gltf", ".obj", ".fbx"]:
        ropa.modelo_3d_uri = url_guardada
    else:
        ropa.imagen_uri = url_guardada
    
    db.commit()
    db.refresh(ropa)
    return {
        "id": 1,
        "archivo_url": url_guardada,
        "tipo": tipo,
        "es_principal": es_principal,
        "orden": orden,
        "producto_id": producto_id
    }

@router_multimedios_compat.delete("/{media_id}")
@router_multimedios_compat.delete("/{media_id}/")
def eliminar_multimedia_compat(media_id: int, db: Session = Depends(get_db)):
    return {"message": "Recurso multimedia eliminado"}

@router_multimedios_compat.patch("/{media_id}")
@router_multimedios_compat.patch("/{media_id}/")
def actualizar_multimedia_compat(media_id: int, data: dict, db: Session = Depends(get_db)):
    return {"message": "Recurso multimedia actualizado"}


# ─── Endpoint para Variantes de Prenda (/api/variantes) ──────────────────────
router_variantes_compat = APIRouter(
    prefix="/api/variantes",
    tags=["CU07. Variantes"]
)

@router_variantes_compat.get("/")
@router_variantes_compat.get("")
def listar_variantes_compat(
    producto_id: Optional[int] = None,
    ropa_id: Optional[int] = None,
    sucursal_id: Optional[int] = None,
    page: Optional[int] = None,
    page_size: int = 1000,
    db: Session = Depends(get_db)
):
    pid = producto_id or ropa_id
    query = db.query(VariantePrenda).options(
        joinedload(VariantePrenda.talla),
        joinedload(VariantePrenda.color),
        joinedload(VariantePrenda.ropa).joinedload(Ropa.categoria),
        joinedload(VariantePrenda.ropa).joinedload(Ropa.proveedor),
        joinedload(VariantePrenda.ropa).joinedload(Ropa.promociones_asociadas).joinedload(PromocionRopa.promocion),
        joinedload(VariantePrenda.inventarios_sucursal)
    )
    if pid:
        query = query.filter(VariantePrenda.ropa_id == pid)
    
    total = query.count()
    items = query.order_by(VariantePrenda.id.asc()).all()
    hoy = date.today()
    results = []
    for v in items:
        ropa = v.ropa
        precio_ropa = float(ropa.precio) if (ropa and ropa.precio is not None) else 0.0
        talla_nom = getattr(v.talla, 'medida', None) or (v.talla.nombre if v.talla else "M")
        color_nom = v.color.nombre if v.color else "Normal"
        color_hx = v.color.codigo_hex if v.color else "#000000"
        
        # Stock real físico
        if sucursal_id:
            inv_suc = next((inv for inv in (v.inventarios_sucursal or []) if inv.sucursal_id == sucursal_id), None)
            if not inv_suc:
                inv_suc = db.query(InventarioSucursal).filter(InventarioSucursal.variante_id == v.id, InventarioSucursal.sucursal_id == sucursal_id).first()
            stock_total = (inv_suc.stock_disponible or inv_suc.stock_fisico or 0) if inv_suc else 0
        else:
            stock_total = sum(inv.stock_disponible or inv.stock_fisico or 0 for inv in (v.inventarios_sucursal or []))
            if stock_total == 0 and not v.inventarios_sucursal:
                invs = db.query(InventarioSucursal).filter(InventarioSucursal.variante_id == v.id).all()
                stock_total = sum(inv.stock_disponible or inv.stock_fisico or 0 for inv in invs)
        
        # Descuento promocional activo
        mejor_descuento = 0.0
        if ropa and ropa.promociones_asociadas:
            descuentos_activos = []
            for pr in ropa.promociones_asociadas:
                if pr.estado and pr.estado.upper() == "ACTIVA" and pr.promocion:
                    p = pr.promocion
                    if getattr(p, "activo", True):
                        f_ini = p.fecha_inicio.date() if hasattr(p.fecha_inicio, "date") else p.fecha_inicio
                        f_fin = p.fecha_fin.date() if hasattr(p.fecha_fin, "date") else p.fecha_fin
                        if f_ini and f_fin and (f_ini <= hoy <= f_fin):
                            descuentos_activos.append(float(p.porcentaje_descuento))
            if descuentos_activos:
                mejor_descuento = max(descuentos_activos)
        
        precio_base = float(v.precio_ajustado or precio_ropa)
        precio_promo = round(precio_base * (1.0 - (mejor_descuento / 100.0)), 2) if mejor_descuento > 0 else precio_base
        en_oferta = mejor_descuento > 0
        
        results.append({
            "id": v.id,
            "sku": v.sku or f"SKU-{v.id}",
            "cod_barra": v.cod_barra or f"BAR-{v.id}",
            "precio": precio_promo if en_oferta else precio_base,
            "precio_original": precio_base,
            "precio_ajustado": precio_promo if en_oferta else precio_base,
            "precio_promocional": precio_promo if en_oferta else None,
            "porcentaje_descuento": mejor_descuento,
            "en_oferta": en_oferta,
            "cantidad": stock_total,
            "stock": stock_total,
            "limite_cantidad": 50,
            "costo_ponderado": float(ropa.costo_estandar or 0.0) if ropa else 0.0,
            "producto": v.ropa_id,
            "producto_id": v.ropa_id,
            "producto_nombre": ropa.nombre if ropa else f"Prenda #{v.ropa_id}",
            "categoria_nombre": ropa.categoria.nombre if (ropa and ropa.categoria) else "General",
            "marca_nombre": ropa.proveedor.razon_social if (ropa and ropa.proveedor) else "FashionStore",
            "imagen_url": _normalizar_media_url(ropa.imagen_uri) if ropa else None,
            "talla_id": v.talla_id,
            "talla_nombre": talla_nom,
            "color_id": v.color_id,
            "color_nombre": color_nom,
            "color_hex": color_hx,
            "talla": {"id": v.talla.id, "nombre": talla_nom} if v.talla else None,
            "color": {"id": v.color.id, "nombre": color_nom, "codigo_hex": color_hx} if v.color else None
        })
    
    if page is not None:
        return {
            "count": total,
            "next": None,
            "previous": None,
            "results": results
        }
    return results

@router_variantes_compat.post("/")
@router_variantes_compat.post("")
def crear_variante_compat(data: dict, db: Session = Depends(get_db)):
    ropa_id = data.get("producto_id") or data.get("ropa_id") or 1
    talla_id = data.get("talla_id") or 1
    color_id = data.get("color_id") or 1
    sku = data.get("sku") or f"SKU-{uuid.uuid4().hex[:6].upper()}"
    cod_barra = data.get("cod_barra") or f"BAR-{uuid.uuid4().hex[:8].upper()}"
    precio_ajustado = data.get("precio_ajustado") or data.get("precio")
    
    nueva = VariantePrenda(
        ropa_id=ropa_id,
        talla_id=talla_id,
        color_id=color_id,
        sku=sku,
        cod_barra=cod_barra,
        precio_ajustado=precio_ajustado
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return {"message": "Variante creada exitosamente", "id": nueva.id}

@router_variantes_compat.put("/{var_id}")
@router_variantes_compat.put("/{var_id}/")
def actualizar_variante_compat(var_id: int, data: dict, db: Session = Depends(get_db)):
    var = db.query(VariantePrenda).filter(VariantePrenda.id == var_id).first()
    if not var:
        raise HTTPException(status_code=404, detail="Variante no encontrada")
    if "talla_id" in data:
        var.talla_id = data["talla_id"]
    if "color_id" in data:
        var.color_id = data["color_id"]
    if "sku" in data:
        var.sku = data["sku"]
    if "cod_barra" in data:
        var.cod_barra = data["cod_barra"]
    if "precio_ajustado" in data:
        var.precio_ajustado = data["precio_ajustado"]
    db.commit()
    db.refresh(var)
    return {"message": "Variante actualizada exitosamente"}

@router_variantes_compat.delete("/{var_id}")
@router_variantes_compat.delete("/{var_id}/")
def eliminar_variante_compat(var_id: int, db: Session = Depends(get_db)):
    var = db.query(VariantePrenda).filter(VariantePrenda.id == var_id).first()
    if not var:
        raise HTTPException(status_code=404, detail="Variante no encontrada")
    db.delete(var)
    db.commit()
    return {"message": "Variante eliminada exitosamente"}
