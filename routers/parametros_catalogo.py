from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import exists

from database import get_db
from models.catalogo import Categoria, Temporada, Color, Proveedor, Ropa, VariantePrenda
from schemas.catalogo import (
    CategoriaCreate, CategoriaResponse,
    TemporadaCreate, TemporadaResponse,
    ColorCreate, ColorResponse,
    ProveedorCreate, ProveedorResponse
)

router = APIRouter(
    prefix="/api/v1/parametros",
    tags=["CU05 y CU06. Gestionar parámetros de moda y proveedores"]
)

# ==========================================
# CATEGORIAS
# ==========================================
@router.get("/categorias", response_model=List[CategoriaResponse])
def listar_categorias(db: Session = Depends(get_db)):
    return db.query(Categoria).order_by(Categoria.id.asc()).all()

@router.post("/categorias", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED)
def crear_categoria(cat_in: CategoriaCreate, db: Session = Depends(get_db)):
    if db.query(exists().where(Categoria.nombre == cat_in.nombre)).scalar():
        raise HTTPException(status_code=400, detail="Excepción A1: La categoría ya existe.")
    
    nueva = Categoria(nombre=cat_in.nombre)
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


@router.put("/categorias/{cat_id}", response_model=CategoriaResponse)
def actualizar_categoria(cat_id: int, cat_in: CategoriaCreate, db: Session = Depends(get_db)):
    cat = db.query(Categoria).filter(Categoria.id == cat_id).first()
    if not cat: raise HTTPException(status_code=404, detail="Categoría no encontrada.")
    cat.nombre = cat_in.nombre
    db.commit()
    db.refresh(cat)
    return cat

