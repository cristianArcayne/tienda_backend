import requests

BASE_URL = "http://localhost:8000/api/v1"

def test_cu18_reportes_voz():
    print("\n=== TEST CU18: Generar reportes mediante comandos de voz ===")
    comandos = [
        "Mostrar ventas por sucursal",
        "Ver ventas por canal de venta",
        "Ver prendas con stock critico"
    ]
    
    for cmd in comandos:
        print(f"\n--> Dictando comando de voz: '{cmd}'")
        res = requests.post(f"{BASE_URL}/reportes-voz/procesar-comando", json={"comando": cmd})
        print(f"Status Code: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            print(f"Intención Detectada: {data.get('intencion_detectada')}")
            print(f"Resumen Ejecutivo: {data.get('resumen_ejecutivo')}")
            print(f"Gráfico Generado: Tipo={data.get('datos_grafico', {}).get('tipo_grafico')}, Labels={data.get('datos_grafico', {}).get('labels')}")
        else:
            print("Error:", res.text)

def test_cu19_resenas_calificaciones():
    print("\n=== TEST CU19: Gestionar reseñas y calificaciones ===")
    
    # 1. Publicar una reseña
    payload = {
        "ropa_id": 1,
        "cliente_ci": "2001",
        "puntuacion_estrellas": 5,
        "comentario": "Excelente calidad de tela denim, la talla M me quedó perfecta. Muy recomendado."
    }
    print(f"--> Registrando reseña de 5 estrellas para Prenda #1...")
    res_post = requests.post(f"{BASE_URL}/resenas", json=payload)
    print(f"Status Code: {res_post.status_code}")
    if res_post.status_code in [200, 201]:
        data = res_post.json()
        print(f"Reseña Publicada #{data.get('id')} por {data.get('cliente_nombre')}")
    
    # 2. Listar reseñas de la prenda #1
    res_get = requests.get(f"{BASE_URL}/resenas/ropa/1")
    if res_get.status_code == 200:
        resenas = res_get.json()
        print(f"Total reseñas listadas para Prenda #1: {len(resenas)}")
    
    # 3. Consultar resumen de calificaciones
    res_summary = requests.get(f"{BASE_URL}/resenas/ropa/1/resumen")
    if res_summary.status_code == 200:
        s_data = res_summary.json()
        print(f"Promedio de Calificación: {s_data.get('promedio_estrellas')} / 5.0 estrellas")
        print(f"Porcentaje de Recomendación: {s_data.get('porcentaje_recomendacion')}%")

if __name__ == "__main__":
    test_cu18_reportes_voz()
    test_cu19_resenas_calificaciones()
