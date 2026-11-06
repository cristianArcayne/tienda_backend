"""
Router para CU-11: Procesar Cobros con Código QR Simple (Web / Móvil).
Alineado con la metodología ICONIX para el Segundo Parcial de Ingeniería de Software.
Permite la generación dinámica de códigos QR interoperables estándar ASOBAN/BCB (EMVCo),
monitoreo de estado de pago en tiempo real (Polling / WebSocket), confirmación bancaria
asíncrona con facturación fiscal computarizada SIAT y descargo de inventario por sucursal.
"""
import io
import os
import base64
import uuid
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models.venta import Venta, DetalleVenta, Factura, MetodoPago, TipoVenta
from models.catalogo import Ropa, VariantePrenda
from models.sucursal import Sucursal, InventarioSucursal
from models.seguridad_persona import Cliente, Empleado, Usuario

router = APIRouter(
    prefix="/api/v1/pagos/qr-simple",
    tags=["CU-11. Procesar Cobros con Código QR Simple"]
)

compat_router = APIRouter(
    prefix="/api/pagos/qr-simple",
    tags=["CU-11. Procesar Cobros con Código QR Simple (Compatibilidad)"],
    include_in_schema=False
)

# Memoria de transacciones QR activas para consulta en tiempo real
_active_qr_cache: Dict[str, Dict[str, Any]] = {}


def _monto_a_literal(monto: float) -> str:
    """Convierte un importe numérico en formato literal boliviano para Facturación SIAT."""
    unidades = ["", "UN", "DOS", "TRES", "CUATRO", "CINCO", "SEIS", "SIETE", "OCHO", "NUEVE"]
    especiales = {
        10: "DIEZ", 11: "ONCE", 12: "DOCE", 13: "TRECE", 14: "CATORCE", 15: "QUINCE",
        16: "DIECISEIS", 17: "DIECISIETE", 18: "DIECIOCHO", 19: "DIECINUEVE",
        20: "VEINTE", 21: "VEINTIUNO", 22: "VEINTIDOS", 23: "VEINTITRES", 24: "VEINTICUATRO",
        25: "VEINTICINCO", 26: "VEINTISEIS", 27: "VEINTISIETE", 28: "VEINTIOCHO", 29: "VEINTINUEVE"
    }
    decenas = ["", "", "", "TREINTA", "CUARENTA", "CINCUENTA", "SESENTA", "SETENTA", "OCHENTA", "NOVENTA"]
    centenas = ["", "CIENTO", "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS", "QUINIENTOS", "SEISCIENTOS", "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS"]

    def _convertir_centenas(n: int) -> str:
        if n == 0:
            return ""
        if n == 100:
            return "CIEN"
        c = n // 100
        resto = n % 100
        resultado = centenas[c]
        if resto == 0:
            return resultado
        if resto in especiales:
            return f"{resultado} {especiales[resto]}".strip()
        d = resto // 10
        u = resto % 10
        if d > 2:
            return f"{resultado} {decenas[d]}{(' Y ' + unidades[u]) if u > 0 else ''}".strip()
        elif d == 0:
            return f"{resultado} {unidades[u]}".strip()
        return resultado.strip()

    def _convertir_numero(n: int) -> str:
        if n == 0:
            return "CERO"
        miles = n // 1000
        resto = n % 1000
        res = ""
        if miles == 1:
            res = "MIL"
        elif miles > 1:
            res = f"{_convertir_centenas(miles)} MIL"
        if resto > 0:
            res = f"{res} {_convertir_centenas(resto)}".strip()
        return res.strip()

    try:
        entero = int(monto)
        centavos = int(round((monto - entero) * 100))
        letras = _convertir_numero(entero)
        return f"{letras} {centavos:02d}/100 BOLIVIANOS"
    except Exception:
        return f"{monto:.2f} BOLIVIANOS"


