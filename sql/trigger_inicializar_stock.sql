-- ====================================================================================
-- SCRIPT DDL: TRIGGER DE INICIALIZACIÓN DE ESPACIOS LÓGICOS DE INVENTARIO
-- MATERIA: Sistemas de Información II (MSc. Ing. Angélica Garzón Cuéllar)
-- PROYECTO: FashionStore - Plataforma de Comercio Electrónico
-- CASO DE USO: CU06. Gestionar sucursales de la cadena (Paso 5 del Flujo)
-- ====================================================================================

-- 1. Asegurar la existencia de las tablas involucradas
CREATE TABLE IF NOT EXISTS sucursales (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    ciudad VARCHAR(60) NOT NULL,
    direccion VARCHAR(200) NOT NULL,
    telefono VARCHAR(25),
    creado_en TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS variantes_prenda (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(60) UNIQUE NOT NULL,
    nombre_prenda VARCHAR(120) NOT NULL,
    precio NUMERIC(10, 2) DEFAULT 0.0 NOT NULL,
    talla_id INT NOT NULL
);

CREATE TABLE IF NOT EXISTS inventario_stock (
    id SERIAL PRIMARY KEY,
    sucursal_id INT NOT NULL REFERENCES sucursales(id) ON DELETE CASCADE,
    variante_id INT NOT NULL REFERENCES variantes_prenda(id) ON DELETE CASCADE,
    stock_fisico INT DEFAULT 0 NOT NULL,
    actualizado_en TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_sucursal_variante_stock UNIQUE (sucursal_id, variante_id)
);

-- ====================================================================================
-- 2. FUNCIÓN PL/pgSQL: fn_inicializar_inventario_sucursal()
-- Propósito: Recorre todas las variantes de prendas existentes en el catálogo e inserta
--            un registro de stock con existencia inicial = 0 para la nueva sucursal.
-- ====================================================================================
CREATE OR REPLACE FUNCTION fn_inicializar_inventario_sucursal()
RETURNS TRIGGER AS $$
DECLARE
    v_total_variantes INT;
BEGIN
    -- Contar variantes existentes
    SELECT COUNT(*) INTO v_total_variantes FROM variantes_prenda;

    -- Si existen variantes activas en el catálogo, generar su espacio lógico en cero
    IF v_total_variantes > 0 THEN
        INSERT INTO inventario_stock (sucursal_id, variante_id, stock_fisico, actualizado_en)
        SELECT 
            NEW.id,
            vp.id,
            0,
            NOW()
        FROM variantes_prenda vp
        ON CONFLICT (sucursal_id, variante_id) DO NOTHING;
    END IF;

    -- Registrar evento informativo en los logs del servidor PostgreSQL
    RAISE NOTICE 'Trigger ejecutado: Sucursal ID % (%) creada. Se inicializaron % registros de inventario en stock = 0.', 
                 NEW.id, NEW.nombre, v_total_variantes;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ====================================================================================
-- 3. DISPARADOR (TRIGGER): trg_after_insert_sucursal_inicializar_stock
-- Tipo: AFTER INSERT ON sucursales FOR EACH ROW
-- ====================================================================================
DROP TRIGGER IF EXISTS trg_after_insert_sucursal_inicializar_stock ON sucursales;

CREATE TRIGGER trg_after_insert_sucursal_inicializar_stock
AFTER INSERT ON sucursales
FOR EACH ROW
EXECUTE FUNCTION fn_inicializar_inventario_sucursal();

-- ====================================================================================
-- 4. PRUEBA DE VALIDACIÓN DEL TRIGGER:
-- Ejecutar estas sentencias para comprobar que el disparador opera automáticamente
-- ====================================================================================
/*
-- A. Insertar prendas de prueba si no existen
INSERT INTO variantes_prenda (sku, nombre_prenda, precio, talla_id)
VALUES 
    ('SKU-CAS-001-S', 'Polera Casual Denim', 149.00, 1),
    ('SKU-CAS-001-M', 'Polera Casual Denim', 149.00, 2),
    ('SKU-VES-002-M', 'Vestido Seda Fiesta', 389.00, 2)
ON CONFLICT (sku) DO NOTHING;

-- B. Insertar una nueva sucursal (debe disparar el Trigger)
INSERT INTO sucursales (nombre, ciudad, direccion, telefono)
VALUES ('Sucursal Equipetrol', 'Santa Cruz', 'Av. San Martín #450', '+591 3 3445566');

-- C. Verificar que automáticamente se crearon los registros con stock 0
SELECT 
    s.nombre AS tienda,
    s.ciudad,
    vp.sku,
    vp.nombre_prenda,
    inv.stock_fisico,
    inv.actualizado_en
FROM inventario_stock inv
JOIN sucursales s ON inv.sucursal_id = s.id
JOIN variantes_prenda vp ON inv.variante_id = vp.id
WHERE s.nombre = 'Sucursal Equipetrol';
*/
