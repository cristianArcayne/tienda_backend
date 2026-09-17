"""
Suite de Pruebas Automatizadas para CU16, CU17, CU18 y CU19 con los modelos UML de FashionStore.
Valida Vestidor Virtual (AR), Recomendador Inteligente (IA), Reportes por Comandos de Voz y Reseñas.
"""
import unittest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
import models
from models.seguridad_persona import Cliente
from models.catalogo import Categoria, Temporada, Proveedor, Ropa, Talla, Color, VariantePrenda, Resena
from models.sucursal import Sucursal, InventarioSucursal
from models.venta import MetodoPago, TipoVenta, Venta, DetalleVenta, Factura

from schemas.innovacion import (
    ValidarAjusteCorporalRequest,
    GenerarOutfitRequest,
    FeedbackRecomendacionRequest,
    ComandoVozTextoRequest,
    ResenaCreateRequest
)
from routers.ar_vestidor import (
    listar_prendas_ar,
    obtener_metadatos_ar_prenda,
    validar_ajuste_corporal
)
from routers.recomendador_ia import (
    generar_outfit,
    listar_sugerencias_cliente,
    registrar_feedback
)
from routers.reportes_voz import procesar_comando_voz_texto
from routers.resenas_calificaciones import (
    crear_resena,
    listar_resenas_prenda,
    obtener_resumen_calificaciones,
    eliminar_resena
)

test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def inicializar_bd(db):
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    # 1. Sucursal
    suc = Sucursal(nombre="Sucursal Central Test", ciudad="Santa Cruz", direccion="Av. Principal")
    db.add(suc)
    db.flush()


    # 2. Cliente
    cli = Cliente(ci=2001, nombre="Elena Morales", telefono="70012345", correo="elena@test.com")
    db.add(cli)
    db.flush()

    # 3. Categorías
    cat_dnm = Categoria(nombre="Denim")
    cat_cas = Categoria(nombre="Casual")
    cat_ves = Categoria(nombre="Vestidos")
    db.add_all([cat_dnm, cat_cas, cat_ves])
    db.flush()

    # 4. Tallas y Colores
    t_m = Talla(medida="M")
    t_l = Talla(medida="L")
    c_blu = Color(nombre="Azul Denim", codigo_hex="#1E3A8A")
    c_blk = Color(nombre="Negro", codigo_hex="#000000")
    db.add_all([t_m, t_l, c_blu, c_blk])
    db.flush()

    # 5. Prendas con Modelos 3D (.glb)
    r1 = Ropa(
        nombre="Chaqueta Denim Vintage",
        precio=350.00,
        imagen_uri="https://img.test/chaqueta.jpg",
        modelo_3d_uri="https://models.test/chaqueta_vintage.glb",
        categoria_id=cat_dnm.id
    )
    r2 = Ropa(
        nombre="Polera Oversize Algodón",
        precio=120.00,
        imagen_uri="https://img.test/polera.jpg",
        modelo_3d_uri="https://models.test/polera_oversize.glb",
        categoria_id=cat_cas.id
    )
    r3 = Ropa(
        nombre="Vestido Seda Floral",
        precio=450.00,
        imagen_uri="https://img.test/vestido.jpg",
        modelo_3d_uri="https://models.test/vestido_floral.glb",
        categoria_id=cat_ves.id
    )
    db.add_all([r1, r2, r3])
    db.flush()

    # 6. Variantes e Inventario
    v1 = VariantePrenda(cod_barra="777001", ropa_id=r1.id, talla_id=t_m.id, color_id=c_blu.id)
    v2 = VariantePrenda(cod_barra="777002", ropa_id=r2.id, talla_id=t_m.id, color_id=c_blk.id)
    db.add_all([v1, v2])
    db.flush()

    inv1 = InventarioSucursal(sucursal_id=suc.id, variante_id=v1.id, stock_fisico=20, stock_reservado=0, stock_disponible=20)
    inv2 = InventarioSucursal(sucursal_id=suc.id, variante_id=v2.id, stock_fisico=3, stock_reservado=0, stock_disponible=3)
    db.add_all([inv1, inv2])
    db.flush()


    # 7. Métodos y Tipos de Venta
    mp = MetodoPago(nombre="Efectivo en Caja")
    tv = TipoVenta(nombre="Presencial POS")
    db.add_all([mp, tv])
    db.flush()

    # 8. Venta de prueba
    vta = Venta(
        cliente_id=cli.ci,
        sucursal_id=suc.id,
        tipo_venta_id=tv.id,
        metodo_pago_id=mp.id,
        total=350.00,
        codigo_transaccion="TRX-TEST-CU18-001",
        estado_pago="PAGADA"
    )
    db.add(vta)
    db.flush()


    det_vta = DetalleVenta(
        venta_id=vta.id,
        variante_id=v1.id,
        cantidad=1,
        subtotal=350.00
    )
    db.add(det_vta)
    db.commit()



