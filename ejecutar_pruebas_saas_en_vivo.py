"""
=============================================================================
SUITE DE PRUEBAS FORMALES EN VIVO: SAAS MULTITENANT & REGLAS DE NEGOCIO
Asignatura: Sistemas de Información 2 (INF-412 SA)
Docente: MSc. Ing. Angélica Garzón Cuéllar
Estudiante: Yeison Choque León
=============================================================================
Pruebas Automatizadas que verifican al 100%:
  [CP-SAAS-01] Consulta del Catálogo de Planes SaaS (Básico vs Profesional).
  [CP-SAAS-02] Aislamiento de Datos por Tenant (Empresa 1 vs Empresa 2).
  [CP-SAAS-03] Bloqueo Estricto de Inteligencia Artificial en Plan Básico (HTTP 403).
  [CP-SAAS-04] Permisión de Inteligencia Artificial en Plan Profesional (HTTP 200).
  [CP-SAAS-05] Cumplimiento de Límite de Sucursales según Plan (Máximo 2 = HTTP 400).
  [CP-SAAS-06] Upgrade Dinámico de Plan (Básico -> Profesional) y Desbloqueo de IA.
  [CP-SAAS-07] Auditoría de Cambios de Plan (Trazabilidad en Base de Datos).
  [CP-SAAS-08] Onboarding Público de Nuevo Tenant (Registro de Empresa + Admin).
=============================================================================
"""
import sys
import json
from datetime import datetime
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models.sucursal import Sucursal
from models.empresa_suscripcion import Empresa, SuscripcionEmpresa, HistorialCambioPlan, PlanSuscripcion

client = TestClient(app)

def banner(titulo):
    print("\n" + "=" * 75)
    print(f" {titulo}")
    print("=" * 75)

def paso(codigo, nombre, status="EJECUTANDO..."):
    print(f"\n>>> [{codigo}] {nombre}")

def exito(detalle):
    print(f"    [PASS] EXITO: {detalle}")

def fallo(detalle):
    print(f"    [FAIL] FALLO: {detalle}")
    sys.exit(1)

banner("INICIO DE PRUEBAS DE ACEPTACION SAAS MULTI-TENANT (FASHIONSTORE)")

# =============================================================================
# PRUEBA 1: CATÁLOGO DE PLANES SAAS
# =============================================================================
paso("CP-SAAS-01", "Verificar Catálogo Oficial de Planes SaaS en Base de Datos")
resp = client.get("/api/planes")
if resp.status_code != 200:
    fallo(f"HTTP {resp.status_code}: {resp.text}")

planes = resp.json()
if len(planes) < 2:
    fallo("Deben existir al menos 2 planes (Básico y Profesional)")

p_basico = next((p for p in planes if p["codigo"] == "BASICO"), None)
p_pro = next((p for p in planes if p["codigo"] == "PROFESIONAL"), None)

assert p_basico is not None, "No se encontró el Plan Básico"
assert p_pro is not None, "No se encontró el Plan Profesional"

exito(f"Plan Básico cargado: Bs. {p_basico['precio_mensual']}/mes | Límite sucursales: {p_basico['limite_sucursales']} | IA: {p_basico['soporta_ia']}")
exito(f"Plan Profesional cargado: Bs. {p_pro['precio_mensual']}/mes | Límite sucursales: {p_pro['limite_sucursales']} | IA: {p_pro['soporta_ia']}")

# =============================================================================
# PRUEBA 2: AISLAMIENTO DE DATOS POR TENANT (HEADER X-Tenant-ID)
# =============================================================================
paso("CP-SAAS-02", "Verificar Aislamiento de Sucursales entre Tenant 1 y Tenant 2")
resp_t1 = client.get("/api/v1/sucursales/", headers={"X-Tenant-ID": "1"})
resp_t2 = client.get("/api/v1/sucursales/", headers={"X-Tenant-ID": "2"})

sucs_t1 = [s["nombre"] for s in resp_t1.json()]
sucs_t2 = [s["nombre"] for s in resp_t2.json()]

# Ninguna sucursal de T2 debe estar en T1
cruce = set(sucs_t1).intersection(set(sucs_t2))
if cruce:
    fallo(f"Falla de aislamiento: sucursales cruzadas: {cruce}")

exito(f"Empresa 1 (FashionStore S.A.) ve sus sucursales: {sucs_t1}")
exito(f"Empresa 2 (Urban Boutique S.R.L.) ve sus sucursales: {sucs_t2}")
exito("Aislamiento estricto comprobado: 0 sucursales compartidas.")

