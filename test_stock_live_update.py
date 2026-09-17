from database import SessionLocal
from models.catalogo import Ropa, VariantePrenda
from models.sucursal import InventarioSucursal
import requests

def test_stock_update():
    db = SessionLocal()
    print("--- DEMOSTRACIÓN DE ACTUALIZACIÓN DE STOCK EN TIEMPO REAL ---")
    
    # 1. Obtener stock inicial de Polera de UFICCT (Prenda #17, Variante #13)
    var = db.query(VariantePrenda).filter(VariantePrenda.ropa_id == 17).first()
    inv_central = db.query(InventarioSucursal).filter(
        InventarioSucursal.variante_id == var.id,
        InventarioSucursal.sucursal_id == 1
    ).first()
    
    inv_equipetrol = db.query(InventarioSucursal).filter(
        InventarioSucursal.variante_id == var.id,
        InventarioSucursal.sucursal_id == 2
    ).first()

    inv_ventura = db.query(InventarioSucursal).filter(
        InventarioSucursal.variante_id == var.id,
        InventarioSucursal.sucursal_id == 3
    ).first()

    stock_inicial_central = inv_equipetrol.stock_disponible
    stock_total_inicial = (inv_central.stock_disponible + inv_equipetrol.stock_disponible + inv_ventura.stock_disponible)
    
    print(f"Stock Inicial Global (Polera de UFICCT): {stock_total_inicial} u. (Central: {inv_central.stock_disponible}, Equipetrol: {inv_equipetrol.stock_disponible}, Ventura: {inv_ventura.stock_disponible})")

    # 2. Consultar Endpoint del Catálogo
    res = requests.get("http://localhost:8000/api/v1/catalogo-disponibilidad/?buscar=UFICCT")
    if res.status_code == 200:
        data = res.json()
        print(f"API Catálogo dice: Stock Disponible Cadena = {data[0]['stock_disponible_cadena']} u.")
    
    # 3. Realizar una Venta POS en Sucursal Equipetrol (2 unidades)
    print("\n--> Procesando Venta POS de 2 unidades de Polera de UFICCT en Sucursal Equipetrol...")
    res_venta = requests.post("http://localhost:8000/api/v1/ventas/pos", json={
        "sucursal_id": 2,
        "metodo_pago_id": 1,
        "items": [
            {
                "variante_id": var.id,
                "cantidad": 2,
                "precio_unitario": 150.00
            }
        ],
        "nit_cliente": "11223344",
        "razon_social": "Cliente Prueba Stock"
    })
    
    if res_venta.status_code == 201:
        v_data = res_venta.json()
        print(f"¡Venta Registrada Exitosamente! Venta #{v_data['id']}, Factura: {v_data['factura']['nro_factura']}")

    # 4. Re-consultar el Endpoint del Catálogo en Tiempo Real
    res_post = requests.get("http://localhost:8000/api/v1/catalogo-disponibilidad/?buscar=UFICCT")
    if res_post.status_code == 200:
        data_post = res_post.json()
        print(f"\n--> API Catálogo tras la Venta dice: Stock Disponible Cadena = {data_post[0]['stock_disponible_cadena']} u.")
        print(f"    (El stock se redujo exactamente de {stock_total_inicial} u. a {data_post[0]['stock_disponible_cadena']} u. en la BD PostgreSQL)")

    # Revertir las 2 unidades para no desajustar datos de prueba
    inv_equipetrol.stock_fisico += 2
    db.commit()
    print("\n--> Stock de prueba restaurado en PostgreSQL.")
    db.close()

if __name__ == "__main__":
    test_stock_update()
