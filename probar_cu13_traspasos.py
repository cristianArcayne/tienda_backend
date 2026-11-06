# -*- coding: utf-8 -*-
"""
=============================================================================
PRUEBAS AUTOMATIZADAS EN VIVO: CU-13 TRASPASOS DE MERCADERÍA INTER-SUCURSALES
Asignatura: Sistemas de Información 2 (INF-412 SA)
Docente: MSc. Ing. Angélica Garzón Cuéllar
Estudiante: Yeison Choque León
=============================================================================
Verifica la trazabilidad auditada bajo los 3 estados del ciclo de vida:
  [CP-CU13-01] Validación de Reglas de Negocio:
               - Origen no puede ser igual a Destino (HTTP 400).
               - Control de existencias físicas en Origen (HTTP 400).
  [CP-CU13-02] Estado 1: 'SOLICITADO' - Alta de orden de transferencia inter-tienda.
  [CP-CU13-03] Estado 2: 'EN_TRANSITO' - Despacho de mercadería con descuento en Origen
               y generación de Kardex MovimientoInventario ('TRASPASO_SALIDA').
  [CP-CU13-04] Estado 3: 'RECIBIDO' - Recepción conforme en Destino con incremento de stock
               y generación de Kardex MovimientoInventario ('TRASPASO_ENTRADA').
  [CP-CU13-05] Cancelación Resiliente: Traspaso en tránsito cancelado restituye stock a Origen.
=============================================================================
"""
import sys
from fastapi.testclient import TestClient

from main import app
from database import SessionLocal
from models.sucursal import Sucursal, InventarioSucursal, Traspaso, MovimientoInventario
from models.catalogo import VariantePrenda

client = TestClient(app)

def banner(titulo):
    print("\n" + "=" * 78)
    print(f" {titulo}")
    print("=" * 78)

def paso(codigo, nombre):
    print(f"\n>>> [{codigo}] {nombre}")

def exito(detalle):
    print(f"    [PASS] EXITO: {detalle}")

def fallo(detalle):
    print(f"    [FAIL] FALLO: {detalle}")
    sys.exit(1)

banner("INICIO DE PRUEBAS DE ACEPTACIÓN: CU-13 TRASPASOS INTER-SUCURSALES")

db = SessionLocal()

# Identificar 2 sucursales activas distintas
sucursales = db.query(Sucursal).filter(Sucursal.activo == True).limit(2).all()
if len(sucursales) < 2:
    fallo("Se requieren al menos 2 sucursales para probar traspasos.")

suc_origen = sucursales[0]
suc_destino = sucursales[1]

# Identificar una variante con stock disponible en origen
var = db.query(VariantePrenda).join(InventarioSucursal).filter(
    InventarioSucursal.sucursal_id == suc_origen.id,
    InventarioSucursal.stock_fisico >= 5
).first()

# Garantizar stock amplio en origen para todas las pruebas
inv_orig_setup = db.query(InventarioSucursal).filter(
    InventarioSucursal.sucursal_id == suc_origen.id,
    InventarioSucursal.variante_id == var.id
).first()
if not inv_orig_setup:
    inv_orig_setup = InventarioSucursal(sucursal_id=suc_origen.id, variante_id=var.id, stock_fisico=50, stock_reservado=0, stock_minimo=5)
    db.add(inv_orig_setup)
else:
    inv_orig_setup.stock_fisico = 50
    inv_orig_setup.stock_reservado = 0
db.commit()

var_id = var.id
print(f"[*] Escenario: Origen='{suc_origen.nombre}' (ID #{suc_origen.id}) -> Destino='{suc_destino.nombre}' (ID #{suc_destino.id})")
print(f"[*] Prenda a transferir: Variante #{var_id} ('{var.ropa.nombre if var.ropa else ''}')")

# =============================================================================
# PRUEBA 1: VALIDACIONES DE REGLA DE NEGOCIO
# =============================================================================
paso("CP-CU13-01", "Validación: Mismo Origen y Destino / Stock Insuficiente")
# 1. Mismo origen y destino
res_err1 = client.post("/api/v1/traspasos/", json={
    "sucursal_origen_id": suc_origen.id,
    "sucursal_destino_id": suc_origen.id,
    "detalles": [{"variante_id": var_id, "cantidad": 2}]
})
if res_err1.status_code == 400 and "misma" in res_err1.text.lower():
    exito("Bloqueo correcto con HTTP 400 cuando Origen == Destino.")
