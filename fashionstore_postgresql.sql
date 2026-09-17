-- ============================================================================
-- FASHIONSTORE DATABASE SCRIPT - POSTGRESQL DUMP
-- Generado el: 2026-09-17 11:33:54
-- Arquitectura Multisucursal Omnicanal + Probadores 3D AR + IA Gemini
-- Materia: Sistemas de Información 2 - UAGRM
-- ============================================================================

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

-- ----------------------------------------------------------------------------
-- 1. LIMPIEZA / RECREACIÓN DE ESTRUCTURA
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS suscripciones_push CASCADE;
DROP TABLE IF EXISTS configuraciones_fidelizacion CASCADE;
DROP TABLE IF EXISTS bitacoras CASCADE;
DROP TABLE IF EXISTS alertas_ia CASCADE;
DROP TABLE IF EXISTS recomendaciones_ia CASCADE;
DROP TABLE IF EXISTS resenas CASCADE;
DROP TABLE IF EXISTS facturas CASCADE;
DROP TABLE IF EXISTS detalles_venta CASCADE;
DROP TABLE IF EXISTS ventas CASCADE;
DROP TABLE IF EXISTS tipos_venta CASCADE;
DROP TABLE IF EXISTS metodos_pago CASCADE;
DROP TABLE IF EXISTS detalles_reserva CASCADE;
DROP TABLE IF EXISTS reservas CASCADE;
DROP TABLE IF EXISTS detalles_carrito_compra CASCADE;
DROP TABLE IF EXISTS carritos_compra CASCADE;
DROP TABLE IF EXISTS promocion_ropa CASCADE;
DROP TABLE IF EXISTS promociones CASCADE;
DROP TABLE IF EXISTS detalles_traspaso CASCADE;
DROP TABLE IF EXISTS traspasos CASCADE;
DROP TABLE IF EXISTS movimientos_inventario CASCADE;
DROP TABLE IF EXISTS inventario_sucursal CASCADE;
DROP TABLE IF EXISTS variantes_prenda CASCADE;
DROP TABLE IF EXISTS ropa CASCADE;
DROP TABLE IF EXISTS tallas CASCADE;
DROP TABLE IF EXISTS colores CASCADE;
DROP TABLE IF EXISTS proveedores CASCADE;
DROP TABLE IF EXISTS temporadas CASCADE;
DROP TABLE IF EXISTS categorias CASCADE;
DROP TABLE IF EXISTS sucursales CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;
DROP TABLE IF EXISTS rol_permisos CASCADE;
DROP TABLE IF EXISTS rol_permiso CASCADE;
DROP TABLE IF EXISTS permisos CASCADE;
DROP TABLE IF EXISTS roles CASCADE;
DROP TABLE IF EXISTS empleados CASCADE;
DROP TABLE IF EXISTS clientes CASCADE;
DROP TABLE IF EXISTS personas CASCADE;

-- ----------------------------------------------------------------------------
-- Tabla: personas
-- ----------------------------------------------------------------------------
CREATE TABLE personas (
    ci VARCHAR(20) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido_pat VARCHAR(100) NOT NULL,
    apellido_mat VARCHAR(100) NULL,
    correo VARCHAR(150) NOT NULL,
    telefono VARCHAR(30) NULL,
    direccion VARCHAR(255) NULL,
    tipo_persona VARCHAR(20) NOT NULL,
    fec_creacion TIMESTAMP WITH TIME ZONE NULL DEFAULT CURRENT_TIMESTAMP
,   PRIMARY KEY (ci)
);

INSERT INTO personas (ci, nombre, apellido_pat, apellido_mat, correo, telefono, direccion, tipo_persona, fec_creacion) VALUES ('1001', 'Super', 'Admin', 'Sistema', 'admin@fashionstore.com', '+591 70011223', 'Av. San Martín #450', 'EMPLEADO', '2026-09-11T10:46:52.525661-04:00');
INSERT INTO personas (ci, nombre, apellido_pat, apellido_mat, correo, telefono, direccion, tipo_persona, fec_creacion) VALUES ('1002', 'Carlos', 'Gutiérrez', 'Mendoza', 'carlos.cajero@fashionstore.com', '+591 71122334', 'Calle Beni #120', 'EMPLEADO', '2026-09-11T10:46:52.525661-04:00');
INSERT INTO personas (ci, nombre, apellido_pat, apellido_mat, correo, telefono, direccion, tipo_persona, fec_creacion) VALUES ('11540380', 'Carlos', 'Mamani', '', 'carlos_20e38c@gmail.com', NULL, NULL, 'CLIENTE', '2026-09-17T10:34:10.683472-04:00');
INSERT INTO personas (ci, nombre, apellido_pat, apellido_mat, correo, telefono, direccion, tipo_persona, fec_creacion) VALUES ('11619521', 'Yeison', 'oen', '', 'yheison@gmail.com', NULL, NULL, 'CLIENTE', '2026-09-13T19:56:31.622167-04:00');
INSERT INTO personas (ci, nombre, apellido_pat, apellido_mat, correo, telefono, direccion, tipo_persona, fec_creacion) VALUES ('14994379', 'Juan', 'Perez', '', 'juan_cd291f@example.com', NULL, NULL, 'CLIENTE', '2026-09-17T10:33:40.988705-04:00');
INSERT INTO personas (ci, nombre, apellido_pat, apellido_mat, correo, telefono, direccion, tipo_persona, fec_creacion) VALUES ('17112834', 'YEISON', 'LEON', '', 'yeisonchoqueleon@gmail.com', NULL, NULL, 'CLIENTE', '2026-09-13T00:02:52.882696-04:00');
INSERT INTO personas (ci, nombre, apellido_pat, apellido_mat, correo, telefono, direccion, tipo_persona, fec_creacion) VALUES ('18320484', 'jason', 'CL', '', 'ariel.mn0a@gmail.com', NULL, NULL, 'CLIENTE', '2026-09-12T22:45:21.967291-04:00');
INSERT INTO personas (ci, nombre, apellido_pat, apellido_mat, correo, telefono, direccion, tipo_persona, fec_creacion) VALUES ('2001', 'María', 'Fernández', 'Rojas', 'maria.cliente@gmail.com', '+591 72233445', 'Barrio Equipetrol #78', 'CLIENTE', '2026-09-11T10:46:52.525661-04:00');
INSERT INTO personas (ci, nombre, apellido_pat, apellido_mat, correo, telefono, direccion, tipo_persona, fec_creacion) VALUES ('2002', 'Juan', 'Pérez', 'Sosa', 'juan.perez@gmail.com', '+591 73344556', 'Av. Banzer Km 4', 'CLIENTE', '2026-09-11T10:46:52.525661-04:00');
INSERT INTO personas (ci, nombre, apellido_pat, apellido_mat, correo, telefono, direccion, tipo_persona, fec_creacion) VALUES ('22615273', 'Test', 'User', '', 'testuser99@sin-correo.com', NULL, NULL, 'CLIENTE', '2026-09-12T23:51:42.723299-04:00');
INSERT INTO personas (ci, nombre, apellido_pat, apellido_mat, correo, telefono, direccion, tipo_persona, fec_creacion) VALUES ('25950728', 'Yeison3', 'Prueba', '', 'yeison3@sin-correo.com', NULL, NULL, 'CLIENTE', '2026-09-12T22:40:27.850819-04:00');
INSERT INTO personas (ci, nombre, apellido_pat, apellido_mat, correo, telefono, direccion, tipo_persona, fec_creacion) VALUES ('admin', 'Administrador', 'del Sistema', NULL, 'cliente_admin@fashionstore.com', '+591 70000000', NULL, 'CLIENTE', '2026-09-13T20:18:09.402562-04:00');
INSERT INTO personas (ci, nombre, apellido_pat, apellido_mat, correo, telefono, direccion, tipo_persona, fec_creacion) VALUES ('descargar_pdf', 'Cliente', 'Web', NULL, 'cliente_descargar_pdf@fashionstore.com', '+591 70000000', NULL, 'CLIENTE', '2026-09-14T13:27:48.203340-04:00');
INSERT INTO personas (ci, nombre, apellido_pat, apellido_mat, correo, telefono, direccion, tipo_persona, fec_creacion) VALUES ('mi_carrito', 'Cliente', 'Web', NULL, 'cliente_mi_carrito@fashionstore.com', '+591 70000000', NULL, 'CLIENTE', '2026-09-14T13:19:46.246816-04:00');

-- ----------------------------------------------------------------------------
-- Tabla: clientes
-- ----------------------------------------------------------------------------
CREATE TABLE clientes (
    ci VARCHAR(20) NOT NULL,
    preferencia_talla VARCHAR(10) NULL,
    preferencia_estilo VARCHAR(100) NULL,
    fecha_registro DATE NOT NULL DEFAULT CURRENT_DATE
,   PRIMARY KEY (ci)
);

INSERT INTO clientes (ci, preferencia_talla, preferencia_estilo, fecha_registro) VALUES ('11540380', 'M', NULL, '2026-09-17');
INSERT INTO clientes (ci, preferencia_talla, preferencia_estilo, fecha_registro) VALUES ('11619521', 'M', NULL, '2026-09-13');
INSERT INTO clientes (ci, preferencia_talla, preferencia_estilo, fecha_registro) VALUES ('14994379', 'M', NULL, '2026-09-17');
INSERT INTO clientes (ci, preferencia_talla, preferencia_estilo, fecha_registro) VALUES ('17112834', 'M', NULL, '2026-09-13');
INSERT INTO clientes (ci, preferencia_talla, preferencia_estilo, fecha_registro) VALUES ('18320484', 'M', NULL, '2026-09-12');
INSERT INTO clientes (ci, preferencia_talla, preferencia_estilo, fecha_registro) VALUES ('2001', 'M', 'Casual Elegante', '2026-09-11');
INSERT INTO clientes (ci, preferencia_talla, preferencia_estilo, fecha_registro) VALUES ('2002', 'L', 'Urbano / Denim', '2026-09-11');
INSERT INTO clientes (ci, preferencia_talla, preferencia_estilo, fecha_registro) VALUES ('22615273', 'M', NULL, '2026-09-12');
INSERT INTO clientes (ci, preferencia_talla, preferencia_estilo, fecha_registro) VALUES ('25950728', 'M', NULL, '2026-09-12');
INSERT INTO clientes (ci, preferencia_talla, preferencia_estilo, fecha_registro) VALUES ('admin', NULL, NULL, '2026-09-13');
INSERT INTO clientes (ci, preferencia_talla, preferencia_estilo, fecha_registro) VALUES ('descargar_pdf', NULL, NULL, '2026-09-14');
INSERT INTO clientes (ci, preferencia_talla, preferencia_estilo, fecha_registro) VALUES ('mi_carrito', NULL, NULL, '2026-09-14');

-- ----------------------------------------------------------------------------
-- Tabla: empleados
-- ----------------------------------------------------------------------------
CREATE TABLE empleados (
    ci VARCHAR(20) NOT NULL,
    fec_contratacion DATE NOT NULL DEFAULT CURRENT_DATE,
    cargo VARCHAR(100) NOT NULL DEFAULT 'Cajero POS'::character varying,
    activo BOOLEAN NOT NULL DEFAULT true,
    sucursal_id INTEGER NULL
,   PRIMARY KEY (ci)
);

INSERT INTO empleados (ci, fec_contratacion, cargo, activo, sucursal_id) VALUES ('1001', '2025-01-01', 'Gerente General', TRUE, NULL);
INSERT INTO empleados (ci, fec_contratacion, cargo, activo, sucursal_id) VALUES ('1002', '2025-03-01', 'Cajero POS Principal', TRUE, NULL);

-- ----------------------------------------------------------------------------
-- Tabla: roles
-- ----------------------------------------------------------------------------
CREATE TABLE roles (
    id INTEGER NOT NULL DEFAULT nextval('roles_id_seq'::regclass),
    nombre VARCHAR(50) NOT NULL,
    descripcion VARCHAR(255) NULL,
    activo BOOLEAN NOT NULL DEFAULT true
,   PRIMARY KEY (id)
);

INSERT INTO roles (id, nombre, descripcion, activo) VALUES (1, 'Administrador', 'Acceso total y configuración del sistema', TRUE);
INSERT INTO roles (id, nombre, descripcion, activo) VALUES (2, 'Cajero POS', 'Procesamiento de ventas físicas en tienda', TRUE);
INSERT INTO roles (id, nombre, descripcion, activo) VALUES (3, 'Vendedor', 'Asesoría y consulta de catálogo omnicanal', TRUE);
INSERT INTO roles (id, nombre, descripcion, activo) VALUES (4, 'Cliente', 'Acceso a e-commerce web y reservas', TRUE);

-- ----------------------------------------------------------------------------
-- Tabla: permisos
-- ----------------------------------------------------------------------------
CREATE TABLE permisos (
    id INTEGER NOT NULL DEFAULT nextval('permisos_id_seq'::regclass),
    nombre VARCHAR(200) NOT NULL,
    codename VARCHAR(100) NOT NULL
,   PRIMARY KEY (id)
);

