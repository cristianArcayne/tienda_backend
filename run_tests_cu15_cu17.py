"""
Script de Validación Automatizada para CU15 (Ventas Digitales E-commerce) y CU17 (Recomendador Inteligente IA).
Conexión directa a PostgreSQL sin mocks.
"""
import sys
import os

from database import SessionLocal
from models.catalogo import Ropa, Categoria, VariantePrenda
from models.sucursal import Sucursal, InventarioSucursal
from models.seguridad_persona import Cliente, Persona
from models.carrito import CarritoCompra, DetalleCarritoCompra
from models.venta import Venta, DetalleVenta, Factura, MetodoPago, TipoVenta
from models.innovacion import RecomendacionIA

from routers.ventas import _ejecutar_venta_pos_core, procesar_venta_ecommerce
from routers.recomendador_ia import generar_outfit, agregar_outfit_a_carrito, registrar_feedback, chat_personal_shopper, OutfitACarritoRequest
from schemas.venta import VentaEcommerceCreate, ItemVentaCreate
from schemas.innovacion import GenerarOutfitRequest, FeedbackRecomendacionRequest, ChatMessageRequest


def test_cu15_ecommerce():
    print("\n--- PRUEBAS CU15: Procesar Ventas Digitales E-commerce ---")
    db = SessionLocal()
    try:
        # 1. Preparar o verificar Cliente
        cliente = db.query(Cliente).first()
        if not cliente:
            persona = db.query(Persona).first()
            if persona:
                cliente = Cliente(ci=persona.ci, nombre=persona.nombre, apellido_pat=persona.apellido_pat, correo=persona.correo, tipo_persona="CLIENTE")
                db.add(cliente)
                db.commit()
                db.refresh(cliente)

        assert cliente is not None, "Debe existir un cliente en la BD"
        cliente_ci = cliente.ci

        # 2. Sucursal y Variante
        sucursal = db.query(Sucursal).first()
        assert sucursal is not None, "Debe existir al menos una sucursal"

        variante = db.query(VariantePrenda).first()
        assert variante is not None, "Debe existir al menos una variante"

        inv = db.query(InventarioSucursal).filter(
            InventarioSucursal.sucursal_id == sucursal.id,
            InventarioSucursal.variante_id == variante.id
        ).first()

        if not inv or inv.stock_fisico < 10:
            if not inv:
                inv = InventarioSucursal(sucursal_id=sucursal.id, variante_id=variante.id, stock_fisico=20, stock_reservado=0)
                db.add(inv)
            else:
                inv.stock_fisico = 20
                inv.stock_reservado = 0
            db.commit()
            db.refresh(inv)

        stock_inicial = inv.stock_fisico

        # 3. Poblar Carrito Persistente del Cliente
        carrito = db.query(CarritoCompra).filter(CarritoCompra.cliente_id == cliente_ci).first()
        if not carrito:
            carrito = CarritoCompra(cliente_id=cliente_ci)
            db.add(carrito)
            db.flush()

        db.query(DetalleCarritoCompra).filter(DetalleCarritoCompra.carrito_id == carrito.id).delete()
        db.add(DetalleCarritoCompra(carrito_id=carrito.id, variante_id=variante.id, cantidad=2))
        db.commit()
        db.refresh(carrito)

        assert len(carrito.detalles) == 1, "El carrito debe contener 1 detalle con 2 prendas"
        print(f"PASS: CU15 - Carrito del cliente {cliente_ci} preparado con {carrito.detalles[0].cantidad} unidades")

        # 4. Procesar Venta Digital E-commerce
        v_ecom = VentaEcommerceCreate(
            cliente_id=str(cliente_ci),
            sucursal_id=sucursal.id,
            metodo_pago_id=2, # Tarjeta
            nit_cliente="1234567019",
            razon_social="Corporación Digital S.A.",
            direccion_envio="Av. Banzer Km 5.5, Santa Cruz"
        )

        venta_resp = procesar_venta_ecommerce(v_ecom, db)
        assert venta_resp.id is not None, "La venta digital debe haber sido creada con ID"
        assert venta_resp.codigo_transaccion.startswith("TRX-ECOM"), f"Código TRX debe ser E-commerce: {venta_resp.codigo_transaccion}"
        assert venta_resp.factura is not None, "Debe haberse emitido la Factura fiscal"
        assert venta_resp.factura.nro_factura.startswith("FAC-ECOM"), f"Factura debe ser E-commerce: {venta_resp.factura.nro_factura}"
        assert venta_resp.factura.nit_cliente == "1234567019"
        print(f"PASS: CU15 - Venta Digital ID {venta_resp.id} procesada exitosamente")
        print(f"       Factura: {venta_resp.factura.nro_factura} | Total: Bs. {venta_resp.total} | TRX: {venta_resp.codigo_transaccion}")

        # 5. Verificar descargo físico de inventario
        db.refresh(inv)
        assert inv.stock_fisico == stock_inicial - 2, f"Stock debió reducirse en 2 (de {stock_inicial} a {stock_inicial-2}), actual: {inv.stock_fisico}"
        print(f"PASS: CU15 - Descargo físico verificado en PostgreSQL: {stock_inicial} -> {inv.stock_fisico} unidades")

        # 6. Verificar que el carrito quedó vacío
        db.refresh(carrito)
        detalles_post = db.query(DetalleCarritoCompra).filter(DetalleCarritoCompra.carrito_id == carrito.id).count()
        assert detalles_post == 0, f"El carrito debió vaciarse automáticamente, quedan: {detalles_post}"
        print("PASS: CU15 - Carrito persistente vaciado de forma atómica tras confirmación de compra")

    finally:
        db.close()