else:
    fallo(f"Debería rechazar mismo origen/destino: {res_err1.text}")

# 2. Exceso de stock
res_err2 = client.post("/api/v1/traspasos/", json={
    "sucursal_origen_id": suc_origen.id,
    "sucursal_destino_id": suc_destino.id,
    "detalles": [{"variante_id": var_id, "cantidad": 999999}]
})
if res_err2.status_code == 400 and "insuficiente" in res_err2.text.lower():
    exito("Bloqueo correcto con HTTP 400 por stock insuficiente en Origen.")
else:
    fallo(f"Debería rechazar por stock insuficiente: {res_err2.text}")

# =============================================================================
# PRUEBA 2: ESTADO 1 - CREACIÓN EN ESTADO 'SOLICITADO'
# =============================================================================
paso("CP-CU13-02", "Ciclo de Vida - Estado 1: 'SOLICITADO' (Sin descuento físico previo)")
db.expire_all()
inv_orig_inicial = db.query(InventarioSucursal).filter(
    InventarioSucursal.sucursal_id == suc_origen.id,
    InventarioSucursal.variante_id == var_id
).first()
stock_orig_inicial = inv_orig_inicial.stock_fisico

payload_traspaso = {
    "sucursal_origen_id": suc_origen.id,
    "sucursal_destino_id": suc_destino.id,
    "observacion": "Reabastecimiento urgente de temporada alta",
    "solicitado_por_ci": "1001",
    "despachar_inmediato": False,  # Queda en SOLICITADO
    "detalles": [{"variante_id": var_id, "cantidad": 3}]
}
res_crear = client.post("/api/v1/traspasos/", json=payload_traspaso)
if res_crear.status_code == 201:
    t_data = res_crear.json()
    traspaso_id = t_data["id"]
    exito(f"Traspaso #{traspaso_id} registrado en estado '{t_data['estado']}'. Total unidades: {t_data['total_unidades']}")
    
    # Verificar que el stock de origen NO se haya descontado aún
    db.expire_all()
    inv_check = db.query(InventarioSucursal).filter(
        InventarioSucursal.sucursal_id == suc_origen.id,
        InventarioSucursal.variante_id == var_id
    ).first()
    if inv_check.stock_fisico == stock_orig_inicial:
        exito(f"Stock en Origen intacto ({inv_check.stock_fisico} u.) mientras la solicitud está pendiente de despacho.")
    else:
        fallo("El stock no debió descontarse en estado SOLICITADO.")
else:
    fallo(f"Error creando traspaso: {res_crear.text}")

# =============================================================================
# PRUEBA 3: ESTADO 2 - DESPACHO Y ESTADO 'EN_TRANSITO'
# =============================================================================
paso("CP-CU13-03", "Ciclo de Vida - Estado 2: 'EN_TRANSITO' (Descuento en Origen + Kardex)")
res_desp = client.post(f"/api/v1/traspasos/{traspaso_id}/despachar")
if res_desp.status_code == 200:
    d_data = res_desp.json()
    exito(f"Traspaso #{traspaso_id} despachado exitosamente. Nuevo estado: '{d_data['estado']}'")
    
    # Verificar descuento en Origen
    db.expire_all()
    inv_orig_desp = db.query(InventarioSucursal).filter(
        InventarioSucursal.sucursal_id == suc_origen.id,
        InventarioSucursal.variante_id == var_id
    ).first()
    if inv_orig_desp.stock_fisico == stock_orig_inicial - 3:
        exito(f"Descuento confirmado en Origen: Stock pasó de {stock_orig_inicial} a {inv_orig_desp.stock_fisico} (-3 unidades).")
    else:
        fallo("Fallo en descuento de stock de origen.")
        
    # Verificar Kardex de salida
    mov_salida = db.query(MovimientoInventario).filter(
        MovimientoInventario.sucursal_id == suc_origen.id,
        MovimientoInventario.variante_id == var_id,
        MovimientoInventario.tipo_movimiento == "TRASPASO_SALIDA"
    ).order_by(MovimientoInventario.id.desc()).first()
    if mov_salida:
        exito(f"Movimiento Kardex generado: Tipo='{mov_salida.tipo_movimiento}' | Motivo='{mov_salida.motivo}'")
    else:
        fallo("No se registró el movimiento de salida en MovimientoInventario.")
else:
    fallo(f"Error despachando traspaso: {res_desp.text}")

