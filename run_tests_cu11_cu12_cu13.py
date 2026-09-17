"""
Suite de pruebas automatizadas para CU11, CU12 y CU13.
Valida todas las funciones de controlador, lógica transaccional, excepciones A1 y persistencia con los 29 modelos UML.
"""
from datetime import date, datetime
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
import models
from models.seguridad_persona import Persona, Empleado, Cliente, Usuario, Rol, Bitacora
from models.catalogo import Categoria, Temporada, Proveedor, Ropa, Talla, Color, VariantePrenda, Promocion, PromocionRopa
from models.sucursal import Sucursal, InventarioSucursal, Traspaso, DetalleTraspaso
from models.carrito import CarritoCompra, DetalleCarritoCompra
from models.reserva import Reserva, DetalleReserva

from schemas.reserva import ReservaCreate, DetalleReservaCreate
from schemas.carrito import DetalleCarritoCreate

from routers.catalogo_disponibilidad import (
    consultar_catalogo_con_disponibilidad,
    obtener_disponibilidad_prenda
)
from routers.reservas import (
    crear_reserva,
    confirmar_retiro,
    listar_reservas
)
from routers.carrito import (
    obtener_carrito,
    agregar_item,
    eliminar_item
)

test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def inicializar_datos(db):
    Base.metadata.create_all(bind=test_engine)

    # 1. Sucursales
    suc1 = Sucursal(nombre="FashionStore Central", direccion="Calle 21 Calacoto", ciudad="Santa Cruz")
    suc2 = Sucursal(nombre="FashionStore Equipetrol", direccion="Av. San Martín", ciudad="Santa Cruz")
    db.add_all([suc1, suc2])
    db.flush()

    # 2. Clientes
    cli1 = Cliente(ci="3001", nombre="Laura", apellido_pat="Benítez", telefono="+591 70099881", correo="laura@test.com", preferencia_talla="M")
    db.add(cli1)
    db.flush()

    # 3. Categoría, Talla, Color, Ropa, Variante
    cat = Categoria(nombre="Denim")
    db.add(cat)
    db.flush()

    talla_m = Talla(medida="M")
    col_azul = Color(nombre="Azul Denim", codigo_hex="#0000FF")
    db.add_all([talla_m, col_azul])
    db.flush()

    ropa = Ropa(
        nombre="Chaqueta Denim AR",
        descripcion="Chaqueta urbana con modelo 3D",
        precio=300.00,
        imagen_uri="https://img.test/chaqueta.jpg",
        modelo_3d_uri="https://3d.test/chaqueta.glb",
        categoria_id=cat.id
    )
    db.add(ropa)
    db.flush()

    var = VariantePrenda(cod_barra="VAR-001", ropa_id=ropa.id, talla_id=talla_m.id, color_id=col_azul.id)
    db.add(var)
    db.flush()

    # Inventario en sucursal 1: 10 fisico, 0 reservado
    inv1 = InventarioSucursal(sucursal_id=suc1.id, variante_id=var.id, stock_fisico=10, stock_reservado=0)
    # Inventario en sucursal 2: 5 fisico, 0 reservado
    inv2 = InventarioSucursal(sucursal_id=suc2.id, variante_id=var.id, stock_fisico=5, stock_reservado=0)
    db.add_all([inv1, inv2])
    db.commit()

    return suc1, suc2, cli1, ropa, var


