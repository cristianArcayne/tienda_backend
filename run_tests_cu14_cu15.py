"""
Suite de pruebas automatizadas para CU14 y CU15 con los 29 modelos UML.
Valida ventas físicas en POS, emisión de facturas fiscales, ventas digitales E-commerce,
descargo logístico inmediato y la Excepción A1 de rollback de stock ante fallos de pasarela.
"""
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
import models
from models.seguridad_persona import Persona, Empleado, Cliente, Usuario, Rol
from models.catalogo import Categoria, Temporada, Proveedor, Ropa, Talla, Color, VariantePrenda
from models.sucursal import Sucursal, InventarioSucursal
from models.carrito import CarritoCompra, DetalleCarritoCompra
from models.venta import MetodoPago, TipoVenta, Venta, DetalleVenta, Factura

from schemas.venta import (
    ItemVentaCreate,
    VentaPOSCreate,
    VentaEcommerceCreate
)
from routers.ventas import (
    procesar_venta_pos,
    procesar_venta_ecommerce,
    obtener_venta,
    listar_ventas
)

test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def inicializar_datos(db):
    Base.metadata.create_all(bind=test_engine)

    # 1. Sucursal
    suc = Sucursal(nombre="FashionStore Ventura Mall", ciudad="Santa Cruz", direccion="4to Anillo")
    db.add(suc)
    db.flush()

    # 2. Empleado y Cliente
    emp = Empleado(ci=101, nombre="Luis", apellido_pat="Arce", telefono="70011111", correo="cajero@test.bo")
    cli = Cliente(ci=201, nombre="María", apellido_pat="Suárez", telefono="70022222", correo="maria@test.bo")
    db.add_all([emp, cli])
    db.flush()

    # 3. Métodos de Pago y Tipos de Venta
    mp_efec = MetodoPago(nombre="Efectivo")
    mp_tarj = MetodoPago(nombre="Tarjeta POS")
    mp_stripe = MetodoPago(nombre="Stripe")
    db.add_all([mp_efec, mp_tarj, mp_stripe])
    db.flush()

    tv_pos = TipoVenta(nombre="Presencial POS")
    tv_ecom = TipoVenta(nombre="Digital E-commerce Web")
    db.add_all([tv_pos, tv_ecom])
    db.flush()

    # 4. Ropa, Talla, Color, Variante
    cat = Categoria(nombre="Lino")
    talla_m = Talla(medida="M")
    col = Color(nombre="Blanco", codigo_hex="#FFFFFF")
    db.add_all([cat, talla_m, col])
    db.flush()

    ropa = Ropa(nombre="Camisa Lino", precio=180.00, categoria_id=cat.id)
    db.add(ropa)
    db.flush()

    var = VariantePrenda(cod_barra="VAR-LIN-001", ropa_id=ropa.id, talla_id=talla_m.id, color_id=col.id)
    db.add(var)
    db.flush()

    # Inventario: 10 fisico, 0 reservado
    inv = InventarioSucursal(sucursal_id=suc.id, variante_id=var.id, stock_fisico=10, stock_reservado=0)
    db.add(inv)
    db.commit()

    return suc, emp, cli, mp_efec, mp_tarj, mp_stripe, tv_pos, tv_ecom, ropa, var