# =============================================================================
# PRUEBA 4: ESTADO 3 - RECEPCIÓN CONFORME EN DESTINO Y ESTADO 'RECIBIDO'
# =============================================================================
paso("CP-CU13-04", "Ciclo de Vida - Estado 3: 'RECIBIDO' (Incremento en Destino + Kardex)")
inv_dest_pre = db.query(InventarioSucursal).filter(
    InventarioSucursal.sucursal_id == suc_destino.id,
    InventarioSucursal.variante_id == var_id
).first()
stock_dest_pre = inv_dest_pre.stock_fisico if inv_dest_pre else 0

res_rec = client.post(f"/api/v1/traspasos/{traspaso_id}/confirmar-recepcion")
if res_rec.status_code == 200:
    r_data = res_rec.json()
    exito(f"Traspaso #{traspaso_id} recepcionado en Destino. Nuevo estado: '{r_data['estado']}' | Fecha: {r_data['fecha_recepcion']}")
    
    # Verificar incremento en Destino
    db.expire_all()
    inv_dest_post = db.query(InventarioSucursal).filter(
        InventarioSucursal.sucursal_id == suc_destino.id,
        InventarioSucursal.variante_id == var_id
    ).first()
    if inv_dest_post.stock_fisico == stock_dest_pre + 3:
        exito(f"Incremento confirmado en Destino: Stock pasó de {stock_dest_pre} a {inv_dest_post.stock_fisico} (+3 unidades).")
    else:
        fallo("Fallo en incremento de stock en destino.")
        
    # Verificar Kardex de entrada
    mov_entrada = db.query(MovimientoInventario).filter(
        MovimientoInventario.sucursal_id == suc_destino.id,
        MovimientoInventario.variante_id == var_id,
        MovimientoInventario.tipo_movimiento == "TRASPASO_ENTRADA"
    ).order_by(MovimientoInventario.id.desc()).first()
    if mov_entrada:
        exito(f"Movimiento Kardex generado: Tipo='{mov_entrada.tipo_movimiento}' | Motivo='{mov_entrada.motivo}'")
    else:
        fallo("No se registró el movimiento de entrada en MovimientoInventario.")
else:
    fallo(f"Error confirmando recepción: {res_rec.text}")

# =============================================================================
# PRUEBA 5: CANCELACIÓN RESILIENTE Y RESTITUCIÓN DE STOCK
# =============================================================================
paso("CP-CU13-05", "Cancelación Resiliente de Traspaso en Tránsito (Restitución a Origen)")
# Crear y despachar de inmediato un traspaso para probar cancelación
res_t2 = client.post("/api/v1/traspasos/", json={
    "sucursal_origen_id": suc_origen.id,
    "sucursal_destino_id": suc_destino.id,
    "observacion": "Traspaso con contingencia en transporte",
    "despachar_inmediato": True,
    "detalles": [{"variante_id": var_id, "cantidad": 2}]
})
t2_id = res_t2.json()["id"]

# Guardar stock actual en origen antes de cancelar
db.expire_all()
inv_orig_antes_cancel = db.query(InventarioSucursal).filter(
    InventarioSucursal.sucursal_id == suc_origen.id,
    InventarioSucursal.variante_id == var_id
).first()
stock_antes_cancel = inv_orig_antes_cancel.stock_fisico

# Cancelar traspaso en tránsito
res_cancel = client.post(f"/api/v1/traspasos/{t2_id}/cancelar")
if res_cancel.status_code == 200:
    c_data = res_cancel.json()
    exito(f"Traspaso #{t2_id} cancelado correctamente. Estado: '{c_data['estado']}'")
    
    # Verificar que el stock volvió a Origen
    db.expire_all()
    inv_orig_restituido = db.query(InventarioSucursal).filter(
        InventarioSucursal.sucursal_id == suc_origen.id,
        InventarioSucursal.variante_id == var_id
    ).first()
    if inv_orig_restituido.stock_fisico == stock_antes_cancel + 2:
        exito(f"Restitución exitosa a Origen: Stock subió de {stock_antes_cancel} a {inv_orig_restituido.stock_fisico} (+2 unidades restituidas).")
    else:
        fallo("No se restituyó el stock a origen tras la cancelación.")
else:
    fallo(f"Error cancelando traspaso: {res_cancel.text}")

