"""
Pruebas Automatizadas (Unit & Integration Tests) para CU16: Vestidor Virtual AR & Virtual Try-On con IA.
Alineado a los requisitos arquitectónicos de Antigravity (Anti-SSRF, Zero Retention, 3-Level Engine Failover).
"""
import sys
import os
import io
import pytest
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def _crear_imagen_dummy_jpeg() -> bytes:
    """Genera una imagen JPEG válida en memoria para pruebas."""
    img = Image.new("RGB", (400, 500), color=(180, 200, 220))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_try_on_invalid_ropa_id_returns_404():
    """
    Verifica protección Anti-SSRF:
    Solicitar try-on con un ID de prenda inexistente debe retornar 404
    y NO intentar descargar ni procesar URLs externas.
    """
    foto_bytes = _crear_imagen_dummy_jpeg()
    files = {
        "foto_usuario": ("test_user.jpg", foto_bytes, "image/jpeg")
    }
    data = {
        "ropa_id": 999999
    }

    response = client.post("/api/v1/ar/try-on-ia", files=files, data=data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Prenda no encontrada."


def test_try_on_valid_garment_returns_try_on_result():
    """
    Verifica el flujo completo de Virtual Try-On con prenda válida (ropa_id=1).
    Debe retornar success=True, imagen_resultado (Base64 data URI), y prenda_nombre.
    """
    foto_bytes = _crear_imagen_dummy_jpeg()
    files = {
        "foto_usuario": ("test_user.jpg", foto_bytes, "image/jpeg")
    }
    data = {
        "ropa_id": 1
    }

    response = client.post("/api/v1/ar/try-on-ia", files=files, data=data)
    assert response.status_code == 200
    res_data = response.json()

    assert res_data["success"] is True
    assert "imagen_resultado" in res_data
    assert res_data["imagen_resultado"].startswith("data:image/")
    assert "prenda_nombre" in res_data
    assert "mensaje" in res_data


def test_catalogo_3d_endpoint():
    """Verifica que el catálogo 3D responda correctamente."""
    response = client.get("/api/v1/ar/catalogo-3d")
    assert response.status_code == 200
    items = response.json()
    assert isinstance(items, list)


def test_validar_ajuste_corporal():
    """Verifica la recomendación biométrica de talla y calce."""
    payload = {
        "ropa_id": 1,
        "pecho_cm": 95.0,
        "cintura_cm": 80.0,
        "cadera_cm": 98.0,
        "altura_cm": 175.0
    }
    response = client.post("/api/v1/ar/validar-ajuste", json=payload)
    assert response.status_code == 200
    res_data = response.json()

    assert res_data["ropa_id"] == 1
    assert "talla_recomendada" in res_data
    assert "porcentaje_calce" in res_data
    assert res_data["porcentaje_calce"] > 0
