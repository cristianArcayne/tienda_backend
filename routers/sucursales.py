"""
Router para CU06: Gestión de Sucursales de la Cadena, Inventario y Traspasos.
Alineado fielmente con SUCURSAL, INVENTARIO_SUCURSAL y TRASPASO del Diagrama UML.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exists, and_

from database import get_db
from models.sucursal import Sucursal, InventarioSucursal, Traspaso, DetalleTraspaso
from models.catalogo import VariantePrenda
from models.venta import Venta
from models.reserva import Reserva
from schemas.sucursal import (
    SucursalCreate,
    SucursalResponse,
    TraspasoCreate,
    TraspasoResponse,
    DetalleTraspasoResponse
)
from routers.bitacora import registrar_bitacora

router = APIRouter(
    prefix="/api/v1/sucursales",
    tags=["CU06. Gestionar sucursales de la cadena"]
)


@router.get(
    "/",
    response_model=List[SucursalResponse],
    summary="Listar todas las sucursales de la cadena",
    description="Recupera todas las tiendas físicas registradas en las diferentes ciudades."
)
def listar_sucursales(db: Session = Depends(get_db)):
    return db.query(Sucursal).order_by(Sucursal.id.asc()).all()


@router.get(
    "/{sucursal_id}",
    response_model=SucursalResponse,
    summary="Consultar detalle de una sucursal",
    description="Obtiene los datos de una tienda física por su ID."
)
def obtener_sucursal(sucursal_id: int, db: Session = Depends(get_db)):
    sucursal = db.query(Sucursal).filter(Sucursal.id == sucursal_id).first()
    if not sucursal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sucursal con ID {sucursal_id} no encontrada."
        )
    return sucursal


@router.post(
    "/",
    response_model=SucursalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nueva sucursal",
    description="Registra una nueva tienda física en el sistema validando no duplicidad."
)
def crear_sucursal(sucursal_in: SucursalCreate, request: Request, db: Session = Depends(get_db)):
    existe_tienda = db.query(
        exists().where(
            and_(
                Sucursal.nombre.ilike(sucursal_in.nombre),
                Sucursal.ciudad.ilike(sucursal_in.ciudad)
            )
        )
    ).scalar()

    if existe_tienda:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una sucursal con el nombre '{sucursal_in.nombre}' en '{sucursal_in.ciudad}'."
        )

    nueva_sucursal = Sucursal(
        nombre=sucursal_in.nombre,
        ciudad=sucursal_in.ciudad,
        direccion=sucursal_in.direccion,
        telefono=sucursal_in.telefono
    )
    db.add(nueva_sucursal)
    db.flush()

    # Inicializar inventario en 0 para todas las variantes existentes
    variantes = db.query(VariantePrenda).all()
    for var in variantes:
        db.add(InventarioSucursal(
            sucursal_id=nueva_sucursal.id,
            variante_id=var.id,
            stock_fisico=0,
            stock_reservado=0
        ))

    db.commit()
    db.refresh(nueva_sucursal)
    
    registrar_bitacora(db, "INSERT", "sucursales", str(nueva_sucursal.id), f"Sucursal creada: {nueva_sucursal.nombre} ({nueva_sucursal.ciudad})", request=request)
    
    return nueva_sucursal


@router.put("/{sucursal_id}", response_model=SucursalResponse)
def actualizar_sucursal(sucursal_id: int, sucursal_in: SucursalCreate, request: Request, db: Session = Depends(get_db)):
    sucursal = db.query(Sucursal).filter(Sucursal.id == sucursal_id).first()
    if not sucursal:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    sucursal.nombre = sucursal_in.nombre
    sucursal.ciudad = sucursal_in.ciudad
    sucursal.direccion = sucursal_in.direccion
    sucursal.telefono = sucursal_in.telefono
    db.commit()
    db.refresh(sucursal)
    
    registrar_bitacora(db, "UPDATE", "sucursales", str(sucursal.id), f"Sucursal actualizada: {sucursal.nombre} ({sucursal.ciudad})", request=request)
    
    return sucursal

@router.delete("/{sucursal_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_sucursal(sucursal_id: int, request: Request, db: Session = Depends(get_db)):
    sucursal = db.query(Sucursal).filter(Sucursal.id == sucursal_id).first()
    if not sucursal:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    
    # Verificar si tiene ventas o reservas
    if db.query(exists().where(Venta.sucursal_id == sucursal_id)).scalar():
        raise HTTPException(status_code=400, detail="No se puede eliminar la sucursal porque tiene ventas registradas.")
    
    if db.query(exists().where(Reserva.sucursal_id == sucursal_id)).scalar():
        raise HTTPException(status_code=400, detail="No se puede eliminar la sucursal porque tiene reservas asociadas.")

    if db.query(exists().where(
        (Traspaso.sucursal_origen_id == sucursal_id) | (Traspaso.sucursal_destino_id == sucursal_id)
    )).scalar():
        raise HTTPException(status_code=400, detail="No se puede eliminar la sucursal porque tiene traspasos asociados.")

    # Eliminar inventario físico asociado
    db.query(InventarioSucursal).filter(InventarioSucursal.sucursal_id == sucursal_id).delete()
    
    nombre_suc = sucursal.nombre
    db.delete(sucursal)
    db.commit()
    
    registrar_bitacora(db, "DELETE", "sucursales", str(sucursal_id), f"Sucursal eliminada: {nombre_suc}", request=request)
    return None

@router.get("/{sucursal_id}/inventario")
def ver_inventario_sucursal(sucursal_id: int, db: Session = Depends(get_db)):
    inventario = db.query(InventarioSucursal).filter(InventarioSucursal.sucursal_id == sucursal_id).all()
    res = []
    for inv in inventario:
        res.append({
            "variante_id": inv.variante_id,
            "stock_fisico": inv.stock_fisico,
            "stock_reservado": inv.stock_reservado,
            "stock_disponible": inv.stock_disponible
        })
    return res

@router.post(
    "/traspasos",
    response_model=TraspasoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar traspaso de stock entre tiendas físicas",
    description="Transfiere prendas físicas desde una sucursal origen hacia una sucursal destino."
)
def registrar_traspaso(traspaso_in: TraspasoCreate, db: Session = Depends(get_db)):
    if traspaso_in.sucursal_origen_id == traspaso_in.sucursal_destino_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La sucursal de origen no puede ser igual a la sucursal de destino."
        )

    nuevo_traspaso = Traspaso(
        empleado_id=traspaso_in.empleado_id,
        sucursal_origen_id=traspaso_in.sucursal_origen_id,
        sucursal_destino_id=traspaso_in.sucursal_destino_id,
        estado="RECIBIDO"
    )
    db.add(nuevo_traspaso)
    db.flush()

    detalles_resp = []
    for d in traspaso_in.detalles:
        # Descargo en origen
        inv_orig = db.query(InventarioSucursal).filter(
            InventarioSucursal.sucursal_id == traspaso_in.sucursal_origen_id,
            InventarioSucursal.variante_id == d.variante_id
        ).first()

        if not inv_orig or inv_orig.stock_fisico < d.cantidad:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente en sucursal origen para la variante {d.variante_id}."
            )

        inv_orig.stock_fisico -= d.cantidad

        # Incremento en destino
        inv_dest = db.query(InventarioSucursal).filter(
            InventarioSucursal.sucursal_id == traspaso_in.sucursal_destino_id,
            InventarioSucursal.variante_id == d.variante_id
        ).first()

        if not inv_dest:
            inv_dest = InventarioSucursal(
                sucursal_id=traspaso_in.sucursal_destino_id,
                variante_id=d.variante_id,
                stock_fisico=d.cantidad,
                stock_reservado=0
            )
            db.add(inv_dest)
        else:
            inv_dest.stock_fisico += d.cantidad

        det = DetalleTraspaso(traspaso_id=nuevo_traspaso.id, variante_id=d.variante_id, cantidad=d.cantidad)
        db.add(det)
        db.flush()
        detalles_resp.append(DetalleTraspasoResponse(id=det.id, variante_id=det.variante_id, cantidad=det.cantidad))

    db.commit()
    db.refresh(nuevo_traspaso)

    return TraspasoResponse(
        id=nuevo_traspaso.id,
        fecha=nuevo_traspaso.fecha,
        estado=nuevo_traspaso.estado,
        empleado_id=nuevo_traspaso.empleado_id,
        sucursal_origen_id=nuevo_traspaso.sucursal_origen_id,
        sucursal_destino_id=nuevo_traspaso.sucursal_destino_id,
        detalles=detalles_resp
    )


# ─── Alias sin versión /api/sucursales ───────────────────────────────────────
router_compat = APIRouter(
    prefix="/api/sucursales",
    tags=["CU06. Gestionar sucursales de la cadena"]
)

@router_compat.get("/", response_model=List[SucursalResponse])
@router_compat.get("", response_model=List[SucursalResponse])
def listar_sucursales_compat(db: Session = Depends(get_db)):
    return listar_sucursales(db=db)

@router_compat.get("/{sucursal_id}", response_model=SucursalResponse)
@router_compat.get("/{sucursal_id}/", response_model=SucursalResponse)
def obtener_sucursal_compat(sucursal_id: int, db: Session = Depends(get_db)):
    return obtener_sucursal(sucursal_id=sucursal_id, db=db)

@router_compat.post("/", response_model=SucursalResponse, status_code=status.HTTP_201_CREATED)
@router_compat.post("", response_model=SucursalResponse, status_code=status.HTTP_201_CREATED)
def crear_sucursal_compat(sucursal_in: SucursalCreate, request: Request, db: Session = Depends(get_db)):
    return crear_sucursal(sucursal_in=sucursal_in, request=request, db=db)

@router_compat.put("/{sucursal_id}", response_model=SucursalResponse)
@router_compat.put("/{sucursal_id}/", response_model=SucursalResponse)
def actualizar_sucursal_compat(sucursal_id: int, sucursal_in: SucursalCreate, request: Request, db: Session = Depends(get_db)):
    return actualizar_sucursal(sucursal_id=sucursal_id, sucursal_in=sucursal_in, request=request, db=db)

@router_compat.delete("/{sucursal_id}", status_code=status.HTTP_204_NO_CONTENT)
@router_compat.delete("/{sucursal_id}/", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_sucursal_compat(sucursal_id: int, request: Request, db: Session = Depends(get_db)):
    return eliminar_sucursal(sucursal_id=sucursal_id, request=request, db=db)

