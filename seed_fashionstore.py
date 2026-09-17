"""
Script de Sembrado de Datos (Seeding) para FashionStore.
Inicializa y puebla las 29 entidades exactas del Diagrama de Clases UML de FashionStore.
"""
from datetime import datetime, date, timedelta
from database import engine, Base, SessionLocal
import models
from models.seguridad_persona import Persona, Empleado, Cliente, Usuario, Rol, Bitacora
from models.catalogo import Categoria, Temporada, Proveedor, Ropa, Talla, Color, VariantePrenda, Promocion, PromocionRopa, Resena
from models.sucursal import Sucursal, InventarioSucursal, Traspaso, DetalleTraspaso
from models.carrito import CarritoCompra, DetalleCarritoCompra
from models.reserva import Reserva, DetalleReserva
from models.venta import MetodoPago, TipoVenta, Venta, DetalleVenta, Factura


def seed_datos():
    # 1. Crear tablas en SQLite/PostgreSQL
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("Iniciando sembrado de las 29 entidades del Diagrama UML de FashionStore...")

    # =========================================================================
    # 1. ROLES Y USUARIOS DE SEGURIDAD
    # =========================================================================
    roles_data = ["Administrador", "Cajero POS", "Vendedor", "Cliente"]
    roles_db = {}
    for r_nom in roles_data:
        r = db.query(Rol).filter(Rol.nombre == r_nom).first()
        if not r:
            r = Rol(nombre=r_nom)
            db.add(r)
            db.flush()
        roles_db[r_nom] = r

    # Personas y Empleados
    emp1 = db.query(Empleado).filter(Empleado.ci == 1001).first()
    if not emp1:
        emp1 = Empleado(
            ci=1001,
            nombre="Carlos Pérez (Cajero Central)",
            telefono="+591 70011223",
            correo="carlos.perez@fashionstore.bo",
            fec_contratacion=date(2025, 1, 15)
        )
        db.add(emp1)
        db.flush()

    emp2 = db.query(Empleado).filter(Empleado.ci == 1002).first()
    if not emp2:
        emp2 = Empleado(
            ci=1002,
            nombre="Ana Ramos (Vendedora Equipetrol)",
            telefono="+591 70044556",
            correo="ana.ramos@fashionstore.bo",
            fec_contratacion=date(2025, 3, 1)
        )
        db.add(emp2)
        db.flush()

    # Clientes
    cli1 = db.query(Cliente).filter(Cliente.ci == 2001).first()
    if not cli1:
        cli1 = Cliente(
            ci=2001,
            nombre="Carla Gutiérrez",
            telefono="+591 71099887",
            correo="carla.gutierrez@gmail.com",
            preferencia_talla="M"
        )
        db.add(cli1)
        db.flush()

    cli2 = db.query(Cliente).filter(Cliente.ci == 2002).first()
    if not cli2:
        cli2 = Cliente(
            ci=2002,
            nombre="Carlos Mendoza",
            telefono="+591 72033445",
            correo="carlos.mendoza@gmail.com",
            preferencia_talla="L"
        )
        db.add(cli2)
        db.flush()

    # Usuarios para login
    usr_admin = db.query(Usuario).filter(Usuario.nombre_usuario == "admin").first()
    if not usr_admin:
        usr_admin = Usuario(
            nombre_usuario="admin",
            contrasena="admin123",
            estado="ACTIVO",
            persona_ci=emp1.ci,
            rol_id=roles_db["Administrador"].id
        )
        db.add(usr_admin)
        db.flush()

    # Bitácora
    db.add(Bitacora(accion="Inicio de sesión en el sistema", ip_usuario="127.0.0.1", usuario_id=usr_admin.id))
    db.flush()

    # =========================================================================
    # 2. PARÁMETROS DE MODA, CATEGORÍAS, PROVEEDORES Y TEMPORADAS
    # =========================================================================
    categorias_nombres = ["Denim & Mezclilla", "Casual & Tops", "Vestidos & Gala", "Calzado Urbano"]
    categorias_db = {}
    for c_nom in categorias_nombres:
        c = db.query(Categoria).filter(Categoria.nombre == c_nom).first()
        if not c:
            c = Categoria(nombre=c_nom)
            db.add(c)
            db.flush()
        categorias_db[c_nom] = c

    temporadas_nombres = ["Verano 2026", "Otoño 2026", "Invierno 2026", "Primavera 2026"]
    temporadas_db = {}
    for t_nom in temporadas_nombres:
        t = db.query(Temporada).filter(Temporada.nombre == t_nom).first()
        if not t:
            t = Temporada(nombre=t_nom)
            db.add(t)
            db.flush()
        temporadas_db[t_nom] = t

    prov1 = db.query(Proveedor).filter(Proveedor.razon_social == "Textiles Andinos S.R.L.").first()
    if not prov1:
        prov1 = Proveedor(
            razon_social="Textiles Andinos S.R.L.",
            telefono="+591 3 3322110",
            contacto="Ing. Juan Pablo Rocha"
        )
        db.add(prov1)
        db.flush()

    # Tallas y Colores
    tallas_list = ["XS", "S", "M", "L", "XL", "38", "40", "42"]
    tallas_db = {}
    for med in tallas_list:
        t = db.query(Talla).filter(Talla.medida == med).first()
        if not t:
            t = Talla(medida=med)
            db.add(t)
            db.flush()
        tallas_db[med] = t

    colores_data = [
        {"nombre": "Azul Denim", "codigo_hex": "#1E3A8A"},
        {"nombre": "Negro Clásico", "codigo_hex": "#000000"},
        {"nombre": "Blanco Puro", "codigo_hex": "#FFFFFF"},
        {"nombre": "Beige Lino", "codigo_hex": "#F5F5DC"}
    ]
    colores_db = {}
    for c_data in colores_data:
        col = db.query(Color).filter(Color.nombre == c_data["nombre"]).first()
        if not col:
            col = Color(nombre=c_data["nombre"], codigo_hex=c_data["codigo_hex"])
            db.add(col)
            db.flush()
        colores_db[c_data["nombre"]] = col

    # =========================================================================
    # 3. ROPA (PRENDAS BASE CON MODELOS 3D AR) Y VARIANTES DE PRENDA
    # =========================================================================
    prendas_seed = [
        {
            "nombre": "Chaqueta Denim Unisex AR",
            "descripcion": "Chaqueta denim 100% algodón con lavado vintage. Compatible con Realidad Aumentada.",
            "precio": 320.00,
            "imagen_uri": "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?w=600",
            "modelo_3d_uri": "https://assets.fashionstore.bo/3d/chaqueta_denim.glb",
            "categoria": "Denim & Mezclilla",
            "temporada": "Otoño 2026",
            "variantes": [
                {"cod_barra": "777001001", "talla": "S", "color": "Azul Denim"},
                {"cod_barra": "777001002", "talla": "M", "color": "Azul Denim"},
                {"cod_barra": "777001003", "talla": "L", "color": "Azul Denim"},
            ]
        },
        {
            "nombre": "Camisa Lino Puro Manga Larga",
            "descripcion": "Camisa ligera y transpirable en lino orgánico.",
            "precio": 180.00,
            "imagen_uri": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=600",
            "modelo_3d_uri": "https://assets.fashionstore.bo/3d/camisa_lino.glb",
            "categoria": "Casual & Tops",
            "temporada": "Verano 2026",
            "variantes": [
                {"cod_barra": "777002001", "talla": "M", "color": "Blanco Puro"},
                {"cod_barra": "777002002", "talla": "L", "color": "Beige Lino"},
            ]
        },
        {
            "nombre": "Vestido Gala Noche Noir 3D",
            "descripcion": "Vestido formal de alta costura con escote en espalda y probador virtual 3D.",
            "precio": 540.00,
            "imagen_uri": "https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=600",
            "modelo_3d_uri": "https://assets.fashionstore.bo/3d/vestido_gala.glb",
            "categoria": "Vestidos & Gala",
            "temporada": "Invierno 2026",
            "variantes": [
                {"cod_barra": "777003001", "talla": "S", "color": "Negro Clásico"},
                {"cod_barra": "777003002", "talla": "M", "color": "Negro Clásico"},
            ]
        }
    ]

    variantes_db = []
    for p_data in prendas_seed:
        ropa = db.query(Ropa).filter(Ropa.nombre == p_data["nombre"]).first()
        if not ropa:
            ropa = Ropa(
                nombre=p_data["nombre"],
                descripcion=p_data["descripcion"],
                precio=p_data["precio"],
                imagen_uri=p_data["imagen_uri"],
                modelo_3d_uri=p_data["modelo_3d_uri"],
                categoria_id=categorias_db[p_data["categoria"]].id,
                temporada_id=temporadas_db[p_data["temporada"]].id,
                proveedor_id=prov1.id
            )
            db.add(ropa)
            db.flush()

        for v_item in p_data["variantes"]:
            var = db.query(VariantePrenda).filter(VariantePrenda.cod_barra == v_item["cod_barra"]).first()
            if not var:
                var = VariantePrenda(
                    cod_barra=v_item["cod_barra"],
                    ropa_id=ropa.id,
                    talla_id=tallas_db[v_item["talla"]].id,
                    color_id=colores_db[v_item["color"]].id
                )
                db.add(var)
                db.flush()
            variantes_db.append(var)

    # Promociones
    promo1 = db.query(Promocion).filter(Promocion.nombre == "Descuento Especial Temporada").first()
    if not promo1:
        promo1 = Promocion(
            nombre="Descuento Especial Temporada",
            porcentaje_descuento=15.00,
            fecha_inicio=date.today() - timedelta(days=5),
            fecha_fin=date.today() + timedelta(days=25)
        )
        db.add(promo1)
        db.flush()
        # Asociar a la primera prenda
        ropa_primera = db.query(Ropa).first()
        if ropa_primera:
            db.add(PromocionRopa(promocion_id=promo1.id, ropa_id=ropa_primera.id, estado="ACTIVA"))
            db.flush()

    # Reseñas
    res1 = db.query(Resena).filter(Resena.cliente_id == cli1.ci).first()
    if not res1 and variantes_db:
        res1 = Resena(
            puntuacion_estrellas=5,
            comentario="Excelente calidad de tela y el modelo 3D en la app móvil me permitió ver cómo me quedaba.",
            cliente_id=cli1.ci,
            ropa_id=variantes_db[0].ropa_id
        )
        db.add(res1)
        db.flush()

    # =========================================================================
    # 4. SUCURSALES E INVENTARIO POR TIENDA (FÍSICO, RESERVADO, DISPONIBLE)
    # =========================================================================
    sucursales_data = [
        {"nombre": "FashionStore Central", "ciudad": "Santa Cruz", "direccion": "Calle 21 de Calacoto #100", "telefono": "+591 3 3344551"},
        {"nombre": "FashionStore Equipetrol", "ciudad": "Santa Cruz", "direccion": "Av. San Martín esq. Calle 5", "telefono": "+591 3 3344552"},
        {"nombre": "FashionStore Ventura Mall", "ciudad": "Santa Cruz", "direccion": "4to Anillo esq. Av. San Martín, Local 142", "telefono": "+591 3 3344553"},
    ]
    sucursales_db = []
    for s_info in sucursales_data:
        suc = db.query(Sucursal).filter(Sucursal.nombre == s_info["nombre"]).first()
        if not suc:
            suc = Sucursal(**s_info)
            db.add(suc)
            db.flush()
        sucursales_db.append(suc)

    # Poblar InventarioSucursal para cada variante en cada tienda
    for suc in sucursales_db:
        for var in variantes_db:
            inv = db.query(InventarioSucursal).filter(
                InventarioSucursal.sucursal_id == suc.id,
                InventarioSucursal.variante_id == var.id
            ).first()
            if not inv:
                stock_f = 12 if "Central" in suc.nombre else 8
                stock_r = 2 if "Central" in suc.nombre else 0
                inv = InventarioSucursal(
                    sucursal_id=suc.id,
                    variante_id=var.id,
                    stock_fisico=stock_f,
                    stock_reservado=stock_r,
                    stock_disponible=(stock_f - stock_r)
                )
                db.add(inv)
                db.flush()

    # Traspaso logístico de prueba
    trasp = db.query(Traspaso).first()
    if not trasp and len(sucursales_db) >= 2 and variantes_db:
        trasp = Traspaso(
            fecha=date.today(),
            estado="RECIBIDO",
            empleado_id=emp1.ci,
            sucursal_origen_id=sucursales_db[0].id,
            sucursal_destino_id=sucursales_db[1].id
        )
        db.add(trasp)
        db.flush()
        db.add(DetalleTraspaso(traspaso_id=trasp.id, variante_id=variantes_db[0].id, cantidad=4))
        db.flush()

    # =========================================================================
    # 5. CARRITO DE COMPRA Y RESERVA WEB-TO-STORE
    # =========================================================================
    cart1 = db.query(CarritoCompra).filter(CarritoCompra.cliente_id == cli1.ci).first()
    if not cart1 and variantes_db:
        cart1 = CarritoCompra(fecha_creacion=date.today(), cliente_id=cli1.ci)
        db.add(cart1)
        db.flush()
        db.add(DetalleCarritoCompra(carrito_id=cart1.id, variante_id=variantes_db[0].id, cantidad=1))
        db.flush()

    reserva1 = db.query(Reserva).filter(Reserva.cliente_id == cli2.ci).first()
    if not reserva1 and variantes_db:
        reserva1 = Reserva(
            fecha=date.today(),
            hora_estimada="17:00",
            estado="PENDIENTE",
            cliente_id=cli2.ci,
            sucursal_id=sucursales_db[0].id
        )
        db.add(reserva1)
        db.flush()
        db.add(DetalleReserva(reserva_id=reserva1.id, variante_id=variantes_db[1].id, cantidad=1))
        db.flush()

    # =========================================================================
    # 6. MÉTODOS DE PAGO, TIPOS DE VENTA, VENTAS Y FACTURAS
    # =========================================================================
    metodos_data = ["Efectivo", "Tarjeta POS", "QR Caja", "Stripe", "Libélula QR", "PayPal"]
    metodos_db = {}
    for m_nom in metodos_data:
        m = db.query(MetodoPago).filter(MetodoPago.nombre == m_nom).first()
        if not m:
            m = MetodoPago(nombre=m_nom)
            db.add(m)
            db.flush()
        metodos_db[m_nom] = m

    tipos_data = ["Presencial POS", "Digital E-commerce Web", "Digital App Móvil"]
    tipos_db = {}
    for t_nom in tipos_data:
        tp = db.query(TipoVenta).filter(TipoVenta.nombre == t_nom).first()
        if not tp:
            tp = TipoVenta(nombre=t_nom)
            db.add(tp)
            db.flush()
        tipos_db[t_nom] = tp

    # Ventas de prueba (POS y Digital)
    v1 = db.query(Venta).filter(Venta.codigo_transaccion == "TRX-POS-2026-001").first()
    if not v1 and variantes_db:
        v1 = Venta(
            fecha=datetime.now() - timedelta(days=2),
            total=320.00,
            codigo_transaccion="TRX-POS-2026-001",
            estado_pago="PAGADA",
            empleado_id=emp1.ci,
            cliente_id=cli1.ci,
            sucursal_id=sucursales_db[0].id,
            metodo_pago_id=metodos_db["Efectivo"].id,
            tipo_venta_id=tipos_db["Presencial POS"].id
        )
        db.add(v1)
        db.flush()
        db.add(DetalleVenta(venta_id=v1.id, variante_id=variantes_db[0].id, cantidad=1, subtotal=320.00))
        db.flush()
        db.add(Factura(
            nro_factura="FAC-POS-00101",
            nit_cliente="4829102",
            razon_social="Carla Gutiérrez",
            fecha_emision=datetime.now() - timedelta(days=2),
            venta_id=v1.id
        ))
        db.flush()

    v2 = db.query(Venta).filter(Venta.codigo_transaccion == "TRX-WEB-2026-002").first()
    if not v2 and len(variantes_db) >= 2:
        v2 = Venta(
            fecha=datetime.now() - timedelta(days=1),
            total=180.00,
            codigo_transaccion="TRX-WEB-2026-002",
            estado_pago="PAGADA",
            empleado_id=None,
            cliente_id=cli2.ci,
            sucursal_id=sucursales_db[0].id,
            metodo_pago_id=metodos_db["Libélula QR"].id,
            tipo_venta_id=tipos_db["Digital E-commerce Web"].id
        )
        db.add(v2)
        db.flush()
        db.add(DetalleVenta(venta_id=v2.id, variante_id=variantes_db[1].id, cantidad=1, subtotal=180.00))
        db.flush()
        db.add(Factura(
            nro_factura="FAC-WEB-00102",
            nit_cliente="1029384",
            razon_social="Carlos Mendoza",
            fecha_emision=datetime.now() - timedelta(days=1),
            venta_id=v2.id
        ))
        db.flush()

    db.commit()
    db.close()
    print("Sembrado de datos completado exitosamente con las 29 entidades!")


if __name__ == "__main__":
    seed_datos()
