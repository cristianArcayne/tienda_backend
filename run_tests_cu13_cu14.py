"""
Suite de Pruebas Automatizadas para CU13 (Carrito de Compras Persistente) y CU14 (Ventas Físicas en POS).
Valida transacciones en base de datos, descargo físico de stock, facturación fiscal y compatibilidad.
"""
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from database import Base
import models
from models.seguridad_persona import Persona, Empleado, Cliente, Usuario, Rol
from models.catalogo import Categoria, Temporada, Proveedor, Ropa, Talla, Color, VariantePrenda
from models.sucursal import Sucursal, InventarioSucursal
from models.carrito import CarritoCompra, DetalleCarritoCompra
from models.venta import Venta, DetalleVenta, Factura, MetodoPago, TipoVenta

from schemas.carrito import DetalleCarritoCreate
from schemas.venta import VentaPOSCreate, ItemVentaCreate

from routers.carrito import (
    obtener_carrito,
    agregar_item,
    actualizar_item,
    eliminar_item,
    vaciar_carrito_v1,
    mi_carrito_compat,
    agregar_producto_compat,
    actualizar_cantidad_compat,
    quitar_producto_compat,
    vaciar_compat,
    ItemOperacionDto
)
from routers.ventas import (
    procesar_venta_pos,
    listar_ventas,
    obtener_venta
)

test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def setup_db(db):
    Base.metadata.create_all(bind=test_engine)

    # 1. Sucursal
    suc1 = Sucursal(nombre="FashionStore Central", direccion="Calle 21 Calacoto", ciudad="Santa Cruz")
    suc2 = Sucursal(nombre="FashionStore Equipetrol", direccion="Av. San Martín", ciudad="Santa Cruz")
    db.add_all([suc1, suc2])
    db.flush()

    # 2. Empleado Cajero y Cliente
    emp1 = Empleado(ci="1001", nombre="Carlos", apellido_pat="Vargas", correo="carlos@fashionstore.com", cargo="Cajero POS")
    cli1 = Cliente(ci="2001", nombre="María", apellido_pat="Fernández", correo="maria@fashionstore.com", telefono="+591 70011223")
    db.add_all([emp1, cli1])
    db.flush()

    # 3. Metodos de Pago y Tipos de Venta
    mp_efectivo = MetodoPago(id=1, nombre="Efectivo")
    mp_tarjeta = MetodoPago(id=2, nombre="Tarjeta POS")
    mp_qr = MetodoPago(id=3, nombre="QR Caja")
    tv_pos = TipoVenta(id=1, nombre="Presencial POS")
    tv_ecom = TipoVenta(id=2, nombre="Digital E-commerce")
    db.add_all([mp_efectivo, mp_tarjeta, mp_qr, tv_pos, tv_ecom])
    db.flush()

    # 4. Catálogo: Prenda y Variante
    cat = Categoria(nombre="Poleras")
    talla_l = Talla(medida="L")
    color_negro = Color(nombre="Negro", codigo_hex="#000000")
    db.add_all([cat, talla_l, color_negro])
    db.flush()

    ropa = Ropa(
        nombre="Polera Oversize Graphic",
        descripcion="Polera urbana 100% algodón",
        precio=150.00,
        categoria_id=cat.id
    )
    db.add(ropa)
    db.flush()

    var = VariantePrenda(cod_barra="VAR-POLERA-01", ropa_id=ropa.id, talla_id=talla_l.id, color_id=color_negro.id)
    db.add(var)
    db.flush()

    # Inventario: 20 unidades físicas en sucursal 1
    inv1 = InventarioSucursal(sucursal_id=suc1.id, variante_id=var.id, stock_fisico=20, stock_reservado=0)
    db.add(inv1)
    db.commit()

    return suc1, emp1, cli1, ropa, var, inv1


