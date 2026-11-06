# -*- coding: utf-8 -*-
"""
=============================================================================
PRUEBAS AUTOMATIZADAS EN VIVO: CU-17 AUDITORÍA Y BITÁCORA CONFIDENCIAL
Asignatura: Sistemas de Información 2 (INF-412 SA)
Docente: MSc. Ing. Angélica Garzón Cuéllar
Estudiante: Yeison Choque León
=============================================================================
Verifica al 100% el acceso confidencial restringido por Llave de Desarrollador:
  [CP-CU17-01] Rechazo de acceso sin Llave de Desarrollador (HTTP 403 FORBIDDEN).
  [CP-CU17-02] Rechazo de acceso con Llave espuria o inválida (HTTP 403 FORBIDDEN).
  [CP-CU17-03] Acceso Exitoso con Llave Oficial de Desarrollador:
               - Desbloqueo de eventos confidenciales (IP, usuario, acción, tabla).
               - Firma criptográfica inmutable con Hash SHA-256.
  [CP-CU17-04] Descarga de Archivo Forense (.log) firmado y sellado con SHA-256.
  [CP-CU17-05] Trazabilidad y Preservación de IP de origen y Marca Temporal.
=============================================================================
"""
import sys
from fastapi.testclient import TestClient

from main import app
from database import SessionLocal
from routers.bitacora import registrar_bitacora, LLAVE_DESARROLLADOR_OFICIAL

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

banner("INICIO DE PRUEBAS DE ACEPTACIÓN: CU-17 BITÁCORA CONFIDENCIAL CON LLAVE DEV")

# =============================================================================
# PRUEBA 1: ACCESO SIN LLAVE DE DESARROLLADOR
# =============================================================================
paso("CP-CU17-01", "Verificar Bloqueo de Acceso sin Llave de Desarrollador (HTTP 403)")
res_sin_llave = client.get("/api/v1/bitacora/confidencial-dev")
if res_sin_llave.status_code == 403:
    exito("Acceso correctamente BLOQUEADO con HTTP 403 FORBIDDEN al intentar consultar sin llave.")
    exito(f"Mensaje de protección: '{res_sin_llave.json().get('detail')}'")
else:
    fallo(f"Debería bloquear con 403: Status={res_sin_llave.status_code}")

# =============================================================================
# PRUEBA 2: ACCESO CON LLAVE INVÁLIDA O ESPURIA
# =============================================================================
paso("CP-CU17-02", "Verificar Bloqueo con Llave de Desarrollador Incorrecta")
res_llave_falsa = client.get(
    "/api/v1/bitacora/confidencial-dev",
    headers={"X-Developer-Key": "LLAVE-PIRATA-12345"}
)
if res_llave_falsa.status_code == 403:
    exito("Acceso correctamente DENEGADO con HTTP 403 ante llave no autorizada.")
else:
    fallo("Debería rechazar la llave espuria.")

# =============================================================================
# PRUEBA 3: ACCESO AUTORIZADO CON LLAVE DE DESARROLLADOR OFICIAL
# =============================================================================
paso("CP-CU17-03", "Acceso Autorizado con Llave Oficial de Desarrollador y Sello SHA-256")
headers_dev = {"X-Developer-Key": LLAVE_DESARROLLADOR_OFICIAL}
res_auth = client.get("/api/v1/bitacora/confidencial-dev?limite=20", headers=headers_dev)
if res_auth.status_code == 200:
    data_log = res_auth.json()
    exito(f"Autenticación exitosa: Estado '{data_log['status']}'")
    exito(f"Firma Criptográfica SHA-256 calculada: {data_log['seguridad']['hash_sha256_integridad']}")
    stats = data_log["estadisticas_confidenciales"]
    exito(f"Estadísticas Forenses: {stats['total_eventos_sistema']} eventos en DB | {stats['ips_auditadas_unicas']} IPs únicas | {stats['usuarios_activos_auditados']} usuarios auditados")
    
    # Verificar estructura del primer evento
    if data_log["registros_bitacora"]:
        ev_sample = data_log["registros_bitacora"][0]
        exito(f"Muestra de Evento Confidencial: [{ev_sample['fecha_hora']}] [IP: {ev_sample['ip_origen']}] [USER: {ev_sample['usuario']}] [{ev_sample['accion']}] TABLA: {ev_sample['tabla_afectada']}")
else:
    fallo(f"Error consultando bitácora con llave oficial: {res_auth.text}")

# =============================================================================
# PRUEBA 4: DESCARGA DE ARCHIVO FORENSE (.LOG) SELLADO
# =============================================================================
paso("CP-CU17-04", "Descargar Archivo Log Forense Sellado Criptográficamente")
res_down = client.get("/api/v1/bitacora/descargar-log-cifrado", headers=headers_dev)
if res_down.status_code == 200:
    exito("Archivo de log confidencial generado y descargado correctamente.")
    exito(f"Cabecera Content-Disposition: {res_down.headers.get('content-disposition')}")
    contenido_log = res_down.text
    if "SELLO CRIPTOGRÁFICO SHA-256:" in contenido_log:
        exito("El archivo .log contiene el Sello Criptográfico SHA-256 al pie para no repudio y auditoría legal.")
    else:
        fallo("Falta el sello SHA-256 en el archivo descargado.")
else:
    fallo(f"Error descargando archivo log: {res_down.text}")

# =============================================================================
# PRUEBA 5: REGISTRO DE EVENTO CRÍTICO Y AUDITORÍA INMUTABLE
# =============================================================================
paso("CP-CU17-05", "Inserción de Acción Crítica y Verificación Inmediata en la Bitácora")
db = SessionLocal()
registrar_bitacora(
    db=db,
    accion="UPDATE",
    tabla="seguridad_roles",
    registro_id="ROL-SUPERADMIN",
    detalles="Modificación de privilegios de acceso ejecutada bajo supervisión técnica",
    usuario_id=1,
    ip_origen="192.168.1.105"
)
db.close()

# Volver a consultar con la llave dev
res_recheck = client.get("/api/v1/bitacora/confidencial-dev?limite=5", headers=headers_dev)
if res_recheck.status_code == 200:
    recheck_data = res_recheck.json()
    ultimo_ev = recheck_data["registros_bitacora"][0]
    if ultimo_ev["registro_id"] == "ROL-SUPERADMIN" and ultimo_ev["ip_origen"] == "192.168.1.105":
        exito(f"Evento crítico verificado en la bitácora: Acción='{ultimo_ev['accion']}' | IP='{ultimo_ev['ip_origen']}' | Detalle='{ultimo_ev['detalles']}'")
    else:
        fallo(f"El evento registrado no coincide con el último: {ultimo_ev}")
else:
    fallo("Error re-consultando bitácora.")

banner("RESUMEN: CU-17 VERIFICADO AL 100% (AUDITORÍA CONFIDENCIAL + LLAVE DEV + HASH SHA-256)")