class TestCU16aCU19(unittest.TestCase):

    def setUp(self):
        self.db = TestingSessionLocal()
        inicializar_bd(self.db)

    def tearDown(self):
        self.db.close()

    # =========================================================================
    # CU16: VESTIDOR VIRTUAL (AR)
    # =========================================================================
    def test_01_cu16_vestidor_virtual_catalogo_y_metadatos(self):
        """CU16: Listado de catálogo 3D y metadatos de renderizado para app móvil"""
        prendas_ar = listar_prendas_ar(categoria_id=None, db=self.db)
        self.assertGreaterEqual(len(prendas_ar), 3)
        self.assertTrue(prendas_ar[0].modelo_3d_uri.endswith(".glb"))
        self.assertIn(prendas_ar[0].posicion_anclaje, ["TORSO", "LEGS", "FULL_BODY", "FEET"])

        # Metadatos de prenda específica
        meta = obtener_metadatos_ar_prenda(ropa_id=1, db=self.db)
        self.assertEqual(meta.ropa_id, 1)
        self.assertEqual(meta.formato_3d, "glb")
        self.assertTrue(meta.soporta_ar_flutter)

        # Validación biométrica
        ajuste = validar_ajuste_corporal(
            ValidarAjusteCorporalRequest(
                ropa_id=1,
                altura_cm=175.0,
                pecho_cm=96.0,
                cintura_cm=82.0,
                cadera_cm=98.0
            ),
            db=self.db
        )
        self.assertEqual(ajuste.talla_recomendada, "M")
        self.assertGreaterEqual(ajuste.porcentaje_calce, 90.0)
        print("  [OK] CU16: Vestidor Virtual AR (Catálogo 3D, Metadatos y Ajuste Biométrico).")

    # =========================================================================
    # CU17: RECOMENDADOR INTELIGENTE (IA)
    # =========================================================================
    def test_02_cu17_recomendador_ia_outfits_y_feedback(self):
        """CU17: Generación de Outfit inteligente (Cross-Selling) y registro de Feedback"""
        req = GenerarOutfitRequest(cliente_id=2001, ropa_principal_id=1, ocasion="Casual")
        outfit = generar_outfit(req, db=self.db)
        
        self.assertIn("Outfit", outfit.outfit_nombre)
        self.assertGreater(outfit.score_afinidad, 90.0)
        self.assertGreater(outfit.descuento_combo_aplicable, 0)
        self.assertEqual(
            outfit.precio_final_con_descuento,
            round(outfit.precio_total_outfit - outfit.descuento_combo_aplicable, 2)
        )

        # Sugerencias por cliente
        sugs = listar_sugerencias_cliente(cliente_ci=2001, db=self.db)
        self.assertGreaterEqual(len(sugs), 1)

        # Feedback
        fb = registrar_feedback(
            FeedbackRecomendacionRequest(recomendacion_id=outfit.id or 1, aceptada=True),
            db=self.db
        )
        self.assertIn("registrado", fb["mensaje"])
        print("  [OK] CU17: Recomendador Inteligente IA (Outfit Cross-Selling y Feedback).")

    # =========================================================================
    # CU18: REPORTES MEDIANTE COMANDOS DE VOZ & ANALÍTICA
    # =========================================================================
    def test_03_cu18_reportes_comandos_voz_analitica(self):
        """CU18: Procesamiento de comandos de voz con generación de KPIs y gráficos"""
        # Comando: Ventas por sucursal
        r_suc = procesar_comando_voz_texto(
            ComandoVozTextoRequest(comando_voz="Ventas por sucursal"),
            db=self.db
        )
        self.assertEqual(r_suc.intencion_detectada, "VENTAS_POR_SUCURSAL")
        self.assertEqual(r_suc.datos_grafico.tipo_grafico, "bar")
        self.assertIn("Bs.", r_suc.resumen_ejecutivo)

        # Comando: Productos más vendidos
        r_top = procesar_comando_voz_texto(
            ComandoVozTextoRequest(comando_voz="Cuáles son los productos más vendidos"),
            db=self.db
        )
        self.assertEqual(r_top.intencion_detectada, "PRODUCTOS_MAS_VENDIDOS")

        # Comando: Alertas de inventario
        r_stock = procesar_comando_voz_texto(
            ComandoVozTextoRequest(comando_voz="Mostrar alertas de stock crítico"),
            db=self.db
        )
        self.assertEqual(r_stock.intencion_detectada, "STOCK_CRITICO")
        print("  [OK] CU18: Comandos de Voz y Analítica (Ventas, Top Productos, Stock Crítico).")

    # =========================================================================
    # CU19: GESTIONAR RESEÑAS Y CALIFICACIONES
    # =========================================================================
    def test_04_cu19_resenas_calificaciones_y_resumen(self):
        """CU19: Creación de reseña, consulta de histograma de satisfacción y eliminación"""
        # Crear reseña
        res_in = ResenaCreateRequest(
            ropa_id=1,
            cliente_ci=2001,
            puntuacion_estrellas=5,
            comentario="Excelente calce y tela de primera."
        )
        res_creada = crear_resena(res_in, db=self.db)
        self.assertEqual(res_creada.puntuacion_estrellas, 5)

        # Listar reseñas de la prenda
        lista = listar_resenas_prenda(ropa_id=1, limit=10, db=self.db)
        self.assertGreaterEqual(len(lista), 1)

        # Consultar métricas de satisfacción
        resumen = obtener_resumen_calificaciones(ropa_id=1, db=self.db)
        self.assertEqual(resumen.promedio_calificacion, 5.0)
        self.assertEqual(resumen.total_resenas, 1)
        self.assertEqual(resumen.desglose_estrellas.estrella_5, 1)

        # Eliminar reseña
        del_resp = eliminar_resena(resena_id=res_creada.id, db=self.db)
        self.assertIn("eliminada", del_resp["mensaje"])
        print("  [OK] CU19: Gestión de Reseñas y Calificaciones (Métricas, Histograma y CRUD).")


if __name__ == "__main__":
    print("\n==================================================================")
    print("EJECUTANDO SUITE DE PRUEBAS AUTOMATIZADAS CU16, CU17, CU18, CU19")
    print("==================================================================\n")
    unittest.main(verbosity=2)
