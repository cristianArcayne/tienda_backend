from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_mis_beneficios():
    res = client.get("/api/v1/ventas/mi-beneficio-fidelizacion/")
    assert res.status_code == 200, f"Error {res.status_code}: {res.text}"
    data = res.json()
    assert "acumulado" in data
    assert "monto_minimo" in data
    assert "monto_descuento" in data
    assert "activo" in data
    assert "elegible" in data
    print("[OK] mis-beneficios:", data)

def test_configuracion_fidelizacion():
    res = client.get("/api/v1/configuracion-fidelizacion/")
    assert res.status_code == 200, f"Error {res.status_code}: {res.text}"
    data = res.json()
    assert "monto_minimo_acumulado" in data
    assert "monto_descuento" in data
    assert "activo" in data
    print("[OK] configuracion-fidelizacion GET:", data)

    res_put = client.put("/api/v1/configuracion-fidelizacion/", json={
        "monto_minimo_acumulado": 150.0,
        "monto_descuento": 20.0,
        "activo": True
    })
    assert res_put.status_code == 200
    print("[OK] configuracion-fidelizacion PUT:", res_put.json())

def test_historial_cliente():
    res = client.get("/api/v1/ventas/historial-cliente/?page=1&page_size=10")
    assert res.status_code == 200, f"Error {res.status_code}: {res.text}"
    data = res.json()
    assert "count" in data
    assert "results" in data
    assert isinstance(data["results"], list)
    print(f"[OK] historial-cliente count: {data['count']}, items: {len(data['results'])}")

def test_alertas_ia():
    res = client.get("/api/v1/ia/alertas/?page=1&page_size=10")
    assert res.status_code == 200, f"Error {res.status_code}: {res.text}"
    data = res.json()
    assert "count" in data
    assert "results" in data
    print(f"[OK] alertas-ia count: {data['count']}, items: {len(data['results'])}")
    if data["results"]:
        a_id = data["results"][0]["id"]
        res_leida = client.patch(f"/api/v1/ia/alertas/{a_id}/marcar-leida/")
        assert res_leida.status_code == 200
        print(f"[OK] marcar-leida {a_id}:", res_leida.json())

def test_notificaciones():
    res = client.get("/api/v1/notificaciones/")
    assert res.status_code == 200, f"Error {res.status_code}: {res.text}"
    data = res.json()
    assert "count" in data
    assert "results" in data
    print(f"[OK] notificaciones count: {data['count']}")

    res_vapid = client.get("/api/notificaciones/vapid-public-key/")
    assert res_vapid.status_code == 200
    assert "public_key" in res_vapid.json()
    print("[OK] vapid-public-key:", res_vapid.json())

    res_sub = client.post("/api/v1/notificaciones/suscribirse/", json={
        "endpoint": "https://test.push.endpoint/123",
        "keys": {
            "p256dh": "test_p256dh_key",
            "auth": "test_auth_key"
        }
    })
    assert res_sub.status_code == 200
    print("[OK] suscribirse:", res_sub.json())

def test_productos():
    res = client.get("/api/v1/productos/?page=1&page_size=100")
    assert res.status_code == 200, f"Error {res.status_code}: {res.text}"
    data = res.json()
    assert "count" in data
    assert "results" in data
    assert len(data["results"]) > 0
    print(f"[OK] productos count: {data['count']}, items: {len(data['results'])}")

if __name__ == "__main__":
    test_mis_beneficios()
    test_configuracion_fidelizacion()
    test_historial_cliente()
    test_alertas_ia()
    test_notificaciones()
    test_productos()
    print("\nTODOS LOS TESTS COMPLETADOS SATISFACTORIAMENTE!")
