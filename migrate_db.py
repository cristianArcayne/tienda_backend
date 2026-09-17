"""
Script de migración / sincronización de esquema para base de datos local SQLite / PostgreSQL.
Agrega las columnas nuevas requeridas para CU11, CU12 y CU13 sin perder datos existentes.
"""
from database import engine, Base
from sqlalchemy import text, inspect
import models

def sincronizar_esquema():
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    print(f"Tablas existentes: {existing_tables}")

    with engine.connect() as conn:
        # 1. Columnas en variantes_prenda
        if "variantes_prenda" in existing_tables:
            cols = [c["name"] for c in inspector.get_columns("variantes_prenda")]
            if "producto_id" not in cols:
                print("Agregando columna 'producto_id' a 'variantes_prenda'...")
                conn.execute(text("ALTER TABLE variantes_prenda ADD COLUMN producto_id INTEGER REFERENCES productos(id)"))
            if "color" not in cols:
                print("Agregando columna 'color' a 'variantes_prenda'...")
                conn.execute(text("ALTER TABLE variantes_prenda ADD COLUMN color VARCHAR(50) DEFAULT 'Estándar'"))

        # 2. Columnas en carritos
        if "carritos" in existing_tables:
            cols = [c["name"] for c in inspector.get_columns("carritos")]
            if "dispositivo_origen" not in cols:
                print("Agregando columna 'dispositivo_origen' a 'carritos'...")
                conn.execute(text("ALTER TABLE carritos ADD COLUMN dispositivo_origen VARCHAR(50) DEFAULT 'WEB_ANGULAR'"))
            if "fecha_sincronizacion" not in cols:
                print("Agregando columna 'fecha_sincronizacion' a 'carritos'...")
                conn.execute(text("ALTER TABLE carritos ADD COLUMN fecha_sincronizacion DATETIME"))

        # 3. Columnas en ventas (CU14 y CU15)
        if "ventas" in existing_tables:
            cols = [c["name"] for c in inspector.get_columns("ventas")]
            if "cajero_id" not in cols:
                print("Agregando columna 'cajero_id' a 'ventas'...")
                conn.execute(text("ALTER TABLE ventas ADD COLUMN cajero_id VARCHAR(50)"))
            if "monto_recibido" not in cols:
                print("Agregando columna 'monto_recibido' a 'ventas'...")
                conn.execute(text("ALTER TABLE ventas ADD COLUMN monto_recibido NUMERIC(10, 2)"))
            if "cambio_devuelto" not in cols:
                print("Agregando columna 'cambio_devuelto' a 'ventas'...")
                conn.execute(text("ALTER TABLE ventas ADD COLUMN cambio_devuelto NUMERIC(10, 2)"))
            if "direccion_envio" not in cols:
                print("Agregando columna 'direccion_envio' a 'ventas'...")
                conn.execute(text("ALTER TABLE ventas ADD COLUMN direccion_envio VARCHAR(255)"))

        conn.commit()

    # 3. Crear tablas nuevas si no existen (ej. reservas)
    Base.metadata.create_all(bind=engine)
    print("Esquema sincronizado exitosamente con SQLAlchemy Base.metadata.create_all()")

if __name__ == "__main__":
    sincronizar_esquema()