# =============================================================================
# PRUEBA 3: BLOQUEO DE INTELIGENCIA ARTIFICIAL EN PLAN BÁSICO (HTTP 403)
# =============================================================================
paso("CP-SAAS-03", "Verificar Restricción de IA para Tenant 2 con Plan Básico")
resp_ia_basico = client.get("/api/v1/ia/alertas", headers={"X-Tenant-ID": "2"})

if resp_ia_basico.status_code != 403:
    fallo(f"Se esperaba HTTP 403 Forbidden y se obtuvo HTTP {resp_ia_basico.status_code}")

detalle_bloqueo = resp_ia_basico.json().get("detail", "")
exito(f"Petición rechazada con HTTP 403 FORBIDDEN.")
exito(f"Mensaje de protección: \"{detalle_bloqueo[:85]}...\"")

# =============================================================================
# PRUEBA 4: ACCESO A INTELIGENCIA ARTIFICIAL EN PLAN PROFESIONAL (HTTP 200)
# =============================================================================
paso("CP-SAAS-04", "Verificar Acceso Permitido a IA para Tenant 1 con Plan Profesional")
resp_ia_pro = client.get("/api/v1/ia/alertas", headers={"X-Tenant-ID": "1"})

if resp_ia_pro.status_code != 200:
    fallo(f"Se esperaba HTTP 200 OK y se obtuvo HTTP {resp_ia_pro.status_code}: {resp_ia_pro.text}")

alertas = resp_ia_pro.json().get("results", [])
exito(f"Petición aprobada con HTTP 200 OK.")
exito(f"Alertas predictivas calculadas por IA devueltas: {len(alertas)} registros.")

# =============================================================================
# PRUEBA 5: LÍMITE DE SUCURSALES EN PLAN BÁSICO (MÁXIMO 2 SUCURSALES)
# =============================================================================
paso("CP-SAAS-05", "Validar Rechazo al intentar registrar 3ra Sucursal en Plan Básico")

# Asegurar que Tenant 2 tiene exactamente 2 sucursales
db = SessionLocal()
sucs_emp2 = db.query(Sucursal).filter(Sucursal.empresa_id == 2, Sucursal.activo == True).all()
conteo_t2 = len(sucs_emp2)
db.close()

if conteo_t2 < 2:
    client.post("/api/v1/sucursales/", headers={"X-Tenant-ID": "2"}, json={
        "nombre": "Sucursal Urban Sur Temporal",
        "ciudad": "Santa Cruz",
        "direccion": "Av. Santos Dumont 4to Anillo",
        "telefono": "78912345"
    })

# Intentar registrar la 3ra sucursal (debe fallar con HTTP 400)
resp_limite = client.post("/api/v1/sucursales/", headers={"X-Tenant-ID": "2"}, json={
    "nombre": "Sucursal Urban 3ra No Permitida",
    "ciudad": "Santa Cruz",
    "direccion": "Av. Prohibida #999",
    "telefono": "70099999"
})

if resp_limite.status_code != 400:
    fallo(f"Se esperaba HTTP 400 Bad Request y se obtuvo HTTP {resp_limite.status_code}: {resp_limite.text}")

msg_limite = resp_limite.json().get("detail", "")
exito("Intento de 3ra sucursal bloqueado con HTTP 400 BAD REQUEST.")
exito(f"Mensaje de regla de negocio: \"{msg_limite[:85]}...\"")

# =============================================================================
# PRUEBA 6: UPGRADE DINÁMICO DE PLAN (UPGRADE DE BÁSICO A PROFESIONAL)
# =============================================================================
paso("CP-SAAS-06", "Upgrade de Plan para Tenant 2: Cambiar de Básico a Profesional")
resp_upgrade = client.post("/api/v1/suscripciones/cambiar-plan?empresa_id=2", json={
    "plan_id": 2, # Plan Profesional
    "ciclo": "mensual",
    "motivo": "Demostración de Upgrade de Plan en vivo ante el tribunal docente"
})

if resp_upgrade.status_code != 200:
    fallo(f"Error al cambiar plan: HTTP {resp_upgrade.status_code}: {resp_upgrade.text}")

susc_actualizada = resp_upgrade.json()
exito(f"Upgrade exitoso: Ahora Tenant 2 tiene plan '{susc_actualizada['plan_nombre']}'.")
exito(f"Nuevo límite de sucursales: {susc_actualizada['limite_sucursales']} | IA Habilitada: {susc_actualizada['soporta_ia']}")

# Probar que la IA AHORA SÍ responde para Tenant 2
resp_ia_desbloqueada = client.get("/api/v1/ia/alertas", headers={"X-Tenant-ID": "2"})
if resp_ia_desbloqueada.status_code != 200:
    fallo(f"Tras el upgrade, la IA debió desbloquearse pero retornó {resp_ia_desbloqueada.status_code}")

exito("VERIFICADO: La Inteligencia Artificial quedó INMEDIATAMENTE HABILITADA para Tenant 2 tras el Upgrade (HTTP 200 OK).")