# =============================================================================
# PRUEBA 6: GUÍA DE REMISIÓN OFICIAL Y CÓDIGO QR DE TRANSPORTE
# =============================================================================
paso("CP-CU13-06", "Emisión de Guía de Remisión Oficial y QR de Transporte")
res_guia = client.get(f"/api/v1/traspasos/{traspaso_id}/guia-remision")
if res_guia.status_code == 200:
    g_data = res_guia.json()
    codigo_guia = g_data.get("guia_remision_codigo")
    qr_data = g_data.get("guia_remision_qr")
    if codigo_guia and codigo_guia.startswith("REM-"):
        exito(f"Guía de Remisión generada: Código='{codigo_guia}'")
    else:
        fallo(f"Código de guía inválido: {codigo_guia}")
    if qr_data and qr_data.startswith("data:image/png;base64,"):
        exito(f"Código QR oficial para chofer/remisión emitido ({len(qr_data)} bytes base64).")
    else:
        fallo("No se generó el código QR de remisión.")
else:
    fallo(f"Error consultando guía de remisión: {res_guia.text}")

# =============================================================================
# PRUEBA 7: FLUJO ALTERNATIVO 6a - RECEPCIÓN CON DISCREPANCIA / MERMA
# =============================================================================
paso("CP-CU13-07", "Flujo Alternativo 6a: Recepción con Discrepancia/Merma en Transporte")
res_t3 = client.post("/api/v1/traspasos/", json={
    "sucursal_origen_id": suc_origen.id,
    "sucursal_destino_id": suc_destino.id,
    "observacion": "Envío de 5 prendas sujeto a auditoría de arribo",
    "despachar_inmediato": True,
    "detalles": [{"variante_id": var_id, "cantidad": 5}]
})
if res_t3.status_code != 201:
    fallo(f"Error creando traspaso para prueba 7: {res_t3.text}")
t3_id = res_t3.json()["id"]

# Recepcionar con 4 conformes y 1 prenda rota/merma
res_disc = client.post(f"/api/v1/traspasos/{t3_id}/confirmar-recepcion-discrepancia", json={
    "observacion": "Paquete llegó con 1 prenda rota por roce en transporte",
    "recibido_por_ci": "EMP-DESTINO-01",
    "detalles": [{
        "variante_id": var_id,
        "cantidad_recibida_conforme": 4,
        "cantidad_danada_o_merma": 1,
        "motivo_merma": "Prenda rasgada durante el traslado inter-tiendas"
    }]
})
if res_disc.status_code == 200:
    d_data = res_disc.json()
    exito(f"Recepción con discrepancia registrada. Estado: '{d_data['estado']}'")
    exito(f"Observación auditada: '{d_data['observacion']}'")
    
    # Verificar movimiento Kardex de MERMA
    db.expire_all()
    mov_merma = db.query(MovimientoInventario).filter(
        MovimientoInventario.sucursal_id == suc_destino.id,
        MovimientoInventario.tipo_movimiento == "MERMA"
    ).order_by(MovimientoInventario.id.desc()).first()
    if mov_merma and "Discrepancia/Merma" in mov_merma.motivo:
        exito(f"Auditoría Kardex confirmada en PostgreSQL: Movimiento #{mov_merma.id} | Tipo='{mov_merma.tipo_movimiento}' | Cantidad={mov_merma.cantidad}")
    else:
        fallo("No se registró el movimiento de merma en el inventario.")
else:
    fallo(f"Error procesando recepción con discrepancia: {res_disc.text}")

# =============================================================================
# PRUEBA 8: MÉTRICAS LOGÍSTICAS DE TRASPASOS EN VIVO
# =============================================================================
paso("CP-CU13-08", "Consulta de Métricas y KPIs Logísticos de Traspasos")
res_met = client.get("/api/v1/traspasos/metricas")
if res_met.status_code == 200:
    m_data = res_met.json()
    exito(f"Métricas obtenidas: Total Traspasos={m_data['total_traspasos']}, En Tránsito={m_data['en_transito_count']}, Recibidos={m_data['recibidos_count']}, Total Prendas={m_data['total_prendas_trasladadas']}")
    exito(f"Sucursal más activa: '{m_data['sucursal_mas_activa']}'")
else:
    fallo(f"Error obteniendo métricas: {res_met.text}")

db.close()

banner("RESUMEN: CU-13 VERIFICADO AL 100% (TRAZABILIDAD EN 3 ESTADOS + KARDEX AUDITADO)")

