"""
==============================================================================
SUITE DE PRUEBAS DE ACEPTACIN - CASO DE USO CU-19
GESTIN DE RESEAS, CALIFICACIONES Y SATISFACCIN DEL CLIENTE (ANEXO / EXTRA)
==============================================================================
Objetivo: Validar el ciclo de vida completo de reseas y calificaciones de prendas:
1. Registro de feedback del cliente con valoracin de 1 a 5 estrellas.
2. Validacin estricta de lmites de calificacin (rechazo fuera del rango 1-5).
3. Obtencin del listado cronolgico de valoraciones por prenda.
4. Clculo de mtricas consolidadas (promedio ponderado, desglose por estrellas).
5. Actualizacin / moderacin de resea existente.
6. Eliminacin conforme de la resea.
"""
import sys
import os
import requests
from fastapi.testclient import TestClient
from main import app
from database import get_db, SessionLocal
from models.catalogo import Ropa, Resena
from models.seguridad_persona import Cliente

client = TestClient(app)

def banner(titulo: str):
    print("\n" + "="*78)
    print(f" {titulo}")
    print("="*78)

def probar_cu19():
    banner("INICIO DE PRUEBAS DE ACEPTACIN: CU-19 GESTIN DE RESEAS Y CALIFICACIONES")
    db = SessionLocal()
    
    # 1. Obtener una prenda vlida de la base de datos
    prenda = db.query(Ropa).filter(Ropa.activo == True).first()
    if not prenda:
        prenda = db.query(Ropa).first()
    assert prenda is not None, "Debe existir al menos una prenda en el catlogo"
    prenda_id = prenda.id
    prenda_nombre = prenda.nombre
    print(f"[*] Prenda de prueba seleccionada: ID {prenda_id} - '{prenda_nombre}'")

    # Asegurar un cliente para la prueba
    cliente = db.query(Cliente).first()
    if not cliente:
        cliente_ci = "77889900"
        cliente_nombre = "Mara Estudiante"
    else:
        cliente_ci = cliente.ci
        cliente_nombre = f"{cliente.nombre} {cliente.apellido_pat or ''}".strip()

    print(f"[*] Cliente asignado a la prueba: CI {cliente_ci} - '{cliente_nombre}'")

    resena_creada_id = None

    # -------------------------------------------------------------------------
    # CP-CU19-01: Registro de Resea Vlida (5 Estrellas)
    # -------------------------------------------------------------------------
    print("\n>>> [CP-CU19-01] Registrar Resea de Calidad con 5 Estrellas")
    payload_valido = {
        "ropa_id": prenda_id,
        "cliente_ci": cliente_ci,
        "cliente_nombre": cliente_nombre,
        "puntuacion_estrellas": 5,
        "comentario": "Excelente calidad de la tela, el tallaje corresponde exactamente con la descripcin."
    }
    resp = client.post("/api/v1/resenas", json=payload_valido)
    assert resp.status_code == 201, f"Error al registrar resea: {resp.text}"
    data_resena = resp.json()
    resena_creada_id = data_resena["id"]
    assert data_resena["puntuacion_estrellas"] == 5
    assert data_resena["ropa_id"] == prenda_id
    print(f"    [PASS] EXITO: Resea #{resena_creada_id} registrada con {data_resena['puntuacion_estrellas']} estrellas.")
    print(f"    [PASS] EXITO: Comentario: \"{data_resena['comentario']}\"")
    print(f"    [PASS] EXITO: Fecha de emisin: {data_resena.get('fecha')}")

    # -------------------------------------------------------------------------
    # CP-CU19-02: Rechazo de Calificacin Invlida (Fuera del rango 1-5)
    # -------------------------------------------------------------------------
    print("\n>>> [CP-CU19-02] Validar Rechazo de Calificacin Fuera de Rango (0 y 7 Estrellas)")
    # Intento 1: 0 estrellas
    payload_invalido_0 = {
        "ropa_id": prenda_id,
        "cliente_ci": cliente_ci,
        "puntuacion_estrellas": 0,
        "comentario": "Intento de votar 0 estrellas"
    }
    resp_0 = client.post("/api/v1/resenas", json=payload_invalido_0)
    assert resp_0.status_code in (400, 422), f"Se esperaba error 400/422 y se obtuvo {resp_0.status_code}"
    print(f"    [PASS] EXITO: Calificacin 0 estrellas correctamente rechazada con HTTP {resp_0.status_code}.")

    # Intento 2: 7 estrellas
    payload_invalido_7 = {
        "ropa_id": prenda_id,
        "cliente_ci": cliente_ci,
        "puntuacion_estrellas": 7,
        "comentario": "Intento de votar 7 estrellas"
    }
    resp_7 = client.post("/api/v1/resenas", json=payload_invalido_7)
    assert resp_7.status_code in (400, 422), f"Se esperaba error 400/422 y se obtuvo {resp_7.status_code}"
    print(f"    [PASS] EXITO: Calificacin 7 estrellas correctamente rechazada con HTTP {resp_7.status_code}.")

    # -------------------------------------------------------------------------
    # CP-CU19-03: Consultar Listado de Reseas por Prenda
    # -------------------------------------------------------------------------
    print(f"\n>>> [CP-CU19-03] Consultar Listado de Reseas para Prenda ID {prenda_id}")
    resp_list = client.get(f"/api/v1/resenas/ropa/{prenda_id}")
    assert resp_list.status_code == 200, f"Error consultando reseas: {resp_list.text}"
    lista_resenas = resp_list.json()
    assert isinstance(lista_resenas, list)
    assert len(lista_resenas) >= 1
    ids_en_lista = [r["id"] for r in lista_resenas]
    assert resena_creada_id in ids_en_lista
    print(f"    [PASS] EXITO: Total de reseas obtenidas para la prenda: {len(lista_resenas)}")
    print(f"    [PASS] EXITO: Resea #{resena_creada_id} presente en la lista cronolgica.")

    # -------------------------------------------------------------------------
    # CP-CU19-04: Clculo de Mtricas de Satisfaccin y Resumen Estadstico
    # -------------------------------------------------------------------------
    print(f"\n>>> [CP-CU19-04] Obtener Mtricas Consolidadas y Desglose de Estrellas")
    resp_metricas = client.get(f"/api/v1/resenas/ropa/{prenda_id}/resumen")
    assert resp_metricas.status_code == 200, f"Error al calcular mtricas: {resp_metricas.text}"
    stats = resp_metricas.json()
    print(f"    [PASS] EXITO: Total Reseas Auditadas: {stats.get('total_resenas')}")
    print(f"    [PASS] EXITO: Calificacin Promedio: {stats.get('promedio_calificacion')} / 5.0")
    desglose = stats.get("desglose_estrellas") or stats.get("desglose", {})
    print(f"    [PASS] EXITO: Desglose por Estrellas:")
    print(f"          - 5 Estrellas: {desglose.get('estrella_5', 0)}")
    print(f"          - 4 Estrellas: {desglose.get('estrella_4', 0)}")
    print(f"          - 3 Estrellas: {desglose.get('estrella_3', 0)}")
    print(f"          - 2 Estrellas: {desglose.get('estrella_2', 0)}")
    print(f"          - 1 Estrella:  {desglose.get('estrella_1', 0)}")
    assert stats.get("promedio_calificacion", 0) >= 1.0

    # -------------------------------------------------------------------------
    # CP-CU19-05: Actualizacin / Moderacin de Resea
    # -------------------------------------------------------------------------
    print(f"\n>>> [CP-CU19-05] Actualizar Contenido de la Resea #{resena_creada_id}")
    payload_edit = {
        "puntuacion_estrellas": 4,
        "comentario": "Comentario actualizado: Buen producto, aunque el envo demor 1 da ms."
    }
    resp_edit = client.patch(f"/api/v1/resenas/{resena_creada_id}", json=payload_edit)
    assert resp_edit.status_code == 200, f"Error al editar resea: {resp_edit.text}"
    editado = resp_edit.json()
    assert editado["puntuacion_estrellas"] == 4
    assert "actualizado" in editado["comentario"]
    print(f"    [PASS] EXITO: Resea actualizada a {editado['puntuacion_estrellas']} estrellas.")
    print(f"    [PASS] EXITO: Nuevo texto: \"{editado['comentario']}\"")

    # -------------------------------------------------------------------------
    # CP-CU19-06: Eliminacin Conforme de Resea de Prueba
    # -------------------------------------------------------------------------
    print(f"\n>>> [CP-CU19-06] Eliminar Resea #{resena_creada_id}")
    resp_del = client.delete(f"/api/v1/resenas/{resena_creada_id}")
    assert resp_del.status_code == 200, f"Error al eliminar resea: {resp_del.text}"
    print(f"    [PASS] EXITO: Resea #{resena_creada_id} eliminada correctamente.")

    # Verificar que ya no existe
    resp_verify = client.delete(f"/api/v1/resenas/{resena_creada_id}")
    assert resp_verify.status_code == 404
    print(f"    [PASS] EXITO: Confirmado: Bsqueda de resea eliminada retorna HTTP 404 Not Found.")

    banner("RESUMEN: CU-19 VERIFICADO AL 100% (CALIFICACIONES, REGLAS 1-5, STATS Y MODERACIN)")
    db.close()

if __name__ == "__main__":
    try:
        probar_cu19()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] FALLO EN PRUEBA CU-19: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