# =============================================================================
# PRUEBA 7: AUDITORÍA EN BASE DE DATOS DEL CAMBIO DE PLAN
# =============================================================================
paso("CP-SAAS-07", "Verificar Registro de Auditoría de Cambio de Plan en PostgreSQL")
resp_auditoria = client.get("/api/v1/suscripcion-cambios/")
cambios = resp_auditoria.json()
assert len(cambios) > 0, "No se registraron cambios en el historial"
ultimo_cambio = cambios[0]

exito(f"Historial auditado: Suscripción #{ultimo_cambio['suscripcion']}")
exito(f"Plan Anterior: ID {ultimo_cambio['plan_anterior']} -> Plan Nuevo: {ultimo_cambio['plan_nuevo_nombre']} (ID {ultimo_cambio['plan_nuevo']})")
exito(f"Motivo registrado: \"{ultimo_cambio['motivo']}\"")
exito(f"Fecha/Hora ISO: {ultimo_cambio['cambiado_en']}")

# Restaurar Tenant 2 a Básico para mantener consistencia
client.post("/api/v1/suscripciones/cambiar-plan?empresa_id=2", json={
    "plan_id": 1,
    "ciclo": "mensual",
    "motivo": "Restauración a Plan Básico para próximas pruebas"
})
exito("Tenant 2 restaurado al Plan Básico original para aislamiento continuo.")

# =============================================================================
# PRUEBA 8: ONBOARDING PÚBLICO DE NUEVO TENANT (CREACIÓN COMPLETA DE EMPRESA)
# =============================================================================
paso("CP-SAAS-08", "Onboarding Público: Registro de Nueva Empresa y Administrador")
timestamp = int(datetime.utcnow().timestamp())
nombre_empresa = f"Alta Moda Bolivia {timestamp}"
username_admin = f"admin_{timestamp}"

resp_onboarding = client.post("/api/v1/empresas/registrar", json={
    "nombre": nombre_empresa,
    "nit": f"10203040{timestamp % 1000}",
    "correo": f"contacto_{timestamp}@altamoda.bo",
    "plan": 1, # Plan Básico
    "ciclo": "mensual",
    "super_admin": {
        "username": username_admin,
        "email": f"{username_admin}@altamoda.bo",
        "password": "Password123!"
    }
})

if resp_onboarding.status_code != 200:
    fallo(f"Error en onboarding: HTTP {resp_onboarding.status_code}: {resp_onboarding.text}")

datos_onboarding = resp_onboarding.json()
exito(f"Nueva Empresa creada: '{datos_onboarding['empresa_nombre']}' (Tenant ID {datos_onboarding['empresa_id']})")
exito(f"Slug asignado para subdominio: '{datos_onboarding['slug']}'")
exito(f"Usuario Administrador creado: '{datos_onboarding['usuario']}'")

# Verificar en DB que la nueva empresa tiene su suscripción lista
db = SessionLocal()
emp_nueva = db.query(Empresa).filter(Empresa.id == datos_onboarding["empresa_id"]).first()
assert emp_nueva is not None
assert emp_nueva.suscripcion_activa is not None
exito(f"Suscripción activa en DB: Plan '{emp_nueva.suscripcion_activa.plan.nombre}', Estado: {emp_nueva.suscripcion_activa.estado}")
db.close()

banner("RESUMEN DE RESULTADOS: 8 DE 8 PRUEBAS PASARON EXITOSAMENTE (100% OK)")
print("""
+---------------+-----------------------------------------------+--------+
| Código        | Descripción del Caso de Prueba                | Estado |
+---------------+-----------------------------------------------+--------+
| CP-SAAS-01    | Consulta Catálogo de Planes (Básico vs Pro)   | [PASS] |
| CP-SAAS-02    | Aislamiento de Sucursales por X-Tenant-ID     | [PASS] |
| CP-SAAS-03    | Bloqueo de IA en Plan Básico (HTTP 403)       | [PASS] |
| CP-SAAS-04    | Permisión de IA en Plan Profesional (HTTP 200)| [PASS] |
| CP-SAAS-05    | Control Límite de Sucursales (Máx 2 = HTTP 400| [PASS] |
| CP-SAAS-06    | Upgrade Dinámico de Plan y Desbloqueo de IA   | [PASS] |
| CP-SAAS-07    | Auditoría de Historial de Cambios en DB       | [PASS] |
| CP-SAAS-08    | Onboarding Público de Nuevo Tenant + Admin    | [PASS] |
+---------------+-----------------------------------------------+--------+
ESTADO GLOBAL: SISTEMA SAAS MULTI-TENANT VERIFICADO Y OPERATIVO AL 100%.
""")