@router.delete("/categorias/{cat_id}")
def eliminar_categoria(cat_id: int, db: Session = Depends(get_db)):
    cat = db.query(Categoria).filter(Categoria.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada.")
    if db.query(exists().where(Ropa.categoria_id == cat_id)).scalar():
        raise HTTPException(status_code=400, detail="Restricción: Tiene prendas asociadas.")
    
    db.delete(cat)
    db.commit()
    return {"message": "Categoría eliminada."}


# ==========================================
# TEMPORADAS
# ==========================================
@router.get("/temporadas", response_model=List[TemporadaResponse])
def listar_temporadas(db: Session = Depends(get_db)):
    return db.query(Temporada).order_by(Temporada.id.asc()).all()

@router.post("/temporadas", response_model=TemporadaResponse, status_code=status.HTTP_201_CREATED)
def crear_temporada(temp_in: TemporadaCreate, db: Session = Depends(get_db)):
    if db.query(exists().where(Temporada.nombre == temp_in.nombre)).scalar():
        raise HTTPException(status_code=400, detail="Excepción A1: La temporada ya existe.")
    
    nueva = Temporada(nombre=temp_in.nombre)
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


@router.put("/temporadas/{temp_id}", response_model=TemporadaResponse)
def actualizar_temporada(temp_id: int, temp_in: TemporadaCreate, db: Session = Depends(get_db)):
    temp = db.query(Temporada).filter(Temporada.id == temp_id).first()
    if not temp: raise HTTPException(status_code=404, detail="Temporada no encontrada.")
    temp.nombre = temp_in.nombre
    db.commit()
    db.refresh(temp)
    return temp

@router.delete("/temporadas/{temp_id}")
def eliminar_temporada(temp_id: int, db: Session = Depends(get_db)):
    temp = db.query(Temporada).filter(Temporada.id == temp_id).first()
    if not temp:
        raise HTTPException(status_code=404, detail="Temporada no encontrada.")
    if db.query(exists().where(Ropa.temporada_id == temp_id)).scalar():
        raise HTTPException(status_code=400, detail="Restricción: Tiene prendas asociadas.")
    
    db.delete(temp)
    db.commit()
    return {"message": "Temporada eliminada."}


# ==========================================
# COLORES
# ==========================================
@router.get("/colores", response_model=List[ColorResponse])
def listar_colores(db: Session = Depends(get_db)):
    return db.query(Color).order_by(Color.id.asc()).all()

@router.post("/colores", response_model=ColorResponse, status_code=status.HTTP_201_CREATED)
def crear_color(col_in: ColorCreate, db: Session = Depends(get_db)):
    if db.query(exists().where(Color.nombre == col_in.nombre)).scalar():
        raise HTTPException(status_code=400, detail="Excepción A1: El color ya existe.")
    
    nueva = Color(nombre=col_in.nombre, codigo_hex=col_in.codigo_hex)
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


@router.put("/colores/{col_id}", response_model=ColorResponse)
def actualizar_color(col_id: int, col_in: ColorCreate, db: Session = Depends(get_db)):
    col = db.query(Color).filter(Color.id == col_id).first()
    if not col: raise HTTPException(status_code=404, detail="Color no encontrado.")
    col.nombre = col_in.nombre
    col.codigo_hex = col_in.codigo_hex
    db.commit()
    db.refresh(col)
    return col

@router.delete("/colores/{col_id}")
def eliminar_color(col_id: int, db: Session = Depends(get_db)):
    col = db.query(Color).filter(Color.id == col_id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Color no encontrado.")
    if db.query(exists().where(VariantePrenda.color_id == col_id)).scalar():
        raise HTTPException(status_code=400, detail="Restricción: Tiene variantes de prenda asociadas.")
    
    db.delete(col)
    db.commit()
    return {"message": "Color eliminado."}


# ==========================================
# PROVEEDORES
# ==========================================
def _formatear_proveedor(p: Proveedor) -> ProveedorResponse:
    return ProveedorResponse(
        id=p.id,
        razon_social=p.razon_social,
        nombre=p.razon_social,
        nit=p.nit,
        correo=p.correo,
        direccion=p.direccion,
        telefono=p.telefono,
        contacto=p.contacto
    )

@router.get("/proveedores", response_model=List[ProveedorResponse])
def listar_proveedores(db: Session = Depends(get_db)):
    proveedores = db.query(Proveedor).order_by(Proveedor.id.asc()).all()
    return [_formatear_proveedor(p) for p in proveedores]

@router.post("/proveedores", response_model=ProveedorResponse, status_code=status.HTTP_201_CREATED)
def crear_proveedor(prov_in: ProveedorCreate, db: Session = Depends(get_db)):
    nombre_final = (prov_in.razon_social or prov_in.nombre or "").strip()
    if not nombre_final:
        raise HTTPException(status_code=400, detail="La razón social o nombre es obligatorio.")

    if db.query(exists().where(Proveedor.razon_social == nombre_final)).scalar():
        raise HTTPException(status_code=400, detail="Excepción A1: El proveedor ya existe.")
    if prov_in.nit and db.query(exists().where(Proveedor.nit == prov_in.nit)).scalar():
        raise HTTPException(status_code=400, detail="Excepción A1: El NIT ya está registrado.")
    
    nueva = Proveedor(
        razon_social=nombre_final,
        nit=prov_in.nit,
        correo=prov_in.correo,
        direccion=prov_in.direccion,
        telefono=prov_in.telefono,
        contacto=prov_in.contacto
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return _formatear_proveedor(nueva)

@router.put("/proveedores/{prov_id}", response_model=ProveedorResponse)
def actualizar_proveedor(prov_id: int, prov_in: ProveedorCreate, db: Session = Depends(get_db)):
    prov = db.query(Proveedor).filter(Proveedor.id == prov_id).first()
    if not prov:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado.")
    
    nombre_final = (prov_in.razon_social or prov_in.nombre or prov.razon_social).strip()
    prov.razon_social = nombre_final
    if prov_in.nit is not None:
        prov.nit = prov_in.nit
    if prov_in.correo is not None:
        prov.correo = prov_in.correo
    if prov_in.direccion is not None:
        prov.direccion = prov_in.direccion
    if prov_in.telefono is not None:
        prov.telefono = prov_in.telefono
    if prov_in.contacto is not None:
        prov.contacto = prov_in.contacto
    db.commit()
    db.refresh(prov)
    return _formatear_proveedor(prov)

@router.delete("/proveedores/{prov_id}")
def eliminar_proveedor(prov_id: int, db: Session = Depends(get_db)):
    prov = db.query(Proveedor).filter(Proveedor.id == prov_id).first()
    if not prov:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado.")
    if db.query(exists().where(Ropa.proveedor_id == prov_id)).scalar():
        raise HTTPException(status_code=400, detail="Restricción: Tiene prendas asociadas.")
    
    db.delete(prov)
    db.commit()
    return {"message": "Proveedor eliminado."}


# ─── Alias /api/proveedores y /api/v1/proveedores (para compatibilidad frontend Angular) ────────
router_proveedores_compat = APIRouter(
    prefix="/api/proveedores",
    tags=["CU06. Gestionar proveedores comerciales"]
)

router_proveedores_v1_compat = APIRouter(
    prefix="/api/v1/proveedores",
    tags=["CU06. Gestionar proveedores comerciales v1"]
)

@router_proveedores_compat.get("/")
@router_proveedores_compat.get("")
@router_proveedores_v1_compat.get("/")
@router_proveedores_v1_compat.get("")
def listar_proveedores_paginados(
    page: Optional[int] = None,
    page_size: int = 10,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Proveedor)
    if search:
        query = query.filter(Proveedor.razon_social.ilike(f"%{search}%"))
    
    total = query.count()
    if page is not None:
        items = query.order_by(Proveedor.id.asc()).offset((page - 1) * page_size).limit(page_size).all()
        results = [_formatear_proveedor(p).model_dump() for p in items]
        base = "/api/proveedores/"
        return {
            "count": total,
            "next": f"{base}?page={page+1}&page_size={page_size}" if page * page_size < total else None,
            "previous": f"{base}?page={page-1}&page_size={page_size}" if page > 1 else None,
            "results": results
        }
    else:
        items = query.order_by(Proveedor.id.asc()).all()
        return [_formatear_proveedor(p) for p in items]

@router_proveedores_compat.get("/{prov_id}", response_model=ProveedorResponse)
@router_proveedores_compat.get("/{prov_id}/", response_model=ProveedorResponse)
@router_proveedores_v1_compat.get("/{prov_id}", response_model=ProveedorResponse)
@router_proveedores_v1_compat.get("/{prov_id}/", response_model=ProveedorResponse)
def obtener_proveedor_compat(prov_id: int, db: Session = Depends(get_db)):
    prov = db.query(Proveedor).filter(Proveedor.id == prov_id).first()
    if not prov:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado.")
    return _formatear_proveedor(prov)

@router_proveedores_compat.post("/", response_model=ProveedorResponse, status_code=status.HTTP_201_CREATED)
@router_proveedores_compat.post("", response_model=ProveedorResponse, status_code=status.HTTP_201_CREATED)
@router_proveedores_v1_compat.post("/", response_model=ProveedorResponse, status_code=status.HTTP_201_CREATED)
@router_proveedores_v1_compat.post("", response_model=ProveedorResponse, status_code=status.HTTP_201_CREATED)
def crear_proveedor_compat(prov_in: ProveedorCreate, db: Session = Depends(get_db)):
    return crear_proveedor(prov_in=prov_in, db=db)

@router_proveedores_compat.put("/{prov_id}", response_model=ProveedorResponse)
@router_proveedores_compat.put("/{prov_id}/", response_model=ProveedorResponse)
@router_proveedores_v1_compat.put("/{prov_id}", response_model=ProveedorResponse)
@router_proveedores_v1_compat.put("/{prov_id}/", response_model=ProveedorResponse)
def actualizar_proveedor_compat(prov_id: int, prov_in: ProveedorCreate, db: Session = Depends(get_db)):
    return actualizar_proveedor(prov_id=prov_id, prov_in=prov_in, db=db)

@router_proveedores_compat.delete("/{prov_id}")
@router_proveedores_compat.delete("/{prov_id}/")
@router_proveedores_v1_compat.delete("/{prov_id}")
@router_proveedores_v1_compat.delete("/{prov_id}/")
def eliminar_proveedor_compat(prov_id: int, db: Session = Depends(get_db)):
    return eliminar_proveedor(prov_id=prov_id, db=db)


# ─── Alias sin versión /api/categorias (para compatibilidad frontend Angular) ────────
router_categorias_compat = APIRouter(
    prefix="/api/categorias",
    tags=["CU05. Parámetros de moda - Categorías"]
)

@router_categorias_compat.get("/")
@router_categorias_compat.get("")
def listar_categorias_compat(
    page: Optional[int] = None,
    page_size: int = 10,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Categoria)
    if search:
        query = query.filter(Categoria.nombre.ilike(f"%{search}%"))
    total = query.count()
    if page is not None:
        items = query.order_by(Categoria.id.asc()).offset((page - 1) * page_size).limit(page_size).all()
        base = "/api/categorias/"
        return {
            "count": total,
            "next": f"{base}?page={page+1}&page_size={page_size}" if page * page_size < total else None,
            "previous": f"{base}?page={page-1}&page_size={page_size}" if page > 1 else None,
            "results": [CategoriaResponse.model_validate(c).model_dump() for c in items]
        }
    return query.order_by(Categoria.id.asc()).all()

@router_categorias_compat.get("/{cat_id}", response_model=CategoriaResponse)
@router_categorias_compat.get("/{cat_id}/", response_model=CategoriaResponse)
def obtener_categoria_compat(cat_id: int, db: Session = Depends(get_db)):
    cat = db.query(Categoria).filter(Categoria.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada.")
    return cat

@router_categorias_compat.post("/", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED)
@router_categorias_compat.post("", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED)
def crear_categoria_compat(cat_in: CategoriaCreate, db: Session = Depends(get_db)):
    return crear_categoria(cat_in=cat_in, db=db)

@router_categorias_compat.put("/{cat_id}", response_model=CategoriaResponse)
@router_categorias_compat.put("/{cat_id}/", response_model=CategoriaResponse)
def actualizar_categoria_compat(cat_id: int, cat_in: CategoriaCreate, db: Session = Depends(get_db)):
    return actualizar_categoria(cat_id=cat_id, cat_in=cat_in, db=db)

@router_categorias_compat.delete("/{cat_id}")
@router_categorias_compat.delete("/{cat_id}/")
def eliminar_categoria_compat(cat_id: int, db: Session = Depends(get_db)):
    return eliminar_categoria(cat_id=cat_id, db=db)


# ─── Alias sin versión /api/temporadas ─────────────────────────────────────────
router_temporadas_compat = APIRouter(
    prefix="/api/temporadas",
    tags=["CU05. Parámetros de moda - Temporadas"]
)

@router_temporadas_compat.get("/")
@router_temporadas_compat.get("")
def listar_temporadas_compat(
    page: Optional[int] = None,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    query = db.query(Temporada)
    total = query.count()
    if page is not None:
        items = query.order_by(Temporada.id.asc()).offset((page - 1) * page_size).limit(page_size).all()
        base = "/api/temporadas/"
        return {
            "count": total,
            "next": f"{base}?page={page+1}&page_size={page_size}" if page * page_size < total else None,
            "previous": f"{base}?page={page-1}&page_size={page_size}" if page > 1 else None,
            "results": [TemporadaResponse.model_validate(t).model_dump() for t in items]
        }
    return query.order_by(Temporada.id.asc()).all()

@router_temporadas_compat.post("/", response_model=TemporadaResponse, status_code=status.HTTP_201_CREATED)
@router_temporadas_compat.post("", response_model=TemporadaResponse, status_code=status.HTTP_201_CREATED)
def crear_temporada_compat(temp_in: TemporadaCreate, db: Session = Depends(get_db)):
    return crear_temporada(temp_in=temp_in, db=db)

@router_temporadas_compat.put("/{temp_id}", response_model=TemporadaResponse)
@router_temporadas_compat.put("/{temp_id}/", response_model=TemporadaResponse)
def actualizar_temporada_compat(temp_id: int, temp_in: TemporadaCreate, db: Session = Depends(get_db)):
    return actualizar_temporada(temp_id=temp_id, temp_in=temp_in, db=db)

@router_temporadas_compat.delete("/{temp_id}")
@router_temporadas_compat.delete("/{temp_id}/")
def eliminar_temporada_compat(temp_id: int, db: Session = Depends(get_db)):
    return eliminar_temporada(temp_id=temp_id, db=db)


# ─── Alias sin versión /api/colores ────────────────────────────────────────────
router_colores_compat = APIRouter(
    prefix="/api/colores",
    tags=["CU05. Parámetros de moda - Colores"]
)

@router_colores_compat.get("/")
@router_colores_compat.get("")
def listar_colores_compat(
    page: Optional[int] = None,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    query = db.query(Color)
    total = query.count()
    if page is not None:
        items = query.order_by(Color.id.asc()).offset((page - 1) * page_size).limit(page_size).all()
        base = "/api/colores/"
        return {
            "count": total,
            "next": f"{base}?page={page+1}&page_size={page_size}" if page * page_size < total else None,
            "previous": f"{base}?page={page-1}&page_size={page_size}" if page > 1 else None,
            "results": [ColorResponse.model_validate(c).model_dump() for c in items]
        }
    return query.order_by(Color.id.asc()).all()

@router_colores_compat.post("/", response_model=ColorResponse, status_code=status.HTTP_201_CREATED)
@router_colores_compat.post("", response_model=ColorResponse, status_code=status.HTTP_201_CREATED)
def crear_color_compat(col_in: ColorCreate, db: Session = Depends(get_db)):
    return crear_color(col_in=col_in, db=db)

@router_colores_compat.put("/{col_id}", response_model=ColorResponse)
@router_colores_compat.put("/{col_id}/", response_model=ColorResponse)
def actualizar_color_compat(col_id: int, col_in: ColorCreate, db: Session = Depends(get_db)):
    return actualizar_color(col_id=col_id, col_in=col_in, db=db)

@router_colores_compat.delete("/{col_id}")
@router_colores_compat.delete("/{col_id}/")
def eliminar_color_compat(col_id: int, db: Session = Depends(get_db)):
    return eliminar_color(col_id=col_id, db=db)