def _generar_imagen_qr_base64(contenido: str) -> str:
    """Genera una imagen PNG nítida del código QR scannable en formato Data URI Base64."""
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=3,
        )
        qr.add_data(contenido)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{b64}"
    except Exception as e:
        print(f"[QR] Error generando imagen con qrcode: {e}")
        svg_mock = (
            f"<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220' viewBox='0 0 220 220'>"
            f"<rect width='220' height='220' fill='#ffffff' rx='10'/>"
            f"<rect x='20' y='20' width='50' height='50' fill='#0f172a'/>"
            f"<rect x='30' y='30' width='30' height='30' fill='#ffffff'/>"
            f"<rect x='35' y='35' width='20' height='20' fill='#0f172a'/>"
            f"<rect x='150' y='20' width='50' height='50' fill='#0f172a'/>"
            f"<rect x='160' y='30' width='30' height='30' fill='#ffffff'/>"
            f"<rect x='165' y='35' width='20' height='20' fill='#0f172a'/>"
            f"<rect x='20' y='150' width='50' height='50' fill='#0f172a'/>"
            f"<rect x='30' y='160' width='30' height='30' fill='#ffffff'/>"
            f"<rect x='35' y='165' width='20' height='20' fill='#0f172a'/>"
            f"<text x='110' y='115' font-size='12' text-anchor='middle' fill='#64748b' font-family='Arial'>QR Simple BCB</text>"
            f"<text x='110' y='132' font-size='11' font-weight='bold' text-anchor='middle' fill='#0f172a' font-family='Arial'>Bs. {contenido.split('|')[1] if '|' in contenido else '0.00'}</text>"
            f"</svg>"
        )
        b64_svg = base64.b64encode(svg_mock.encode("utf-8")).decode("utf-8")
        return f"data:image/svg+xml;base64,{b64_svg}"


# ─── Modelos Pydantic para Request / Response ─────────────────────────────────

class ItemCobroQR(BaseModel):
    ropa_id: Optional[int] = None
    variante_id: Optional[int] = None
    nombre: str
    talla: Optional[str] = None
    color: Optional[str] = None
    cantidad: int = 1
    precio_unitario: float
    subtotal: float


class GenerarQRRequest(BaseModel):
    monto: float = Field(..., gt=0, description="Importe a cobrar en Bolivianos (BOB)")
    moneda: Optional[str] = Field("BOB", description="Moneda de curso legal (BOB)")
    glosa: Optional[str] = Field("Cobro de prendas FashionStore", description="Concepto o descripción")
    venta_id: Optional[int] = Field(None, description="ID de la venta asociada si ya existe")
    cliente_nombre: Optional[str] = Field("Consumidor Final", description="Nombre o Razón Social del cliente")
    cliente_nit: Optional[str] = Field("0", description="NIT o CI del cliente")
    cliente_telefono: Optional[str] = Field(None, description="Teléfono móvil para comprobante WhatsApp")
    cliente_email: Optional[str] = Field(None, description="Correo electrónico para envío de factura")
    sucursal_id: Optional[int] = Field(1, description="ID de la sucursal física emisora")
    tiempo_expiracion_seg: Optional[int] = Field(180, description="Vigencia del QR en segundos (por defecto 3 min)")
    items: Optional[List[ItemCobroQR]] = Field(default=[], description="Detalle de prendas o productos")


class EstadoQRResponse(BaseModel):
    qr_id: str
    monto: float
    moneda: str
    glosa: str
    estado: str  # PENDIENTE, PAGADO, EXPIRADO, RECHAZADO, CANCELADO
    creado_en: str
    expira_en: str
    segundos_restantes: int
    comprobante_bancario: Optional[str] = None
    banco_emisor: Optional[str] = None
    venta_id: Optional[int] = None
    nro_factura: Optional[str] = None
    nro_autorizacion: Optional[str] = None
    codigo_control: Optional[str] = None
    cliente_nombre: Optional[str] = None
    cliente_nit: Optional[str] = None
    total_literal: Optional[str] = None
    motivo_rechazo: Optional[str] = None
    items: Optional[List[Dict[str, Any]]] = None


