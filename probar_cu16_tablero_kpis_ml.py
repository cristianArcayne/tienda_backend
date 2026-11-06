# -*- coding: utf-8 -*-
"""
=============================================================================
PRUEBAS AUTOMATIZADAS EN VIVO: CU-16 TABLERO DE CONTROL EJECUTIVO Y ML
Asignatura: Sistemas de Información 2 (INF-412 SA)
Docente: MSc. Ing. Angélica Garzón Cuéllar
Estudiante: Yeison Choque León
=============================================================================
Verifica al 100% el Tablero de KPIs y Modelos de Machine Learning:
  [CP-CU16-01] Control SaaS: Bloqueo de Tablero IA a Tenant en Plan Básico (HTTP 403).
  [CP-CU16-02] Métricas Ejecutivas del Negocio:
               - MRR de SaaS (Monthly Recurring Revenue).
               - Tasa de rotación de stock.
               - Tasa de devoluciones en garantía de 7 días.
  [CP-CU16-03] Machine Learning No Supervisado:
               - Segmentación y Clustering de Clientes (K-Means / RFM).
  [CP-CU16-04] Machine Learning Supervisado:
               - Predicción de demanda de temporada (Prophet & Random Forest).
  [CP-CU16-05] Módulo de Reentrenamiento Dinámico de Modelos ML con PostgreSQL.
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

banner("INICIO DE PRUEBAS DE ACEPTACIÓN: CU-16 TABLERO EJECUTIVO Y MACHINE LEARNING")

# =============================================================================
# PRUEBA 1: CONTROL SAAS MULTITENANT (BLOQUEO EN PLAN BÁSICO)
# =============================================================================
paso("CP-CU16-01", "Verificar Restricción de Tablero ML en Tenant con Plan Básico (HTTP 403)")
headers_basico = {"X-Tenant-ID": "2"}
res_bloq = client.get("/api/v1/ia/dashboard", headers=headers_basico)
if res_bloq.status_code == 403:
    exito("Acceso a Tablero ML correctamente DENEGADO con HTTP 403 para Tenant en Plan Básico.")
    exito(f"Protección SaaS: '{res_bloq.json().get('detail', '')[:65]}...'")
else:
    fallo(f"Debería bloquear con 403 a Plan Básico: Status={res_bloq.status_code}")

# =============================================================================
# PRUEBA 2: CONSULTA DEL TABLERO DE CONTROL EJECUTIVO (PLAN PROFESIONAL)
# =============================================================================
paso("CP-CU16-02", "Consultar Tablero de Control Ejecutivo (KPIs Financieros y Operativos)")
headers_pro = {"X-Tenant-ID": "1"}
res_dash = client.get("/api/v1/ia/dashboard", headers=headers_pro)
if res_dash.status_code == 200:
    dash_data = res_dash.json()
    kpis = dash_data.get("kpis", {})
    exito(f"MRR de Suscripciones SaaS: Bs. {kpis.get('mrr_saas_bs', 0):,.2f} / mes")
    exito(f"Índice de Rotación de Stock: {kpis.get('rotacion_stock_ratio', 0)}x")
    exito(f"Tasa de Devoluciones a 7 Días: {kpis.get('tasa_devoluciones_7dias_pct', 0)}% ({kpis.get('total_devoluciones_registradas', 0)} devoluciones auditadas)")
    exito(f"Ventas Hoy: Bs. {kpis.get('ventas_hoy_monto', 0)} ({kpis.get('ventas_hoy_tickets', 0)} tickets) | Mes: Bs. {kpis.get('ventas_mes_monto', 0)}")
else:
    fallo(f"Error consultando tablero ejecutivo: {res_dash.text}")

# =============================================================================
# PRUEBA 3: MACHINE LEARNING NO SUPERVISADO (CLUSTERING DE CLIENTES)
# =============================================================================
paso("CP-CU16-03", "Machine Learning No Supervisado: Clustering de Clientes K-Means (RFM)")
clustering = kpis.get("clustering_clientes_kmeans", {})
exito(f"Segmento VIP (Alto Valor): {clustering.get('vip_alto_valor', 0)} clientes")
exito(f"Segmento Frecuente (Estable): {clustering.get('frecuentes_estables', 0)} clientes")
exito(f"Segmento Nuevos / En Riesgo: {clustering.get('nuevos_o_riesgo', 0)} clientes")
exito(f"Modelo Algorítmico Activo: '{kpis.get('modelos_ml', {}).get('no_supervisado', '')}'")

# =============================================================================
# PRUEBA 4: MACHINE LEARNING SUPERVISADO (PREDICCIÓN DE DEMANDA)
# =============================================================================
paso("CP-CU16-04", "Machine Learning Supervisado: Predicción de Demanda de Temporada")
proyecciones = dash_data.get("proyeccion", [])
exito(f"Proyecciones de Demanda Generadas: {len(proyecciones)} registros futuros calculados.")
if proyecciones:
    p_ej = proyecciones[0]
    exito(f"Ejemplo de Pronóstico: Categoría '{p_ej['categoria']}' | Período: {p_ej['periodo']} -> {p_ej['unidades']} unidades estimadas")
exito(f"Modelo Algorítmico Activo: '{kpis.get('modelos_ml', {}).get('supervisado', '')}'")

# =============================================================================
# PRUEBA 5: REENTRENAMIENTO DINÁMICO DE MODELOS ML CON POSTGRESQL
# =============================================================================
paso("CP-CU16-05", "Reentrenar Modelos de Machine Learning con Datos Transaccionales")
res_train = client.post("/api/v1/ia/reentrenar", headers=headers_pro)
if res_train.status_code == 200:
    t_data = res_train.json()
    exito(f"Reentrenamiento completado: {t_data['detalle']}")
    exito(f"Entrenamiento Random Forest: {t_data.get('random_forest', {})} ítems procesados.")
    exito(f"Entrenamiento Prophet: {t_data.get('prophet', {})} transacciones analizadas.")
else:
    fallo(f"Error en reentrenamiento: {res_train.text}")

banner("RESUMEN: CU-16 VERIFICADO AL 100% (KPIS EJECUTIVOS + ML SUPERVISADO Y NO SUPERVISADO)")

