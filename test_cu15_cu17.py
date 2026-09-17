import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_cu17_ia():
    print("\n--- TEST CU17: Recomendador Inteligente IA ---")
    url = f"{BASE_URL}/ia/generar-outfit"
    payload = {
        "cliente_id": "2001",
        "ocasion": "Formal"
    }
    res = requests.post(url, json=payload)
    print(f"Status Code: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        print(f"Outfit Generado: {data.get('outfit_nombre')}")
        print(f"Prenda Principal: {data.get('prenda_principal', {}).get('nombre')}")
        print(f"Total Outfit: {data.get('precio_final_con_descuento')} Bs.")
    else:
        print("Error:", res.text)

def test_cu15_ecommerce_checkout():
    print("\n--- TEST CU15: Procesar Ventas Digitales E-commerce ---")
    res = requests.post("http://localhost:8000/api/ventas/", json={
        "tipo": "digital",
        "estado": "completado",
        "metodo": "tarjeta",
        "monto_recibido": 500,
        "precio_total": 500,
        "descuento_total": 0,
        "usuario_id": "2001",
        "nit_cliente": "1234567",
        "razon_social": "Cliente Test E-commerce",
        "detalles": [
            {
                "variante_producto_id": 1,
                "cantidad": 1,
                "precio_unitario": 250.00
            }
        ]
    })
    print(f"Status Code: {res.status_code}")
    if res.status_code in [200, 201]:
        data = res.json()
        print(f"Venta Creada #{data.get('id')} - Nro Factura: {data.get('nro_factura')}")
        print(f"Código Trx: {data.get('nro_comprobante')}")
    else:
        print("Error:", res.text)

if __name__ == "__main__":
    test_cu17_ia()
    test_cu15_ecommerce_checkout()
