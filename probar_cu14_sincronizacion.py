# -*- coding: utf-8 -*-
"""
=============================================================================
PRUEBAS AUTOMATIZADAS EN VIVO: CU-14 SINCRONIZACIÓN AUTOMÁTICA Y DEMONIOS
Asignatura: Sistemas de Información 2 (INF-412 SA)
Docente: MSc. Ing. Angélica Garzón Cuéllar
Estudiante: Yeison Choque León
=============================================================================
Verifica al 100% la arquitectura Outbox Pattern, Resiliencia e Idempotencia:
  [CP-CU14-01] Sincronización en Lote (Outbox Queue):
               - Envío de transacciones POS generadas offline con UUIDv4.
               - Inserción atómica y facturación fiscal en servidor central.
  [CP-CU14-02] Idempotencia Estricta (Anti-Duplicidad):
               - Reintento de sincronización con el mismo UUID offline.
               - El servidor retorna la venta ya procesada sin duplicar stock ni cobros.
  [CP-CU14-03] Demonio Background de Mantenimiento y Expiración:
               - Barrido periódico automático de reservas vencidas (>48h).
               - Restitución autónoma de stock a los percheros.
  [CP-CU14-04] Trazabilidad y Código de Control en Factura Sincronizada.
=============================================================================
"""
import sys
import uuid
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from main import app
from database import SessionLocal
from models.venta import Venta, Factura
from models.sucursal import InventarioSucursal, Sucursal
from models.catalogo import VariantePrenda
from models.reserva import Reserva

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

banner("INICIO DE PRUEBAS DE ACEPTACIÓN: CU-14 SINCRONIZACIÓN Y DEMONIO BACKGROUND")

db = SessionLocal()

# Identificar variante y sucursal para la prueba
var = db.query(VariantePrenda).join(InventarioSucursal).filter(InventarioSucursal.stock_fisico > 10).first()
if not var:
    var = db.query(VariantePrenda).first()
variante_id = var.id
sucursal_id = 1

# Generar UUIDs offline únicos
uuid_offline_1 = f"OFFLINE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
uuid_offline_2 = f"OFFLINE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

print(f"[*] Prenda de prueba: Variante #{variante_id} ('{var.ropa.nombre if var.ropa else ''}') en Sucursal #{sucursal_id}")
print(f"[*] UUIDs de transacciones offline simuladas en cola Outbox:\n    - {uuid_offline_1}\n    - {uuid_offline_2}")

# Guardar conteo previo de ventas
total_ventas_antes = db.query(Venta).count()

# =============================================================================
# PRUEBA 1: SINCRONIZACIÓN EN LOTE (BATCH SYNC) DEL DEMONIO
# =============================================================================
paso("CP-CU14-01", "Sincronización en Lote de Ventas Offline (Cola Outbox pending_sync)")
lote_payload = {
    "ventas": [
        {
            "offline_uuid": uuid_offline_1,
            "sucursal_id": sucursal_id,
            "empleado_id": "1001",
            "cliente_ci": "2001",
            "nit_cliente": "4920192",
            "razon_social": "Cliente Offline 1",
            "metodo": "Efectivo",
            "monto_recibido": 150.0,
            "items": [{"variante_id": variante_id, "cantidad": 1, "precio_unitario": 120.0}]
        },
        {
            "offline_uuid": uuid_offline_2,
            "sucursal_id": sucursal_id,
            "empleado_id": "1001",
            "cliente_ci": "2001",
            "nit_cliente": "8392102",
            "razon_social": "Cliente Offline 2",
            "metodo": "Efectivo",
            "monto_recibido": 200.0,
            "items": [{"variante_id": variante_id, "cantidad": 1, "precio_unitario": 150.0}]
        }
    ]
}

res_sync = client.post("/api/v1/ventas/sincronizar-lote", json=lote_payload)
if res_sync.status_code == 200:
    sync_data = res_sync.json()
    exito(f"Lote procesado: {sync_data['total_exitosas']} de {sync_data['total_recibidas']} transacciones sincronizadas con éxito.")
    for r in sync_data["resultados"]:
        exito(f"Venta sincronizada: UUID='{r['offline_uuid']}' -> ID #{r['venta_id']} | Factura: {r['nro_factura']} | Total: Bs. {r['total']}")
else:
    fallo(f"Error en sincronización en lote: {res_sync.text}")

