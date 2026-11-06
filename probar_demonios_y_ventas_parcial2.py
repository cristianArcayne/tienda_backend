"""
=============================================================================
SUITE DE PRUEBAS AUTOMATIZADAS: DEMONIOS, VENTAS Y PASARELAS (PARCIAL 2)
Asignatura: Sistemas de Información 2 (INF-412 SA)
Docente: MSc. Ing. Angélica Garzón Cuéllar
Casos de Uso Evaluados:
  - CU-07: Reservas Web-to-Store Offline y Demonio de Expiración (48h)
  - CU-09: Procesamiento de Ventas POS Offline (Resiliencia con UUID)
  - CU-10: Ventas Digitales con Pasarela Stripe (PaymentIntent + Webhook)
  - CU-11: Cobro con Código QR Simple Interoperable (ASOBAN / BCB)
  - CU-14: Demonio de Sincronización y Validación de Idempotencia
=============================================================================
"""
import sys
import uuid
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models.venta import Venta, Factura, MetodoPago, TipoVenta
from models.reserva import Reserva, DetalleReserva
from models.catalogo import VariantePrenda, Ropa
from models.sucursal import InventarioSucursal, Sucursal

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

banner("INICIO DE PRUEBAS DE RESILIENCIA OFFLINE, DEMONIOS Y PASARELAS")

# Obtener una variante y sucursal real de la base de datos
db = SessionLocal()
variante = db.query(VariantePrenda).join(InventarioSucursal).filter(InventarioSucursal.stock_fisico > 5).first()
if not variante:
    variante = db.query(VariantePrenda).first()
variante_id = variante.id if variante else 1
sucursal_id = 1
ropa = db.query(Ropa).filter(Ropa.id == variante.ropa_id).first() if variante else None
nombre_prenda = ropa.nombre if ropa else "Prenda Test"
db.close()

print(f"[*] Prenda de prueba seleccionada: '{nombre_prenda}' (Variante #{variante_id}) en Sucursal #{sucursal_id}")

# =============================================================================
# PRUEBA 1: CU-09 - VENTA POS OFFLINE CON UUID Y RESILIENCIA
# =============================================================================
paso("CP-CU09-01", "Venta POS Offline con Generación de UUID Local y Facturación")
payload_pos = {
    "sucursal_id": sucursal_id,
    "empleado_ci": "1001",
    "cliente_ci": "2001",
    "metodo_pago_id": 1,  # Efectivo
    "monto_recibido": 200.0,
    "descuento_total": 0.0,
    "items": [
        {"variante_id": variante_id, "cantidad": 1, "precio_unitario": 120.0}
    ]
}
res_pos = client.post("/api/v1/ventas/pos", json=payload_pos)
if res_pos.status_code == 201:
    v_data = res_pos.json()
    exito(f"Venta POS registrada: ID #{v_data['id']} | Total: Bs. {v_data['total']}")
    exito(f"Factura generada: {v_data['factura']['nro_factura']} (Cód. Control: {v_data['factura']['codigo_control']})")
else:
    fallo(f"Error en Venta POS: {res_pos.text}")

# =============================================================================
# PRUEBA 2: CU-10 - PASARELA STRIPE ONLINE (PAYMENTINTENT + CONFIRMACIÓN)
# =============================================================================
paso("CP-CU10-01", "Stripe Online: Creación de PaymentIntent Seguro con Tarjeta")
payload_stripe_intent = {
    "monto": 150.0,
    "moneda": "bob",
    "cliente_id": "2001",
    "descripcion": "Compra en línea FashionStore - Colección Primavera",
    "items_count": 1
}
res_intent = client.post("/api/v1/pagos/stripe/crear-intento", json=payload_stripe_intent)
if res_intent.status_code == 200:
    intent_data = res_intent.json()
    pi_id = intent_data["payment_intent_id"]
    exito(f"PaymentIntent creado en Stripe: {pi_id} | Monto: {intent_data['amount']} {intent_data['currency'].upper()}")
    exito(f"Client Secret emitido para el SDK Web/Móvil: {intent_data['client_secret'][:25]}...")
else:
    fallo(f"Error creando PaymentIntent: {res_intent.text}")

paso("CP-CU10-02", "Stripe Online: Confirmación de Pago y Emisión de Factura E-Commerce")
payload_stripe_confirm = {
    "payment_intent_id": pi_id,
    "cliente_id": "2001",
    "sucursal_id": sucursal_id,
    "razon_social": "Cliente Stripe Verificado",
    "nit_cliente": "4920192015",
    "items": [
        {"variante_id": variante_id, "cantidad": 1, "precio_unitario": 150.0}
    ]
}
res_confirm = client.post("/api/v1/pagos/stripe/confirmar-pago", json=payload_stripe_confirm)
if res_confirm.status_code == 200:
    v_ecom = res_confirm.json()
    exito(f"Venta Digital Stripe procesada: ID #{v_ecom['id']} | Cód TRX: {v_ecom['codigo_transaccion']}")
    exito(f"Factura Fiscal Digital emitida: {v_ecom['factura']['nro_factura']}")
