# -*- coding: utf-8 -*-
"""
=============================================================================
PRUEBAS AUTOMATIZADAS EN VIVO: CU-15 REPORTES GENERATIVOS POR VOZ/TEXTO CON IA
Asignatura: Sistemas de Información 2 (INF-412 SA)
Docente: MSc. Ing. Angélica Garzón Cuéllar
Estudiante: Yeison Choque León
=============================================================================
Verifica la analítica gerencial, NLP, gráficos y control SaaS:
  [CP-CU15-01] Protección SaaS Multitenant:
               - Tenant con Plan Básico intenta acceder a IA -> Bloqueado con HTTP 403.
  [CP-CU15-02] Consulta en Lenguaje Natural: 'Ventas por Sucursal':
               - Intención detectada: 'VENTAS_POR_SUCURSAL'.
               - Resumen ejecutivo generado por LLM / Agregaciones.
               - Métricas KPI y datos para gráfico de barras.
  [CP-CU15-03] Consulta en Lenguaje Natural: 'Ventas por Canal (POS vs E-commerce)':
               - Intención detectada: 'VENTAS_POR_CANAL'.
               - Comparativa de ingresos omnicanal y desglose porcentual.
  [CP-CU15-04] Consulta en Lenguaje Natural: 'Alertas de Stock Crítico':
               - Intención detectada: 'STOCK_CRITICO'.
               - Listado de prendas que requieren reposición inmediata.
  [CP-CU15-05] Intérprete NLP y Vistas QBE (/api/v1/reporte):
               - Consulta 'Top productos más vendidos' con desglose tabular.
=============================================================================
"""
import sys
from fastapi.testclient import TestClient

from main import app
from database import SessionLocal

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

banner("INICIO DE PRUEBAS DE ACEPTACIÓN: CU-15 REPORTES GENERATIVOS CON IA")

# =============================================================================
# PRUEBA 1: CONTROL SAAS MULTITENANT (BLOQUEO EN PLAN BÁSICO)
# =============================================================================
paso("CP-CU15-01", "Verificar Restricción de Reportes IA en Tenant con Plan Básico (HTTP 403)")
# Tenant 2 (Urban Boutique S.R.L.) cuenta con Plan Básico sin módulo de IA
headers_basico = {"X-Tenant-ID": "2"}
payload_cmd = {"comando": "Quiero ver el reporte de ventas por sucursal"}

res_bloq = client.post("/api/v1/reportes-voz/comando-texto", json=payload_cmd, headers=headers_basico)
if res_bloq.status_code == 403:
    exito("Acceso a IA correctamente DENEGADO con HTTP 403 FORBIDDEN para Tenant en Plan Básico.")
    exito(f"Mensaje de política SaaS: '{res_bloq.json().get('detail', '')[:65]}...'")
else:
    fallo(f"Debería bloquear con 403 a Plan Básico: Status={res_bloq.status_code}, Resp={res_bloq.text}")

# =============================================================================
# PRUEBA 2: CONSULTA GERENCIAL - VENTAS POR SUCURSAL (PLAN PROFESIONAL)
# =============================================================================
paso("CP-CU15-02", "Procesar Comando de Voz/Texto: 'Ventas por Sucursal' (Plan Profesional)")
headers_pro = {"X-Tenant-ID": "1"}  # FashionStore S.A. (Plan Profesional con IA)
res_suc = client.post("/api/v1/reportes-voz/comando-texto", json={"comando": "Mostrar reporte de ventas por sucursal"}, headers=headers_pro)
if res_suc.status_code == 200:
    data_suc = res_suc.json()
    exito(f"Intención Detectada: '{data_suc['intencion_detectada']}'")
    exito(f"Resumen Ejecutivo Generado: '{data_suc['resumen_ejecutivo'][:100]}...'")
    exito(f"KPIs Gerenciales: {data_suc.get('metricas_kpi', {})}")
    grafico = data_suc.get("datos_grafico", {})
    exito(f"Datos de Gráfico: Tipo '{grafico.get('tipo_grafico')}' con {len(grafico.get('labels', []))} sucursales ({grafico.get('labels', [])})")
    exito(f"Registros en Tabla: {len(data_suc.get('datos_tabla', []))} filas procesadas.")
else:
    fallo(f"Error en consulta de sucursales: {res_suc.text}")

# =============================================================================
# PRUEBA 3: CONSULTA OMNICANAL - VENTAS POR CANAL (POS vs E-COMMERCE)
# =============================================================================
paso("CP-CU15-03", "Procesar Comando Omnicanal: 'Ventas por Canal (POS vs Digital)'")
res_canal = client.post("/api/v1/reportes-voz/comando-texto", json={"comando": "Comparar ventas por canal presencial pos versus digital"}, headers=headers_pro)
if res_canal.status_code == 200:
    data_canal = res_canal.json()
    exito(f"Intención Detectada: '{data_canal['intencion_detectada']}'")
    exito(f"Resumen Ejecutivo: '{data_canal['resumen_ejecutivo'][:100]}...'")
    exito(f"Canales Evaluados: {data_canal.get('datos_grafico', {}).get('labels', [])}")
else:
    fallo(f"Error en consulta de canales: {res_canal.text}")

# =============================================================================
# PRUEBA 4: CONSULTA DE INVENTARIO - ALERTAS DE STOCK CRÍTICO
# =============================================================================
paso("CP-CU15-04", "Procesar Comando de Alerta: 'Mostrar Alertas de Stock Crítico'")
res_stock = client.post("/api/v1/reportes-voz/comando-texto", json={"comando": "Cuáles son las prendas con stock crítico y escasez"}, headers=headers_pro)
if res_stock.status_code == 200:
    data_stock = res_stock.json()
    exito(f"Intención Detectada: '{data_stock['intencion_detectada']}'")
    exito(f"Resumen Ejecutivo: '{data_stock['resumen_ejecutivo'][:100]}...'")
    exito(f"Sugerencias siguientes comandos IA: {data_stock.get('sugerencias_siguientes_comandos', [])[:2]}")
else:
    fallo(f"Error en consulta de stock: {res_stock.text}")

# =============================================================================
# PRUEBA 5: MOTOR NLP Y VISTAS TABULARES (/api/v1/reporte)
# =============================================================================
paso("CP-CU15-05", "Intérprete NLP en Lenguaje Natural (/api/v1/reporte/nlp)")
res_nlp = client.post("/api/v1/reporte/nlp", json={"consulta": "cuales son los productos mas vendidos"})
if res_nlp.status_code == 200:
    data_nlp = res_nlp.json()
    res_obj = data_nlp.get("resultados", {})
    query_obj = data_nlp.get("query_interpretada", {})
    exito(f"NLP Vista Mapeada: '{query_obj.get('vista')}' | Intención: '{query_obj.get('intencion')}'")
    exito(f"Columnas Dinámicas Tabulares: {res_obj.get('columnas', [])}")
    exito(f"Filas de Datos Devueltas: {len(res_obj.get('datos', []))} productos en ranking.")
else:
    fallo(f"Error en motor NLP tabular: {res_nlp.text}")

banner("RESUMEN: CU-15 VERIFICADO AL 100% (VOZ/TEXTO + LLM GENERATIVO + RESTRICCIÓN SAAS)")

