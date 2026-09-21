import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models.catalogo import Ropa

def actualizar():
    db = SessionLocal()
    try:
        ropas = db.query(Ropa).all()
        print(f"[*] Actualizando {len(ropas)} prendas en la base de datos Neon Cloud...")

        for r in ropas:
            nom = (r.nombre or "").lower()
            if "polera" in nom and "cat" in nom:
                r.imagen_uri = "/static/uploads/polera_cat_gris.png"
            elif "chamarra" in nom and "racco" in nom:
                r.imagen_uri = "/static/uploads/chamarra_racco_negra.png"
            elif "denim" in nom or "vaquera" in nom:
                r.imagen_uri = "/static/uploads/chaqueta_denim_clasica.jpg"
            elif "cotton" in nom or "blanca" in nom or "algodon" in nom:
                r.imagen_uri = "/static/uploads/polera_blanca_algodon.jpg"
            elif "vestido" in nom:
                r.imagen_uri = "/static/uploads/vestido_estampado_floral.jpg"
            elif "cuero" in nom or "sudadera" in nom or "roja" in nom:
                r.imagen_uri = "/static/uploads/sudadera_roja_casual.jpg"
            elif "uficct" in nom:
                r.imagen_uri = "/static/uploads/polera_cat_gris.png"
            elif "camisa" in nom:
                r.imagen_uri = "/static/uploads/polera_blanca_algodon.jpg"
            elif r.imagen_uri and r.imagen_uri.startswith("http"):
                r.imagen_uri = "/static/uploads/chaqueta_denim_clasica.jpg"

            print(f" -> ID {r.id}: {r.nombre} ==> {r.imagen_uri}")

        db.commit()
        print("[*] Actualizacion completada exitosamente en Neon PostgreSQL!")
    except Exception as e:
        db.rollback()
        print(f"[!] Error al actualizar: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    actualizar()

