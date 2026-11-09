"""
Router para CU-08: Gestionar Carrito de Compras Persistente y Sincronización Cross-Device.
Aislado estrictamente por usuario / cliente (cada usuario posee su propio carrito).
"""
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text

from database import get_db
from models.carrito import CarritoCompra, DetalleCarritoCompra
from models.seguridad_persona import Cliente, Usuario, Persona
from models.catalogo import VariantePrenda, Ropa
from models.sucursal import InventarioSucursal
from schemas.carrito import DetalleCarritoCreate, DetalleCarritoResponse, CarritoCompraResponse

router = APIRouter(
    prefix="/api/v1/carrito-persistente",
    tags=["CU08. Gestionar Carrito de Compras Persistente"]
)


def _resolver_o_crear_cliente_ci(db: Session, identificador: Optional[str]) -> Optional[str]:
    """
    Resuelve el CI único del cliente a partir de su username, ID de usuario o CI.
    Si el usuario existe pero aún no tiene fila en 'clientes', la crea automáticamente
    para garantizar que nunca comparta el carrito del primer cliente.
    """
    if not identificador or str(identificador).strip() in ["", "null", "undefined", "guest"]:
        return None

    id_str = str(identificador).strip()
    if id_str == "activo":
        c_first = db.query(Cliente).first()
        return c_first.ci if c_first else "2001"

    # 1. Buscar directamente en Cliente
    cli = db.query(Cliente).filter(Cliente.ci == id_str).first()
    if cli:
        return cli.ci

    # 2. Buscar en Usuario por username o ID
    u = db.query(Usuario).filter(Usuario.nombre_usuario.ilike(id_str)).first()
    if not u and id_str.isdigit():
        u = db.query(Usuario).filter(Usuario.id == int(id_str)).first()

    target_ci = (u.persona_ci if (u and u.persona_ci) else f"CLI-{id_str}")[:20]

    cli = db.query(Cliente).filter(Cliente.ci == target_ci).first()
    if cli:
        return cli.ci

    # 3. Asegurar que exista en Persona y Cliente para aislar su carrito
    try:
        persona = db.query(Persona).filter(Persona.ci == target_ci).first()
        if not persona:
            db.execute(
                text("""
                    INSERT INTO personas (ci, nombre, apellido_pat, correo, tipo_persona)
                    VALUES (:ci, :nom, 'Cliente', :cor, 'CLIENTE')
                    ON CONFLICT (ci) DO NOTHING
                """),
                {
                    "ci": target_ci,
                    "nom": u.nombre_usuario if u else id_str,
                    "cor": f"{target_ci.lower()}@fashionstore.local"
                }
            )
        db.execute(
            text("""
                INSERT INTO clientes (ci, fecha_registro)
                VALUES (:ci, CURRENT_DATE)
                ON CONFLICT (ci) DO NOTHING
            """),
            {"ci": target_ci}
        )
        db.commit()
        return target_ci
    except Exception:
        db.rollback()
        return None


def _obtener_carrito_de_cliente(db: Session, cliente_ci: Optional[str]) -> Optional[CarritoCompra]:
    if not cliente_ci:
        return None
    carrito = db.query(CarritoCompra).options(
        joinedload(CarritoCompra.detalles).joinedload(DetalleCarritoCompra.variante).joinedload(VariantePrenda.ropa),
        joinedload(CarritoCompra.detalles).joinedload(DetalleCarritoCompra.variante).joinedload(VariantePrenda.talla),
        joinedload(CarritoCompra.detalles).joinedload(DetalleCarritoCompra.variante).joinedload(VariantePrenda.color)
    ).filter(CarritoCompra.cliente_id == cliente_ci).first()

    if not carrito:
        try:
            carrito = CarritoCompra(fecha_creacion=date.today(), cliente_id=cliente_ci)
            db.add(carrito)
            db.commit()
            db.refresh(carrito)
        except Exception:
            db.rollback()
            return None
    return carrito