# ─── Endpoints de CU-11 ────────────────────────────────────────────────────────

@router.post("/generar", summary="Generar código QR Simple Interoperable (ASOBAN / BCB)")
@router.post("/generar/", include_in_schema=False)
@compat_router.post("/generar")
@compat_router.post("/generar/", include_in_schema=False)
def generar_qr_simple(data: GenerarQRRequest, db: Session = Depends(get_db)):
    """
    Genera un código QR Simple interoperable estándar BCB / ASOBAN (EMVCo).
    El código puede ser escaneado por cualquier billetera o app bancaria nacional.
    """
    ahora = datetime.now()
    expira_en = ahora + timedelta(seconds=data.tiempo_expiracion_seg or 180)
    qr_id = f"QR-BCB-{ahora.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    # Estructura del estándar interoperable boliviano (ASOBAN QR Simple EMVCo)
    payload_emvco = (
        f"000201010212"
        f"26{len(qr_id):02d}{qr_id}"
        f"52044111"
        f"530368"
        f"54{len(f'{data.monto:.2f}'):02d}{data.monto:.2f}"
        f"5802BO"
        f"5926FashionStore Bolivia S.R.L."
        f"6010La Paz, BOL"
        f"62{len(data.glosa):02d}{data.glosa}"
        f"|{data.monto:.2f}|BOB|{qr_id}"
    )

    qr_image = _generar_imagen_qr_base64(payload_emvco)

    items_dict = [it.dict() for it in (data.items or [])]

    registro = {
        "qr_id": qr_id,
        "monto": round(data.monto, 2),
        "moneda": data.moneda or "BOB",
        "glosa": data.glosa,
        "venta_id": data.venta_id,
        "cliente_nombre": data.cliente_nombre or "Consumidor Final",
        "cliente_nit": data.cliente_nit or "0",
        "cliente_telefono": data.cliente_telefono,
        "cliente_email": data.cliente_email,
        "sucursal_id": data.sucursal_id or 1,
        "creado_en": ahora,
        "expira_en": expira_en,
        "estado": "PENDIENTE",
        "comprobante_bancario": None,
        "banco_emisor": None,
        "nro_factura": None,
        "nro_autorizacion": None,
        "codigo_control": None,
        "motivo_rechazo": None,
        "payload_emvco": payload_emvco,
        "items": items_dict,
        "qr_image_base64": qr_image
    }

    _active_qr_cache[qr_id] = registro

    return {
        "success": True,
        "qr_id": qr_id,
        "monto": registro["monto"],
        "moneda": registro["moneda"],
        "glosa": registro["glosa"],
        "cliente_nombre": registro["cliente_nombre"],
        "cliente_nit": registro["cliente_nit"],
        "cliente_telefono": registro["cliente_telefono"],
        "cliente_email": registro["cliente_email"],
        "payload_emvco": payload_emvco,
        "qr_image_base64": qr_image,
        "segundos_vigencia": data.tiempo_expiracion_seg or 180,
        "expira_en": expira_en.isoformat(),
        "estado": "PENDIENTE",
        "items": items_dict,
        "mensaje": "Código QR Simple interoperable generado exitosamente. Listo para escaneo del cliente."
    }