INSERT INTO permisos (id, nombre, codename) VALUES (1, 'Ver Catálogo', 'inventario.view_catalogo');
INSERT INTO permisos (id, nombre, codename) VALUES (2, 'Ver Producto', 'inventario.view_producto');
INSERT INTO permisos (id, nombre, codename) VALUES (3, 'Ver Detalle de Producto', 'inventario.view_producto_detalle');
INSERT INTO permisos (id, nombre, codename) VALUES (4, 'Agregar Producto', 'inventario.add_producto');
INSERT INTO permisos (id, nombre, codename) VALUES (5, 'Modificar Producto', 'inventario.change_producto');
INSERT INTO permisos (id, nombre, codename) VALUES (6, 'Eliminar Producto', 'inventario.delete_producto');
INSERT INTO permisos (id, nombre, codename) VALUES (7, 'Ver Categoría', 'inventario.view_categoria');
INSERT INTO permisos (id, nombre, codename) VALUES (8, 'Agregar Categoría', 'inventario.add_categoria');
INSERT INTO permisos (id, nombre, codename) VALUES (9, 'Modificar Categoría', 'inventario.change_categoria');
INSERT INTO permisos (id, nombre, codename) VALUES (10, 'Eliminar Categoría', 'inventario.delete_categoria');
INSERT INTO permisos (id, nombre, codename) VALUES (11, 'Ver Proveedor', 'compras.view_proveedor');
INSERT INTO permisos (id, nombre, codename) VALUES (12, 'Agregar Proveedor', 'compras.add_proveedor');
INSERT INTO permisos (id, nombre, codename) VALUES (13, 'Modificar Proveedor', 'compras.change_proveedor');
INSERT INTO permisos (id, nombre, codename) VALUES (14, 'Eliminar Proveedor', 'compras.delete_proveedor');
INSERT INTO permisos (id, nombre, codename) VALUES (15, 'Ver Compra', 'compras.view_compra');
INSERT INTO permisos (id, nombre, codename) VALUES (16, 'Agregar Compra', 'compras.add_compra');
INSERT INTO permisos (id, nombre, codename) VALUES (17, 'Modificar Compra', 'compras.change_compra');
INSERT INTO permisos (id, nombre, codename) VALUES (18, 'Eliminar Compra', 'compras.delete_compra');
INSERT INTO permisos (id, nombre, codename) VALUES (19, 'Ver Marca', 'inventario.view_marca');
INSERT INTO permisos (id, nombre, codename) VALUES (20, 'Agregar Marca', 'inventario.add_marca');
INSERT INTO permisos (id, nombre, codename) VALUES (21, 'Modificar Marca', 'inventario.change_marca');
INSERT INTO permisos (id, nombre, codename) VALUES (22, 'Eliminar Marca', 'inventario.delete_marca');
INSERT INTO permisos (id, nombre, codename) VALUES (23, 'Ver Variante de Producto', 'inventario.view_varianteproducto');
INSERT INTO permisos (id, nombre, codename) VALUES (24, 'Agregar Variante de Producto', 'inventario.add_varianteproducto');
INSERT INTO permisos (id, nombre, codename) VALUES (25, 'Modificar Variante de Producto', 'inventario.change_varianteproducto');
INSERT INTO permisos (id, nombre, codename) VALUES (26, 'Eliminar Variante de Producto', 'inventario.delete_varianteproducto');
INSERT INTO permisos (id, nombre, codename) VALUES (27, 'Ver Multimedia', 'inventario.view_multimedio');
INSERT INTO permisos (id, nombre, codename) VALUES (28, 'Agregar Multimedia', 'inventario.add_multimedio');
INSERT INTO permisos (id, nombre, codename) VALUES (29, 'Modificar Multimedia', 'inventario.change_multimedio');
INSERT INTO permisos (id, nombre, codename) VALUES (30, 'Eliminar Multimedia', 'inventario.delete_multimedio');
INSERT INTO permisos (id, nombre, codename) VALUES (31, 'Ver Usuario', 'seguridad.view_usuario');
INSERT INTO permisos (id, nombre, codename) VALUES (32, 'Agregar Usuario', 'seguridad.add_usuario');
INSERT INTO permisos (id, nombre, codename) VALUES (33, 'Modificar Usuario', 'seguridad.change_usuario');
INSERT INTO permisos (id, nombre, codename) VALUES (34, 'Eliminar Usuario', 'seguridad.delete_usuario');
INSERT INTO permisos (id, nombre, codename) VALUES (35, 'Ver Dashboard', 'seguridad.view_dashboard');
INSERT INTO permisos (id, nombre, codename) VALUES (36, 'Ver Bitácora', 'seguridad.view_bitacora');
INSERT INTO permisos (id, nombre, codename) VALUES (37, 'Ver Bitácora de Auditoría', 'seguridad.view_bitacoraauditoria');
INSERT INTO permisos (id, nombre, codename) VALUES (38, 'Ver Backup', 'seguridad.view_backup');
INSERT INTO permisos (id, nombre, codename) VALUES (39, 'Agregar Backup', 'seguridad.add_backup');
INSERT INTO permisos (id, nombre, codename) VALUES (40, 'Restaurar Backup', 'seguridad.add_restore');
INSERT INTO permisos (id, nombre, codename) VALUES (41, 'Generar Reporte', 'seguridad.add_reporte');
INSERT INTO permisos (id, nombre, codename) VALUES (42, 'Generar Predicción', 'seguridad.add_prediccion');
INSERT INTO permisos (id, nombre, codename) VALUES (43, 'Ver Notificación', 'notificaciones.view_notificacion');
INSERT INTO permisos (id, nombre, codename) VALUES (44, 'Modificar Empresa', 'seguridad.change_empresa');
INSERT INTO permisos (id, nombre, codename) VALUES (45, 'Ver Mi Suscripción', 'seguridad.view_mi_suscripcion');
INSERT INTO permisos (id, nombre, codename) VALUES (46, 'Modificar Mi Suscripción', 'seguridad.change_mi_suscripcion');
INSERT INTO permisos (id, nombre, codename) VALUES (47, 'Ver Alertas IA', 'ia.view_alerta');
INSERT INTO permisos (id, nombre, codename) VALUES (48, 'Agregar Alerta IA', 'ia.add_alerta');
INSERT INTO permisos (id, nombre, codename) VALUES (49, 'Modificar Alerta IA', 'ia.change_alerta');
INSERT INTO permisos (id, nombre, codename) VALUES (50, 'Eliminar Alerta IA', 'ia.delete_alerta');
INSERT INTO permisos (id, nombre, codename) VALUES (51, 'Ver Sugerencia de Compra', 'ia.view_sugerenciacompra');
INSERT INTO permisos (id, nombre, codename) VALUES (52, 'Modificar Sugerencia de Compra', 'ia.change_sugerenciacompra');
INSERT INTO permisos (id, nombre, codename) VALUES (53, 'Ver Rol/Grupo', 'auth.view_group');
INSERT INTO permisos (id, nombre, codename) VALUES (54, 'Agregar Rol/Grupo', 'auth.add_group');
INSERT INTO permisos (id, nombre, codename) VALUES (55, 'Modificar Rol/Grupo', 'auth.change_group');
INSERT INTO permisos (id, nombre, codename) VALUES (56, 'Eliminar Rol/Grupo', 'auth.delete_group');
INSERT INTO permisos (id, nombre, codename) VALUES (57, 'Ver Venta', 'venta.view_venta');
INSERT INTO permisos (id, nombre, codename) VALUES (58, 'Agregar Venta', 'venta.add_venta');
INSERT INTO permisos (id, nombre, codename) VALUES (59, 'Modificar Venta', 'venta.change_venta');
INSERT INTO permisos (id, nombre, codename) VALUES (60, 'Eliminar Venta', 'venta.delete_venta');
INSERT INTO permisos (id, nombre, codename) VALUES (61, 'Ver Config. Fidelización', 'venta.view_configuracionfidelizacion');
INSERT INTO permisos (id, nombre, codename) VALUES (62, 'Modificar Config. Fidelización', 'venta.change_configuracionfidelizacion');
INSERT INTO permisos (id, nombre, codename) VALUES (63, 'Ver Permiso', 'auth.view_permission');
INSERT INTO permisos (id, nombre, codename) VALUES (64, 'Modificar Permiso', 'auth.change_permission');

-- ----------------------------------------------------------------------------
-- Tabla: rol_permiso
-- ----------------------------------------------------------------------------
CREATE TABLE rol_permiso (
    rol_id INTEGER NOT NULL,
    permiso_id INTEGER NOT NULL
,   PRIMARY KEY (rol_id, permiso_id)
);

-- ----------------------------------------------------------------------------
-- Tabla: rol_permisos
-- ----------------------------------------------------------------------------
CREATE TABLE rol_permisos (
    rol_id INTEGER NOT NULL,
    permiso_id INTEGER NOT NULL
,   PRIMARY KEY (rol_id, permiso_id)
);

-- ----------------------------------------------------------------------------
-- Tabla: usuarios
-- ----------------------------------------------------------------------------
CREATE TABLE usuarios (
    id INTEGER NOT NULL DEFAULT nextval('usuarios_id_seq'::regclass),
    persona_ci VARCHAR(20) NOT NULL,
    rol_id INTEGER NOT NULL,
    username VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT true,
    ultimo_login TIMESTAMP WITH TIME ZONE NULL
,   PRIMARY KEY (id)
);

