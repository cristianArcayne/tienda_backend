import time
import os
from database import SessionLocal
from models.catalogo import Ropa, VariantePrenda
from models.sucursal import InventarioSucursal, Sucursal

def insertar_prendas_variadas():
    db = SessionLocal()
    try:
        sucursal = db.query(Sucursal).first()
        suc_id = sucursal.id if sucursal else 1

        prendas_data = [
            # POLERAS DE DIFERENTE MODELO
            {
                "nombre": "Polera Oversize Negra Urban",
                "descripcion": "Polera oversize de corte urbano en algodón peinado premium",
                "precio": 139.00,
                "costo_estandar": 70.00,
                "imagen_uri": "/static/uploads/polera_oversize_negra.jpg",
                "modelo_3d_uri": "/static/uploads/polera_textil_3d.glb",
                "categoria_id": 2,
                "color_id": 2
            },
            {
                "nombre": "Polera Sport Athletic Azul",
                "descripcion": "Polera deportiva transpirable de secado rápido azul navy",
                "precio": 119.00,
                "costo_estandar": 60.00,
                "imagen_uri": "/static/uploads/polera_sport_azul.jpg",
                "modelo_3d_uri": "/static/uploads/polera_textil_3d.glb",
                "categoria_id": 2,
                "color_id": 1
            },
            {
                "nombre": "Polera Streetwear Graphic Roja",
                "descripcion": "Polera casual estampada estilo streetwear algodón suave",
                "precio": 129.00,
                "costo_estandar": 65.00,
                "imagen_uri": "/static/uploads/polera_graphic_roja.jpg",
                "modelo_3d_uri": "/static/uploads/polera_textil_3d.glb",
                "categoria_id": 2,
                "color_id": 2
            },
            {
                "nombre": "Polera Polo Clásica Verde",
                "descripcion": "Polera estilo polo cuello estructurado en piqué verde militar",
                "precio": 149.00,
                "costo_estandar": 75.00,
                "imagen_uri": "/static/uploads/polera_polo_verde.jpg",
                "modelo_3d_uri": "/static/uploads/polera_textil_3d.glb",
                "categoria_id": 2,
                "color_id": 4
            },

            # CHOMPAS / SWEATERS DE DIFERENTES COLORES (SIN CAPUCHA)
            {
                "nombre": "Chompa Cuello Redondo Azul Marino",
                "descripcion": "Chompa de abrigo sin capucha en tono azul marino cuello redondo",
                "precio": 189.00,
                "costo_estandar": 95.00,
                "imagen_uri": "/static/uploads/chompa_azul_marino.jpg",
                "modelo_3d_uri": "/static/uploads/chaqueta_cuero_3d.glb",
                "categoria_id": 6,
                "color_id": 1
            },
            {
                "nombre": "Chompa Tejida Beige Natural",
                "descripcion": "Chompa de lana suave color beige natural sin capucha ideal para vestidor virtual",
                "precio": 209.00,
                "costo_estandar": 105.00,
                "imagen_uri": "/static/uploads/chompa_beige_fino.jpg",
                "modelo_3d_uri": "/static/uploads/chaqueta_cuero_3d.glb",
                "categoria_id": 6,
                "color_id": 4
            },
            {
                "nombre": "Chompa Algodón Gris Jaspeado",
                "descripcion": "Chompa cómoda sin capucha cuello crewneck color gris jaspeado",
                "precio": 179.00,
                "costo_estandar": 90.00,
                "imagen_uri": "/static/uploads/chompa_gris_jaspeado.jpg",
                "modelo_3d_uri": "/static/uploads/chaqueta_cuero_3d.glb",
                "categoria_id": 6,
                "color_id": 3
            },
            {
                "nombre": "Chompa Casual Burdeos Premium",
                "descripcion": "Chompa de punto fino color burdeos estilo elegante sin capucha",
                "precio": 219.00,
                "costo_estandar": 110.00,
                "imagen_uri": "/static/uploads/chompa_burdeos_premium.jpg",
                "modelo_3d_uri": "/static/uploads/chaqueta_cuero_3d.glb",
                "categoria_id": 6,
                "color_id": 2
            }
        ]

        tallas_ids = [2, 3, 4, 5]  # S, M, L, XL
        insertadas = []

        for p_data in prendas_data:
            # Crear prenda principal
            ropa = Ropa(
                nombre=p_data["nombre"],
                descripcion=p_data["descripcion"],
                precio=p_data["precio"],
                costo_estandar=p_data["costo_estandar"],
                imagen_uri=p_data["imagen_uri"],
                modelo_3d_uri=p_data["modelo_3d_uri"],
                categoria_id=p_data["categoria_id"],
                activo=True
            )
            db.add(ropa)
            db.flush()

            # Crear variantes por talla
            for t_id in tallas_ids:
                ts = int(time.time() * 1000) % 100000
                sku_clean = p_data["nombre"].replace(" ", "-")[:10].upper()
                bar = f"779088{ropa.id}{t_id}{ts}"
                
                var = VariantePrenda(
                    ropa_id=ropa.id,
                    talla_id=t_id,
                    color_id=p_data["color_id"],
                    cod_barra=bar,
                    sku=f"{sku_clean}-T{t_id}",
                    activo=True
                )
                db.add(var)
                db.flush()

                # Stock en inventario
                inv = InventarioSucursal(
                    sucursal_id=suc_id,
                    variante_id=var.id,
                    stock_fisico=25,
                    stock_reservado=0,
                    stock_minimo=5
                )
                db.add(inv)

            insertadas.append(f"ID {ropa.id}: {ropa.nombre}")

        db.commit()
        print(f"✅ ¡{len(insertadas)} prendas registradas exitosamente en la DB!")
        for item in insertadas:
            print(f"   • {item}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error al registrar prendas: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    insertar_prendas_variadas()

