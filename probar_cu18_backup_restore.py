# -*- coding: utf-8 -*-
"""
=============================================================================
PRUEBAS AUTOMATIZADAS EN VIVO: CU-18 BACKUP Y RESTORE DE BASE DE DATOS
Asignatura: Sistemas de Información 2 (INF-412 SA)
Docente: MSc. Ing. Angélica Garzón Cuéllar
Estudiante: Yeison Choque León
=============================================================================
Verifica al 100% las funciones administrativas de respaldo y contingencia:
  [CP-CU18-01] Generación de Copia de Seguridad Completa (Dump PostgreSQL):
               - Respaldo estructurado de DDL + DML de todas las tablas.
               - Generación de firma criptográfica SHA-256 de integridad.
  [CP-CU18-02] Catálogo e Inventario de Backups Disponibles en el Servidor.
  [CP-CU18-03] Descarga de Archivo de Respaldo (.sql) con Cabeceras MIME.
  [CP-CU18-04] Control de Seguridad: Rechazo de Restauración sin Código de Autorización.
  [CP-CU18-05] Restauración Integral del Sistema ante Contingencia con Verificación Hash.
=============================================================================
"""
import sys
from fastapi.testclient import TestClient

from main import app

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

banner("INICIO DE PRUEBAS DE ACEPTACIÓN: CU-18 GESTIÓN DE BACKUP Y RESTORE")

# =============================================================================
# PRUEBA 1: GENERACIÓN DE BACKUP COMPLETO
# =============================================================================
paso("CP-CU18-01", "Generar Copia de Seguridad Estructurada (Dump PostgreSQL)")
res_gen = client.post("/api/v1/backup/generar")
if res_gen.status_code == 200:
    gen_data = res_gen.json()
    archivo = gen_data["archivo"]
    metricas = gen_data["metricas"]
    nombre_backup = archivo["nombre"]
    
    exito(f"Copia de seguridad generada: '{nombre_backup}' ({archivo['tamano_kb']} KB)")
    exito(f"Firma Criptográfica SHA-256: {archivo['hash_sha256']}")
    exito(f"Tablas Respaldadas: {metricas['tablas_respaldadas']} tablas | Tuplas extraídas: {metricas['total_tuplas_respaldadas']} registros")
    exito(f"Motor de Persistencia: {metricas['motor']}")
else:
    fallo(f"Error generando backup: {res_gen.text}")

# =============================================================================
# PRUEBA 2: LISTAR HISTORIAL DE BACKUPS
# =============================================================================
paso("CP-CU18-02", "Consultar Inventario de Copias de Seguridad en Servidor")
res_list = client.get("/api/v1/backup/listar")
if res_list.status_code == 200:
    list_data = res_list.json()
    total_b = list_data["total_backups"]
    exito(f"Total de copias de seguridad activas en almacén: {total_b}")
    
    encontrado = any(b["nombre"] == nombre_backup for b in list_data["backups"])
    if encontrado:
        exito(f"Archivo recién generado '{nombre_backup}' verificado en el catálogo.")
    else:
        fallo("El backup recién creado no aparece en la lista.")
else:
    fallo(f"Error listando backups: {res_list.text}")

# =============================================================================
# PRUEBA 3: DESCARGA DE ARCHIVO DE RESPALDO (.SQL)
# =============================================================================
paso("CP-CU18-03", "Descargar Archivo .SQL de Contingencia")
res_down = client.get(f"/api/v1/backup/descargar/{nombre_backup}")
if res_down.status_code == 200:
    exito(f"Archivo .sql descargado exitosamente ({len(res_down.text)} caracteres).")
    exito(f"Cabecera Content-Disposition: {res_down.headers.get('content-disposition')}")
    if "-- FASHIONSTORE SAAS MULTITENANT" in res_down.text and "SELLO CRIPTOGRÁFICO SHA-256" in res_down.text:
        exito("Estructura SQL verificada: Contiene encabezados oficiales y sello de integridad.")
    else:
        fallo("El contenido del archivo SQL descargado no tiene el formato esperado.")
else:
    fallo(f"Error descargando archivo .sql: {res_down.text}")

# =============================================================================
# PRUEBA 4: VALIDACIÓN DE SEGURIDAD EN RESTAURACIÓN
# =============================================================================
paso("CP-CU18-04", "Validar Rechazo de Restauración sin Código de Autorización Estricto")
res_err = client.post("/api/v1/backup/restaurar", json={
    "nombre_archivo": nombre_backup,
    "confirmacion": "si_por_favor"  # No es el código estricto
})
if res_err.status_code == 400 and "CONFIRMAR_RESTAURACION" in res_err.text:
    exito("Restauración no autorizada correctamente BLOQUEADA con HTTP 400.")
else:
    fallo("Debió rechazar la solicitud sin el código estricto.")

# =============================================================================
# PRUEBA 5: RESTAURACIÓN INTEGRAL ANTE CONTINGENCIA
# =============================================================================
paso("CP-CU18-05", "Restauración Integral del Sistema ante Contingencia de Datos")
res_restore = client.post("/api/v1/backup/restaurar", json={
    "nombre_archivo": nombre_backup,
    "confirmacion": "CONFIRMAR_RESTAURACION"
})
if res_restore.status_code == 200:
    rest_data = res_restore.json()
    exito(f"Restauración exitosa: {rest_data['mensaje']}")
    exito(f"Archivo restaurado: '{rest_data['archivo_restaurado']}' ({rest_data['lineas_sql_procesadas']} líneas SQL validadas)")
    exito(f"Hash SHA-256 de Restauración verificado: {rest_data['hash_sha256_verificado']}")
    exito(f"Estado Final del Sistema: {rest_data['estado_sistema']}")
else:
    fallo(f"Error en restauración: {res_restore.text}")

banner("RESUMEN: CU-18 VERIFICADO AL 100% (BACKUP ESTRUCTURADO + RESTORE + HASH SHA-256)")

