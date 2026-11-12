import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models.catalogo import Ropa

MAPEO_IMAGENES = {
    1: "/static/uploads/chaqueta_denim_clasica.jpg",
    2: "/static/uploads/polera_oversize_negra.jpg",
    7: "/static/uploads/chaqueta_cuero_ar.jpg",
    17: "/static/uploads/media_17_ad5eb277.jpg",
    21: "/static/uploads/media_21_f24afa4b.webp",
    23: "/static/uploads/polera_cat_gris.png",
    24: "/static/uploads/polera_graphic_roja.jpg",
    25: "https://images.unsplash.com/photo-1596755094514-f87e34085b2c",
    26: "/static/uploads/polera_sport_azul.jpg",
    27: "/static/uploads/vestido_seda_gala.jpg",
    28: "/static/uploads/traje_ejecutivo_milano.jpg",
    29: "/static/uploads/chompa_azul_marino.jpg",
    30: "/static/uploads/media_30_24c173db.webp",
    31: "/static/uploads/polera_blanca_algodon.jpg",
    32: "/static/uploads/chompa_burdeos_premium.jpg",
    33: "https://images.unsplash.com/photo-1542291026-7eec264c27ff",
    34: "/static/uploads/polera_sport_azul.jpg",
    35: "/static/uploads/chaqueta_denim_clasica_negro.jpg",
    36: "/static/uploads/camisa_manga_larga.jpg",
    37: "/static/uploads/lentes_moda.jpg",
}

def actualizar_imagenes():
    db = SessionLocal()
    try:
        ropas = db.query(Ropa).order_by(Ropa.id).all()
        print(f"[*] Actualizando imágenes en Neon PostgreSQL para {len(ropas)} prendas...")

        for r in ropas:
            old_uri = r.imagen_uri
            if r.id in MAPEO_IMAGENES:
                r.imagen_uri = MAPEO_IMAGENES[r.id]
            else:
                nom = (r.nombre or "").lower()
                if "denim" in nom or "chaqueta" in nom:
                    r.imagen_uri = "/static/uploads/chaqueta_denim_clasica.jpg"
                elif "cuero" in nom:
                    r.imagen_uri = "/static/uploads/chaqueta_cuero_ar.jpg"
                elif "vestido" in nom:
                    r.imagen_uri = "/static/uploads/vestido_seda_gala.jpg"
                elif "traje" in nom:
                    r.imagen_uri = "/static/uploads/traje_ejecutivo_milano.jpg"
                elif "chompa" in nom:
                    r.imagen_uri = "/static/uploads/chompa_azul_marino.jpg"
                elif "lentes" in nom:
                    r.imagen_uri = "/static/uploads/lentes_moda.jpg"
                elif "camisa" in nom:
                    r.imagen_uri = "/static/uploads/camisa_manga_larga.jpg"
                else:
                    r.imagen_uri = "/static/uploads/polera_blanca_algodon.jpg"

            print(f" -> ID {r.id:2d} | {r.nombre[:30]:30s} | {old_uri} ==> {r.imagen_uri}")

        db.commit()
        print("[*] ¡Actualización de base de datos completada exitosamente!")
    except Exception as e:
        db.rollback()
        print(f"[!] Error durante la actualización: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    actualizar_imagenes()