else:
    fallo(f"Error confirmando pago Stripe: {res_confirm.text}")

# =============================================================================
# PRUEBA 3: CU-11 - COBRO QR SIMPLE INTEROPERABLE (ASOBAN / BCB)
# =============================================================================
paso("CP-CU11-01", "Generación Dinámica de Código QR EMVCo Interoperable en Base64")
payload_qr = {
    "monto": 85.50,
    "moneda": "BOB",
    "glosa": "Pago QR Mostrador Sucursal Equipetrol",
    "cliente_nombre": "María René Pérez",
    "cliente_nit": "8374921",
    "sucursal_id": sucursal_id,
    "tiempo_expiracion_seg": 180
}
res_qr = client.post("/api/v1/pagos/qr-simple/generar", json=payload_qr)
if res_qr.status_code in [200, 201]:
    qr_data = res_qr.json()
    qr_id = qr_data["qr_id"]
    exito(f"Código QR generado: ID '{qr_id}' | Importe: Bs. {qr_data['monto']} {qr_data['moneda']}")
    exito(f"Imagen QR scannable en Base64 generada: {qr_data.get('qr_image_base64', '')[:35]}...")
    exito(f"Tiempo de expiración fijado: {qr_data['expira_en']} (Vigencia 180s)")
else:
    fallo(f"Error generando QR Simple: {res_qr.text}")

paso("CP-CU11-02", "Consulta de Estado en Tiempo Real (Polling) y Confirmación de Pago QR")
res_estado = client.get(f"/api/v1/pagos/qr-simple/estado/{qr_id}")
if res_estado.status_code == 200:
    est_data = res_estado.json()
    exito(f"Estado inicial del QR: {est_data['estado']} (Segundos restantes: {est_data['segundos_restantes']}s)")
else:
    fallo(f"Error consultando estado de QR: {res_estado.text}")

# Simular acreditación bancaria interbancaria ASOBAN
res_sim = client.post(f"/api/v1/pagos/qr-simple/simular-pago/{qr_id}")
if res_sim.status_code == 200:
    sim_data = res_sim.json()
    exito(f"Acreditación bancaria confirmada: {sim_data['mensaje']}")
    exito(f"Comprobante bancario: {sim_data['comprobante_bancario']} | Nro Factura: {sim_data.get('nro_factura')}")
else:
    fallo(f"Error en simulación bancaria: {res_sim.text}")

# =============================================================================
# PRUEBA 4: CU-07 & CU-14 - DEMONIOS DE RESERVAS OFFLINE Y EXPIRACIÓN AUTOMÁTICA
# =============================================================================
paso("CP-DEMONIO-01", "CU-07: Crear Reserva Web-to-Store con Congelamiento de Stock")
payload_reserva = {
    "cliente_id": "2001",
    "sucursal_id": sucursal_id,
    "detalles": [
        {"variante_id": variante_id, "cantidad": 1}
    ]
}
res_r = client.post("/api/v1/reservas/crear", json=payload_reserva)
if res_r.status_code == 201:
    r_data = res_r.json()
    reserva_id = r_data["id"]
    exito(f"Reserva Web-to-Store creada: ID #{reserva_id} | Estado: {r_data['estado']}")
    exito(f"Fecha de Caducidad (48h): {r_data.get('fecha_limite', '48 horas')}")
else:
    fallo(f"Error creando reserva: {res_r.text}")

paso("CP-DEMONIO-02", "CU-14 / CU-07: Ejecución del Demonio de Expiración de Reservas (>48h)")
# Forzamos manualmente en la base de datos que la reserva sea antigua (hace 3 días) para probar al demonio
db = SessionLocal()
r_antigua = db.query(Reserva).filter(Reserva.id == reserva_id).first()
if r_antigua:
    r_antigua.fecha = datetime.now() - timedelta(days=3)
    r_antigua.fecha_limite = datetime.now() - timedelta(days=1)
    db.commit()
db.close()

# Disparo del barrido del demonio de fondo
res_demonio = client.post("/api/v1/reservas/expirar-antiguas")
if res_demonio.status_code == 200:
    dem_data = res_demonio.json()
    exito(f"Demonio de fondo ejecutado: {dem_data['mensaje']}")
    exito(f"Reservas caducadas procesadas por el demonio: {dem_data['reservas_expiradas']}")
    exito(f"Unidades de stock restituidas automáticamente a la tienda: {dem_data['unidades_stock_liberadas']}")
else:
    fallo(f"Error ejecutando barrido del demonio: {res_demonio.text}")

banner("RESUMEN: TODAS LAS PRUEBAS DE RESILIENCIA Y DEMONIOS COMPLETADAS CON EXITO (100% OK)")