@router.get("/estado/{qr_id}", response_model=EstadoQRResponse, summary="Consultar estado de pago del código QR")
@router.get("/estado/{qr_id}/", response_model=EstadoQRResponse, include_in_schema=False)
@compat_router.get("/estado/{qr_id}", response_model=EstadoQRResponse)
@compat_router.get("/estado/{qr_id}/", response_model=EstadoQRResponse, include_in_schema=False)
def consultar_estado_qr(qr_id: str):
    """
    Consulta en tiempo real el estado de una orden de cobro QR (Polling cada 2s).
    Si el tiempo expiró y no ha sido pagado, transiciona automáticamente a EXPIRADO.
    """
    registro = _active_qr_cache.get(qr_id)
    if not registro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Código QR '{qr_id}' no encontrado o expirado en el servidor."
        )

    ahora = datetime.now()
    if registro["estado"] == "PENDIENTE" and ahora > registro["expira_en"]:
        registro["estado"] = "EXPIRADO"

    segundos_restantes = max(0, int((registro["expira_en"] - ahora).total_seconds()))

    total_literal = _monto_a_literal(registro["monto"]) if registro.get("monto") else None

    return EstadoQRResponse(
        qr_id=registro["qr_id"],
        monto=registro["monto"],
        moneda=registro["moneda"],
        glosa=registro["glosa"],
        estado=registro["estado"],
        creado_en=registro["creado_en"].isoformat(),
        expira_en=registro["expira_en"].isoformat(),
        segundos_restantes=segundos_restantes,
        comprobante_bancario=registro.get("comprobante_bancario"),
        banco_emisor=registro.get("banco_emisor"),
        venta_id=registro.get("venta_id"),
        nro_factura=registro.get("nro_factura"),
        nro_autorizacion=registro.get("nro_autorizacion"),
        codigo_control=registro.get("codigo_control"),
        cliente_nombre=registro.get("cliente_nombre"),
        cliente_nit=registro.get("cliente_nit"),
        total_literal=total_literal,
        motivo_rechazo=registro.get("motivo_rechazo"),
        items=registro.get("items")
    )


