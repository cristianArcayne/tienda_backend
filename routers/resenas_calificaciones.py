"""
Router para CU19: Gestionar Reseñas y Calificaciones.
Registro de feedback del cliente, cálculo de satisfacción y promedios de calificación en el catálogo.
"""
from typing import List, Optional, Dict, Any, Union
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from database import get_db
from models.catalogo import Resena, Ropa
from models.seguridad_persona import Cliente
from schemas.innovacion import (
    ResenaCreateRequest,
    ResenaUpdateRequest,
    ResenaItemResponse,
    ResumenCalificacionesRopaResponse,
    DesgloseEstrellas
)

router = APIRouter(
    prefix="/api/v1/resenas",
    tags=["CU19. Gestionar reseñas y calificaciones"]
)

compat_router = APIRouter(
    prefix="/api/resenas",
    tags=["CU19. Gestionar reseñas y calificaciones"],
    include_in_schema=False
)

def obtener_nombre_cliente(cliente: Optional[Cliente], fallback_ci: any) -> str:
    if cliente and getattr(cliente, 'nombre', None):
        ap = getattr(cliente, 'apellido_pat', '') or ''
        return f"{cliente.nombre} {ap}".strip()
    return f"Cliente #{fallback_ci}"

def resolver_o_crear_cliente(db: Session, cliente_ci_raw: str, cliente_nombre_raw: Optional[str] = None) -> Cliente:
    import uuid
    ci_clean = str(cliente_ci_raw).strip() if cliente_ci_raw else "admin"
    
    # Si es admin o ID 1 o 1001, usar el cliente 'admin'
    if ci_clean in ["1", "1001", "admin"]:
        c = db.query(Cliente).filter(Cliente.ci == "admin").first()
        if c:
            if cliente_nombre_raw and cliente_nombre_raw != "Administrador del Sistema":
                c.nombre = cliente_nombre_raw
                c.apellido_pat = ""
                db.commit()
            return c

    # 1. Buscar si existe un Cliente con ese CI
    c = db.query(Cliente).filter(Cliente.ci == ci_clean).first()
    if c:
        if cliente_nombre_raw and cliente_nombre_raw not in ["Cliente", "Consumidor Final"]:
            partes = cliente_nombre_raw.split(" ", 1)
            c.nombre = partes[0]
            c.apellido_pat = partes[1] if len(partes) > 1 else ""
            db.commit()
        return c

    # 2. Si no existe, crear uno nuevo asegurando tipo_persona='CLIENTE'
    from models.seguridad_persona import Persona
    p_existente = db.query(Persona).filter(Persona.ci == ci_clean).first()
    nuevo_ci = str(uuid.uuid4().int)[:8] if p_existente else ci_clean
    
    nombre_display = cliente_nombre_raw or ci_clean.capitalize()
    partes = nombre_display.split(" ", 1)
    nom = partes[0]
    ape = partes[1] if len(partes) > 1 else ""
    email = f"cliente_{nuevo_ci}@fashionstore.bo"
    
    nuevo_cliente = Cliente(
        ci=nuevo_ci,
        nombre=nom,
        apellido_pat=ape,
        apellido_mat="",
        correo=email,
        preferencia_talla="M",
        fecha_registro=date.today()
    )
    db.add(nuevo_cliente)
    db.commit()
    db.refresh(nuevo_cliente)
    return nuevo_cliente


@router.post("", response_model=ResenaItemResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ResenaItemResponse, status_code=status.HTTP_201_CREATED)
@compat_router.post("", response_model=ResenaItemResponse, status_code=status.HTTP_201_CREATED)
@compat_router.post("/", response_model=ResenaItemResponse, status_code=status.HTTP_201_CREATED)
def crear_resena(resena_in: ResenaCreateRequest, db: Session = Depends(get_db)):
    rid = resena_in.ropa_id or resena_in.producto_id or 1
    estrellas = resena_in.puntuacion_estrellas or resena_in.calificacion or 5

    # 1. Validar existencia de ropa
    prenda = db.query(Ropa).filter(Ropa.id == rid).first()
    if not prenda:
        prenda = db.query(Ropa).first()
        rid = prenda.id if prenda else 1

    cliente = resolver_o_crear_cliente(db, str(resena_in.cliente_ci or "admin"), resena_in.cliente_nombre)

    # 2. Crear y persistir reseña en PostgreSQL
    nueva_resena = Resena(
        ropa_id=rid,
        cliente_id=cliente.ci,
        puntuacion_estrellas=estrellas,
        comentario=resena_in.comentario,
        fecha=date.today()
    )
    db.add(nueva_resena)
    db.commit()
    db.refresh(nueva_resena)

    cli_nom = obtener_nombre_cliente(cliente, cliente.ci)

    return ResenaItemResponse(
        id=nueva_resena.id,
        ropa_id=nueva_resena.ropa_id,
        cliente_ci=nueva_resena.cliente_id,
        cliente_nombre=cli_nom,
        puntuacion_estrellas=nueva_resena.puntuacion_estrellas,
        comentario=nueva_resena.comentario,
        fecha=nueva_resena.fecha
    )