INSERT INTO usuarios (id, persona_ci, rol_id, username, password_hash, activo, ultimo_login) VALUES (1, '1001', 1, 'admin', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', TRUE, NULL);
INSERT INTO usuarios (id, persona_ci, rol_id, username, password_hash, activo, ultimo_login) VALUES (2, '25950728', 4, 'yeison3', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', TRUE, NULL);
INSERT INTO usuarios (id, persona_ci, rol_id, username, password_hash, activo, ultimo_login) VALUES (3, '18320484', 4, 'Yeison', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', TRUE, NULL);
INSERT INTO usuarios (id, persona_ci, rol_id, username, password_hash, activo, ultimo_login) VALUES (4, '22615273', 4, 'testuser99', 'bd94dcda26fccb4e68d6a31f9b5aac0b571ae266d822620e901ef7ebe3a11d4f', TRUE, NULL);
INSERT INTO usuarios (id, persona_ci, rol_id, username, password_hash, activo, ultimo_login) VALUES (5, '17112834', 4, 'YEISONN', '844eb1123796bbe327ab6fe391b913e263f538601d3f7f63bbedd839b5e1651c', TRUE, NULL);
INSERT INTO usuarios (id, persona_ci, rol_id, username, password_hash, activo, ultimo_login) VALUES (6, '11619521', 4, 'Yheison', '8df71dc7e10c9f566fc4d3fef71adc7b2e20166193b59bd803a7516edc5da81c', TRUE, NULL);
INSERT INTO usuarios (id, persona_ci, rol_id, username, password_hash, activo, ultimo_login) VALUES (7, '14994379', 4, 'user_cd291f', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', TRUE, NULL);
INSERT INTO usuarios (id, persona_ci, rol_id, username, password_hash, activo, ultimo_login) VALUES (8, '11540380', 4, 'cliente_20e38c', 'a109e36947ad56de1dca1cc49f0ef8ac9ad9a7b1aa0df41fb3c4cb73c1ff01ea', TRUE, NULL);

-- ----------------------------------------------------------------------------
-- Tabla: sucursales
-- ----------------------------------------------------------------------------
CREATE TABLE sucursales (
    id INTEGER NOT NULL DEFAULT nextval('sucursales_id_seq'::regclass),
    nombre VARCHAR(100) NOT NULL,
    direccion VARCHAR(255) NOT NULL,
    ciudad VARCHAR(100) NOT NULL DEFAULT 'Santa Cruz de la Sierra'::character varying,
    telefono VARCHAR(30) NULL,
    latitud NUMERIC(12,2) NULL,
    longitud NUMERIC(12,2) NULL,
    es_almacen_central BOOLEAN NOT NULL DEFAULT false,
    activo BOOLEAN NOT NULL DEFAULT true
,   PRIMARY KEY (id)
);

INSERT INTO sucursales (id, nombre, direccion, ciudad, telefono, latitud, longitud, es_almacen_central, activo) VALUES (1, 'Sucursal Central', 'Calle 21 de Calacoto #100', 'Santa Cruz', '+591 3 3322114', '-17.7833000', '-63.1821000', TRUE, TRUE);
INSERT INTO sucursales (id, nombre, direccion, ciudad, telefono, latitud, longitud, es_almacen_central, activo) VALUES (2, 'Sucursal Equipetrol', 'Av. San Martín esq. Calle 5', 'Santa Cruz', '+591 3 3344556', '-17.7712000', '-63.1950000', FALSE, TRUE);
INSERT INTO sucursales (id, nombre, direccion, ciudad, telefono, latitud, longitud, es_almacen_central, activo) VALUES (3, 'Sucursal Ventura Mall', '4to Anillo esq. Av. San Martín', 'Santa Cruz', '+591 3 3377889', '-17.7554000', '-63.2012000', FALSE, TRUE);

-- ----------------------------------------------------------------------------
-- Tabla: categorias
-- ----------------------------------------------------------------------------
CREATE TABLE categorias (
    id INTEGER NOT NULL DEFAULT nextval('categorias_id_seq'::regclass),
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT NULL,
    activo BOOLEAN NOT NULL DEFAULT true
,   PRIMARY KEY (id)
);

INSERT INTO categorias (id, nombre, descripcion, activo) VALUES (1, 'Denim & Jeans', 'Pantalones, chaquetas y faldas de mezclilla de alta resistencia', TRUE);
INSERT INTO categorias (id, nombre, descripcion, activo) VALUES (2, 'Casual & Poleras', 'Prendas cómodas de algodón 100% para uso diario', TRUE);
INSERT INTO categorias (id, nombre, descripcion, activo) VALUES (3, 'Vestidos & Fiesta', 'Vestidos de gala, cóctel y eventos especiales', TRUE);
INSERT INTO categorias (id, nombre, descripcion, activo) VALUES (4, 'Calzado & Accesorios', 'Zapatos, cinturones y carteras de cuero', TRUE);
INSERT INTO categorias (id, nombre, descripcion, activo) VALUES (5, 'Invierno Actualizado', NULL, TRUE);
INSERT INTO categorias (id, nombre, descripcion, activo) VALUES (6, 'Ropa de Invierno', NULL, TRUE);
INSERT INTO categorias (id, nombre, descripcion, activo) VALUES (8, 'PARO AURA', NULL, TRUE);

-- ----------------------------------------------------------------------------
-- Tabla: temporadas
-- ----------------------------------------------------------------------------
CREATE TABLE temporadas (
    id INTEGER NOT NULL DEFAULT nextval('temporadas_id_seq'::regclass),
    nombre VARCHAR(100) NOT NULL,
    fec_inicio DATE NULL,
    fec_fin DATE NULL,
    activo BOOLEAN NOT NULL DEFAULT true
,   PRIMARY KEY (id)
);

INSERT INTO temporadas (id, nombre, fec_inicio, fec_fin, activo) VALUES (1, 'Verano 2026', '2025-12-01', '2026-03-31', TRUE);
INSERT INTO temporadas (id, nombre, fec_inicio, fec_fin, activo) VALUES (2, 'Otoño 2026', '2026-04-01', '2026-06-30', TRUE);
INSERT INTO temporadas (id, nombre, fec_inicio, fec_fin, activo) VALUES (3, 'Invierno 2026', '2026-07-01', '2026-09-30', TRUE);
INSERT INTO temporadas (id, nombre, fec_inicio, fec_fin, activo) VALUES (4, 'Primavera 2026', '2026-10-01', '2026-11-30', TRUE);
INSERT INTO temporadas (id, nombre, fec_inicio, fec_fin, activo) VALUES (6, 'Examen', NULL, NULL, TRUE);

-- ----------------------------------------------------------------------------
-- Tabla: proveedores
-- ----------------------------------------------------------------------------
CREATE TABLE proveedores (
    id INTEGER NOT NULL DEFAULT nextval('proveedores_id_seq'::regclass),
    razon_social VARCHAR(150) NOT NULL,
    nit VARCHAR(30) NULL,
    contacto VARCHAR(100) NULL,
    telefono VARCHAR(30) NULL,
    direccion VARCHAR(255) NULL,
    correo VARCHAR(150) NULL,
    activo BOOLEAN NOT NULL DEFAULT true
,   PRIMARY KEY (id)
);

INSERT INTO proveedores (id, razon_social, nit, contacto, telefono, direccion, correo, activo) VALUES (1, 'Textiles Andinos S.R.L.', '1029384701', 'Ing. Roberto Paz', '+591 3 3445566', 'Parque Industrial Mz 14', 'ventas@textilesandinos.bo', TRUE);
INSERT INTO proveedores (id, razon_social, nit, contacto, telefono, direccion, correo, activo) VALUES (5, 'FICCT services Cristian', NULL, NULL, '12345', 'SE descarga musica', NULL, TRUE);

-- ----------------------------------------------------------------------------
-- Tabla: colores
-- ----------------------------------------------------------------------------
CREATE TABLE colores (
    id INTEGER NOT NULL DEFAULT nextval('colores_id_seq'::regclass),
    nombre VARCHAR(50) NOT NULL,
    codigo_hex VARCHAR(10) NOT NULL
,   PRIMARY KEY (id)
);

INSERT INTO colores (id, nombre, codigo_hex) VALUES (1, 'Azul Denim', '#1E3A8A');
INSERT INTO colores (id, nombre, codigo_hex) VALUES (2, 'Negro Clásico', '#000000');
INSERT INTO colores (id, nombre, codigo_hex) VALUES (3, 'Blanco Puro', '#FFFFFF');
INSERT INTO colores (id, nombre, codigo_hex) VALUES (4, 'Beige Natural', '#F5F5DC');
INSERT INTO colores (id, nombre, codigo_hex) VALUES (9, 'NAZ', '#8000ff');

-- ----------------------------------------------------------------------------
-- Tabla: tallas
-- ----------------------------------------------------------------------------
CREATE TABLE tallas (
    id INTEGER NOT NULL DEFAULT nextval('tallas_id_seq'::regclass),
    medida VARCHAR(20) NOT NULL,
    tipo VARCHAR(50) NOT NULL DEFAULT 'Ropa General'::character varying,
    guia_medida VARCHAR(150) NULL
,   PRIMARY KEY (id)
);

INSERT INTO tallas (id, medida, tipo, guia_medida) VALUES (1, 'XS', 'Ropa Superior', NULL);
INSERT INTO tallas (id, medida, tipo, guia_medida) VALUES (2, 'S', 'Ropa Superior', NULL);
INSERT INTO tallas (id, medida, tipo, guia_medida) VALUES (3, 'M', 'Ropa Superior', NULL);
INSERT INTO tallas (id, medida, tipo, guia_medida) VALUES (4, 'L', 'Ropa Superior', NULL);
INSERT INTO tallas (id, medida, tipo, guia_medida) VALUES (5, 'XL', 'Ropa Superior', NULL);
INSERT INTO tallas (id, medida, tipo, guia_medida) VALUES (6, '38', 'Pantalones', NULL);
INSERT INTO tallas (id, medida, tipo, guia_medida) VALUES (7, '40', 'Pantalones', NULL);
INSERT INTO tallas (id, medida, tipo, guia_medida) VALUES (8, '42', 'Pantalones', NULL);

-- ----------------------------------------------------------------------------
-- Tabla: ropa
-- ----------------------------------------------------------------------------
CREATE TABLE ropa (
    id INTEGER NOT NULL DEFAULT nextval('ropa_id_seq'::regclass),
    categoria_id INTEGER NOT NULL,
    temporada_id INTEGER NULL,
    proveedor_id INTEGER NULL,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT NULL,
    precio NUMERIC(12,2) NOT NULL,
    costo_estandar NUMERIC(12,2) NULL DEFAULT 0.00,
    genero VARCHAR(20) NULL,
    imagen_uri VARCHAR(500) NULL,
    modelo_3d_uri VARCHAR(500) NULL,
    activo BOOLEAN NOT NULL DEFAULT true,
    fec_creacion TIMESTAMP WITH TIME ZONE NULL DEFAULT CURRENT_TIMESTAMP
,   PRIMARY KEY (id)
);

INSERT INTO ropa (id, categoria_id, temporada_id, proveedor_id, nombre, descripcion, precio, costo_estandar, genero, imagen_uri, modelo_3d_uri, activo, fec_creacion) VALUES (1, 1, 1, 1, 'Chaqueta Denim Vintage', 'Chaqueta vaquera corte clásico con acabados desgastados', '349.99', '180.00', 'Unisex', 'https://images.unsplash.com/photo-1576995853123-5a10305d93c0', '/static/uploads/calzado_deportivo_3d.glb', TRUE, '2026-09-11T10:46:52.543732-04:00');
INSERT INTO ropa (id, categoria_id, temporada_id, proveedor_id, nombre, descripcion, precio, costo_estandar, genero, imagen_uri, modelo_3d_uri, activo, fec_creacion) VALUES (2, 2, 1, 1, 'Polera Oversize Cotton', 'Polera holgada de algodón pima transpirable', '129.50', '55.00', 'Hombre', 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518', '/static/uploads/traje_hombre_3d.glb', TRUE, '2026-09-11T10:46:52.543732-04:00');
INSERT INTO ropa (id, categoria_id, temporada_id, proveedor_id, nombre, descripcion, precio, costo_estandar, genero, imagen_uri, modelo_3d_uri, activo, fec_creacion) VALUES (3, 3, 1, 1, 'Vestido Seda Floral', 'Vestido largo de seda con estampado botánico de temporada', '450.00', '210.00', 'Mujer', 'https://images.unsplash.com/photo-1572804013309-59a88b7e92f1', '/static/uploads/polera_textil_3d.glb', TRUE, '2026-09-11T10:46:52.543732-04:00');
INSERT INTO ropa (id, categoria_id, temporada_id, proveedor_id, nombre, descripcion, precio, costo_estandar, genero, imagen_uri, modelo_3d_uri, activo, fec_creacion) VALUES (7, 1, 1, 1, 'Chaqueta Cuero 3D AR Edition', 'Chaqueta moderna con soporte de visualización 3D y probador virtual AR', '350.00', '0.00', NULL, 'https://images.unsplash.com/photo-1551028719-00167b16eac5', '/static/uploads/chaqueta_cuero_3d.glb', TRUE, '2026-09-13T11:13:27.216050-04:00');
INSERT INTO ropa (id, categoria_id, temporada_id, proveedor_id, nombre, descripcion, precio, costo_estandar, genero, imagen_uri, modelo_3d_uri, activo, fec_creacion) VALUES (8, 1, 1, 1, 'Chaqueta Cuero 3D Modificada', 'Descripción actualizada con nuevo precio y modelo', '320.00', '0.00', NULL, 'https://images.unsplash.com/photo-1551028719-00167b16eac5', '/static/uploads/chaqueta_cuero_3d.glb', TRUE, '2026-09-13T11:16:31.297057-04:00');
INSERT INTO ropa (id, categoria_id, temporada_id, proveedor_id, nombre, descripcion, precio, costo_estandar, genero, imagen_uri, modelo_3d_uri, activo, fec_creacion) VALUES (9, 1, 1, 1, 'Chaqueta Cuero 3D Test', 'Chaqueta de cuero sintético premium con modelo AR', '299.99', '0.00', NULL, 'https://images.unsplash.com/photo-1551028719-00167b16eac5', '/static/uploads/chaqueta_cuero_3d.glb', TRUE, '2026-09-13T11:16:43.799315-04:00');
INSERT INTO ropa (id, categoria_id, temporada_id, proveedor_id, nombre, descripcion, precio, costo_estandar, genero, imagen_uri, modelo_3d_uri, activo, fec_creacion) VALUES (14, 1, 1, 1, 'Vestido Gala 3D AR 530250 (Edición Especial)', 'Descripción ampliada con detalles de confección', '520.00', '0.00', NULL, 'https://images.unsplash.com/photo-1566174053879-31528523f8ae', '/static/uploads/polera_textil_3d.glb', TRUE, '2026-09-13T14:29:36.491336-04:00');
INSERT INTO ropa (id, categoria_id, temporada_id, proveedor_id, nombre, descripcion, precio, costo_estandar, genero, imagen_uri, modelo_3d_uri, activo, fec_creacion) VALUES (17, 2, 1, 5, 'Polera de UFICCT', 'sdsdfs', '150.00', '0.00', NULL, '/static/uploads/media_17_ad5eb277.jpg', '/static/uploads/chaqueta_cuero_3d.glb', TRUE, '2026-09-13T14:39:24.616031-04:00');

-- ----------------------------------------------------------------------------
-- Tabla: variantes_prenda
-- ----------------------------------------------------------------------------
CREATE TABLE variantes_prenda (
    id INTEGER NOT NULL DEFAULT nextval('variantes_prenda_id_seq'::regclass),
    ropa_id INTEGER NOT NULL,
    talla_id INTEGER NOT NULL,
    color_id INTEGER NOT NULL,
    sku VARCHAR(60) NOT NULL,
    cod_barra VARCHAR(60) NULL,
    precio_ajustado NUMERIC(12,2) NULL,
    activo BOOLEAN NOT NULL DEFAULT true
,   PRIMARY KEY (id)
);

INSERT INTO variantes_prenda (id, ropa_id, talla_id, color_id, sku, cod_barra, precio_ajustado, activo) VALUES (1, 1, 3, 1, 'DNM-VNT-M-BLU', '777000100101', '349.99', TRUE);
INSERT INTO variantes_prenda (id, ropa_id, talla_id, color_id, sku, cod_barra, precio_ajustado, activo) VALUES (2, 1, 4, 1, 'DNM-VNT-L-BLU', '777000100102', '349.99', TRUE);
INSERT INTO variantes_prenda (id, ropa_id, talla_id, color_id, sku, cod_barra, precio_ajustado, activo) VALUES (3, 1, 3, 2, 'DNM-VNT-M-BLK', '777000100103', '349.99', TRUE);
INSERT INTO variantes_prenda (id, ropa_id, talla_id, color_id, sku, cod_barra, precio_ajustado, activo) VALUES (4, 2, 2, 3, 'POL-OVR-S-WHT', '777000200101', '129.50', TRUE);
INSERT INTO variantes_prenda (id, ropa_id, talla_id, color_id, sku, cod_barra, precio_ajustado, activo) VALUES (5, 2, 3, 3, 'POL-OVR-M-WHT', '777000200102', '129.50', TRUE);
INSERT INTO variantes_prenda (id, ropa_id, talla_id, color_id, sku, cod_barra, precio_ajustado, activo) VALUES (6, 2, 4, 2, 'POL-OVR-L-BLK', '777000200103', '129.50', TRUE);
INSERT INTO variantes_prenda (id, ropa_id, talla_id, color_id, sku, cod_barra, precio_ajustado, activo) VALUES (7, 3, 3, 4, 'VES-FLR-M-BGE', '777000300101', '450.00', TRUE);
INSERT INTO variantes_prenda (id, ropa_id, talla_id, color_id, sku, cod_barra, precio_ajustado, activo) VALUES (8, 8, 1, 1, 'CHQ-CUERO-XS-AZUL', '7770001112223', '299.99', TRUE);
INSERT INTO variantes_prenda (id, ropa_id, talla_id, color_id, sku, cod_barra, precio_ajustado, activo) VALUES (11, 14, 2, 1, 'VG-M-NEG-530250', '77700530250', '520.00', TRUE);
INSERT INTO variantes_prenda (id, ropa_id, talla_id, color_id, sku, cod_barra, precio_ajustado, activo) VALUES (13, 17, 3, 1, 'POL-17-M-STD', '777000000017', '150.00', TRUE);
INSERT INTO variantes_prenda (id, ropa_id, talla_id, color_id, sku, cod_barra, precio_ajustado, activo) VALUES (14, 7, 3, 1, 'CHA-7-M-STD', '777000000007', '350.00', TRUE);
INSERT INTO variantes_prenda (id, ropa_id, talla_id, color_id, sku, cod_barra, precio_ajustado, activo) VALUES (15, 9, 3, 1, 'CHA-9-M-STD', '777000000009', '299.99', TRUE);

-- ----------------------------------------------------------------------------
-- Tabla: inventario_sucursal
-- ----------------------------------------------------------------------------
CREATE TABLE inventario_sucursal (
    id INTEGER NOT NULL DEFAULT nextval('inventario_sucursal_id_seq'::regclass),
    sucursal_id INTEGER NOT NULL,
    variante_id INTEGER NOT NULL,
    stock_fisico INTEGER NOT NULL DEFAULT 0,
    stock_reservado INTEGER NOT NULL DEFAULT 0,
    stock_disponible INTEGER NULL,
    stock_minimo INTEGER NOT NULL DEFAULT 2,
    fec_actualizacion TIMESTAMP WITH TIME ZONE NULL DEFAULT CURRENT_TIMESTAMP
,   PRIMARY KEY (id)
);

INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (1, 1, 1, 38, 2, 36, 5, '2026-09-14T18:45:31.129404-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (2, 1, 2, 18, 0, 18, 5, '2026-09-13T17:15:33.310847-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (3, 1, 3, 15, 0, 15, 5, '2026-09-11T10:46:52.551595-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (4, 1, 4, 30, 0, 30, 5, '2026-09-11T10:46:52.551595-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (5, 1, 5, 40, 2, 38, 5, '2026-09-11T10:46:52.551595-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (6, 1, 6, 25, 0, 25, 5, '2026-09-11T10:46:52.551595-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (7, 1, 7, 10, 0, 10, 2, '2026-09-11T10:46:52.551595-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (8, 2, 1, 16, 1, 15, 3, '2026-09-13T17:06:35.996984-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (9, 2, 2, 10, 0, 10, 3, '2026-09-11T10:46:52.551595-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (10, 2, 3, 8, 0, 8, 3, '2026-09-11T10:46:52.551595-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (11, 2, 4, 15, 0, 15, 3, '2026-09-11T10:46:52.551595-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (12, 2, 5, 20, 0, 20, 3, '2026-09-11T10:46:52.551595-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (13, 2, 6, 14, 0, 14, 3, '2026-09-11T10:46:52.551595-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (14, 2, 7, 5, 0, 5, 2, '2026-09-11T10:46:52.551595-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (15, 3, 1, 18, 0, 18, 4, '2026-09-11T10:46:52.551595-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (16, 3, 2, 17, 0, 17, 4, '2026-09-13T17:28:13.504122-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (17, 3, 3, 12, 0, 12, 4, '2026-09-11T10:46:52.551595-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (18, 3, 4, 25, 0, 25, 4, '2026-09-11T10:46:52.551595-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (19, 3, 5, 30, 0, 30, 4, '2026-09-11T10:46:52.551595-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (20, 3, 6, 18, 0, 18, 4, '2026-09-11T10:46:52.551595-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (21, 3, 7, 8, 0, 8, 2, '2026-09-11T10:46:52.551595-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (54, 1, 8, 29, 0, 29, 5, '2026-09-13T17:15:33.314597-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (55, 1, 11, 1, 0, 1, 5, '2026-09-13T17:10:31.656430-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (56, 2, 8, 0, 0, 0, 5, '2026-09-13T21:13:56.988128-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (57, 2, 11, 0, 0, 0, 5, '2026-09-13T21:13:56.988148-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (58, 3, 8, 1, 0, 1, 5, '2026-09-13T17:28:13.507812-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (59, 3, 11, 0, 0, 0, 5, '2026-09-13T21:14:02.104845-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (60, 1, 13, 2, 1, 1, 5, '2026-09-14T18:48:11.611278-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (61, 2, 13, 17, 0, 17, 5, '2026-09-14T19:00:24.487903-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (62, 3, 13, 15, 0, 15, 5, '2026-09-13T21:34:20.146873-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (63, 1, 14, 15, 0, 15, 5, '2026-09-13T21:34:20.150583-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (64, 2, 14, 15, 0, 15, 5, '2026-09-13T21:34:20.150586-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (65, 3, 14, 15, 0, 15, 5, '2026-09-13T21:34:20.150586-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (66, 1, 15, 15, 0, 15, 5, '2026-09-13T21:34:20.151852-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (67, 2, 15, 15, 0, 15, 5, '2026-09-13T21:34:20.151854-04:00');
INSERT INTO inventario_sucursal (id, sucursal_id, variante_id, stock_fisico, stock_reservado, stock_disponible, stock_minimo, fec_actualizacion) VALUES (68, 3, 15, 15, 0, 15, 5, '2026-09-13T21:34:20.151855-04:00');

-- ----------------------------------------------------------------------------
-- Tabla: movimientos_inventario
-- ----------------------------------------------------------------------------
CREATE TABLE movimientos_inventario (
    id INTEGER NOT NULL DEFAULT nextval('movimientos_inventario_id_seq'::regclass),
    sucursal_id INTEGER NOT NULL,
    variante_id INTEGER NOT NULL,
    tipo_movimiento VARCHAR(30) NOT NULL,
    cantidad INTEGER NOT NULL,
    stock_anterior INTEGER NOT NULL,
    stock_nuevo INTEGER NOT NULL,
    motivo VARCHAR(255) NULL,
    fecha TIMESTAMP WITH TIME ZONE NOT NULL,
    usuario_ci VARCHAR(50) NULL
,   PRIMARY KEY (id)
);

INSERT INTO movimientos_inventario (id, sucursal_id, variante_id, tipo_movimiento, cantidad, stock_anterior, stock_nuevo, motivo, fecha, usuario_ci) VALUES (1, 1, 1, 'ENTRADA', 15, 25, 40, 'Lote reposición semanal Proveedor Textil', '2026-09-13T21:06:15.396159-04:00', NULL);
INSERT INTO movimientos_inventario (id, sucursal_id, variante_id, tipo_movimiento, cantidad, stock_anterior, stock_nuevo, motivo, fecha, usuario_ci) VALUES (2, 1, 1, 'DANIO', -2, 40, 38, 'Prenda rota durante exhibición en tienda', '2026-09-13T21:06:15.409841-04:00', NULL);
INSERT INTO movimientos_inventario (id, sucursal_id, variante_id, tipo_movimiento, cantidad, stock_anterior, stock_nuevo, motivo, fecha, usuario_ci) VALUES (3, 1, 1, 'ENTRADA', 15, 38, 53, 'Lote reposición semanal Proveedor Textil', '2026-09-13T21:06:35.951150-04:00', NULL);
INSERT INTO movimientos_inventario (id, sucursal_id, variante_id, tipo_movimiento, cantidad, stock_anterior, stock_nuevo, motivo, fecha, usuario_ci) VALUES (4, 1, 1, 'DANIO', -2, 53, 51, 'Prenda rota durante exhibición en tienda', '2026-09-13T21:06:35.961656-04:00', NULL);
INSERT INTO movimientos_inventario (id, sucursal_id, variante_id, tipo_movimiento, cantidad, stock_anterior, stock_nuevo, motivo, fecha, usuario_ci) VALUES (5, 1, 1, 'TRASPASO_SALIDA', -4, 51, 47, 'Despacho por Traspaso #1 hacia Sucursal Equipetrol', '2026-09-13T21:06:35.984139-04:00', NULL);
INSERT INTO movimientos_inventario (id, sucursal_id, variante_id, tipo_movimiento, cantidad, stock_anterior, stock_nuevo, motivo, fecha, usuario_ci) VALUES (6, 2, 1, 'TRASPASO_ENTRADA', 4, 12, 16, 'Recepción de mercadería por Traspaso #1 desde Sucursal Central', '2026-09-13T21:06:35.997697-04:00', NULL);
INSERT INTO movimientos_inventario (id, sucursal_id, variante_id, tipo_movimiento, cantidad, stock_anterior, stock_nuevo, motivo, fecha, usuario_ci) VALUES (7, 1, 8, 'ENTRADA', 20, 0, 20, 'Ingreso de mercadería / Lote nuevo', '2026-09-13T21:09:54.580218-04:00', NULL);
INSERT INTO movimientos_inventario (id, sucursal_id, variante_id, tipo_movimiento, cantidad, stock_anterior, stock_nuevo, motivo, fecha, usuario_ci) VALUES (8, 1, 8, 'ENTRADA', 10, 20, 30, 'Ingreso de mercadería / Lote nuevo', '2026-09-13T21:10:11.617738-04:00', NULL);
INSERT INTO movimientos_inventario (id, sucursal_id, variante_id, tipo_movimiento, cantidad, stock_anterior, stock_nuevo, motivo, fecha, usuario_ci) VALUES (9, 1, 11, 'ENTRADA', 1, 0, 1, 'Ingreso de mercadería / Lote nuevo', '2026-09-13T21:10:31.659556-04:00', NULL);
INSERT INTO movimientos_inventario (id, sucursal_id, variante_id, tipo_movimiento, cantidad, stock_anterior, stock_nuevo, motivo, fecha, usuario_ci) VALUES (10, 1, 2, 'TRASPASO_SALIDA', -2, 20, 18, 'Despacho por Traspaso #2 hacia Sucursal Ventura Mall', '2026-09-13T21:15:33.341377-04:00', NULL);
INSERT INTO movimientos_inventario (id, sucursal_id, variante_id, tipo_movimiento, cantidad, stock_anterior, stock_nuevo, motivo, fecha, usuario_ci) VALUES (11, 1, 8, 'TRASPASO_SALIDA', -1, 30, 29, 'Despacho por Traspaso #2 hacia Sucursal Ventura Mall', '2026-09-13T21:15:33.341393-04:00', NULL);
INSERT INTO movimientos_inventario (id, sucursal_id, variante_id, tipo_movimiento, cantidad, stock_anterior, stock_nuevo, motivo, fecha, usuario_ci) VALUES (12, 3, 2, 'TRASPASO_ENTRADA', 2, 15, 17, 'Recepción de mercadería por Traspaso #2 desde Sucursal Central', '2026-09-13T21:28:13.526815-04:00', NULL);
INSERT INTO movimientos_inventario (id, sucursal_id, variante_id, tipo_movimiento, cantidad, stock_anterior, stock_nuevo, motivo, fecha, usuario_ci) VALUES (13, 3, 8, 'TRASPASO_ENTRADA', 1, 0, 1, 'Recepción de mercadería por Traspaso #2 desde Sucursal Central', '2026-09-13T21:28:13.526834-04:00', NULL);

-- ----------------------------------------------------------------------------
-- Tabla: traspasos
-- ----------------------------------------------------------------------------
CREATE TABLE traspasos (
    id INTEGER NOT NULL DEFAULT nextval('traspasos_id_seq'::regclass),
    sucursal_origen_id INTEGER NOT NULL,
    sucursal_destino_id INTEGER NOT NULL,
    solicitado_por_ci VARCHAR(20) NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'PENDIENTE'::character varying,
    observacion TEXT NULL,
    fec_solicitud TIMESTAMP WITH TIME ZONE NULL DEFAULT CURRENT_TIMESTAMP,
    fec_recepcion TIMESTAMP WITH TIME ZONE NULL
,   PRIMARY KEY (id)
);

INSERT INTO traspasos (id, sucursal_origen_id, sucursal_destino_id, solicitado_por_ci, estado, observacion, fec_solicitud, fec_recepcion) VALUES (1, 1, 2, NULL, 'RECIBIDO', 'Rebalanceo de stock de Central a Equipetrol', '2026-09-13T17:06:35.974406-04:00', '2026-09-13T17:06:35.997036-04:00');
INSERT INTO traspasos (id, sucursal_origen_id, sucursal_destino_id, solicitado_por_ci, estado, observacion, fec_solicitud, fec_recepcion) VALUES (2, 1, 3, NULL, 'RECIBIDO', 'Traspaso de reposición de mercadería', '2026-09-13T17:15:33.294618-04:00', '2026-09-13T17:28:13.508164-04:00');

-- ----------------------------------------------------------------------------
-- Tabla: detalles_traspaso
-- ----------------------------------------------------------------------------
CREATE TABLE detalles_traspaso (
    id INTEGER NOT NULL DEFAULT nextval('detalles_traspaso_id_seq'::regclass),
    traspaso_id INTEGER NOT NULL,
    variante_id INTEGER NOT NULL,
    cantidad INTEGER NOT NULL
,   PRIMARY KEY (id)
);

INSERT INTO detalles_traspaso (id, traspaso_id, variante_id, cantidad) VALUES (1, 1, 1, 4);
INSERT INTO detalles_traspaso (id, traspaso_id, variante_id, cantidad) VALUES (2, 2, 2, 2);
INSERT INTO detalles_traspaso (id, traspaso_id, variante_id, cantidad) VALUES (3, 2, 8, 1);

-- ----------------------------------------------------------------------------
-- Tabla: promociones
-- ----------------------------------------------------------------------------
CREATE TABLE promociones (
    id INTEGER NOT NULL DEFAULT nextval('promociones_id_seq'::regclass),
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT NULL,
    porcentaje_descuento NUMERIC(12,2) NOT NULL,
    fec_inicio TIMESTAMP WITH TIME ZONE NOT NULL,
    fec_fin TIMESTAMP WITH TIME ZONE NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT true
,   PRIMARY KEY (id)
);

INSERT INTO promociones (id, nombre, descripcion, porcentaje_descuento, fec_inicio, fec_fin, activo) VALUES (1, 'Cyber Fashion 15% OFF', 'Descuento especial de temporada en línea Denim', '27.00', '2026-09-10T10:46:00-04:00', '2026-09-26T10:46:00-04:00', FALSE);
INSERT INTO promociones (id, nombre, descripcion, porcentaje_descuento, fec_inicio, fec_fin, activo) VALUES (3, 'Liquidación de Primavera 25% OFF', '25% de descuento en vestidos, faldas y prendas de temporada primavera-verano.', '25.00', '2026-08-31T20:00:00-04:00', '2026-09-30T19:59:59-04:00', TRUE);
INSERT INTO promociones (id, nombre, descripcion, porcentaje_descuento, fec_inicio, fec_fin, activo) VALUES (4, 'Descuento Calzados & Casual 20%', 'Ahorra un 20% en toda la colección de zapatillas y calzado deportivo.', '20.00', '2026-09-11T20:00:00-04:00', '2026-10-15T19:59:59-04:00', TRUE);
INSERT INTO promociones (id, nombre, descripcion, porcentaje_descuento, fec_inicio, fec_fin, activo) VALUES (6, 'EXAMENES', 'LLEVE CASE', '27.00', '2026-09-13T16:49:00-04:00', '2026-09-27T16:49:00-04:00', FALSE);

-- ----------------------------------------------------------------------------
-- Tabla: promocion_ropa
-- ----------------------------------------------------------------------------
CREATE TABLE promocion_ropa (
    id INTEGER NOT NULL DEFAULT nextval('promocion_ropa_id_seq'::regclass),
    promocion_id INTEGER NOT NULL,
    ropa_id INTEGER NOT NULL,
    fec_asignacion TIMESTAMP WITH TIME ZONE NULL DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(20) NULL DEFAULT 'ACTIVA'::character varying
,   PRIMARY KEY (id)
);

INSERT INTO promocion_ropa (id, promocion_id, ropa_id, fec_asignacion, estado) VALUES (4, 3, 2, '2026-09-13T19:31:57.718055-04:00', 'ACTIVA');
INSERT INTO promocion_ropa (id, promocion_id, ropa_id, fec_asignacion, estado) VALUES (5, 3, 3, '2026-09-13T19:31:57.718057-04:00', 'ACTIVA');
INSERT INTO promocion_ropa (id, promocion_id, ropa_id, fec_asignacion, estado) VALUES (6, 4, 7, '2026-09-13T19:32:37.863925-04:00', 'ACTIVA');
INSERT INTO promocion_ropa (id, promocion_id, ropa_id, fec_asignacion, estado) VALUES (7, 4, 8, '2026-09-13T19:32:37.863927-04:00', 'ACTIVA');
INSERT INTO promocion_ropa (id, promocion_id, ropa_id, fec_asignacion, estado) VALUES (8, 4, 14, '2026-09-13T19:32:37.863928-04:00', 'ACTIVA');
INSERT INTO promocion_ropa (id, promocion_id, ropa_id, fec_asignacion, estado) VALUES (16, 1, 1, '2026-09-13T20:48:57.682895-04:00', 'ACTIVA');
INSERT INTO promocion_ropa (id, promocion_id, ropa_id, fec_asignacion, estado) VALUES (17, 1, 17, '2026-09-13T20:48:57.682910-04:00', 'ACTIVA');
INSERT INTO promocion_ropa (id, promocion_id, ropa_id, fec_asignacion, estado) VALUES (20, 6, 17, '2026-09-17T14:39:03.017833-04:00', 'ACTIVA');
INSERT INTO promocion_ropa (id, promocion_id, ropa_id, fec_asignacion, estado) VALUES (21, 6, 14, '2026-09-17T14:39:03.017843-04:00', 'ACTIVA');
INSERT INTO promocion_ropa (id, promocion_id, ropa_id, fec_asignacion, estado) VALUES (22, 6, 9, '2026-09-17T14:39:03.017847-04:00', 'ACTIVA');

-- ----------------------------------------------------------------------------
-- Tabla: carritos_compra
-- ----------------------------------------------------------------------------
CREATE TABLE carritos_compra (
    id INTEGER NOT NULL DEFAULT nextval('carritos_compra_id_seq'::regclass),
    cliente_ci VARCHAR(20) NOT NULL,
    fec_creacion TIMESTAMP WITH TIME ZONE NULL DEFAULT CURRENT_TIMESTAMP,
    fec_actualizacion TIMESTAMP WITH TIME ZONE NULL DEFAULT CURRENT_TIMESTAMP
,   PRIMARY KEY (id)
);

INSERT INTO carritos_compra (id, cliente_ci, fec_creacion, fec_actualizacion) VALUES (1, '2001', '2026-09-14T14:02:51.608580-04:00', '2026-09-14T14:02:51.608652-04:00');
INSERT INTO carritos_compra (id, cliente_ci, fec_creacion, fec_actualizacion) VALUES (2, 'admin', '2026-09-14T14:34:05.386270-04:00', '2026-09-14T18:54:32.949592-04:00');
INSERT INTO carritos_compra (id, cliente_ci, fec_creacion, fec_actualizacion) VALUES (3, 'mi_carrito', '2026-09-14T17:19:46.475097-04:00', '2026-09-14T17:19:46.477627-04:00');
INSERT INTO carritos_compra (id, cliente_ci, fec_creacion, fec_actualizacion) VALUES (4, 'descargar_pdf', '2026-09-14T17:27:48.210698-04:00', '2026-09-14T17:27:48.211256-04:00');

-- ----------------------------------------------------------------------------
-- Tabla: detalles_carrito_compra
-- ----------------------------------------------------------------------------
CREATE TABLE detalles_carrito_compra (
    id INTEGER NOT NULL DEFAULT nextval('detalles_carrito_compra_id_seq'::regclass),
    carrito_id INTEGER NOT NULL,
    variante_id INTEGER NOT NULL,
    cantidad INTEGER NOT NULL DEFAULT 1,
    fec_agregado TIMESTAMP WITH TIME ZONE NULL DEFAULT CURRENT_TIMESTAMP
,   PRIMARY KEY (id)
);

INSERT INTO detalles_carrito_compra (id, carrito_id, variante_id, cantidad, fec_agregado) VALUES (22, 1, 1, 1, '2026-09-14T17:12:10.809944-04:00');
INSERT INTO detalles_carrito_compra (id, carrito_id, variante_id, cantidad, fec_agregado) VALUES (23, 1, 13, 1, '2026-09-14T17:12:10.809954-04:00');
INSERT INTO detalles_carrito_compra (id, carrito_id, variante_id, cantidad, fec_agregado) VALUES (24, 1, 4, 1, '2026-09-14T17:12:10.809957-04:00');
INSERT INTO detalles_carrito_compra (id, carrito_id, variante_id, cantidad, fec_agregado) VALUES (25, 1, 7, 1, '2026-09-14T17:12:10.809960-04:00');

-- ----------------------------------------------------------------------------
-- Tabla: reservas
-- ----------------------------------------------------------------------------
CREATE TABLE reservas (
    id INTEGER NOT NULL DEFAULT nextval('reservas_id_seq'::regclass),
    cliente_ci VARCHAR(20) NOT NULL,
    sucursal_id INTEGER NOT NULL,
    fec_reserva TIMESTAMP WITH TIME ZONE NULL DEFAULT CURRENT_TIMESTAMP,
    fec_limite TIMESTAMP WITH TIME ZONE NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'PENDIENTE'::character varying,
    observacion TEXT NULL
,   PRIMARY KEY (id)
);

INSERT INTO reservas (id, cliente_ci, sucursal_id, fec_reserva, fec_limite, estado, observacion) VALUES (7, '2001', 1, '2026-09-14T00:06:57.121375-04:00', '2026-09-16T00:06:57.121375-04:00', 'PENDIENTE', 'Tarde');
INSERT INTO reservas (id, cliente_ci, sucursal_id, fec_reserva, fec_limite, estado, observacion) VALUES (9, '2001', 1, '2026-09-14T00:07:58.268246-04:00', '2026-09-16T00:07:58.268246-04:00', 'PENDIENTE', 'Tarde');
INSERT INTO reservas (id, cliente_ci, sucursal_id, fec_reserva, fec_limite, estado, observacion) VALUES (10, 'admin', 1, '2026-09-14T00:18:09.444801-04:00', '2026-09-16T00:18:09.444801-04:00', 'PENDIENTE', 'Hoy - dom, 13 sept | Turno: Tarde (14:00 - 18:00)');

-- ----------------------------------------------------------------------------
-- Tabla: detalles_reserva
-- ----------------------------------------------------------------------------
CREATE TABLE detalles_reserva (
    id INTEGER NOT NULL DEFAULT nextval('detalles_reserva_id_seq'::regclass),
    reserva_id INTEGER NOT NULL,
    variante_id INTEGER NOT NULL,
    cantidad INTEGER NOT NULL DEFAULT 1,
    precio_unitario NUMERIC(12,2) NOT NULL
,   PRIMARY KEY (id)
);

INSERT INTO detalles_reserva (id, reserva_id, variante_id, cantidad, precio_unitario) VALUES (2, 7, 1, 1, '349.99');
INSERT INTO detalles_reserva (id, reserva_id, variante_id, cantidad, precio_unitario) VALUES (3, 9, 1, 1, '349.99');
INSERT INTO detalles_reserva (id, reserva_id, variante_id, cantidad, precio_unitario) VALUES (4, 10, 13, 1, '150.00');

-- ----------------------------------------------------------------------------
-- Tabla: metodos_pago
-- ----------------------------------------------------------------------------
CREATE TABLE metodos_pago (
    id INTEGER NOT NULL DEFAULT nextval('metodos_pago_id_seq'::regclass),
    nombre VARCHAR(50) NOT NULL,
    tipo VARCHAR(30) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT true
,   PRIMARY KEY (id)
);

INSERT INTO metodos_pago (id, nombre, tipo, activo) VALUES (1, 'Efectivo en Caja', 'EFECTIVO', TRUE);
INSERT INTO metodos_pago (id, nombre, tipo, activo) VALUES (2, 'Tarjeta de Débito / Crédito POS', 'TARJETA_POS', TRUE);
INSERT INTO metodos_pago (id, nombre, tipo, activo) VALUES (3, 'QR Simple en Caja', 'QR_CAJA', TRUE);
INSERT INTO metodos_pago (id, nombre, tipo, activo) VALUES (4, 'Pasarela Stripe', 'PASARELA_DIGITAL', TRUE);
INSERT INTO metodos_pago (id, nombre, tipo, activo) VALUES (5, 'Pasarela Libélula QR', 'PASARELA_DIGITAL', TRUE);
INSERT INTO metodos_pago (id, nombre, tipo, activo) VALUES (6, 'PayPal Express', 'PASARELA_DIGITAL', TRUE);

-- ----------------------------------------------------------------------------
-- Tabla: tipos_venta
-- ----------------------------------------------------------------------------
CREATE TABLE tipos_venta (
    id INTEGER NOT NULL DEFAULT nextval('tipos_venta_id_seq'::regclass),
    nombre VARCHAR(50) NOT NULL,
    descripcion VARCHAR(255) NULL
,   PRIMARY KEY (id)
);

INSERT INTO tipos_venta (id, nombre, descripcion) VALUES (1, 'Presencial POS', 'Venta física asistida por cajero en sucursal');
INSERT INTO tipos_venta (id, nombre, descripcion) VALUES (2, 'Digital E-commerce Web', 'Compra en línea mediante plataforma web');
INSERT INTO tipos_venta (id, nombre, descripcion) VALUES (3, 'Digital App Móvil', 'Compra en línea desde aplicación móvil');

-- ----------------------------------------------------------------------------
-- Tabla: ventas
-- ----------------------------------------------------------------------------
CREATE TABLE ventas (
    id INTEGER NOT NULL DEFAULT nextval('ventas_id_seq'::regclass),
    cliente_ci VARCHAR(20) NULL,
    empleado_ci VARCHAR(20) NULL,
    sucursal_id INTEGER NOT NULL,
    tipo_venta_id INTEGER NOT NULL,
    metodo_pago_id INTEGER NOT NULL,
    monto_total NUMERIC(12,2) NOT NULL,
    descuento_total NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    monto_neto NUMERIC(12,2) NOT NULL,
    monto_recibido NUMERIC(12,2) NULL DEFAULT 0.00,
    cambio_devuelto NUMERIC(12,2) NULL DEFAULT 0.00,
    estado VARCHAR(30) NOT NULL DEFAULT 'COMPLETADA'::character varying,
    referencia_pago VARCHAR(150) NULL,
    fec_venta TIMESTAMP WITH TIME ZONE NULL DEFAULT CURRENT_TIMESTAMP
,   PRIMARY KEY (id)
);

INSERT INTO ventas (id, cliente_ci, empleado_ci, sucursal_id, tipo_venta_id, metodo_pago_id, monto_total, descuento_total, monto_neto, monto_recibido, cambio_devuelto, estado, referencia_pago, fec_venta) VALUES (4, NULL, '1001', 1, 1, 1, '600.00', '0.00', '600.00', '600.00', '0.00', 'COMPLETADA', 'TRX-POS-20260914-94F5C4', '2026-09-14T14:38:57.127994-04:00');
INSERT INTO ventas (id, cliente_ci, empleado_ci, sucursal_id, tipo_venta_id, metodo_pago_id, monto_total, descuento_total, monto_neto, monto_recibido, cambio_devuelto, estado, referencia_pago, fec_venta) VALUES (5, '2001', '1001', 1, 2, 2, '699.98', '0.00', '699.98', '699.98', '0.00', 'COMPLETADA', 'TRX-ECOM-20260914-281945', '2026-09-14T14:49:49.787468-04:00');
INSERT INTO ventas (id, cliente_ci, empleado_ci, sucursal_id, tipo_venta_id, metodo_pago_id, monto_total, descuento_total, monto_neto, monto_recibido, cambio_devuelto, estado, referencia_pago, fec_venta) VALUES (6, NULL, '1001', 1, 2, 2, '300.00', '0.00', '300.00', '300.00', '0.00', 'COMPLETADA', 'TRX-ECOM-20260914-FDDC42', '2026-09-14T15:09:32.150646-04:00');
INSERT INTO ventas (id, cliente_ci, empleado_ci, sucursal_id, tipo_venta_id, metodo_pago_id, monto_total, descuento_total, monto_neto, monto_recibido, cambio_devuelto, estado, referencia_pago, fec_venta) VALUES (7, '2001', '1001', 1, 2, 2, '699.98', '0.00', '699.98', '699.98', '0.00', 'COMPLETADA', 'TRX-ECOM-20260914-2954B3', '2026-09-14T15:13:43.053372-04:00');
INSERT INTO ventas (id, cliente_ci, empleado_ci, sucursal_id, tipo_venta_id, metodo_pago_id, monto_total, descuento_total, monto_neto, monto_recibido, cambio_devuelto, estado, referencia_pago, fec_venta) VALUES (8, '2001', '1001', 1, 2, 2, '699.98', '0.00', '699.98', '699.98', '0.00', 'COMPLETADA', 'TRX-ECOM-20260914-502104', '2026-09-14T13:12:10.633177-04:00');
INSERT INTO ventas (id, cliente_ci, empleado_ci, sucursal_id, tipo_venta_id, metodo_pago_id, monto_total, descuento_total, monto_neto, monto_recibido, cambio_devuelto, estado, referencia_pago, fec_venta) VALUES (11, NULL, '1001', 1, 2, 1, '109.50', '0.00', '109.50', '120.00', '10.50', 'COMPLETADA', 'TRX-ECOM-20260914-2B5E68', '2026-09-14T13:54:57.584780-04:00');
INSERT INTO ventas (id, cliente_ci, empleado_ci, sucursal_id, tipo_venta_id, metodo_pago_id, monto_total, descuento_total, monto_neto, monto_recibido, cambio_devuelto, estado, referencia_pago, fec_venta) VALUES (12, '2001', '1001', 1, 2, 2, '250.00', '0.00', '250.00', '500.00', '250.00', 'COMPLETADA', 'TRX-ECOM-20260914-ACFB7A', '2026-09-14T14:45:31.127741-04:00');
INSERT INTO ventas (id, cliente_ci, empleado_ci, sucursal_id, tipo_venta_id, metodo_pago_id, monto_total, descuento_total, monto_neto, monto_recibido, cambio_devuelto, estado, referencia_pago, fec_venta) VALUES (13, NULL, '1001', 1, 1, 1, '328.50', '0.00', '328.50', '400.00', '71.50', 'COMPLETADA', 'TRX-POS-20260914-86688F', '2026-09-14T14:48:11.605957-04:00');
INSERT INTO ventas (id, cliente_ci, empleado_ci, sucursal_id, tipo_venta_id, metodo_pago_id, monto_total, descuento_total, monto_neto, monto_recibido, cambio_devuelto, estado, referencia_pago, fec_venta) VALUES (14, NULL, '1001', 2, 1, 1, '300.00', '0.00', '300.00', '300.00', '0.00', 'COMPLETADA', 'TRX-POS-20260914-4ED659', '2026-09-14T15:00:22.272565-04:00');

-- ----------------------------------------------------------------------------
-- Tabla: detalles_venta
-- ----------------------------------------------------------------------------
CREATE TABLE detalles_venta (
    id INTEGER NOT NULL DEFAULT nextval('detalles_venta_id_seq'::regclass),
    venta_id INTEGER NOT NULL,
    variante_id INTEGER NOT NULL,
    cantidad INTEGER NOT NULL,
    precio_unitario NUMERIC(12,2) NOT NULL,
    subtotal NUMERIC(12,2) NOT NULL,
    descuento NUMERIC(12,2) NOT NULL DEFAULT 0.00
,   PRIMARY KEY (id)
);

INSERT INTO detalles_venta (id, venta_id, variante_id, cantidad, precio_unitario, subtotal, descuento) VALUES (3, 4, 13, 4, '150.00', '600.00', '0.00');
INSERT INTO detalles_venta (id, venta_id, variante_id, cantidad, precio_unitario, subtotal, descuento) VALUES (4, 5, 1, 2, '349.99', '699.98', '0.00');
INSERT INTO detalles_venta (id, venta_id, variante_id, cantidad, precio_unitario, subtotal, descuento) VALUES (5, 6, 13, 2, '150.00', '300.00', '0.00');
INSERT INTO detalles_venta (id, venta_id, variante_id, cantidad, precio_unitario, subtotal, descuento) VALUES (6, 7, 1, 2, '349.99', '699.98', '0.00');
INSERT INTO detalles_venta (id, venta_id, variante_id, cantidad, precio_unitario, subtotal, descuento) VALUES (7, 8, 1, 2, '349.99', '699.98', '0.00');
INSERT INTO detalles_venta (id, venta_id, variante_id, cantidad, precio_unitario, subtotal, descuento) VALUES (10, 11, 13, 1, '109.50', '109.50', '40.50');
INSERT INTO detalles_venta (id, venta_id, variante_id, cantidad, precio_unitario, subtotal, descuento) VALUES (11, 12, 1, 1, '250.00', '250.00', '0.00');
INSERT INTO detalles_venta (id, venta_id, variante_id, cantidad, precio_unitario, subtotal, descuento) VALUES (12, 13, 13, 3, '109.50', '328.50', '121.50');
INSERT INTO detalles_venta (id, venta_id, variante_id, cantidad, precio_unitario, subtotal, descuento) VALUES (13, 14, 13, 2, '150.00', '300.00', '81.00');

-- ----------------------------------------------------------------------------
-- Tabla: facturas
-- ----------------------------------------------------------------------------
CREATE TABLE facturas (
    id INTEGER NOT NULL DEFAULT nextval('facturas_id_seq'::regclass),
    venta_id INTEGER NOT NULL,
    nro_factura VARCHAR(50) NOT NULL,
    nro_autorizacion VARCHAR(100) NOT NULL,
    nit_emisor VARCHAR(30) NOT NULL DEFAULT '1029384756'::character varying,
    razon_social_emisor VARCHAR(150) NOT NULL DEFAULT 'FashionStore S.R.L.'::character varying,
    nit_cliente VARCHAR(30) NOT NULL,
    razon_social_cliente VARCHAR(150) NOT NULL,
    codigo_control VARCHAR(50) NULL,
    fecha_emision TIMESTAMP WITH TIME ZONE NULL DEFAULT CURRENT_TIMESTAMP,
    fec_limite_emision DATE NOT NULL,
    total_literal VARCHAR(255) NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'VALIDA'::character varying
,   PRIMARY KEY (id)
);

INSERT INTO facturas (id, venta_id, nro_factura, nro_autorizacion, nit_emisor, razon_social_emisor, nit_cliente, razon_social_cliente, codigo_control, fecha_emision, fec_limite_emision, total_literal, estado) VALUES (3, 4, 'FAC-POS-2026-4F5DAE', 'AUT-202609-97B2335F', '1029384025', 'FashionStore Bolivia S.R.L.', '0', 'Sin Nombre', '1C-50-B7', '2026-09-14T14:38:57.142182-04:00', '2027-03-13', '600.00 BOLIVIANOS', 'VALIDA');
INSERT INTO facturas (id, venta_id, nro_factura, nro_autorizacion, nit_emisor, razon_social_emisor, nit_cliente, razon_social_cliente, codigo_control, fecha_emision, fec_limite_emision, total_literal, estado) VALUES (4, 5, 'FAC-ECOM-2026-2CB5E0', 'AUT-202609-E7C8C9EB', '1029384025', 'FashionStore Bolivia S.R.L.', '1234567019', 'Corporación Digital S.A.', 'FE-E3-E1', '2026-09-14T14:49:49.799720-04:00', '2027-03-13', '699.98 BOLIVIANOS', 'VALIDA');
INSERT INTO facturas (id, venta_id, nro_factura, nro_autorizacion, nit_emisor, razon_social_emisor, nit_cliente, razon_social_cliente, codigo_control, fecha_emision, fec_limite_emision, total_literal, estado) VALUES (5, 6, 'FAC-ECOM-2026-E7CA26', 'AUT-202609-2AD4F651', '1029384025', 'FashionStore Bolivia S.R.L.', '0', 'Sin Nombre', 'FD-DE-B5', '2026-09-14T15:09:32.163324-04:00', '2027-03-13', '300.00 BOLIVIANOS', 'VALIDA');
INSERT INTO facturas (id, venta_id, nro_factura, nro_autorizacion, nit_emisor, razon_social_emisor, nit_cliente, razon_social_cliente, codigo_control, fecha_emision, fec_limite_emision, total_literal, estado) VALUES (6, 7, 'FAC-ECOM-2026-AF8D35', 'AUT-202609-B49B8346', '1029384025', 'FashionStore Bolivia S.R.L.', '1234567019', 'Corporación Digital S.A.', '30-B4-BB', '2026-09-14T15:13:43.057955-04:00', '2027-03-13', '699.98 BOLIVIANOS', 'VALIDA');
INSERT INTO facturas (id, venta_id, nro_factura, nro_autorizacion, nit_emisor, razon_social_emisor, nit_cliente, razon_social_cliente, codigo_control, fecha_emision, fec_limite_emision, total_literal, estado) VALUES (7, 8, 'FAC-ECOM-2026-834C10', 'AUT-202609-2920E36D', '1029384025', 'FashionStore Bolivia S.R.L.', '1234567019', 'Corporación Digital S.A.', 'E7-8B-35', '2026-09-14T13:12:10.643702-04:00', '2027-03-13', '699.98 BOLIVIANOS', 'VALIDA');
INSERT INTO facturas (id, venta_id, nro_factura, nro_autorizacion, nit_emisor, razon_social_emisor, nit_cliente, razon_social_cliente, codigo_control, fecha_emision, fec_limite_emision, total_literal, estado) VALUES (10, 11, 'FAC-ECOM-2026-163D77', 'AUT-202609-44D0119A', '1029384025', 'FashionStore Bolivia S.R.L.', '0', 'Sin Nombre', '25-F6-B3', '2026-09-14T13:54:57.590954-04:00', '2027-03-13', '109.50 BOLIVIANOS', 'VALIDA');
INSERT INTO facturas (id, venta_id, nro_factura, nro_autorizacion, nit_emisor, razon_social_emisor, nit_cliente, razon_social_cliente, codigo_control, fecha_emision, fec_limite_emision, total_literal, estado) VALUES (11, 12, 'FAC-ECOM-2026-E567B9', 'AUT-202609-5E22D47B', '1029384025', 'FashionStore Bolivia S.R.L.', '1234567', 'Cliente Test E-commerce', 'DA-E5-88', '2026-09-14T14:45:31.127741-04:00', '2027-03-13', '250.00 BOLIVIANOS', 'VALIDA');
INSERT INTO facturas (id, venta_id, nro_factura, nro_autorizacion, nit_emisor, razon_social_emisor, nit_cliente, razon_social_cliente, codigo_control, fecha_emision, fec_limite_emision, total_literal, estado) VALUES (12, 13, 'FAC-POS-2026-26D9E1', 'AUT-202609-3FFDCA54', '1029384025', 'FashionStore Bolivia S.R.L.', '0', 'Sin Nombre', 'E5-88-2D', '2026-09-14T14:48:11.605957-04:00', '2027-03-13', '328.50 BOLIVIANOS', 'VALIDA');
INSERT INTO facturas (id, venta_id, nro_factura, nro_autorizacion, nit_emisor, razon_social_emisor, nit_cliente, razon_social_cliente, codigo_control, fecha_emision, fec_limite_emision, total_literal, estado) VALUES (13, 14, 'FAC-POS-2026-ABAD40', 'AUT-202609-0A9ED1E4', '1029384025', 'FashionStore Bolivia S.R.L.', '11223344', 'Cliente Prueba Stock', '38-AF-5A', '2026-09-14T15:00:22.272565-04:00', '2027-03-13', '300.00 BOLIVIANOS', 'VALIDA');

-- ----------------------------------------------------------------------------
-- Tabla: resenas
-- ----------------------------------------------------------------------------
CREATE TABLE resenas (
    id INTEGER NOT NULL DEFAULT nextval('resenas_id_seq'::regclass),
    ropa_id INTEGER NOT NULL,
    cliente_ci VARCHAR(20) NOT NULL,
    calificacion INTEGER NOT NULL,
    comentario TEXT NULL,
    fec_publicacion TIMESTAMP WITH TIME ZONE NULL DEFAULT CURRENT_TIMESTAMP
,   PRIMARY KEY (id)
);

INSERT INTO resenas (id, ropa_id, cliente_ci, calificacion, comentario, fec_publicacion) VALUES (1, 1, '2001', 5, 'Excelente calidad de tela denim, la talla M me quedó perfecta. Muy recomendado.', '2026-09-14T00:00:00-04:00');
INSERT INTO resenas (id, ropa_id, cliente_ci, calificacion, comentario, fec_publicacion) VALUES (2, 1, '2001', 5, 'Excelente calidad de tela denim, la talla M me quedó perfecta. Muy recomendado.', '2026-09-14T00:00:00-04:00');
INSERT INTO resenas (id, ropa_id, cliente_ci, calificacion, comentario, fec_publicacion) VALUES (3, 17, '2001', 5, 'PIXEL', '2026-09-15T00:00:00-04:00');
INSERT INTO resenas (id, ropa_id, cliente_ci, calificacion, comentario, fec_publicacion) VALUES (4, 17, '2001', 5, 'PRUEBASA', '2026-09-15T00:00:00-04:00');

-- ----------------------------------------------------------------------------
-- Tabla: recomendaciones_ia
-- ----------------------------------------------------------------------------
CREATE TABLE recomendaciones_ia (
    id INTEGER NOT NULL DEFAULT nextval('recomendaciones_ia_id_seq'::regclass),
    cliente_id VARCHAR(20) NOT NULL,
    ropa_principal_id INTEGER NULL,
    outfit_nombre VARCHAR(150) NOT NULL,
    prendas_sugeridas_ids TEXT NOT NULL,
    tipo_algoritmo VARCHAR(50) NOT NULL,
    score_afinidad NUMERIC(12,2) NOT NULL,
    aceptada BOOLEAN NOT NULL,
    fec_generacion TIMESTAMP WITH TIME ZONE NOT NULL
,   PRIMARY KEY (id)
);

INSERT INTO recomendaciones_ia (id, cliente_id, ropa_principal_id, outfit_nombre, prendas_sugeridas_ids, tipo_algoritmo, score_afinidad, aceptada, fec_generacion) VALUES (1, '2001', 1, 'Outfit Formal Vanguardia - Chaqueta Denim Vintage', '17,2,3', 'ESTILO_CRUZADO_HISTORIAL_CLIENTE', '96.50', TRUE, '2026-09-14T14:14:41.487613');
INSERT INTO recomendaciones_ia (id, cliente_id, ropa_principal_id, outfit_nombre, prendas_sugeridas_ids, tipo_algoritmo, score_afinidad, aceptada, fec_generacion) VALUES (2, '2001', 1, 'Outfit Formal Vanguardia - Chaqueta Denim Vintage', '17,2,3', 'ESTILO_CRUZADO_HISTORIAL_CLIENTE', '96.50', FALSE, '2026-09-14T14:14:41.508321');
INSERT INTO recomendaciones_ia (id, cliente_id, ropa_principal_id, outfit_nombre, prendas_sugeridas_ids, tipo_algoritmo, score_afinidad, aceptada, fec_generacion) VALUES (3, '2001', 1, 'Outfit Formal Vanguardia - Chaqueta Denim Vintage', '17,2,3', 'ESTILO_CRUZADO_HISTORIAL_CLIENTE', '96.50', TRUE, '2026-09-14T14:49:49.934452');
INSERT INTO recomendaciones_ia (id, cliente_id, ropa_principal_id, outfit_nombre, prendas_sugeridas_ids, tipo_algoritmo, score_afinidad, aceptada, fec_generacion) VALUES (4, '2001', 1, 'Outfit Formal Vanguardia - Chaqueta Denim Vintage', '17,2,3', 'ESTILO_CRUZADO_HISTORIAL_CLIENTE', '96.50', FALSE, '2026-09-14T14:49:50.004031');
INSERT INTO recomendaciones_ia (id, cliente_id, ropa_principal_id, outfit_nombre, prendas_sugeridas_ids, tipo_algoritmo, score_afinidad, aceptada, fec_generacion) VALUES (5, '2001', 1, 'Outfit Formal Vanguardia - Chaqueta Denim Vintage', '17,2,3', 'ESTILO_CRUZADO_HISTORIAL_CLIENTE', '96.50', TRUE, '2026-09-14T15:13:43.112906');
INSERT INTO recomendaciones_ia (id, cliente_id, ropa_principal_id, outfit_nombre, prendas_sugeridas_ids, tipo_algoritmo, score_afinidad, aceptada, fec_generacion) VALUES (6, '2001', 1, 'Outfit Formal Vanguardia - Chaqueta Denim Vintage', '17,2,3', 'ESTILO_CRUZADO_HISTORIAL_CLIENTE', '96.50', FALSE, '2026-09-14T15:13:43.136029');
INSERT INTO recomendaciones_ia (id, cliente_id, ropa_principal_id, outfit_nombre, prendas_sugeridas_ids, tipo_algoritmo, score_afinidad, aceptada, fec_generacion) VALUES (7, '2001', 1, 'Outfit Formal Vanguardia - Chaqueta Denim Vintage', '17,2,3', 'ESTILO_CRUZADO_HISTORIAL_CLIENTE', '96.50', TRUE, '2026-09-14T17:12:10.755395');
INSERT INTO recomendaciones_ia (id, cliente_id, ropa_principal_id, outfit_nombre, prendas_sugeridas_ids, tipo_algoritmo, score_afinidad, aceptada, fec_generacion) VALUES (8, '2001', 1, 'Outfit Formal Vanguardia - Chaqueta Denim Vintage', '17,2,3', 'ESTILO_CRUZADO_HISTORIAL_CLIENTE', '96.50', FALSE, '2026-09-14T17:12:10.837188');
INSERT INTO recomendaciones_ia (id, cliente_id, ropa_principal_id, outfit_nombre, prendas_sugeridas_ids, tipo_algoritmo, score_afinidad, aceptada, fec_generacion) VALUES (9, '2001', 1, 'Outfit Formal Vanguardia - Chaqueta Denim Vintage', '17,2,3', 'ESTILO_CRUZADO_HISTORIAL_CLIENTE', '96.50', FALSE, '2026-09-14T18:45:29.028931');
INSERT INTO recomendaciones_ia (id, cliente_id, ropa_principal_id, outfit_nombre, prendas_sugeridas_ids, tipo_algoritmo, score_afinidad, aceptada, fec_generacion) VALUES (10, '2001', 1, 'Outfit Casual Vanguardia - Chaqueta Denim Vintage', '17,2,3', 'ESTILO_CRUZADO_HISTORIAL_CLIENTE', '96.50', FALSE, '2026-09-15T17:00:10.731612');
INSERT INTO recomendaciones_ia (id, cliente_id, ropa_principal_id, outfit_nombre, prendas_sugeridas_ids, tipo_algoritmo, score_afinidad, aceptada, fec_generacion) VALUES (11, '2001', 1, 'Outfit Casual Vanguardia - Chaqueta Denim Vintage', '17,2,3', 'ESTILO_CRUZADO_HISTORIAL_CLIENTE', '96.50', FALSE, '2026-09-15T17:04:07.641498');
INSERT INTO recomendaciones_ia (id, cliente_id, ropa_principal_id, outfit_nombre, prendas_sugeridas_ids, tipo_algoritmo, score_afinidad, aceptada, fec_generacion) VALUES (12, '2001', 1, 'Outfit Casual Vanguardia - Chaqueta Denim Vintage', '17,2,3', 'ESTILO_CRUZADO_HISTORIAL_CLIENTE', '96.50', FALSE, '2026-09-15T18:59:18.674909');
INSERT INTO recomendaciones_ia (id, cliente_id, ropa_principal_id, outfit_nombre, prendas_sugeridas_ids, tipo_algoritmo, score_afinidad, aceptada, fec_generacion) VALUES (13, '2001', 1, 'Outfit Fiesta Vanguardia - Chaqueta Denim Vintage', '17,2,3', 'ESTILO_CRUZADO_HISTORIAL_CLIENTE', '96.50', FALSE, '2026-09-15T19:00:05.488307');
INSERT INTO recomendaciones_ia (id, cliente_id, ropa_principal_id, outfit_nombre, prendas_sugeridas_ids, tipo_algoritmo, score_afinidad, aceptada, fec_generacion) VALUES (14, '2001', 1, 'Outfit Formal Vanguardia - Chaqueta Denim Vintage', '17,2,3', 'ESTILO_CRUZADO_HISTORIAL_CLIENTE', '96.50', FALSE, '2026-09-15T19:00:06.425832');
INSERT INTO recomendaciones_ia (id, cliente_id, ropa_principal_id, outfit_nombre, prendas_sugeridas_ids, tipo_algoritmo, score_afinidad, aceptada, fec_generacion) VALUES (15, '2001', 1, 'Outfit Casual Vanguardia - Chaqueta Denim Vintage', '17,2,3', 'ESTILO_CRUZADO_HISTORIAL_CLIENTE', '96.50', FALSE, '2026-09-15T19:00:07.314495');
INSERT INTO recomendaciones_ia (id, cliente_id, ropa_principal_id, outfit_nombre, prendas_sugeridas_ids, tipo_algoritmo, score_afinidad, aceptada, fec_generacion) VALUES (16, '2001', 1, 'Outfit Casual Vanguardia - Chaqueta Denim Vintage', '17,2,3', 'ESTILO_CRUZADO_HISTORIAL_CLIENTE', '96.50', FALSE, '2026-09-15T19:13:43.800139');
INSERT INTO recomendaciones_ia (id, cliente_id, ropa_principal_id, outfit_nombre, prendas_sugeridas_ids, tipo_algoritmo, score_afinidad, aceptada, fec_generacion) VALUES (17, '2001', 1, 'Outfit Casual Vanguardia - Chaqueta Denim Vintage', '17,2,3', 'ESTILO_CRUZADO_HISTORIAL_CLIENTE', '96.50', FALSE, '2026-09-16T03:35:53.690502');

-- ----------------------------------------------------------------------------
-- Tabla: alertas_ia
-- ----------------------------------------------------------------------------
CREATE TABLE alertas_ia (
    id INTEGER NOT NULL DEFAULT nextval('alertas_ia_id_seq'::regclass),
    tipo VARCHAR(50) NOT NULL,
    variante_id INTEGER NOT NULL,
    stock_actual INTEGER NOT NULL,
    limite_minimo INTEGER NOT NULL,
    demanda_proyectada INTEGER NULL,
    dias_proyectados INTEGER NULL,
    deficit INTEGER NOT NULL,
    leida BOOLEAN NOT NULL,
    fecha_creacion TIMESTAMP WITH TIME ZONE NOT NULL
,   PRIMARY KEY (id)
);

-- ----------------------------------------------------------------------------
-- Tabla: bitacoras
-- ----------------------------------------------------------------------------
CREATE TABLE bitacoras (
    id BIGINT NOT NULL DEFAULT nextval('bitacoras_id_seq'::regclass),
    usuario_id INTEGER NULL,
    accion VARCHAR(100) NOT NULL,
    tabla_afectada VARCHAR(100) NULL,
    registro_id VARCHAR(50) NULL,
    ip_origen VARCHAR(45) NULL,
    detalles TEXT NULL,
    fecha_hora TIMESTAMP WITH TIME ZONE NULL DEFAULT CURRENT_TIMESTAMP
,   PRIMARY KEY (id)
);

INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (1, 1, 'UPDATE', 'roles', '2', '127.0.0.1', 'Rol actualizado: Cajero', '2026-09-13T09:19:01.090649-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (2, 1, 'UPDATE', 'roles', '2', '127.0.0.1', 'Rol actualizado: Cajero POS', '2026-09-13T09:19:21.856158-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (3, 1, 'UPDATE', 'roles', '2', '127.0.0.1', 'Rol actualizado: Cajero', '2026-09-13T09:20:23.628807-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (4, 1, 'UPDATE', 'usuarios', '5', '127.0.0.1', 'Usuario actualizado: YEISONN', '2026-09-13T09:20:41.081852-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (5, 1, 'UPDATE', 'usuarios', '5', '127.0.0.1', 'Usuario actualizado: YEISONN', '2026-09-13T09:20:57.200011-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (6, 1, 'UPDATE', 'usuarios', '5', '127.0.0.1', 'Usuario actualizado: YEISONN', '2026-09-13T09:21:33.633059-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (7, 1, 'UPDATE', 'roles', '2', '127.0.0.1', 'Rol actualizado: Cajero POS', '2026-09-13T09:21:44.654809-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (8, 1, 'INSERT', 'roles', '5', '127.0.0.1', 'Rol creado: Cajero 2', '2026-09-13T09:21:54.145342-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (9, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-13T10:29:48.007963-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (10, 1, 'LOGOUT', 'usuarios', '1', '127.0.0.1', 'Cierre de sesión: admin', '2026-09-13T10:42:49.577421-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (11, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-13T10:42:51.109476-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (12, 1, 'INSERT', 'sucursales', '12', '127.0.0.1', 'Sucursal creada: Indina (Santa Cruz)', '2026-09-13T11:58:43.603595-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (13, 1, 'UPDATE', 'sucursales', '12', '127.0.0.1', 'Sucursal actualizada: Indina (Santa Cruz)', '2026-09-13T11:59:31.107001-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (14, 1, 'INSERT', 'sucursales', '13', '127.0.0.1', 'Sucursal creada: INDINA (Santa Cruz)', '2026-09-13T13:56:06.293153-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (15, 1, 'UPDATE', 'sucursales', '13', '127.0.0.1', 'Sucursal actualizada: INDINA (La Paz)', '2026-09-13T13:56:24.818174-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (16, 1, 'LOGOUT', 'usuarios', '1', '127.0.0.1', 'Cierre de sesión: admin', '2026-09-13T13:58:27.709954-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (17, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-13T13:58:29.175553-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (18, 1, 'DELETE', 'sucursales', '13', '127.0.0.1', 'Sucursal eliminada: INDINA', '2026-09-13T14:08:28.612020-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (19, 1, 'INSERT', 'sucursales', '14', '127.0.0.1', 'Sucursal creada: Sucursal Test Borrado (Cochabamba)', '2026-09-13T14:11:21.884488-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (20, 1, 'DELETE', 'sucursales', '14', '127.0.0.1', 'Sucursal eliminada: Sucursal Test Borrado', '2026-09-13T14:11:23.966089-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (21, 1, 'INSERT', 'sucursales', '15', '127.0.0.1', 'Sucursal creada: INDAN (Santa Cruz)', '2026-09-13T14:12:51.340551-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (22, 1, 'DELETE', 'sucursales', '15', '127.0.0.1', 'Sucursal eliminada: INDAN', '2026-09-13T14:13:04.523692-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (23, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-13T15:30:13.446528-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (24, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-13T15:30:21.184164-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (25, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-13T17:28:49.300826-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (26, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-13T17:28:54.322466-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (27, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-13T17:29:00.781965-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (28, 1, 'LOGOUT', 'usuarios', '1', '127.0.0.1', 'Cierre de sesión: admin', '2026-09-13T19:53:06.997659-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (29, 5, 'LOGIN', 'usuarios', '5', '127.0.0.1', 'Inicio de sesión exitoso: YEISONN', '2026-09-13T19:53:14.746278-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (30, 5, 'LOGOUT', 'usuarios', '5', '127.0.0.1', 'Cierre de sesión: YEISONN', '2026-09-13T19:55:03.047880-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (31, 6, 'LOGIN', 'usuarios', '6', '127.0.0.1', 'Inicio de sesión exitoso: Yheison', '2026-09-13T19:56:35.674592-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (32, 6, 'LOGOUT', 'usuarios', '6', '127.0.0.1', 'Cierre de sesión: Yheison', '2026-09-13T19:57:15.580347-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (33, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-13T19:57:20.395883-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (34, 1, 'DELETE', 'roles', '5', '127.0.0.1', 'Rol eliminado: Cajero 2', '2026-09-13T19:57:42.793382-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (35, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-14T10:39:34.023559-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (36, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-14T10:41:10.380986-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (37, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-14T10:41:31.811450-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (38, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-14T10:48:21.308064-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (39, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-14T11:05:02.406075-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (40, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-14T13:51:47.579182-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (41, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-14T14:46:08.460346-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (42, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-14T14:46:48.012663-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (43, 1, 'LOGOUT', 'usuarios', '1', '127.0.0.1', 'Cierre de sesión: admin', '2026-09-15T12:51:31.594737-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (44, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-15T12:51:58.497572-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (45, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-16T18:28:38.021306-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (46, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-16T18:45:25.465492-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (47, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-16T19:07:33.943291-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (48, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-16T19:08:01.677187-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (49, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-16T23:25:13.970047-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (50, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-16T23:32:55.623761-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (51, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-16T23:39:36.504828-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (52, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-17T10:31:23.215070-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (53, 1, 'UPDATE', 'roles', '4', '127.0.0.1', 'Rol actualizado: Cliente Yeison', '2026-09-17T10:32:48.235462-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (54, 1, 'UPDATE', 'roles', '4', '127.0.0.1', 'Rol actualizado: Cliente', '2026-09-17T10:33:14.832224-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (55, 8, 'LOGIN', 'usuarios', '8', '127.0.0.1', 'Inicio de sesión exitoso: cliente_20e38c', '2026-09-17T10:34:12.748440-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (56, 1, 'LOGOUT', 'usuarios', '1', '127.0.0.1', 'Cierre de sesión: admin', '2026-09-17T10:48:30.462723-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (57, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-17T10:51:52.982689-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (58, 1, 'LOGOUT', 'usuarios', '1', '127.0.0.1', 'Cierre de sesión: admin', '2026-09-17T10:55:28.422428-04:00');
INSERT INTO bitacoras (id, usuario_id, accion, tabla_afectada, registro_id, ip_origen, detalles, fecha_hora) VALUES (59, 1, 'LOGIN', 'usuarios', '1', '127.0.0.1', 'Inicio de sesión exitoso: admin', '2026-09-17T10:55:44.679432-04:00');

-- ----------------------------------------------------------------------------
-- Tabla: configuraciones_fidelizacion
-- ----------------------------------------------------------------------------
CREATE TABLE configuraciones_fidelizacion (
    id INTEGER NOT NULL DEFAULT nextval('configuraciones_fidelizacion_id_seq'::regclass),
    monto_minimo_acumulado NUMERIC(12,2) NOT NULL,
    monto_descuento NUMERIC(12,2) NOT NULL,
    activo BOOLEAN NOT NULL,
    fecha_actualizacion TIMESTAMP WITH TIME ZONE NOT NULL
,   PRIMARY KEY (id)
);

INSERT INTO configuraciones_fidelizacion (id, monto_minimo_acumulado, monto_descuento, activo, fecha_actualizacion) VALUES (1, '150.00', '20.00', TRUE, '2026-09-17T04:19:53.468667');

-- ----------------------------------------------------------------------------
-- Tabla: suscripciones_push
-- ----------------------------------------------------------------------------
CREATE TABLE suscripciones_push (
    id INTEGER NOT NULL DEFAULT nextval('suscripciones_push_id_seq'::regclass),
    usuario_id INTEGER NULL,
    endpoint TEXT NOT NULL,
    p256dh TEXT NOT NULL,
    auth TEXT NOT NULL,
    user_agent VARCHAR(255) NULL,
    activa BOOLEAN NOT NULL,
    ultima_promocion_id INTEGER NULL,
    ultimo_envio TIMESTAMP WITH TIME ZONE NULL,
    ultimo_error TEXT NULL,
    fecha_creacion TIMESTAMP WITH TIME ZONE NOT NULL
,   PRIMARY KEY (id)
);

INSERT INTO suscripciones_push (id, usuario_id, endpoint, p256dh, auth, user_agent, activa, ultima_promocion_id, ultimo_envio, ultimo_error, fecha_creacion) VALUES (1, NULL, 'https://test.push.endpoint/123', 'test_p256dh_key', 'test_auth_key', 'testclient', TRUE, NULL, NULL, NULL, '2026-09-17T04:19:53.609922');

-- ----------------------------------------------------------------------------
-- REINICIO DE SECUENCIAS (AUTOINCREMENTO)
-- ----------------------------------------------------------------------------
SELECT setval('temporadas_id_seq', COALESCE((SELECT MAX(id) FROM temporadas), 1));
SELECT setval('roles_id_seq', COALESCE((SELECT MAX(id) FROM roles), 1));
SELECT setval('usuarios_id_seq', COALESCE((SELECT MAX(id) FROM usuarios), 1));
SELECT setval('bitacoras_id_seq', COALESCE((SELECT MAX(id) FROM bitacoras), 1));
SELECT setval('categorias_id_seq', COALESCE((SELECT MAX(id) FROM categorias), 1));
SELECT setval('proveedores_id_seq', COALESCE((SELECT MAX(id) FROM proveedores), 1));
SELECT setval('ropa_id_seq', COALESCE((SELECT MAX(id) FROM ropa), 1));
SELECT setval('tallas_id_seq', COALESCE((SELECT MAX(id) FROM tallas), 1));
SELECT setval('colores_id_seq', COALESCE((SELECT MAX(id) FROM colores), 1));
SELECT setval('variantes_prenda_id_seq', COALESCE((SELECT MAX(id) FROM variantes_prenda), 1));
SELECT setval('promociones_id_seq', COALESCE((SELECT MAX(id) FROM promociones), 1));
SELECT setval('promocion_ropa_id_seq', COALESCE((SELECT MAX(id) FROM promocion_ropa), 1));
SELECT setval('resenas_id_seq', COALESCE((SELECT MAX(id) FROM resenas), 1));
SELECT setval('sucursales_id_seq', COALESCE((SELECT MAX(id) FROM sucursales), 1));
SELECT setval('inventario_sucursal_id_seq', COALESCE((SELECT MAX(id) FROM inventario_sucursal), 1));
SELECT setval('traspasos_id_seq', COALESCE((SELECT MAX(id) FROM traspasos), 1));
SELECT setval('detalles_traspaso_id_seq', COALESCE((SELECT MAX(id) FROM detalles_traspaso), 1));
SELECT setval('carritos_compra_id_seq', COALESCE((SELECT MAX(id) FROM carritos_compra), 1));
SELECT setval('detalles_carrito_compra_id_seq', COALESCE((SELECT MAX(id) FROM detalles_carrito_compra), 1));
SELECT setval('reservas_id_seq', COALESCE((SELECT MAX(id) FROM reservas), 1));
SELECT setval('metodos_pago_id_seq', COALESCE((SELECT MAX(id) FROM metodos_pago), 1));
SELECT setval('detalles_reserva_id_seq', COALESCE((SELECT MAX(id) FROM detalles_reserva), 1));
SELECT setval('tipos_venta_id_seq', COALESCE((SELECT MAX(id) FROM tipos_venta), 1));
SELECT setval('ventas_id_seq', COALESCE((SELECT MAX(id) FROM ventas), 1));
SELECT setval('detalles_venta_id_seq', COALESCE((SELECT MAX(id) FROM detalles_venta), 1));
SELECT setval('facturas_id_seq', COALESCE((SELECT MAX(id) FROM facturas), 1));
SELECT setval('recomendaciones_ia_id_seq', COALESCE((SELECT MAX(id) FROM recomendaciones_ia), 1));
SELECT setval('permisos_id_seq', COALESCE((SELECT MAX(id) FROM permisos), 1));
SELECT setval('movimientos_inventario_id_seq', COALESCE((SELECT MAX(id) FROM movimientos_inventario), 1));
SELECT setval('alertas_ia_id_seq', COALESCE((SELECT MAX(id) FROM alertas_ia), 1));
SELECT setval('configuraciones_fidelizacion_id_seq', COALESCE((SELECT MAX(id) FROM configuraciones_fidelizacion), 1));
SELECT setval('suscripciones_push_id_seq', COALESCE((SELECT MAX(id) FROM suscripciones_push), 1));

-- FIN DEL SCRIPT