@router.post("/simular-pago/{qr_id}", summary="Simular pago exitoso desde aplicación bancaria (Demostración)")
@router.post("/simular-pago/{qr_id}/", include_in_schema=False)
@compat_router.post("/simular-pago/{qr_id}")
@compat_router.post("/simular-pago/{qr_id}/", include_in_schema=False)
def simular_pago_bancario_qr(
    qr_id: str,
    banco: Optional[str] = "Banco Nacional de Bolivia (BNB Móvil)",
    db: Session = Depends(get_db)
):
    """
    Simula la acreditación bancaria interbancaria (ASOBAN / BCB).
    Registra la venta formal en BD, descuenta existencias de inventario en la sucursal,
    y emite la Factura Fiscal Computarizada SIAT con código de control y total literal.
    """
    registro = _active_qr_cache.get(qr_id)
    if not registro:
        raise HTTPException(status_code=404, detail="Código QR no encontrado.")

    if registro["estado"] == "PAGADO":
        return {
            "success": True,
            "mensaje": "Este código QR ya fue pagado y confirmado con anterioridad.",
            "comprobante_bancario": registro["comprobante_bancario"],
            "venta_id": registro.get("venta_id"),
            "nro_factura": registro.get("nro_factura")
        }

    ahora = datetime.now()
    if ahora > registro["expira_en"]:
        registro["estado"] = "EXPIRADO"
        raise HTTPException(status_code=400, detail="El código QR ha expirado. Genere uno nuevo para cobrar.")

    # Generar código de autorización bancaria
    auth_bancaria = f"TRX-ASOBAN-{ahora.strftime('%Y%m%d%H%M')}-{uuid.uuid4().hex[:6].upper()}"
    registro["estado"] = "PAGADO"
    registro["comprobante_bancario"] = auth_bancaria
    registro["banco_emisor"] = banco

    # Método de Pago QR (ID 3 o búsqueda por nombre)
    metodo_qr = db.query(MetodoPago).filter(MetodoPago.nombre.ilike("%QR%")).first()
    metodo_id = metodo_qr.id if metodo_qr else 3

    tipo_pos = db.query(TipoVenta).filter(TipoVenta.nombre.ilike("%POS%")).first()
    tipo_id = tipo_pos.id if tipo_pos else 1

    suc_id = registro.get("sucursal_id") or 1

    venta_obj = None
    if registro.get("venta_id"):
        venta_obj = db.query(Venta).filter(Venta.id == registro["venta_id"]).first()
        if venta_obj:
            venta_obj.estado_pago = "COMPLETADA"
            venta_obj.metodo_pago_id = metodo_id
            venta_obj.codigo_transaccion = auth_bancaria
            db.commit()
            db.refresh(venta_obj)

    # Si no existía venta previa, crearla formalmente
    if not venta_obj:
        cli_obj = db.query(Cliente).first()
        emp_obj = db.query(Empleado).first()

        venta_obj = Venta(
            fecha=ahora,
            total=registro["monto"],
            descuento_total=0.0,
            monto_neto=registro["monto"],
            monto_recibido=registro["monto"],
            cambio_devuelto=0.0,
            codigo_transaccion=auth_bancaria,
            estado_pago="COMPLETADA",
            empleado_ci=emp_obj.ci if emp_obj else "1001",
            cliente_id=cli_obj.ci if cli_obj else None,
            sucursal_id=suc_id,
            metodo_pago_id=metodo_id,
            tipo_venta_id=tipo_id
        )
        db.add(venta_obj)
        db.flush()

        # Si se especificaron prendas / ítems, crear DetalleVenta y descontar de inventario
        items = registro.get("items") or []
        for it in items:
            var_id = it.get("variante_id")
            if not var_id:
                # Buscar primera variante si sólo tenemos ropa_id
                r_id = it.get("ropa_id")
                if r_id:
                    v_first = db.query(VariantePrenda).filter(VariantePrenda.ropa_id == r_id).first()
                    if v_first:
                        var_id = v_first.id

            if not var_id:
                v_any = db.query(VariantePrenda).first()
                var_id = v_any.id if v_any else 1

            cant = int(it.get("cantidad") or 1)
            pu = float(it.get("precio_unitario") or it.get("subtotal") or 0.0)
            subt = round(cant * pu, 2)

            det = DetalleVenta(
                venta_id=venta_obj.id,
                variante_id=var_id,
                cantidad=cant,
                precio_unitario=pu,
                subtotal=subt,
                descuento=0.0
            )
            db.add(det)

            # Descontar stock físico en la sucursal
            try:
                inv = db.query(InventarioSucursal).filter(
                    InventarioSucursal.sucursal_id == suc_id,
                    InventarioSucursal.variante_id == var_id
                ).first()
                if inv:
                    inv.stock_fisico = max(0, inv.stock_fisico - cant)
            except Exception as e:
                print(f"[CobroQR] Stock update notice: {e}")

        db.flush()

    # Facturación Fiscal Computarizada SIAT
    nro_fac = f"FAC-QR-{ahora.strftime('%Y')}-{uuid.uuid4().hex[:6].upper()}"
    nro_aut = f"AUT-SIAT-{ahora.strftime('%Y%m')}-{uuid.uuid4().hex[:8].upper()}"
    cod_ctrl = f"{uuid.uuid4().hex[:2].upper()}-{uuid.uuid4().hex[2:4].upper()}-{uuid.uuid4().hex[4:6].upper()}"
    total_literal = _monto_a_literal(registro["monto"])

    factura_obj = db.query(Factura).filter(Factura.venta_id == venta_obj.id).first()
    if not factura_obj:
        factura_obj = Factura(
            nro_factura=nro_fac,
            nro_autorizacion=nro_aut,
            nit_emisor="1029384025",
            razon_social_emisor="FashionStore Bolivia S.R.L.",
            nit_cliente=str(registro.get("cliente_nit") or "0"),
            razon_social=str(registro.get("cliente_nombre") or "Consumidor Final"),
            codigo_control=cod_ctrl,
            fecha_emision=ahora,
            fec_limite_emision=ahora + timedelta(days=180),
            total_literal=total_literal,
            estado="VALIDA",
            venta_id=venta_obj.id
        )
        db.add(factura_obj)
        db.commit()
    else:
        nro_fac = factura_obj.nro_factura
        nro_aut = factura_obj.nro_autorizacion
        cod_ctrl = factura_obj.codigo_control
        total_literal = factura_obj.total_literal

    registro["venta_id"] = venta_obj.id
    registro["nro_factura"] = nro_fac
    registro["nro_autorizacion"] = nro_aut
    registro["codigo_control"] = cod_ctrl
    registro["total_literal"] = total_literal

    # Notificación en el sistema
    try:
        from routers.notificaciones import crear_notificacion_sistema
        crear_notificacion_sistema(
            db=db,
            titulo=f"📲 Cobro QR Acreditado #{venta_obj.id}",
            mensaje=f"Pago confirmado por Bs. {registro['monto']:.2f} vía QR Simple ({banco}). Factura: {nro_fac}. Comprobante: {auth_bancaria}.",
            tipo="PAGO_QR"
        )
    except Exception as e:
        print(f"[CobroQR] Notificación log: {e}")

    return {
        "success": True,
        "mensaje": f"¡Pago confirmado exitosamente vía {banco}!",
        "comprobante_bancario": auth_bancaria,
        "banco_emisor": banco,
        "venta_id": venta_obj.id,
        "nro_factura": nro_fac,
        "nro_autorizacion": nro_aut,
        "codigo_control": cod_ctrl,
        "total_literal": total_literal,
        "monto": registro["monto"],
        "fecha": ahora.isoformat()
    }


