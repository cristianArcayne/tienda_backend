from database import SessionLocal
from models.catalogo import Ropa, VariantePrenda
from models.sucursal import InventarioSucursal, Sucursal

def check_stock():
    db = SessionLocal()
    print("=== ESTADO REAL DE INVENTARIO Y STOCK EN BASE DE DATOS POSTGRESQL ===")
    sucursales = db.query(Sucursal).all()
    print(f"Sucursales registradas: {[(s.id, s.nombre, s.ciudad) for s in sucursales]}\n")

    ropas = db.query(Ropa).all()
    for r in ropas:
        print(f"Prenda ID {r.id}: {r.nombre} (Precio: {r.precio} BOB)")
        variantes = db.query(VariantePrenda).filter(VariantePrenda.ropa_id == r.id).all()
        stock_total_fisico = 0
        stock_total_reservado = 0
        stock_total_disponible = 0
        
        for v in variantes:
            talla_nom = v.talla.medida if v.talla else "Única"
            color_nom = v.color.nombre if v.color else "Estándar"
            invs = db.query(InventarioSucursal).filter(InventarioSucursal.variante_id == v.id).all()
            for inv in invs:
                suc_nom = inv.sucursal.nombre if inv.sucursal else f"Sucursal {inv.sucursal_id}"
                sf = inv.stock_fisico
                sr = inv.stock_reservado
                sd = inv.stock_disponible
                stock_total_fisico += sf
                stock_total_reservado += sr
                stock_total_disponible += sd
                print(f"  |- Variante #{v.id} [{talla_nom} / {color_nom}] @ {suc_nom}: Stock Fisico={sf}, Reservado={sr}, Disponible={sd}")
        print(f"  --> TOTAL CADENA GLOBAL: Físico={stock_total_fisico}, Reservado={stock_total_reservado}, Disponible={stock_total_disponible}\n")

    db.close()

if __name__ == "__main__":
    check_stock()