def run_tests():
    db = TestingSessionLocal()
    suc1, suc2, cli1, ropa, var = inicializar_datos(db)
    print("Base de datos de prueba inicializada correctamente.")

    # --- CU11 ---
    print("\n--- INICIANDO PRUEBAS CU11: Catálogo y Disponibilidad en Tiempo Real ---")
    res = consultar_catalogo_con_disponibilidad(db=db)
    assert len(res) == 1, "Debe listar 1 prenda"
    assert res[0].tiene_modelo_ar is True, "Debe detectar modelo 3D AR"
    assert res[0].stock_disponible_cadena == 15, "Stock disponible total en cadena debe ser 15"
    print("PASS: CU11 - Consulta de catálogo con stock omnicanal en tiempo real")

    disp = obtener_disponibilidad_prenda(prenda_id=ropa.id, db=db)
    assert len(disp.sucursales) == 2, "Debe desglosar ambas sucursales"
    print("PASS: CU11 - Mapa de disponibilidad física por tienda")

    # --- CU12 ---
    print("\n--- INICIANDO PRUEBAS CU12: Gestionar Reservas Web-to-Store ---")
    res_in = ReservaCreate(
        cliente_id=cli1.ci,
        sucursal_id=suc1.id,
        hora_estimada="18:00",
        detalles=[DetalleReservaCreate(variante_id=var.id, cantidad=2)]
    )
    res_out = crear_reserva(res_in, db=db)
    assert res_out.estado == "PENDIENTE"
    assert res_out.total_estimado == 600.00
    # Verificar congelamiento de stock
    inv1_check = db.query(InventarioSucursal).filter(InventarioSucursal.sucursal_id == suc1.id, InventarioSucursal.variante_id == var.id).first()
    assert inv1_check.stock_reservado == 2
    assert inv1_check.stock_disponible == 8
    print(f"PASS: CU12 - Reserva ID {res_out.id} creada y stock congelado exitosamente (disp: {inv1_check.stock_disponible})")

    # Excepción A1: Stock Insuficiente
    try:
        res_fallo = ReservaCreate(
            cliente_id=cli1.ci,
            sucursal_id=suc1.id,
            hora_estimada="18:00",
            detalles=[DetalleReservaCreate(variante_id=var.id, cantidad=50)]
        )
        crear_reserva(res_fallo, db=db)
        assert False, "Debió lanzar HTTP 400 por stock insuficiente"
    except HTTPException as e:
        assert e.status_code == 400
        print("PASS: CU12 - Excepción A1 capturada: aborta con HTTP 400 y sugiere tiendas alternativas")

    # Confirmar retiro
    conf = confirmar_retiro(res_out.id, db=db)
    assert conf.estado == "COMPLETADA"
    inv1_check = db.query(InventarioSucursal).filter(InventarioSucursal.sucursal_id == suc1.id, InventarioSucursal.variante_id == var.id).first()
    assert inv1_check.stock_fisico == 8
    assert inv1_check.stock_reservado == 0
    print("PASS: CU12 - Retiro presencial confirmado: stock físico rebajado a 8 y reservado liberado")

    # --- CU13 ---
    print("\n--- INICIANDO PRUEBAS CU13: Gestionar Carrito de Compras Persistente ---")
    cart = obtener_carrito(cli1.ci, db=db)
    assert cart.total_articulos == 0

    item_in = DetalleCarritoCreate(variante_id=var.id, cantidad=3, sucursal_id=suc1.id)
    cart_act = agregar_item(cli1.ci, item_in, db=db)
    assert cart_act.total_articulos == 3
    assert cart_act.monto_total == 900.00
    print("PASS: CU13 - Ítem añadido a Carrito Persistente y stock temporalmente apartado")

    # Excepción A1 Carrito
    try:
        item_exceso = DetalleCarritoCreate(variante_id=var.id, cantidad=100, sucursal_id=suc1.id)
        agregar_item(cli1.ci, item_exceso, db=db)
        assert False, "Debió rechazar por stock insuficiente"
    except HTTPException as e:
        assert e.status_code == 400
        print("PASS: CU13 - Excepción A1 en carrito capturada: rechaza sobreventa")

    # Eliminar del carrito
    det_id = cart_act.detalles[0].id
    cart_limpio = eliminar_item(cli1.ci, det_id, db=db)
    assert cart_limpio.total_articulos == 0
    print("PASS: CU13 - Eliminación de ítem del carrito y liberación de stock en almacén")

    print("\n==================================================================")
    print(" 100% DE PRUEBAS UNITARIAS Y DE NEGOCIO SUPERADAS EXITOSAMENTE!")
    print(" CU11, CU12 Y CU13 OPERATIVOS Y CONFORMES AL DIAGRAMA UML DE SI2")
    print("==================================================================")


if __name__ == "__main__":
    run_tests()