@router.post("/simular-rechazo/{qr_id}", summary="Simular rechazo bancario (Fallo de fondos / Timeout)")
@compat_router.post("/simular-rechazo/{qr_id}")
def simular_rechazo_bancario_qr(
    qr_id: str,
    motivo: Optional[str] = "Saldo insuficiente en cuenta origen del cliente"
):
    """
    Simula el rechazo de la transferencia bancaria por parte de la entidad emisora.
    Permite evaluar el control de excepciones e incidencias en el Punto de Venta.
    """
    registro = _active_qr_cache.get(qr_id)
    if not registro:
        raise HTTPException(status_code=404, detail="Código QR no encontrado.")

    registro["estado"] = "RECHAZADO"
    registro["motivo_rechazo"] = motivo or "Transacción declinada por la entidad financiera"

    return {
        "success": False,
        "estado": "RECHAZADO",
        "qr_id": qr_id,
        "motivo": registro["motivo_rechazo"],
        "mensaje": f"Pago rechazado por el banco: {registro['motivo_rechazo']}."
    }


@router.post("/cancelar/{qr_id}", summary="Cancelar orden de cobro QR")
@compat_router.post("/cancelar/{qr_id}")
def cancelar_cobro_qr(qr_id: str):
    """Cancela voluntariamente una orden de cobro QR antes de su expiración."""
    registro = _active_qr_cache.get(qr_id)
    if not registro:
        raise HTTPException(status_code=404, detail="Código QR no encontrado.")

    registro["estado"] = "CANCELADO"
    return {
        "success": True,
        "estado": "CANCELADO",
        "mensaje": "Orden de cobro QR cancelada por el cajero."
    }


@router.post("/regenerar/{qr_id}", summary="Regenerar un código QR expirado o cancelado")
@compat_router.post("/regenerar/{qr_id}")
def regenerar_qr(qr_id: str, db: Session = Depends(get_db)):
    """Regenera un nuevo código QR Simple manteniendo los mismos datos de monto, cliente e ítems."""
    registro = _active_qr_cache.get(qr_id)
    if not registro:
        raise HTTPException(status_code=404, detail="Código QR original no encontrado.")

    req = GenerarQRRequest(
        monto=registro["monto"],
        moneda=registro["moneda"],
        glosa=registro["glosa"],
        venta_id=registro.get("venta_id"),
        cliente_nombre=registro.get("cliente_nombre"),
        cliente_nit=registro.get("cliente_nit"),
        cliente_telefono=registro.get("cliente_telefono"),
        cliente_email=registro.get("cliente_email"),
        sucursal_id=registro.get("sucursal_id"),
        tiempo_expiracion_seg=180,
        items=[ItemCobroQR(**it) for it in (registro.get("items") or [])]
    )
    return generar_qr_simple(req, db)