def test_cu17_recomendador_ia():
    print("\n--- PRUEBAS CU17: Recomendador Inteligente (IA) ---")
    db = SessionLocal()
    try:
        cliente = db.query(Cliente).first()
        cliente_ci = cliente.ci if cliente else "2001"

        # 1. Generar Outfit Inteligente
        req = GenerarOutfitRequest(
            cliente_id=str(cliente_ci),
            ocasion="Formal",
            estilo_preferido="Vanguardia"
        )
        outfit = generar_outfit(req, db)
        assert outfit is not None, "Debe retornar un outfit"
        assert outfit.prenda_principal is not None, "Debe tener prenda principal"
        assert len(outfit.prendas_complementarias) >= 1, "Debe tener al menos una prenda complementaria"
        assert outfit.descuento_combo_aplicable > 0, "Debe calcular descuento promocional por combo"
        assert outfit.precio_final_con_descuento < outfit.precio_total_outfit, "El precio final con descuento debe ser menor"
        print(f"PASS: CU17 - Outfit '{outfit.outfit_nombre}' generado con {outfit.score_afinidad}% de afinidad IA")
        print(f"       Total regular: Bs. {outfit.precio_total_outfit} | Descuento combo: Bs. {outfit.descuento_combo_aplicable} | Final: Bs. {outfit.precio_final_con_descuento}")

        # 2. Verificar persistencia en RecomendacionIA
        rec_db = db.query(RecomendacionIA).filter(RecomendacionIA.cliente_id == str(cliente_ci)).order_by(RecomendacionIA.id.desc()).first()
        assert rec_db is not None, "Debe persistir en la tabla recomendaciones_ia"
        print(f"PASS: CU17 - Recomendación persistida en PostgreSQL con ID {rec_db.id} y score {rec_db.score_afinidad}%")

        # 3. Registrar Feedback
        fb_req = FeedbackRecomendacionRequest(
            recomendacion_id=rec_db.id,
            aceptada=True,
            comentario="Excelente combinación para la fiesta de gala"
        )
        fb_resp = registrar_feedback(fb_req, db)
        assert fb_resp["aceptada"] is True
        print(f"PASS: CU17 - Feedback del cliente registrado en PostgreSQL (Aceptada = {fb_resp['aceptada']})")

        # 4. Añadir Outfit al Carrito Persistente
        ropa_ids = [outfit.prenda_principal.ropa_id] + [p.ropa_id for p in outfit.prendas_complementarias]
        outfit_cart_req = OutfitACarritoRequest(
            cliente_id=str(cliente_ci),
            ropa_ids=ropa_ids
        )
        cart_resp = agregar_outfit_a_carrito(outfit_cart_req, db)
        assert cart_resp["items_agregados"] > 0, "Debe haber agregado prendas al carrito"
        print(f"PASS: CU17 - {cart_resp['items_agregados']} prendas del combo añadidas al Carrito en PostgreSQL")

        # 5. Chatbot Personal Shopper
        chat_req = ChatMessageRequest(
            mensaje="Hola, necesito un outfit elegante para una boda de noche",
            cliente_id=str(cliente_ci)
        )
        chat_resp = chat_personal_shopper(chat_req, db)
        assert chat_resp.respuesta_texto is not None
        assert chat_resp.outfit_recomendado is not None
        print(f"PASS: CU17 - Chat Personal Shopper respondió correctamente con outfit ocasión '{chat_resp.outfit_recomendado.ocasion}'")

    finally:
        db.close()


if __name__ == "__main__":
    print("==================================================================")
    print(" INICIANDO VALIDACIÓN AUTOMATIZADA: CU15 Y CU17")
    print("==================================================================")
    test_cu15_ecommerce()
    test_cu17_recomendador_ia()
    print("\n==================================================================")
    print(" 100% DE PRUEBAS SUPERADAS PARA CU15 Y CU17 CON ÉXITO")
    print("==================================================================")

