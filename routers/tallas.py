from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import exists

from database import get_db
from models.catalogo import Talla, VariantePrenda
from schemas.talla import TallaCreate, TallaResponse

router = APIRouter(
    prefix="/api/v1/tallas",
    tags=["CU05. Gestionar parámetros de moda"]
)


@router.get(
    "/",
    response_model=List[TallaResponse],
    summary="Listar todas las tallas",
    description="Recupera el listado completo de tallas registradas para prendas textiles y calzado."
)
def listar_tallas(db: Session = Depends(get_db)):
    """
    Flujo básico: Consulta todas las tallas ordenadas por identificador.
    """
    tallas = db.query(Talla).order_by(Talla.id.asc()).all()
    return tallas


@router.post(
    "/",
    response_model=TallaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nueva talla",
    description="Inserta una nueva talla validando previamente que no existan duplicados (Excepción A1)."
)
def crear_talla(talla_in: TallaCreate, db: Session = Depends(get_db)):
    """
    Flujo del proceso - CU05:
    1. Recibe la medida y datos de la talla.
    2. Valida mediante .filter(medida=...).first() que no exista colisión.
    3. Excepción A1: Si existe, rechaza con HTTP 400.
    4. Guarda la nueva talla en la base de datos.
    """
    # Validación de no duplicados (Excepción A1)
    talla_existente = db.query(
        exists().where(Talla.medida == talla_in.medida)
    ).scalar()

    if talla_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Excepción A1: La talla '{talla_in.medida}' ya existe en el catálogo de parámetros."
        )

    # Inserción en base de datos
    nueva_talla = Talla(
        medida=talla_in.medida,
        tipo=talla_in.tipo,
        guia_medida=talla_in.guia_medida
    )
    db.add(nueva_talla)
    db.commit()
    db.refresh(nueva_talla)

    return nueva_talla



@router.put("/{talla_id}", response_model=TallaResponse)
def actualizar_talla(talla_id: int, talla_in: TallaCreate, db: Session = Depends(get_db)):
    talla = db.query(Talla).filter(Talla.id == talla_id).first()
    if not talla: raise HTTPException(status_code=404, detail="Talla no encontrada.")
    talla.medida = talla_in.medida
    talla.tipo = talla_in.tipo
    talla.guia_medida = talla_in.guia_medida
    db.commit()
    db.refresh(talla)
    return talla

@router.delete(
    "/{talla_id}",
    status_code=status.HTTP_200_OK,
    summary="Eliminar una talla con validación de dependencias",
    description="Elimina la talla solo si no está vinculada a ninguna VariantePrenda en el catálogo."
)
def eliminar_talla(talla_id: int, db: Session = Depends(get_db)):
    """
    Flujo de eliminación con control de integridad:
    1. Verifica la existencia de la talla solicitada.
    2. Comprueba mediante .filter(talla_id=...).first() si tiene dependencias en VariantePrenda.
    3. Si tiene dependencias: aborta con HTTP 400 (Restricción de Integridad Relacional).
    4. Si está libre: procede con el borrado físico.
    """
    # 1. Verificar si la talla existe
    talla = db.query(Talla).filter(Talla.id == talla_id).first()
    if not talla:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Talla con ID {talla_id} no encontrada."
        )

    # 2. Comprobar si está enlazada a alguna VariantePrenda (Control de Dependencias)
    tiene_dependencias = db.query(
        exists().where(VariantePrenda.talla_id == talla_id)
    ).scalar()

    if tiene_dependencias:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Excepción A1 (Restricción de Integridad Relacional): No es posible eliminar la "
                f"talla '{talla.medida}' (ID {talla_id}) porque se encuentra actualmente enlazada "
                f"a variantes de prendas activas en el catálogo."
            )
        )

    # 3. Borrado seguro
    db.delete(talla)
    db.commit()

    return {
        "status": "success",
        "message": f"La talla '{talla.medida}' ha sido eliminada exitosamente del sistema."
    }


# ─── Alias sin versión /api/tallas (para compatibilidad frontend Angular) ────────
from typing import Optional

router_compat = APIRouter(
    prefix="/api/tallas",
    tags=["CU05. Gestionar parámetros de moda"]
)

@router_compat.get("/")
def listar_tallas_compat(
    page: Optional[int] = None,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    query = db.query(Talla)
    total = query.count()
    if page is not None:
        items = query.order_by(Talla.id.asc()).offset((page - 1) * page_size).limit(page_size).all()
        base = "/api/tallas/"
        return {
            "count": total,
            "next": f"{base}?page={page+1}&page_size={page_size}" if page * page_size < total else None,
            "previous": f"{base}?page={page-1}&page_size={page_size}" if page > 1 else None,
            "results": [TallaResponse.model_validate(t).model_dump() for t in items]
        }
    return query.order_by(Talla.id.asc()).all()

@router_compat.post("/", response_model=TallaResponse, status_code=status.HTTP_201_CREATED)
def crear_talla_compat(talla_in: TallaCreate, db: Session = Depends(get_db)):
    return crear_talla(talla_in=talla_in, db=db)

@router_compat.put("/{talla_id}", response_model=TallaResponse)
def actualizar_talla_compat(talla_id: int, talla_in: TallaCreate, db: Session = Depends(get_db)):
    return actualizar_talla(talla_id=talla_id, talla_in=talla_in, db=db)

@router_compat.delete("/{talla_id}")
def eliminar_talla_compat(talla_id: int, db: Session = Depends(get_db)):
    return eliminar_talla(talla_id=talla_id, db=db)