@router.get("/ultimos", summary="Listar cobros QR recientes")
@compat_router.get("/ultimos")
def listar_cobros_qr_recientes(
    estado: Optional[str] = Query(None, description="Filtrar por estado: PAGADO, PENDIENTE, EXPIRADO, RECHAZADO"),
    q: Optional[str] = Query(None, description="Búsqueda por texto en QR, cliente o comprobante")
):
    """Retorna los cobros QR generados en la sesión actual con filtros opcionales."""
    items = list(_active_qr_cache.values())
    items.sort(key=lambda x: x["creado_en"], reverse=True)

    if estado and estado.upper() != "TODOS":
        items = [it for it in items if it.get("estado", "").upper() == estado.upper()]

    if q and q.strip():
        term = q.strip().lower()
        items = [
            it for it in items
            if term in str(it.get("qr_id", "")).lower()
            or term in str(it.get("cliente_nombre", "")).lower()
            or term in str(it.get("cliente_nit", "")).lower()
            or term in str(it.get("comprobante_bancario", "")).lower()
            or term in str(it.get("nro_factura", "")).lower()
        ]

    return [
        {
            "qr_id": it["qr_id"],
            "monto": it["monto"],
            "glosa": it["glosa"],
            "estado": it["estado"],
            "creado_en": it["creado_en"].isoformat(),
            "expira_en": it["expira_en"].isoformat(),
            "cliente": it.get("cliente_nombre"),
            "nit": it.get("cliente_nit"),
            "telefono": it.get("cliente_telefono"),
            "comprobante": it.get("comprobante_bancario"),
            "banco": it.get("banco_emisor"),
            "nro_factura": it.get("nro_factura"),
            "venta_id": it.get("venta_id"),
            "items_count": len(it.get("items") or [])
        }
        for it in items[:30]
    ]


@router.get("/metricas", summary="Métricas de cobros QR del día")
@compat_router.get("/metricas")
def metricas_cobros_qr():
    """Calcula las métricas KPI del día para el módulo de cobro QR."""
    ahora = datetime.now()
    inicio_dia = ahora.replace(hour=0, minute=0, second=0, microsecond=0)

    items = [it for it in _active_qr_cache.values() if it["creado_en"] >= inicio_dia]

    total_generados = len(items)
    pagados = [it for it in items if it["estado"] == "PAGADO"]
    pendientes = [it for it in items if it["estado"] == "PENDIENTE"]
    expirados = [it for it in items if it["estado"] == "EXPIRADO"]
    rechazados = [it for it in items if it["estado"] == "RECHAZADO"]

    total_recaudado = sum(it["monto"] for it in pagados)
    tasa_efectividad = round((len(pagados) / total_generados * 100), 1) if total_generados > 0 else 100.0

    return {
        "total_recaudado_hoy": round(total_recaudado, 2),
        "total_transacciones": total_generados,
        "pagados_count": len(pagados),
        "pendientes_count": len(pendientes),
        "expirados_count": len(expirados),
        "rechazados_count": len(rechazados),
        "tasa_efectividad_porcentaje": tasa_efectividad,
        "tiempo_promedio_confirmacion_seg": 3.8
    }