@router.get("", response_model=Union[List[ResenaItemResponse], Dict[str, Any]])
@router.get("/", response_model=Union[List[ResenaItemResponse], Dict[str, Any]])
@compat_router.get("", response_model=Union[List[ResenaItemResponse], Dict[str, Any]])
@compat_router.get("/", response_model=Union[List[ResenaItemResponse], Dict[str, Any]])
def listar_todas_las_resenas(
    limit: int = Query(100, ge=1, le=500),
    ropa_id: Optional[int] = None,
    producto_id: Optional[int] = None,
    page_size: Optional[int] = None,
    page: Optional[int] = None,
    db: Session = Depends(get_db)
):
    target_ropa = ropa_id or producto_id
    query = db.query(Resena).options(joinedload(Resena.cliente))
    if target_ropa:
        query = query.filter(Resena.ropa_id == target_ropa)
    
    eff_limit = page_size or limit
    resenas = query.order_by(Resena.id.desc()).limit(eff_limit).all()

    resultado = []
    for r in resenas:
        cli_nom = obtener_nombre_cliente(r.cliente, r.cliente_id)
        resultado.append(
            ResenaItemResponse(
                id=r.id,
                ropa_id=r.ropa_id,
                producto=r.ropa_id,
                cliente_ci=r.cliente_id,
                cliente_nombre=cli_nom,
                usuario_username=cli_nom,
                usuario=1,
                puntuacion_estrellas=r.puntuacion_estrellas,
                calificacion=r.puntuacion_estrellas,
                comentario=r.comentario,
                fecha=r.fecha,
                fecha_creacion=r.fecha.isoformat() if hasattr(r.fecha, 'isoformat') else str(r.fecha)
            )
        )
    
    if page_size is not None or page is not None:
        return {
            "count": len(resultado),
            "results": resultado
        }
    return resultado


