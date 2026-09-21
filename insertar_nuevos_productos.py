import time
import os
from database import SessionLocal
from models.catalogo import Ropa, VariantePrenda
from models.sucursal import InventarioSucursal, Sucursal

def insertar_prendas():
    db = SessionLocal()
    try:
        sucursal = db.query(Sucursal).first()
        suc_id = sucursal.id if sucursal else 1

        # 1. Polera CAT Original Gris
        p1 = Ropa(
            nombre="Polera CAT Original Gris",
            descripcion="Polera urbana de algodon CAT con logo frontal sobre fondo neutro",
            precio=149.00,
            costo_estandar=75.00,
            imagen_uri="/static/uploads/polera_cat_gris.png",
            modelo_3d_uri="/static/uploads/polera_textil_3d.glb",
            categoria_id=2,
            activo=True
        )
        db.add(p1)
        db.flush()

        # 2. Chamarra Termica RACCO Negra
        p2 = Ropa(
            nombre="Chamarra Termica RACCO Negra",
            descripcion="Chamarra acolchada de invierno RACCO con capucha y acabado impermeable",
            precio=329.00,
            costo_estandar=180.00,
            imagen_uri="/static/uploads/chamarra_racco_negra.png",
            modelo_3d_uri="/static/uploads/chaqueta_cuero_3d.glb",
            categoria_id=6,
            activo=True
        )
        db.add(p2)
        db.flush()

        # Tallas: S(2), M(3), L(4), XL(5)
        tallas = [2, 3, 4, 5]

        for t_id in tallas:
            # Variantes Polera CAT (Color Beige/Gris id=4)
            bar1 = f"779001{p1.id}{t_id}{int(time.time() * 100) % 10000}"
            var1 = VariantePrenda(
                ropa_id=p1.id,
                talla_id=t_id,
                color_id=4,
                cod_barra=bar1,
                sku=f"CAT-GRIS-T{t_id}",
                activo=True
            )
            db.add(var1)
            db.flush()

            inv1 = InventarioSucursal(
                sucursal_id=suc_id,
                variante_id=var1.id,
                stock_fisico=20,
                stock_reservado=0,
                stock_minimo=5
            )
            db.add(inv1)

            # Variantes Chamarra RACCO (Color Negro id=2)
            bar2 = f"779002{p2.id}{t_id}{int(time.time() * 100) % 10000}"
            var2 = VariantePrenda(
                ropa_id=p2.id,
                talla_id=t_id,
                color_id=2,
                cod_barra=bar2,
                sku=f"RACCO-NEG-T{t_id}",
                activo=True
            )
            db.add(var2)
            db.flush()

            inv2 = InventarioSucursal(
                sucursal_id=suc_id,
                variante_id=var2.id,
                stock_fisico=15,
                stock_reservado=0,
                stock_minimo=5
            )
            db.add(inv2)

        db.commit()
        print(f" Prendas insertadas con xito en Neon DB! Polera ID: {p1.id}, Chamarra ID: {p2.id}")

    except Exception as e:
        db.rollback()
        print(f" Error insertando prendas: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    insertar_prendas()
