import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
import models
from models.catalogo import Categoria, Producto, Recurso3D
from models.parametros import Talla, VariantePrenda
from models.sucursal import Sucursal, InventarioStock
from models.carrito import CarritoPersistente, ItemCarrito
from models.reserva import Reserva
from main import app

# Configuración de base de datos de pruebas en memoria SQLite
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Crea el esquema y datos de prueba base para los 3 Casos de Uso"""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # 1. Categorías
    cat1 = Categoria(nombre="Denim & Jeans", descripcion="Prendas de mezclilla y corte urbano")
    cat2 = Categoria(nombre="Alta Moda", descripcion="Vestidos de gala y sastrería")
    db.add_all([cat1, cat2])
    db.flush()

    # 2. Tallas
    talla_m = Talla(medida="M", tipo="Textil", guia_medida="Pecho 96-102 cm")
    talla_l = Talla(medida="L", tipo="Textil", guia_medida="Pecho 104-110 cm")
    db.add_all([talla_m, talla_l])
    db.flush()

    # 3. Sucursales físicas de la cadena
    suc1 = Sucursal(
        nombre="FashionStore Central",
        ciudad="Santa Cruz",
        direccion="Calle 21 de Calacoto #100",
        telefono="77112233"
    )
    suc2 = Sucursal(
        nombre="FashionStore Equipetrol",
        ciudad="Santa Cruz",
        direccion="Av. San Martín esq. Calle 5",
        telefono="77445566"
    )
    db.add_all([suc1, suc2])
    db.flush()

    # 4. Producto con Recurso 3D AR
    prod1 = Producto(
        codigo="CHAQ-DEN-001",
        nombre="Chaqueta Denim Unisex AR",
        descripcion="Chaqueta de mezclilla premium con modelo 3D para vestidor virtual",
        precio_base=320.00,
        id_categoria=cat1.id
    )
    db.add(prod1)
    db.flush()

    # Recurso 3D
    rec_3d = Recurso3D(
        producto_id=prod1.id,
        tipo_recurso="MODELO_3D_GLB",
        url_archivo="https://assets.fashionstore.bo/models/chaqueta_denim.glb",
        es_principal=False,
        es_compatible_ar=True
    )
    rec_foto = Recurso3D(
        producto_id=prod1.id,
        tipo_recurso="FOTOGRAFIA",
        url_archivo="https://assets.fashionstore.bo/img/chaqueta_denim_front.jpg",
        es_principal=True,
        es_compatible_ar=False
    )
    db.add_all([rec_3d, rec_foto])
    db.flush()

    # 5. Variantes de Prenda (Talla + Color)
    var_m_azul = VariantePrenda(
        sku="SKU-CHAQ-DEN-M-AZUL",
        nombre_prenda="Chaqueta Denim M Azul",
        precio=320.00,
        producto_id=prod1.id,
        talla_id=talla_m.id,
        color="Azul Clásico"
    )
    var_l_azul = VariantePrenda(
        sku="SKU-CHAQ-DEN-L-AZUL",
        nombre_prenda="Chaqueta Denim L Azul",
        precio=320.00,
        producto_id=prod1.id,
        talla_id=talla_l.id,
        color="Azul Clásico"
    )
    db.add_all([var_m_azul, var_l_azul])
    db.flush()

    # 6. Inventario por Sucursal
    # var_m_azul en Sucursal Central: 10 fisico, 2 reservado -> 8 disponible
    inv1 = InventarioStock(
        sucursal_id=suc1.id,
        variante_id=var_m_azul.id,
        stock_fisico=10,
        stock_reservado=2
    )
    # var_m_azul en Sucursal Equipetrol: 2 fisico, 0 reservado -> 2 disponible
    inv2 = InventarioStock(
        sucursal_id=suc2.id,
        variante_id=var_m_azul.id,
        stock_fisico=2,
        stock_reservado=0
    )
    # var_l_azul en Sucursal Central: 5 fisico, 0 reservado -> 5 disponible
    inv3 = InventarioStock(
        sucursal_id=suc1.id,
        variante_id=var_l_azul.id,
        stock_fisico=5,
        stock_reservado=0
    )
    db.add_all([inv1, inv2, inv3])

    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)


# ==============================================================================
# PRUEBAS CU11: Consultar catálogo y disponibilidad en tiempo real
# ==============================================================================

def test_cu11_catalogo_disponibilidad_general():
    """CU11: Consulta el catálogo con desglose omnicanal de existencias físicas en tiempo real"""
    resp = client.get("/api/v1/catalogo-disponibilidad/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1

    prenda = data[0]
    assert prenda["codigo"] == "CHAQ-DEN-001"
    assert prenda["tiene_modelo_ar"] is True
    assert len(prenda["recursos_multimedia"]) == 2
    assert prenda["disponibilidad_total_cadena"] > 0

    # Validar que cada variante contiene el desglose de sucursales
    variantes = prenda["variantes"]
    assert len(variantes) == 2

    var_m = next(v for v in variantes if "M" in v["talla_medida"])
    assert var_m["color"] == "Azul Clásico"

    # En Sucursal Central debe tener disponible = 10 - 2 = 8
    suc_central = next(s for s in var_m["stocks_por_sucursal"] if s["sucursal_nombre"] == "FashionStore Central")
    assert suc_central["stock_fisico"] == 10
    assert suc_central["stock_reservado"] == 2
    assert suc_central["stock_disponible"] == 8
    assert suc_central["estado_stock"] == "DISPONIBLE"


def test_cu11_filtros_talla_color_ar():
    """CU11: Filtrado combinado por talla, color y soporte AR"""
    # Filtro por Talla M
    resp_talla = client.get("/api/v1/catalogo-disponibilidad/?talla=M")
    assert resp_talla.status_code == 200
    prendas = resp_talla.json()
    assert len(prendas) >= 1
    assert all(all("M" in v["talla_medida"] for v in p["variantes"]) for p in prendas)

    # Filtro por Color
    resp_color = client.get("/api/v1/catalogo-disponibilidad/?color=Azul")
    assert resp_color.status_code == 200
    assert len(resp_color.json()) >= 1

    # Filtro solo AR
    resp_ar = client.get("/api/v1/catalogo-disponibilidad/?solo_ar=true")
    assert resp_ar.status_code == 200
    assert all(p["tiene_modelo_ar"] for p in resp_ar.json())


def test_cu11_detalle_sucursales_prenda():
    """CU11: Detalle de existencias de una prenda en todas las sucursales"""
    resp = client.get("/api/v1/catalogo-disponibilidad/1/sucursales")
    assert resp.status_code == 200
    data = resp.json()
    assert data["codigo_prenda"] == "CHAQ-DEN-001"
    assert len(data["sucursales"]) >= 2
    assert data["total_disponible"] > 0


# ==============================================================================
# PRUEBAS CU12: Gestionar reservas Web-to-Store
# ==============================================================================

def test_cu12_crear_reserva_web_to_store_exitosa():
    """CU12: Apartado digital exitoso con congelamiento atómico de stock (48h)"""
    payload = {
        "usuario_id": "usr_carlos_web",
        "cliente_nombre": "Carlos Montellano",
        "cliente_email": "carlos.montellano@gmail.com",
        "cliente_telefono": "78099887",
        "sucursal_id": 1,      # Sucursal Central (tiene 8 disponibles)
        "variante_id": 1,      # Chaqueta Denim M Azul
        "cantidad": 2,
        "canal_origen": "WEB_ANGULAR",
        "notas": "Pasaré a retirar el viernes por la tarde"
    }
    resp = client.post("/api/v1/reservas/web-to-store", json=payload)
    assert resp.status_code == 201
    data = resp.json()

    assert data["codigo_reserva"].startswith("RES-")
    assert data["estado"] == "PENDIENTE_RETIRO"
    assert data["cantidad"] == 2
    assert data["precio_congelado"] == 320.00
    assert data["total_estimado"] == 640.00
    assert "48 horas" in data["voucher_instrucciones"]

    # Verificar que el stock_reservado se incrementó en la base de datos (de 2 a 4)
    db = TestingSessionLocal()
    inv = db.query(InventarioStock).filter(
        InventarioStock.sucursal_id == 1,
        InventarioStock.variante_id == 1
    ).first()
    assert inv.stock_reservado == 4  # 2 previos + 2 de la reserva
    assert inv.stock_disponible == 6  # 10 - 4 = 6
    db.close()


def test_cu12_excepcion_a1_stock_insuficiente_con_sugerencias():
    """
    CU12 - Control de Excepción A1:
    Si la sucursal seleccionada no tiene stock suficiente, aborta con HTTP 400
    y sugiere sucursales alternativas que sí cuentan con existencias.
    """
    payload = {
        "usuario_id": "usr_maria_app",
        "cliente_nombre": "María René Morales",
        "cliente_email": "maria.morales@correo.bo",
        "sucursal_id": 2,      # Sucursal Equipetrol (solo tiene 2 disponibles)
        "variante_id": 1,      # Chaqueta Denim M Azul
        "cantidad": 5,         # Solicita 5 (excede las 2 disponibles)
        "canal_origen": "APP_FLUTTER"
    }
    resp = client.post("/api/v1/reservas/web-to-store", json=payload)
    assert resp.status_code == 400
    data = resp.json()["detail"]

    assert data["codigo_error"] == "EXCEPCION_A1_SIN_STOCK_SUCURSAL"
    assert "Prenda Agotada" in data["mensaje"]
    assert data["stock_disponible_actual"] == 2
    assert data["cantidad_solicitada"] == 5

    # Debe sugerir automáticamente la Sucursal Central que sí tiene existencias
    alternativas = data["sucursales_alternativas"]
    assert len(alternativas) >= 1
    assert alternativas[0]["sucursal_nombre"] == "FashionStore Central"
    assert alternativas[0]["stock_disponible"] >= 5


def test_cu12_confirmar_retiro_presencial_en_caja():
    """CU12: Cajero valida voucher y confirma entrega: descuenta stock físico y reservado"""
    # 1. Obtener la reserva previa
    db = TestingSessionLocal()
    reserva = db.query(Reserva).filter(Reserva.usuario_id == "usr_carlos_web").first()
    reserva_id = reserva.id
    codigo = reserva.codigo_reserva
    db.close()

    # 2. Consultar por código de voucher
    resp_get = client.get(f"/api/v1/reservas/{codigo}")
    assert resp_get.status_code == 200
    assert resp_get.json()["codigo_reserva"] == codigo

    # 3. Confirmar retiro en caja
    resp_confirmar = client.post(f"/api/v1/reservas/{reserva_id}/confirmar-retiro")
    assert resp_confirmar.status_code == 200
    assert resp_confirmar.json()["estado"] == "RETIRADA_Y_PAGADA"

    # 4. Verificar descuento en almacén físico
    db = TestingSessionLocal()
    inv = db.query(InventarioStock).filter(
        InventarioStock.sucursal_id == 1,
        InventarioStock.variante_id == 1
    ).first()
    # Físico bajó de 10 a 8, reservado bajó de 4 a 2
    assert inv.stock_fisico == 8
    assert inv.stock_reservado == 2
    db.close()


# ==============================================================================
# PRUEBAS CU13: Gestionar carrito de compras persistente
# ==============================================================================

def test_cu13_agregar_item_carrito_persistente():
    """CU13: Añadir prenda al carrito persistente y verificar persistencia en BD"""
    payload = {
        "usuario_id": "usr_cross_device_007",
        "variante_id": 2,      # Chaqueta Denim L Azul
        "sucursal_id": 1,      # Sucursal Central (tiene 5 disponibles)
        "cantidad": 2,
        "dispositivo": "APP_FLUTTER"
    }
    resp = client.post("/api/v1/carrito-persistente/items", json=payload)
    assert resp.status_code == 201
    data = resp.json()

    assert data["usuario_id"] == "usr_cross_device_007"
    assert data["dispositivo_origen"] == "APP_FLUTTER"
    assert data["total_articulos"] == 2
    assert data["total_monto"] == 640.00
    assert len(data["items"]) == 1

    item = data["items"][0]
    assert item["sku"] == "SKU-CHAQ-DEN-L-AZUL"
    assert item["cantidad"] == 2
    assert item["sucursal_nombre"] == "FashionStore Central"


def test_cu13_persistencia_cross_device():
    """
    CU13 - Verificación de persistencia multi-dispositivo:
    Al consultar el carrito desde la Web Angular para el mismo usuario_id,
    sus selecciones guardadas en la App Flutter permanecen intactas en PostgreSQL.
    """
    resp = client.get("/api/v1/carrito-persistente/usr_cross_device_007")
    assert resp.status_code == 200
    data = resp.json()

    assert data["usuario_id"] == "usr_cross_device_007"
    assert data["total_articulos"] == 2
    assert len(data["items"]) == 1
    assert "sincronizado y persistido" in data["mensaje_persistencia"]


def test_cu13_modificar_cantidad_y_control_stock():
    """CU13: Modificar cantidad en carrito reajustando stock reservado"""
    # Obtener el item_id
    resp_cart = client.get("/api/v1/carrito-persistente/usr_cross_device_007")
    item_id = resp_cart.json()["items"][0]["id"]

    # Incrementar de 2 a 3 unidades
    resp_put = client.put(f"/api/v1/carrito-persistente/items/{item_id}", json={"nueva_cantidad": 3})
    assert resp_put.status_code == 200
    assert resp_put.json()["total_articulos"] == 3

    # Excepción A1: intentar subir a 10 unidades (solo había 5 en físico)
    resp_exceder = client.put(f"/api/v1/carrito-persistente/items/{item_id}", json={"nueva_cantidad": 10})
    assert resp_exceder.status_code == 400
    assert "Excepción A1" in resp_exceder.json()["detail"]


def test_cu13_sincronizar_carrito_en_login():
    """
    CU13: Sincronización al iniciar sesión:
    Unifica artículos del carrito local/invitado con el carrito persistente del usuario.
    """
    payload_sync = {
        "usuario_id": "usr_cross_device_007",
        "dispositivo_origen": "WEB_ANGULAR",
        "items_locales": [
            {
                "variante_id": 1,  # Chaqueta Denim M Azul
                "sucursal_id": 1,
                "cantidad": 1
            }
        ]
    }
    resp_sync = client.post("/api/v1/carrito-persistente/sincronizar", json=payload_sync)
    assert resp_sync.status_code == 200
    data = resp_sync.json()

    assert data["usuario_id"] == "usr_cross_device_007"
    # Debe tener los 3 de la variante L + 1 de la variante M sincronizada = 4 artículos
    assert data["total_articulos"] == 4
    assert len(data["items"]) == 2
    assert "Sincronización multi-dispositivo (WEB_ANGULAR) exitosa" in data["mensaje_persistencia"]


def test_cu13_eliminar_item_y_liberar_stock():
    """CU13: Eliminar ítem del carrito libera el stock reservado"""
    resp_cart = client.get("/api/v1/carrito-persistente/usr_cross_device_007")
    items = resp_cart.json()["items"]
    item_m = next(i for i in items if "M" in i["talla"])

    resp_del = client.delete(f"/api/v1/carrito-persistente/items/{item_m['id']}")
    assert resp_del.status_code == 200
    data = resp_del.json()
    assert len(data["items"]) == 1
    assert "Se liberaron 1 unidad(es)" in data["mensaje_persistencia"]