def run_tests():
    db = TestingSessionLocal()
    suc, emp, cli, mp_efec, mp_tarj, mp_stripe, tv_pos, tv_ecom, ropa, var = inicializar_datos(db)
    print("Base de datos de prueba configurada exitosamente.")

    # =========================================================================
    # CU14: PROCESAR VENTAS FÍSICAS EN POS
    # =========================================================================
    print("\n==================================================================")
    print("--- INICIANDO PRUEBAS CU14: Procesar Ventas Físicas en POS ---")
    print("==================================================================")

    # 1. Venta POS en efectivo con cálculo de cambio
    venta_pos_in = VentaPOSCreate(
        empleado_id=emp.ci,
        cliente_id=cli.ci,
        sucursal_id=suc.id,
        metodo_pago_id=mp_efec.id,
        nit_cliente="1234567",
        razon_social="María Suárez",
        monto_recibido=400.00,
        items=[ItemVentaCreate(variante_id=var.id, cantidad=2)]
    )

    v_pos_res = procesar_venta_pos(venta_pos_in, db=db)
    assert v_pos_res.total == 360.00
    assert v_pos_res.cambio_devuelto == 40.00
    assert v_pos_res.factura is not None
    assert v_pos_res.factura.nit_cliente == "1234567"

    # Verificar descargo de stock
    inv_check = db.query(InventarioSucursal).filter(InventarioSucursal.sucursal_id == suc.id, InventarioSucursal.variante_id == var.id).first()
    assert inv_check.stock_fisico == 8
    print(f"PASS: CU14 - Venta POS {v_pos_res.factura.nro_factura} completada. Total: S/ {v_pos_res.total}, Cambio: S/ {v_pos_res.cambio_devuelto}. Stock bajó a {inv_check.stock_fisico}")

    # 2. Excepción A1: Stock Insuficiente en POS
    try:
        venta_exceso = VentaPOSCreate(
            empleado_id=emp.ci,
            sucursal_id=suc.id,
            metodo_pago_id=mp_tarj.id,
            items=[ItemVentaCreate(variante_id=var.id, cantidad=20)]
        )
        procesar_venta_pos(venta_exceso, db=db)
        assert False, "Debió rechazar venta POS por stock insuficiente"
    except HTTPException as e:
        assert e.status_code == 400
        print("PASS: CU14 - Excepción A1 capturada: rechazo por stock insuficiente en mostrador")

    # =========================================================================
    # CU15: PROCESAR VENTAS DIGITALES (E-COMMERCE)
    # =========================================================================
    print("\n==================================================================")
    print("--- INICIANDO PRUEBAS CU15: Procesar Ventas Digitales (E-commerce) ---")
    print("==================================================================")

    # 1. Crear carrito para cliente
    cart = CarritoCompra(cliente_id=cli.ci)
    db.add(cart)
    db.flush()
    db.add(DetalleCarritoCompra(carrito_id=cart.id, variante_id=var.id, cantidad=2))
    # Simular apartado temporal
    inv_check.stock_reservado = 2
    db.commit()

    # 2. Excepción A1: Pago rechazado por pasarela externa (Rollback)
    venta_ecom_fallida = VentaEcommerceCreate(
        cliente_id=cli.ci,
        sucursal_id=suc.id,
        metodo_pago_id=mp_stripe.id,
        token_pasarela="tok_tarjeta_rechazada_fondos_insuficientes"
    )
    try:
        procesar_venta_ecommerce(venta_ecom_fallida, db=db)
        assert False, "Debió abortar por pasarela rechazada"
    except HTTPException as e:
        assert e.status_code == 402
        # Verificar rollback de stock
        inv_check = db.query(InventarioSucursal).filter(InventarioSucursal.sucursal_id == suc.id, InventarioSucursal.variante_id == var.id).first()
        assert inv_check.stock_fisico == 8
        assert inv_check.stock_reservado == 0
        print(f"PASS: CU15 - Excepción A1 capturada: Pago rechazado por pasarela externa.")
        print(f"             Rollback ejecutado: Stock físico preservado intacto ({inv_check.stock_fisico}) y stock reservado liberado ({inv_check.stock_reservado}).")

    # 3. Compra digital exitosa (reutiliza los 2 ítems del carrito)
    inv_check.stock_reservado = 2
    db.commit()

    venta_ecom_exitosa = VentaEcommerceCreate(
        cliente_id=cli.ci,
        sucursal_id=suc.id,
        metodo_pago_id=mp_stripe.id,
        token_pasarela="tok_aprobado_exitoso",
        nit_cliente="1234567",
        razon_social="María Suárez"
    )
    v_ecom_res = procesar_venta_ecommerce(venta_ecom_exitosa, db=db)
    assert v_ecom_res.total == 360.00
    assert v_ecom_res.factura is not None
    inv_check = db.query(InventarioSucursal).filter(InventarioSucursal.sucursal_id == suc.id, InventarioSucursal.variante_id == var.id).first()
    assert inv_check.stock_fisico == 6
    assert inv_check.stock_reservado == 0
    print(f"PASS: CU15 - Venta digital {v_ecom_res.factura.nro_factura} procesada con éxito.")
    print(f"             Descargo logístico definitivo: Stock físico = {inv_check.stock_fisico}, Stock reservado = {inv_check.stock_reservado}")

    # Listar ventas
    historial = listar_ventas(db=db)
    assert len(historial) == 2
    print(f"PASS: Listado general de auditoría de ventas recuperado ({len(historial)} ventas registradas)")

    print("\n==================================================================")
    print(" 100% DE PRUEBAS PARA CU14 Y CU15 SUPERADAS EXITOSAMENTE!")
    print(" LOGÍSTICA OMNICANAL, FACTURACIÓN Y ROLLBACK VERIFICADOS")
    print("==================================================================")


if __name__ == "__main__":
    run_tests()