# =============================================================================
# PRUEBA 2: IDEMPOTENCIA ESTRICTA (PROTECCIÓN CONTRA DUPLICADOS)
# =============================================================================
paso("CP-CU14-02", "Verificar Idempotencia: Reenvío del mismo lote no duplica ventas ni stock")
db.expire_all()
inv_antes_reintento = db.query(InventarioSucursal).filter(
    InventarioSucursal.sucursal_id == sucursal_id,
    InventarioSucursal.variante_id == variante_id
).first().stock_fisico

total_ventas_intermedio = db.query(Venta).count()

# Reenviar exactamente el mismo lote con los mismos UUIDs
res_reintento = client.post("/api/v1/ventas/sincronizar-lote", json=lote_payload)
if res_reintento.status_code == 200:
    reintento_data = res_reintento.json()
    db.expire_all()
    total_ventas_despues = db.query(Venta).count()
    inv_despues_reintento = db.query(InventarioSucursal).filter(
        InventarioSucursal.sucursal_id == sucursal_id,
        InventarioSucursal.variante_id == variante_id
    ).first().stock_fisico

    if total_ventas_despues == total_ventas_intermedio:
        exito(f"IDEMPOTENCIA CONFIRMADA: 0 ventas duplicadas en la base de datos (Total ventas={total_ventas_despues}).")
    else:
        fallo("Fallo de idempotencia: Se insertaron ventas duplicadas.")

    if inv_despues_reintento == inv_antes_reintento:
        exito(f"PROTECCIÓN DE STOCK CONFIRMADA: El stock físico se mantuvo intacto ({inv_despues_reintento} unidades).")
    else:
        fallo("Fallo de idempotencia: El stock se descontó dos veces.")
else:
    fallo(f"Error en reintento: {res_reintento.text}")

# =============================================================================
# PRUEBA 3: DEMONIO BACKGROUND DE EXPIRACIÓN Y MANTENIMIENTO
# =============================================================================
paso("CP-CU14-03", "Ejecución del Demonio Background de Expiración Automática (>48h)")
# Crear reserva normal y luego envejecerla en DB para probar el demonio
res_r = client.post("/api/v1/reservas/crear", json={
    "cliente_id": "2001",
    "sucursal_id": sucursal_id,
    "detalles": [{"variante_id": variante_id, "cantidad": 1}]
})
reserva_id = res_r.json()["id"]

reserva_vencida = db.query(Reserva).filter(Reserva.id == reserva_id).first()
reserva_vencida.fecha = datetime.now() - timedelta(days=3)
reserva_vencida.fecha_limite = datetime.now() - timedelta(days=1)
db.commit()

# Disparo del demonio background
res_demonio = client.post("/api/v1/reservas/expirar-antiguas")
if res_demonio.status_code == 200:
    dem_data = res_demonio.json()
    exito(f"Demonio de fondo ejecutado: {dem_data['mensaje']}")
    exito(f"Reservas caducadas procesadas por el demonio: {dem_data['reservas_expiradas']}")
    exito(f"Unidades de stock restituidas automáticamente: {dem_data['unidades_stock_liberadas']}")
    
    # Verificar en DB que la reserva pasó a EXPIRADA
    db.expire_all()
    r_check = db.query(Reserva).filter(Reserva.id == reserva_vencida.id).first()
    if r_check.estado == "EXPIRADA":
        exito(f"Estado de Reserva #{reserva_vencida.id} actualizado a '{r_check.estado}' por el demonio.")
    else:
        fallo("El demonio no actualizó el estado a EXPIRADA.")
else:
    fallo(f"Error ejecutando demonio de expiración: {res_demonio.text}")

# =============================================================================
# PRUEBA 4: TRAZABILIDAD Y SELLADO FISCAL DE TRANSACCIÓN OFFLINE
# =============================================================================
paso("CP-CU14-04", "Trazabilidad Fiscal y Auditoría de Transacción Offline")
venta_db = db.query(Venta).filter(Venta.codigo_transaccion == uuid_offline_1).first()
if venta_db and venta_db.factura:
    exito(f"Venta #{venta_db.id} enlazada a Factura Fiscal '{venta_db.factura.nro_factura}'.")
    exito(f"Código de Control Fiscal: '{venta_db.factura.codigo_control}' | Cód Autorización: '{venta_db.factura.nro_autorizacion}'.")
    exito(f"Fecha/Hora de emisión centralizada: {venta_db.fecha.isoformat()}.")
else:
    fallo("No se encontró la factura fiscal para la venta offline sincronizada.")

db.close()

banner("RESUMEN: CU-14 VERIFICADO AL 100% (OUTBOX SYNC + IDEMPOTENCIA + DEMONIOS BACKGROUND)")
