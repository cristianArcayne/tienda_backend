"""
Router para CU13: Gestionar Carrito de Compras Persistente y Sincronización Omnicanal.
Alineado fielmente con CARRITO_COMPRA, DETALLE_CARRITO_COMPRA y CLIENTE del Diagrama UML.
"""
import io
from datetime import datetime
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from database import get_db
from models.carrito import CarritoCompra, DetalleCarritoCompra
from models.seguridad_persona import Cliente, Persona
from models.catalogo import VariantePrenda, Ropa, Talla, Color, Promocion, PromocionRopa
from models.sucursal import InventarioSucursal, Sucursal
from schemas.carrito import DetalleCarritoCreate, DetalleCarritoResponse, CarritoCompraResponse

router = APIRouter(
    prefix="/api/v1/carrito",
    tags=["CU13. Gestionar Carrito de Compras Persistente"]
)

router_compat = APIRouter(
    prefix="/api/carrito",
    tags=["CU13. Carrito Persistente (Compatibilidad Frontend)"]
)


def _calcular_precio_unitario_promo(ropa: Optional[Ropa], precio_ajustado: Optional[float] = None) -> tuple[float, float, float]:
    from datetime import date
    hoy = date.today()
    precio_base = float(precio_ajustado or (ropa.precio if (ropa and ropa.precio is not None) else 0.0))
    mejor_descuento = 0.0
    if ropa and getattr(ropa, 'promociones_asociadas', None):
        for pr in ropa.promociones_asociadas:
            if pr.estado and pr.estado.upper() == "ACTIVA" and pr.promocion:
                p = pr.promocion
                if getattr(p, "activo", True):
                    f_ini = p.fecha_inicio.date() if hasattr(p.fecha_inicio, "date") else p.fecha_inicio
                    f_fin = p.fecha_fin.date() if hasattr(p.fecha_fin, "date") else p.fecha_fin
                    if f_ini and f_fin and (f_ini <= hoy <= f_fin):
                        mejor_descuento = max(mejor_descuento, float(p.porcentaje_descuento))
    precio_promo = round(precio_base * (1.0 - (mejor_descuento / 100.0)), 2) if mejor_descuento > 0 else precio_base
    return precio_base, mejor_descuento, precio_promo


def _obtener_o_crear_cliente(db: Session, cliente_id_str: str) -> Cliente:
    cliente = db.query(Cliente).filter(Cliente.ci == cliente_id_str).first()
    if not cliente:
        persona = db.query(Persona).filter(Persona.ci == cliente_id_str).first()
        if persona:
            cliente = Cliente(
                ci=persona.ci,
                nombre=persona.nombre,
                apellido_pat=persona.apellido_pat,
                apellido_mat=persona.apellido_mat,
                correo=persona.correo,
                telefono=persona.telefono,
                tipo_persona="CLIENTE"
            )
            db.add(cliente)
            db.flush()
        else:
            primer_cli = db.query(Cliente).first()
            if primer_cli and cliente_id_str in ["default", "guest", "null", "undefined", "1029384"]:
                return primer_cli
            cliente = Cliente(
                ci=cliente_id_str,
                nombre="Cliente",
                apellido_pat="Web",
                correo=f"cliente_{cliente_id_str}@fashionstore.com",
                telefono="+591 70000000",
                tipo_persona="CLIENTE"
            )
            db.add(cliente)
            db.flush()
    return cliente


def _obtener_o_crear_carrito(db: Session, cliente_ci: str) -> CarritoCompra:
    carrito = db.query(CarritoCompra).options(
        joinedload(CarritoCompra.detalles).joinedload(DetalleCarritoCompra.variante).joinedload(VariantePrenda.ropa).joinedload(Ropa.promociones_asociadas).joinedload(PromocionRopa.promocion),
        joinedload(CarritoCompra.detalles).joinedload(DetalleCarritoCompra.variante).joinedload(VariantePrenda.talla),
        joinedload(CarritoCompra.detalles).joinedload(DetalleCarritoCompra.variante).joinedload(VariantePrenda.color),
        joinedload(CarritoCompra.cliente)
    ).filter(CarritoCompra.cliente_id == cliente_ci).first()

    if not carrito:
        carrito = CarritoCompra(
            cliente_id=cliente_ci,
            fecha_creacion=datetime.utcnow()
        )
        db.add(carrito)
        db.commit()
        db.refresh(carrito)

    return carrito