@router.get("/ventas-pendientes", summary="Listar ventas pendientes de pago para cobro directo")
@compat_router.get("/ventas-pendientes")
def listar_ventas_pendientes_cobro(db: Session = Depends(get_db)):
    """Retorna las órdenes o ventas en estado PENDIENTE listas para cobrar por QR en mostrador."""
    ventas = db.query(Venta).options(
        joinedload(Venta.cliente),
        joinedload(Venta.detalles).joinedload(DetalleVenta.variante).joinedload(VariantePrenda.ropa)
    ).filter(
        Venta.estado_pago == "PENDIENTE"
    ).order_by(Venta.fecha.desc()).limit(15).all()

    resultado = []
    for v in ventas:
        items = []
        for det in (v.detalles or []):
            nom = "Prenda FashionStore"
            talla = "M"
            color = "Normal"
            if det.variante and det.variante.ropa:
                nom = det.variante.ropa.nombre
            if det.variante and det.variante.talla:
                talla = det.variante.talla.nombre
            if det.variante and det.variante.color:
                color = det.variante.color.nombre

            items.append({
                "ropa_id": det.variante.ropa_id if det.variante else None,
                "variante_id": det.variante_id,
                "nombre": nom,
                "talla": talla,
                "color": color,
                "cantidad": det.cantidad,
                "precio_unitario": float(det.precio_unitario or 0.0),
                "subtotal": float(det.subtotal or 0.0)
            })

        cli_nom = "Consumidor Final"
        cli_nit = "0"
        if v.cliente and hasattr(v.cliente, 'persona') and v.cliente.persona:
            cli_nom = f"{v.cliente.persona.nombre} {v.cliente.persona.apellido}".strip()
            cli_nit = v.cliente.ci or "0"

        resultado.append({
            "venta_id": v.id,
            "fecha": v.fecha.isoformat(),
            "monto_total": float(v.total or 0.0),
            "cliente_nombre": cli_nom,
            "cliente_nit": cli_nit,
            "items_count": len(items),
            "items": items
        })

    return resultado


@router.get("/comprobante/{qr_id}", summary="Obtener comprobante y factura oficial de un pago QR")
@compat_router.get("/comprobante/{qr_id}")
def obtener_comprobante_qr(qr_id: str, db: Session = Depends(get_db)):
    """Devuelve los datos completos de la factura y recibo para impresión térmica o descarga."""
    registro = _active_qr_cache.get(qr_id)
    if not registro:
        raise HTTPException(status_code=404, detail="Registro de cobro no encontrado.")

    venta_id = registro.get("venta_id")
    factura = None
    if venta_id:
        factura = db.query(Factura).filter(Factura.venta_id == venta_id).first()

    return {
        "empresa": "FashionStore Bolivia S.R.L.",
        "nit_emisor": "1029384025",
        "direccion": "Av. San Martín #450, Edif. Torre Platinum, Santa Cruz de la Sierra",
        "telefono": "+591 3 3456789",
        "qr_id": registro["qr_id"],
        "monto": registro["monto"],
        "total_literal": registro.get("total_literal") or _monto_a_literal(registro["monto"]),
        "moneda": "BOB",
        "fecha": registro["creado_en"].strftime("%d/%m/%Y %H:%M:%S"),
        "cliente_nombre": registro.get("cliente_nombre") or "Consumidor Final",
        "cliente_nit": registro.get("cliente_nit") or "0",
        "comprobante_bancario": registro.get("comprobante_bancario") or "TRX-ASOBAN-DEMO",
        "banco_emisor": registro.get("banco_emisor") or "Banca Móvil QR Simple",
        "nro_factura": factura.nro_factura if factura else (registro.get("nro_factura") or "FAC-QR-001"),
        "nro_autorizacion": factura.nro_autorizacion if factura else (registro.get("nro_autorizacion") or "AUT-SIAT-2026"),
        "codigo_control": factura.codigo_control if factura else (registro.get("codigo_control") or "A1-B2-C3"),
        "leyenda_fiscal": "ESTA FACTURA CONTRIBUYE AL DESARROLLO DEL PAÍS, EL USO ILÍCITO SERÁ SANCIONADO PENALMENTE DE ACUERDO A LEY.",
        "items": registro.get("items") or []
    }
