"""
Script de exportación completa para la base de datos PostgreSQL (fashionstore_db).
Genera fashionstore_postgresql.sql con todo el DDL (CREATE TABLE) y DML (INSERT INTO)
actualizado con todos los datos reales existentes en la base de datos.
"""
import psycopg2
import os
from datetime import datetime, date, time
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

def dump_database():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_DATABASE", "fashionstore_db"),
        user=os.getenv("DB_USERNAME", "postgres"),
        password=os.getenv("DB_PASSWORD", "")
    )
    cur = conn.cursor()

    sql_output = []
    sql_output.append("-- ============================================================================")
    sql_output.append("-- FASHIONSTORE DATABASE SCRIPT - POSTGRESQL DUMP")
    sql_output.append(f"-- Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sql_output.append("-- Arquitectura Multisucursal Omnicanal + Probadores 3D AR + IA Gemini")
    sql_output.append("-- Materia: Sistemas de Información 2 - UAGRM")
    sql_output.append("-- ============================================================================\n")
    sql_output.append("SET statement_timeout = 0;")
    sql_output.append("SET lock_timeout = 0;")
    sql_output.append("SET client_encoding = 'UTF8';")
    sql_output.append("SET standard_conforming_strings = on;")
    sql_output.append("SET check_function_bodies = false;")
    sql_output.append("SET xmloption = content;")
    sql_output.append("SET client_min_messages = warning;")
    sql_output.append("SET row_security = off;\n")

    # Orden lógico de tablas respetando dependencias FK
    tables_order = [
        "personas", "clientes", "empleados", "roles", "permisos", "rol_permiso", "rol_permisos", "usuarios",
        "sucursales", "categorias", "temporadas", "proveedores", "colores", "tallas",
        "ropa", "variantes_prenda", "inventario_sucursal", "movimientos_inventario", "traspasos", "detalles_traspaso",
        "promociones", "promocion_ropa", "carritos_compra", "detalles_carrito_compra",
        "reservas", "detalles_reserva", "metodos_pago", "tipos_venta", "ventas", "detalles_venta", "facturas",
        "resenas", "recomendaciones_ia", "alertas_ia", "bitacoras", "configuraciones_fidelizacion", "suscripciones_push"
    ]

    # Obtener todas las tablas en la DB
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")
    existing_tables = set(t[0] for t in cur.fetchall())

    # Asegurar que todas las tablas existentes estén procesadas
    for t in existing_tables:
        if t not in tables_order:
            tables_order.append(t)

    sql_output.append("-- ----------------------------------------------------------------------------")
    sql_output.append("-- 1. LIMPIEZA / RECREACIÓN DE ESTRUCTURA")
    sql_output.append("-- ----------------------------------------------------------------------------")
    for t in reversed(tables_order):
        if t in existing_tables:
            sql_output.append(f"DROP TABLE IF EXISTS {t} CASCADE;")
    sql_output.append("")

    # Función para formatear valores SQL
    def format_val(val):
        if val is None:
            return "NULL"
        elif isinstance(val, (bool)):
            return "TRUE" if val else "FALSE"
        elif isinstance(val, (int, float)):
            return str(val)
        elif isinstance(val, (datetime, date, time)):
            return f"'{val.isoformat()}'"
        else:
            val_str = str(val).replace("'", "''")
            return f"'{val_str}'"

    # Generar DDL e INSERTs para cada tabla
    for table in tables_order:
        if table not in existing_tables:
            continue

        # Obtener columnas de la tabla
        cur.execute(f"""
            SELECT column_name, data_type, is_nullable, column_default, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = '{table}' AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)
        columns_info = cur.fetchall()
        if not columns_info:
            continue

        sql_output.append(f"-- ----------------------------------------------------------------------------")
        sql_output.append(f"-- Tabla: {table}")
        sql_output.append(f"-- ----------------------------------------------------------------------------")
        
        create_cols = []
        col_names = []
        for col, dtype, is_null, default, max_len in columns_info:
            col_names.append(col)
            null_str = "NULL" if is_null == 'YES' else "NOT NULL"
            
            # Mapear tipos a SQL estándar
            type_str = dtype.upper()
            if dtype == 'character varying':
                type_str = f"VARCHAR({max_len})" if max_len else "VARCHAR(255)"
            elif dtype == 'text':
                type_str = "TEXT"
            elif dtype == 'integer':
                type_str = "INTEGER"
            elif dtype == 'bigint':
                type_str = "BIGINT"
            elif dtype == 'boolean':
                type_str = "BOOLEAN"
            elif dtype == 'double precision' or dtype == 'numeric':
                type_str = "NUMERIC(12,2)"
            elif dtype.startswith('timestamp'):
                type_str = "TIMESTAMP WITH TIME ZONE"
            elif dtype == 'date':
                type_str = "DATE"

            default_str = f" DEFAULT {default}" if default else ""
            create_cols.append(f"    {col} {type_str} {null_str}{default_str}")

        sql_output.append(f"CREATE TABLE {table} (")
        sql_output.append(",\n".join(create_cols))
        
        # Primary Key
        cur.execute(f"""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tco
            JOIN information_schema.key_column_usage kcu
              ON kcu.constraint_name = tco.constraint_name
             AND kcu.table_schema = tco.table_schema
            WHERE tco.constraint_type = 'PRIMARY KEY'
              AND tco.table_name = '{table}' AND tco.table_schema = 'public';
        """)
        pk_cols = [r[0] for r in cur.fetchall()]
        if pk_cols:
            sql_output.append(f",   PRIMARY KEY ({', '.join(pk_cols)})")
        sql_output.append(");\n")

        # Registros INSERT
        cols_joined = ", ".join(col_names)
        cur.execute(f"SELECT {cols_joined} FROM {table} ORDER BY 1 ASC;")
        rows = cur.fetchall()

        if rows:
            for row in rows:
                vals_joined = ", ".join(format_val(v) for v in row)
                sql_output.append(f"INSERT INTO {table} ({cols_joined}) VALUES ({vals_joined});")
            sql_output.append("")

    # Reiniciar Secuencias de Autoincremento
    sql_output.append("-- ----------------------------------------------------------------------------")
    sql_output.append("-- REINICIO DE SECUENCIAS (AUTOINCREMENTO)")
    sql_output.append("-- ----------------------------------------------------------------------------")
    cur.execute("""
        SELECT sequence_name 
        FROM information_schema.sequences 
        WHERE sequence_schema='public';
    """)
    sequences = [s[0] for s in cur.fetchall()]
    for seq in sequences:
        # Extraer tabla asociada
        table_guess = seq.replace("_id_seq", "").replace("_seq", "")
        if table_guess in existing_tables:
            sql_output.append(f"SELECT setval('{seq}', COALESCE((SELECT MAX(id) FROM {table_guess}), 1));")

    sql_output.append("\n-- FIN DEL SCRIPT")
    
    conn.close()

    # Guardar en fashionstore_postgresql.sql
    output_filepath = os.path.join(os.path.dirname(__file__), "fashionstore_postgresql.sql")
    with open(output_filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(sql_output))

    print(f"¡Script generado exitosamente en {output_filepath} con {len(sql_output)} líneas!")

if __name__ == "__main__":
    dump_database()