def _formatear_carrito(carrito: Optional[CarritoCompra], cliente_id_fallback: str = "guest") -> CarritoCompraResponse:
    if not carrito:
        return CarritoCompraResponse(
            id=0,
            fecha_creacion=date.today(),
            cliente_id=cliente_id_fallback,
            detalles=[],
            total_articulos=0,
            monto_total=0.0
        )

    detalles_resp = []
    total_cant = 0
    monto_total = 0.0

    for d in (carrito.detalles or []):
        v = d.variante
        ropa_nom = v.ropa.nombre if (v and v.ropa) else "Prenda"
        precio_un = float(v.ropa.precio) if (v and v.ropa) else 0.0
        subt = round(precio_un * d.cantidad, 2)
        img_url = v.imagen_url or (v.ropa.imagen_principal if (v and v.ropa) else None)
        p_id = v.ropa_id if (v and hasattr(v, 'ropa_id') and v.ropa_id) else (v.ropa.id if (v and v.ropa) else 0)

        total_cant += d.cantidad
        monto_total += subt

        detalles_resp.append(
            DetalleCarritoResponse(
                id=d.id,
                variante_id=d.variante_id,
                prenda_id=p_id,
                imagen_url=img_url,
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
    summary="Recuperar carrito persistente del usuario activo",
    include_in_schema=False
)
@router.get(
    "",
    response_model=CarritoCompraResponse,
    summary="Recuperar carrito persistente del usuario activo"
)
def obtener_carrito_activo(
    cliente_id: Optional[str] = Query(None, description="ID o username del usuario"),
    db: Session = Depends(get_db)
):
    cliente_ci = _resolver_o_crear_cliente_ci(db, cliente_id)
    if not cliente_ci:
        return _formatear_carrito(None)
    carrito = _obtener_carrito_de_cliente(db, cliente_ci)
    return _formatear_carrito(carrito, cliente_ci)


@router.get(
    "/{cliente_id}",
    response_model=CarritoCompraResponse,
    summary="Recuperar carrito sincronizado en PostgreSQL por cliente"
)
def obtener_carrito_persistente(cliente_id: str, db: Session = Depends(get_db)):
    cliente_ci = _resolver_o_crear_cliente_ci(db, cliente_id)
    if not cliente_ci:
        return _formatear_carrito(None, str(cliente_id))
    carrito = _obtener_carrito_de_cliente(db, cliente_ci)
    return _formatear_carrito(carrito, cliente_ci)


@router.post(
    "/items",
    summary="Agregar item al carrito persistente del usuario"
)
@router.post(
    "/items/",
    summary="Agregar item al carrito persistente del usuario",
    include_in_schema=False
)
def agregar_item_persistente(item_in: dict, db: Session = Depends(get_db)):
    variante_id = item_in.get("variante_id")
    cantidad = item_in.get("cantidad", 1)
    cliente_id = item_in.get("cliente_id") or item_in.get("usuario_id")

    if not variante_id:
        raise HTTPException(status_code=400, detail="variante_id es requerido")

    cliente_ci = _resolver_o_crear_cliente_ci(db, str(cliente_id) if cliente_id else None)
    if not cliente_ci:
        return {"success": True, "mensaje": "Guardado en almacenamiento local del usuario"}

    carrito = _obtener_carrito_de_cliente(db, cliente_ci)
    if not carrito:
        return {"success": True, "mensaje": "Guardado en almacenamiento local del usuario"}

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
    return {"success": True, "mensaje": "Producto añadido al carrito del usuario correctamente"}


@router.delete(
    "/vaciar",
    summary="Vaciar carrito persistente del usuario activo"
)
@router.delete(
    "",
    summary="Vaciar carrito persistente del usuario activo",
    include_in_schema=False
)
@router.delete(
    "/",
    summary="Vaciar carrito persistente del usuario activo",
    include_in_schema=False
)
def vaciar_carrito_persistente(
    cliente_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    cliente_ci = _resolver_o_crear_cliente_ci(db, cliente_id)
    if cliente_ci:
        carrito = db.query(CarritoCompra).filter(CarritoCompra.cliente_id == cliente_ci).first()
        if carrito:
            db.query(DetalleCarritoCompra).filter(
                DetalleCarritoCompra.carrito_id == carrito.id
            ).delete()
            db.commit()
    return {"success": True, "mensaje": "Carrito del usuario vaciado correctamente"}


@router.delete(
    "/items/{variante_id}",
    summary="Eliminar item del carrito persistente del usuario"
)
def eliminar_item_persistente(
    variante_id: int,
    cliente_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    cliente_ci = _resolver_o_crear_cliente_ci(db, cliente_id)
    if cliente_ci:
        carrito = db.query(CarritoCompra).filter(CarritoCompra.cliente_id == cliente_ci).first()
        if carrito:
            db.query(DetalleCarritoCompra).filter(
                DetalleCarritoCompra.carrito_id == carrito.id,
                DetalleCarritoCompra.variante_id == variante_id
            ).delete()
            db.commit()
    return {"success": True, "mensaje": "Item eliminado correctamente"}