@router.get("/ropa/{ropa_id}", response_model=List[ResenaItemResponse])
@router.get("/ropa/{ropa_id}/", response_model=List[ResenaItemResponse])
@compat_router.get("/ropa/{ropa_id}", response_model=List[ResenaItemResponse])
@compat_router.get("/ropa/{ropa_id}/", response_model=List[ResenaItemResponse])
def listar_resenas_prenda(
    ropa_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    prenda = db.query(Ropa).filter(Ropa.id == ropa_id).first()
    if not prenda:
        raise HTTPException(status_code=404, detail="Prenda no encontrada.")

    resenas = db.query(Resena).options(joinedload(Resena.cliente))\
        .filter(Resena.ropa_id == ropa_id)\
        .order_by(Resena.id.desc())\
        .limit(limit).all()

    resultado = []
    for r in resenas:
        cli_nom = obtener_nombre_cliente(r.cliente, r.cliente_id)
        resultado.append(
            ResenaItemResponse(
                id=r.id,
                ropa_id=r.ropa_id,
                cliente_ci=r.cliente_id,
                cliente_nombre=cli_nom,
                puntuacion_estrellas=r.puntuacion_estrellas,
                comentario=r.comentario,
                fecha=r.fecha
            )
        )

    return resultado


@router.get("/ropa/{ropa_id}/resumen", response_model=ResumenCalificacionesRopaResponse)
@router.get("/ropa/{ropa_id}/resumen/", response_model=ResumenCalificacionesRopaResponse)
@compat_router.get("/ropa/{ropa_id}/resumen", response_model=ResumenCalificacionesRopaResponse)
@compat_router.get("/ropa/{ropa_id}/resumen/", response_model=ResumenCalificacionesRopaResponse)
def obtener_resumen_calificaciones(ropa_id: int, db: Session = Depends(get_db)):
    prenda = db.query(Ropa).filter(Ropa.id == ropa_id).first()
    if not prenda:
        raise HTTPException(status_code=404, detail="Prenda no encontrada.")

    resenas = db.query(Resena).options(joinedload(Resena.cliente))\
        .filter(Resena.ropa_id == ropa_id).all()

    total = len(resenas)
    if total == 0:
        return ResumenCalificacionesRopaResponse(
            ropa_id=prenda.id,
            ropa_nombre=prenda.nombre,
            promedio_calificacion=5.0,
            total_resenas=0,
            porcentaje_recomendacion=100.0,
            desglose_estrellas=DesgloseEstrellas(),
            ultimas_resenas=[]
        )

    suma = sum([r.puntuacion_estrellas for r in resenas])
    promedio = round(suma / total, 1)

    # Conteo por estrellas
    e5 = sum(1 for r in resenas if r.puntuacion_estrellas == 5)
    e4 = sum(1 for r in resenas if r.puntuacion_estrellas == 4)
    e3 = sum(1 for r in resenas if r.puntuacion_estrellas == 3)
    e2 = sum(1 for r in resenas if r.puntuacion_estrellas == 2)
    e1 = sum(1 for r in resenas if r.puntuacion_estrellas == 1)

    positivas = e5 + e4
    pct_rec = round((positivas / total) * 100, 1)

    # Ordenar las reseñas de la más reciente a la más antigua
    resenas_ordenadas = sorted(resenas, key=lambda x: x.id, reverse=True)

    ultimas = [
        ResenaItemResponse(
            id=r.id,
            ropa_id=r.ropa_id,
            cliente_ci=r.cliente_id,
            cliente_nombre=obtener_nombre_cliente(r.cliente, r.cliente_id),
            puntuacion_estrellas=r.puntuacion_estrellas,
            comentario=r.comentario,
            fecha=r.fecha
        )
        for r in resenas_ordenadas[:20]
    ]

    return ResumenCalificacionesRopaResponse(
        ropa_id=prenda.id,
        ropa_nombre=prenda.nombre,
        promedio_calificacion=promedio,
        total_resenas=total,
        porcentaje_recomendacion=pct_rec,
        desglose_estrellas=DesgloseEstrellas(
            estrella_5=e5,
            estrella_4=e4,
            estrella_3=e3,
            estrella_2=e2,
            estrella_1=e1
        ),
        ultimas_resenas=ultimas
    )


@router.patch("/{resena_id}", response_model=ResenaItemResponse)
@router.patch("/{resena_id}/", response_model=ResenaItemResponse)
@router.put("/{resena_id}", response_model=ResenaItemResponse)
@router.put("/{resena_id}/", response_model=ResenaItemResponse)
@compat_router.patch("/{resena_id}", response_model=ResenaItemResponse)
@compat_router.patch("/{resena_id}/", response_model=ResenaItemResponse)
@compat_router.put("/{resena_id}", response_model=ResenaItemResponse)
@compat_router.put("/{resena_id}/", response_model=ResenaItemResponse)
def actualizar_resena(
    resena_id: int,
    req: ResenaUpdateRequest,
    db: Session = Depends(get_db)
):
    resena = db.query(Resena).options(joinedload(Resena.cliente)).filter(Resena.id == resena_id).first()
    if not resena:
        raise HTTPException(status_code=404, detail="Reseña no encontrada.")

    if req.puntuacion_estrellas is not None:
        resena.puntuacion_estrellas = req.puntuacion_estrellas
    elif req.calificacion is not None:
        resena.puntuacion_estrellas = req.calificacion

    if req.comentario is not None:
        resena.comentario = req.comentario

    db.commit()
    db.refresh(resena)

    cli_nom = obtener_nombre_cliente(resena.cliente, resena.cliente_id)
    return ResenaItemResponse(
        id=resena.id,
        ropa_id=resena.ropa_id,
        producto=resena.ropa_id,
        cliente_ci=resena.cliente_id,
        cliente_nombre=cli_nom,
        usuario_username=cli_nom,
        usuario=1,
        puntuacion_estrellas=resena.puntuacion_estrellas,
        calificacion=resena.puntuacion_estrellas,
        comentario=resena.comentario,
        fecha=resena.fecha,
        fecha_creacion=resena.fecha.isoformat() if hasattr(resena.fecha, 'isoformat') else str(resena.fecha)
    )


@router.delete("/{resena_id}", status_code=status.HTTP_200_OK)
@router.delete("/{resena_id}/", status_code=status.HTTP_200_OK)
@compat_router.delete("/{resena_id}", status_code=status.HTTP_200_OK)
@compat_router.delete("/{resena_id}/", status_code=status.HTTP_200_OK)
def eliminar_resena(resena_id: int, db: Session = Depends(get_db)):
    resena = db.query(Resena).filter(Resena.id == resena_id).first()
    if not resena:
        raise HTTPException(status_code=404, detail="Reseña no encontrada.")

    db.delete(resena)
    db.commit()
    return {"mensaje": f"Reseña ID {resena_id} eliminada exitosamente.", "id": resena_id}