def _formatear_carrito(carrito: CarritoCompra) -> CarritoCompraResponse:
    detalles_resp = []
    total_cant = 0
    monto_total = 0.0

    for d in (carrito.detalles or []):
        v = d.variante
        ropa_nom = v.ropa.nombre if (v and v.ropa) else "Prenda"
        p_base, p_desc, p_promo = _calcular_precio_unitario_promo(v.ropa if v else None, float(v.precio_ajustado) if (v and v.precio_ajustado) else None)
        precio_un = p_promo
        subt = round(precio_un * d.cantidad, 2)

        total_cant += d.cantidad
        monto_total += subt

        detalles_resp.append(
            DetalleCarritoResponse(
                id=d.id,
                variante_id=d.variante_id,
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


def _formatear_carrito_frontend(carrito: CarritoCompra) -> dict:
    detalles = []
    total = 0.0
    ahorro_total = 0.0
    for d in (carrito.detalles or []):
        v = d.variante
        ropa_nom = v.ropa.nombre if (v and v.ropa) else f"Prenda #{d.variante_id}"
        p_base, p_desc, p_promo = _calcular_precio_unitario_promo(v.ropa if v else None, float(v.precio_ajustado) if (v and v.precio_ajustado) else None)
        precio_un = p_promo
        subt = round(precio_un * d.cantidad, 2)
        total += subt
        if p_desc > 0:
            ahorro_total += round((p_base - p_promo) * d.cantidad, 2)

        detalles.append({
            "id": d.id,
            "variante_producto": d.variante_id,
            "cantidad": d.cantidad,
            "subtotal": subt,
            "variante_producto_info": {
                "id": v.id if v else d.variante_id,
                "producto": v.ropa_id if (v and v.ropa) else 1,
                "producto_nombre": ropa_nom,
                "precio": precio_un,
                "precio_original": p_base,
                "precio_promocional": p_promo if p_desc > 0 else None,
                "porcentaje_descuento": p_desc,
                "en_oferta": p_desc > 0,
                "talla_nombre": getattr(v.talla, 'medida', None) or (v.talla.nombre if (v and v.talla) else "Única"),
                "color_nombre": v.color.nombre if (v and v.color) else "Estándar",
                "color_hex": v.color.codigo_hex if (v and v.color) else "#000000",
                "sku": v.cod_barra if (v and v.cod_barra) else (v.sku if v else f"SKU-{d.variante_id}"),
                "imagen_url": v.ropa.imagen_uri if (v and v.ropa) else None
            }
        })
    total = round(total, 2)
    cli_nombre = f"{carrito.cliente.nombre} {getattr(carrito.cliente, 'apellido_pat', '')}".strip() if carrito.cliente else str(carrito.cliente_id)
    return {
        "id": carrito.id,
        "usuario": 1,
        "usuario_username": cli_nombre,
        "cliente_ci": carrito.cliente_id,
        "detalles": detalles,
        "total": total,
        "descuento_promociones": round(ahorro_total, 2),
        "total_articulos": sum(d["cantidad"] for d in detalles),
        "fecha_actualizacion": carrito.fecha_actualizacion.isoformat() if carrito.fecha_actualizacion else (carrito.fecha_creacion.isoformat() if carrito.fecha_creacion else ""),
        "beneficio_fidelizacion": {
            "acumulado": total,
            "monto_minimo": 100.0,
            "monto_descuento": 0.0,
            "activo": False,
            "usado": False,
            "elegible": False
        }
    }


# ==============================================================================
# ENDPOINTS REST API V1 (/api/v1/carrito)
# ==============================================================================

@router.get(
    "/{cliente_id}",
    response_model=CarritoCompraResponse,
    summary="Consultar carrito persistente de un cliente"
)
def obtener_carrito(cliente_id: Union[str, int], db: Session = Depends(get_db)):
    cliente_str = str(cliente_id).strip()
    cliente = _obtener_o_crear_cliente(db, cliente_str)
    carrito = _obtener_o_crear_carrito(db, cliente.ci)
    return _formatear_carrito(carrito)


@router.post(
    "/{cliente_id}/items",
    response_model=CarritoCompraResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Añadir prenda al carrito persistente"
)
def agregar_item(cliente_id: Union[str, int], item_in: DetalleCarritoCreate, db: Session = Depends(get_db)):
    cliente_str = str(cliente_id).strip()
    cliente = _obtener_o_crear_cliente(db, cliente_str)
    carrito = _obtener_o_crear_carrito(db, cliente.ci)

    # Validar existencias en almacén
    suc_id = item_in.sucursal_id or 1
    inv = db.query(InventarioSucursal).filter(
        InventarioSucursal.sucursal_id == suc_id,
        InventarioSucursal.variante_id == item_in.variante_id
    ).first()

    disponible = inv.stock_disponible if inv else 0
    if not inv or disponible < item_in.cantidad:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Excepción A1 (Stock Insuficiente): Solicitadas {item_in.cantidad} unidades, disponibles en tienda: {disponible}."
        )

    # Registrar o acumular en DetalleCarritoCompra
    det = db.query(DetalleCarritoCompra).filter(
        DetalleCarritoCompra.carrito_id == carrito.id,
        DetalleCarritoCompra.variante_id == item_in.variante_id
    ).first()

    if det:
        det.cantidad += item_in.cantidad
    else:
        det = DetalleCarritoCompra(
            carrito_id=carrito.id,
            variante_id=item_in.variante_id,
            cantidad=item_in.cantidad
        )
        db.add(det)

    carrito.fecha_actualizacion = datetime.utcnow()
    db.commit()

    carrito_cargado = _obtener_o_crear_carrito(db, cliente.ci)
    return _formatear_carrito(carrito_cargado)


@router.put(
    "/{cliente_id}/items/{detalle_id}",
    response_model=CarritoCompraResponse,
    summary="Actualizar cantidad de una prenda en el carrito"
)
def actualizar_item(cliente_id: Union[str, int], detalle_id: int, cantidad: int = Query(..., gt=0), db: Session = Depends(get_db)):
    cliente_str = str(cliente_id).strip()
    cliente = _obtener_o_crear_cliente(db, cliente_str)
    carrito = _obtener_o_crear_carrito(db, cliente.ci)

    det = db.query(DetalleCarritoCompra).filter(
        DetalleCarritoCompra.id == detalle_id,
        DetalleCarritoCompra.carrito_id == carrito.id
    ).first()

    if not det:
        raise HTTPException(status_code=404, detail="Ítem no encontrado en el carrito.")

    det.cantidad = cantidad
    carrito.fecha_actualizacion = datetime.utcnow()
    db.commit()

    carrito_cargado = _obtener_o_crear_carrito(db, cliente.ci)
    return _formatear_carrito(carrito_cargado)


@router.delete(
    "/{cliente_id}/items/{detalle_id}",
    response_model=CarritoCompraResponse,
    summary="Eliminar prenda del carrito"
)
def eliminar_item(cliente_id: Union[str, int], detalle_id: int, db: Session = Depends(get_db)):
    cliente_str = str(cliente_id).strip()
    cliente = _obtener_o_crear_cliente(db, cliente_str)
    carrito = _obtener_o_crear_carrito(db, cliente.ci)

    det = db.query(DetalleCarritoCompra).filter(
        DetalleCarritoCompra.id == detalle_id,
        DetalleCarritoCompra.carrito_id == carrito.id
    ).first()

    if not det:
        raise HTTPException(status_code=404, detail="Ítem no encontrado en el carrito.")

    db.delete(det)
    carrito.fecha_actualizacion = datetime.utcnow()
    db.commit()

    carrito_cargado = _obtener_o_crear_carrito(db, cliente.ci)
    return _formatear_carrito(carrito_cargado)


@router.delete(
    "/{cliente_id}/vaciar",
    response_model=CarritoCompraResponse,
    summary="Vaciar todos los artículos del carrito persistente"
)
def vaciar_carrito_v1(cliente_id: Union[str, int], db: Session = Depends(get_db)):
    cliente_str = str(cliente_id).strip()
    cliente = _obtener_o_crear_cliente(db, cliente_str)
    carrito = _obtener_o_crear_carrito(db, cliente.ci)

    db.query(DetalleCarritoCompra).filter(DetalleCarritoCompra.carrito_id == carrito.id).delete()
    carrito.fecha_actualizacion = datetime.utcnow()
    db.commit()

    carrito_cargado = _obtener_o_crear_carrito(db, cliente.ci)
    return _formatear_carrito(carrito_cargado)


# ==============================================================================
# ENDPOINTS COMPATIBILIDAD FRONTEND (/api/carrito)
# ==============================================================================

class ItemOperacionDto(BaseModel):
    variante_id: int
    cantidad: Optional[int] = 1


@router_compat.get("/mi_carrito/")
@router_compat.get("/mi_carrito")
@router_compat.get("/")
@router_compat.get("")
@router_compat.get("/{cliente_ci}/")
@router_compat.get("/{cliente_ci}")
def mi_carrito_compat(cliente_ci: Optional[str] = "2001", db: Session = Depends(get_db)):
    cliente = _obtener_o_crear_cliente(db, cliente_ci or "2001")
    carrito = _obtener_o_crear_carrito(db, cliente.ci)
    return _formatear_carrito_frontend(carrito)


@router_compat.post("/agregar_producto/")
def agregar_producto_compat(dto: ItemOperacionDto, cliente_ci: Optional[str] = "2001", db: Session = Depends(get_db)):
    cliente = _obtener_o_crear_cliente(db, cliente_ci or "2001")
    carrito = _obtener_o_crear_carrito(db, cliente.ci)

    cant = dto.cantidad or 1
    det = db.query(DetalleCarritoCompra).filter(
        DetalleCarritoCompra.carrito_id == carrito.id,
        DetalleCarritoCompra.variante_id == dto.variante_id
    ).first()

    if det:
        det.cantidad += cant
    else:
        det = DetalleCarritoCompra(
            carrito_id=carrito.id,
            variante_id=dto.variante_id,
            cantidad=cant
        )
        db.add(det)

    carrito.fecha_actualizacion = datetime.utcnow()
    db.commit()

    carrito_cargado = _obtener_o_crear_carrito(db, cliente.ci)
    return _formatear_carrito_frontend(carrito_cargado)


@router_compat.post("/actualizar_cantidad/")
def actualizar_cantidad_compat(dto: ItemOperacionDto, cliente_ci: Optional[str] = "2001", db: Session = Depends(get_db)):
    cliente = _obtener_o_crear_cliente(db, cliente_ci or "2001")
    carrito = _obtener_o_crear_carrito(db, cliente.ci)

    det = db.query(DetalleCarritoCompra).filter(
        DetalleCarritoCompra.carrito_id == carrito.id,
        DetalleCarritoCompra.variante_id == dto.variante_id
    ).first()

    if not det:
        raise HTTPException(status_code=404, detail="Prenda no encontrada en el carrito")

    det.cantidad = dto.cantidad or 1
    carrito.fecha_actualizacion = datetime.utcnow()
    db.commit()

    carrito_cargado = _obtener_o_crear_carrito(db, cliente.ci)
    return _formatear_carrito_frontend(carrito_cargado)


@router_compat.post("/quitar_producto/")
def quitar_producto_compat(dto: ItemOperacionDto, cliente_ci: Optional[str] = "2001", db: Session = Depends(get_db)):
    cliente = _obtener_o_crear_cliente(db, cliente_ci or "2001")
    carrito = _obtener_o_crear_carrito(db, cliente.ci)

    det = db.query(DetalleCarritoCompra).filter(
        DetalleCarritoCompra.carrito_id == carrito.id,
        DetalleCarritoCompra.variante_id == dto.variante_id
    ).first()

    if det:
        db.delete(det)
        carrito.fecha_actualizacion = datetime.utcnow()
        db.commit()

    carrito_cargado = _obtener_o_crear_carrito(db, cliente.ci)
    return _formatear_carrito_frontend(carrito_cargado)


@router_compat.post("/vaciar/")
def vaciar_compat(cliente_ci: Optional[str] = "2001", db: Session = Depends(get_db)):
    cliente = _obtener_o_crear_cliente(db, cliente_ci or "2001")
    carrito = _obtener_o_crear_carrito(db, cliente.ci)

    db.query(DetalleCarritoCompra).filter(DetalleCarritoCompra.carrito_id == carrito.id).delete()
    carrito.fecha_actualizacion = datetime.utcnow()
    db.commit()

    carrito_cargado = _obtener_o_crear_carrito(db, cliente.ci)
    return _formatear_carrito_frontend(carrito_cargado)


@router_compat.post("/descargar_pdf/")
@router_compat.post("/descargar_pdf")
@router_compat.get("/descargar_pdf/")
@router_compat.get("/descargar_pdf")
def descargar_pdf_cotizacion(
    cliente_ci: Optional[str] = "2001",
    body: Optional[dict] = None,
    db: Session = Depends(get_db)
):
    cliente = _obtener_o_crear_cliente(db, cliente_ci or "2001")
    carrito = _obtener_o_crear_carrito(db, cliente.ci)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        name="TitleStyle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=8
    )
    elements.append(Paragraph("<b>FashionStore Bolivia S.R.L.</b>", title_style))
    elements.append(Paragraph("<b>Cotización Proforma de Carrito de Compras</b>", styles["Heading2"]))
    elements.append(Paragraph(f"<b>Cliente:</b> {cliente.nombre} {getattr(cliente, 'apellido_pat', '')} (CI: {cliente.ci})", styles["Normal"]))
    elements.append(Paragraph(f"<b>Fecha de Emisión:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    elements.append(Spacer(1, 14))

    table_data = [["#", "Prenda", "Talla", "Color", "Cant.", "P. Unitario", "Subtotal"]]
    total = 0.0
    ahorro_promos = 0.0

    for idx, d in enumerate(carrito.detalles or [], start=1):
        v = d.variante
        nom = v.ropa.nombre if (v and v.ropa) else f"Variante #{d.variante_id}"
        talla = getattr(v.talla, 'medida', None) or (v.talla.nombre if (v and v.talla) else "Única")
        col = v.color.nombre if (v and v.color) else "Estándar"
        p_base, p_desc, p_promo = _calcular_precio_unitario_promo(v.ropa if v else None, float(v.precio_ajustado) if (v and v.precio_ajustado) else None)
        p_unit = p_promo
        subt = round(p_unit * d.cantidad, 2)
        total += subt
        if p_desc > 0:
            ahorro_promos += round((p_base - p_promo) * d.cantidad, 2)
            p_unit_str = f"Bs. {p_promo:.2f} (-{p_desc:.0f}%)"
        else:
            p_unit_str = f"Bs. {p_unit:.2f}"
        table_data.append([str(idx), nom, talla, col, str(d.cantidad), p_unit_str, f"Bs. {subt:.2f}"])

    descuento_fidelidad = 0.0
    total_neto = round(total - descuento_fidelidad, 2)

    if ahorro_promos > 0:
        table_data.append(["", "", "", "", "", "AHORRO PROMOS:", f"- Bs. {ahorro_promos:.2f}"])
    table_data.append(["", "", "", "", "", "TOTAL A PAGAR:", f"Bs. {total:.2f}"])

    t = Table(table_data, colWidths=[25, 175, 45, 60, 35, 90, 90])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#3b82f6")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#dbeafe" if ahorro_promos > 0 else "#f1f5f9")),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<i>* Esta cotización proforma no constituye factura legal y está sujeta a disponibilidad de stock en sucursal.</i>", styles["Italic"]))

    doc.build(elements)
    buffer.seek(0)

    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=cotizacion_carrito_fashionstore.pdf"}
    )