def run_tests():
    db = TestingSessionLocal()
    suc1, emp1, cli1, ropa, var, inv1 = setup_db(db)
    print("==================================================================")
    print(" INICIANDO VALIDACIÓN AUTOMATIZADA: CU13 Y CU14")
    print("==================================================================")

    # --- CU13: Carrito de Compras Persistente ---
    print("\n--- PRUEBAS CU13: Carrito Persistente ---")
    cart0 = obtener_carrito(cliente_id="2001", db=db)
    assert cart0.total_articulos == 0
    print("PASS: CU13 - Carrito inicial vacío recuperado")

    # Agregar prenda al carrito
    item_in = DetalleCarritoCreate(variante_id=var.id, cantidad=2, sucursal_id=suc1.id)
    cart1 = agregar_item("2001", item_in, db=db)
    assert cart1.total_articulos == 2
    assert cart1.monto_total == 300.00
    print(f"PASS: CU13 - Prenda añadida al carrito ({cart1.total_articulos} artículos, Total: Bs. {cart1.monto_total})")

    # Actualizar cantidad
    det_id = cart1.detalles[0].id
    cart2 = actualizar_item("2001", det_id, cantidad=5, db=db)
    assert cart2.total_articulos == 5
    assert cart2.monto_total == 750.00
    print(f"PASS: CU13 - Cantidad actualizada en base de datos (Total: Bs. {cart2.monto_total})")

    # Probar compatibilidad frontend (mi_carrito_compat y agregar_producto_compat)
    compat_res = mi_carrito_compat(cliente_ci="2001", db=db)
    assert compat_res["total"] == 750.00
    assert len(compat_res["detalles"]) == 1
    assert compat_res["detalles"][0]["variante_producto_info"]["producto_nombre"] == "Polera Oversize Graphic"
    print("PASS: CU13 - Endpoint /api/carrito/mi_carrito/ compatible con frontend Angular")

    # Vaciar carrito
    cart_vacio = vaciar_carrito_v1("2001", db=db)
    assert cart_vacio.total_articulos == 0
    print("PASS: CU13 - Carrito vaciado exitosamente en base de datos")

    # --- CU14: Procesar Ventas Físicas en POS ---
    print("\n--- PRUEBAS CU14: Procesar Ventas Físicas en POS ---")
    # Stock inicial en sucursal 1 = 20
    inv_check_ini = db.query(InventarioSucursal).filter(InventarioSucursal.sucursal_id == suc1.id, InventarioSucursal.variante_id == var.id).first()
    assert inv_check_ini.stock_fisico == 20

    # Registrar venta física de 3 unidades con billete de 500 Bs. (Total = 450 Bs, Cambio = 50 Bs)
    venta_in = VentaPOSCreate(
        sucursal_id=suc1.id,
        metodo_pago_id=1,  # Efectivo
        empleado_id=emp1.ci,
        cliente_id=cli1.ci,
        nit_cliente="1234567019",
        razon_social="María Fernández",
        monto_recibido=500.00,
        items=[ItemVentaCreate(variante_id=var.id, cantidad=3)]
    )

    venta_res = procesar_venta_pos(venta_in, db=db)
    assert venta_res.id is not None
    assert venta_res.estado_pago in ["COMPLETADA", "PAGADA"]
    assert venta_res.total == 450.00
    assert venta_res.monto_recibido == 500.00
    assert venta_res.cambio_devuelto == 50.00
    assert venta_res.factura is not None
    assert venta_res.factura.nit_cliente == "1234567019"
    assert "FAC-POS-" in venta_res.factura.nro_factura
    print(f"PASS: CU14 - Venta POS ID {venta_res.id} procesada exitosamente")
    print(f"       Factura: {venta_res.factura.nro_factura} | Total: Bs. {venta_res.total} | Cambio: Bs. {venta_res.cambio_devuelto}")

    # Verificar descargo físico de stock (20 - 3 = 17)
    inv_check_post = db.query(InventarioSucursal).filter(InventarioSucursal.sucursal_id == suc1.id, InventarioSucursal.variante_id == var.id).first()
    assert inv_check_post.stock_fisico == 17
    print(f"PASS: CU14 - Descargo físico verificado en almacén: {inv_check_ini.stock_fisico} -> {inv_check_post.stock_fisico} unidades")

    # Excepción A1: Stock Insuficiente en Mostrador
    try:
        venta_exceso = VentaPOSCreate(
            sucursal_id=suc1.id,
            metodo_pago_id=1,
            empleado_id=emp1.ci,
            cliente_id=cli1.ci,
            items=[ItemVentaCreate(variante_id=var.id, cantidad=50)]
        )
        procesar_venta_pos(venta_exceso, db=db)
        assert False, "Debió rechazar por stock insuficiente"
    except HTTPException as e:
        assert e.status_code == 400
        print("PASS: CU14 - Excepción A1 capturada: Venta rechazada por stock insuficiente en tienda")

    # Listar historial de ventas
    todas_ventas = listar_ventas(sucursal_id=suc1.id, db=db)
    assert len(todas_ventas) >= 1
    print(f"PASS: CU14 - Historial de ventas consultado ({len(todas_ventas)} registros)")

    print("\n==================================================================")
    print(" 100% DE PRUEBAS SUPERADAS PARA CU13 Y CU14 CON ÉXITO")
    print("==================================================================")


if __name__ == "__main__":
    run_tests()

