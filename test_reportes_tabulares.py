import requests

BASE_URL = "http://localhost:8000/api/v1"

def test_reportes_tabulares_qbe():
    print("=== TEST: REPORTES TABULARES DINÁMICOS QBE ===")
    
    # 1. Obtener vistas disponibles
    res_vistas = requests.get(f"{BASE_URL}/reporte/vistas")
    print(f"Status Vistas: {res_vistas.status_code}")
    if res_vistas.status_code == 200:
        vistas = res_vistas.json().get("vistas", [])
        print(f"Vistas Registradas: {[v['nombre'] for v in vistas]}")
    
    # 2. Ejecutar Reporte Tabular de Ventas
    qbe_payload = {
        "vista": "ventas",
        "columnas": ["id", "codigo_transaccion", "fecha", "total", "monto_neto", "sucursal_nombre", "cliente_nombre", "tipo_venta"],
        "limite": 10
    }
    res_qbe = requests.post(f"{BASE_URL}/reporte/qbe", json=qbe_payload)
    print(f"\nStatus QBE: {res_qbe.status_code}")
    if res_qbe.status_code == 200:
        data = res_qbe.json()
        print(f"Total Registros Encontrados: {data.get('total_registros')}")
        print(f"Columnas Generadas: {data.get('columnas')}")
        print(f"Resumen Agregaciones (Totales): {data.get('resumen_agregaciones')}")
        if data.get("datos"):
            print(f"Primera Fila: {data.get('datos')[0]}")

if __name__ == "__main__":
    test_reportes_tabulares_qbe()
