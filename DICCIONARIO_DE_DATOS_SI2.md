# 📚 DICCIONARIO DE DATOS - FASHIONSTORE
**Materia:** Sistemas de Información 2 (SI2)  
**Docente:** MSc. Ing. Angélica Garzón Cuéllar  
**Motor de Base de Datos:** PostgreSQL 14+ / 15+ / 16+  
**Total de Entidades:** 29 Tablas Relacionales (3ra Forma Normal)

---

## 📑 ÍNDICE DE MÓDULOS

1. [Módulo 1: Seguridad, Personas y Auditoría](#1-módulo-de-seguridad-personas-y-auditoría)
2. [Módulo 2: Catálogo, 3D AR y Promociones](#2-módulo-de-catálogo-3d-ar-y-promociones)
3. [Módulo 3: Sucursales, Inventario y Logística](#3-módulo-de-sucursales-inventario-y-logística)
4. [Módulo 4: Experiencia E-Commerce y Omnicanalidad](#4-módulo-de-experiencia-e-commerce-y-omnicanalidad)
5. [Módulo 5: Ventas y Facturación Fiscal](#5-módulo-de-ventas-y-facturación-fiscal)

---

## 1. MÓDULO DE SEGURIDAD, PERSONAS Y AUDITORÍA

### 1.1. Tabla: `personas` (Entidad Base Polimórfica)
| Campo | Tipo de Dato | Nulo | Clave | Restricciones / Descripción |
| :--- | :--- | :---: | :---: | :--- |
| `ci` | VARCHAR(20) | NO | **PK** | Cédula de Identidad única |
| `nombre` | VARCHAR(100) | NO | | Nombre(s) de la persona |
| `apellido_pat`| VARCHAR(100) | NO | | Primer apellido |
| `apellido_mat`| VARCHAR(100) | SÍ | | Segundo apellido |
| `correo` | VARCHAR(150) | NO | **UQ** | Correo electrónico único |
| `telefono` | VARCHAR(30) | SÍ | | Número de contacto |
| `direccion` | VARCHAR(255) | SÍ | | Dirección física domiciliaria |
| `tipo_persona`| VARCHAR(20) | NO | | `CHECK (tipo_persona IN ('EMPLEADO', 'CLIENTE', 'AMBOS'))` |
| `fec_creacion`| TIMESTAMP | NO | | Fecha y hora de registro inicial |

### 1.2. Tabla: `empleados` (Subtipo de Persona)
| Campo | Tipo de Dato | Nulo | Clave | Restricciones / Descripción |
| :--- | :--- | :---: | :---: | :--- |
| `ci` | VARCHAR(20) | NO | **PK, FK** | Hereda de `personas.ci` (CASCADE) |
| `fec_contratacion`| DATE | NO | | Fecha de inicio laboral |
| `cargo` | VARCHAR(100) | NO | | Cargo (Ej. Cajero POS, Gerente, Vendedor) |
| `activo` | BOOLEAN | NO | | Estado laboral activo/inactivo |

### 1.3. Tabla: `clientes` (Subtipo de Persona)
| Campo | Tipo de Dato | Nulo | Clave | Restricciones / Descripción |
| :--- | :--- | :---: | :---: | :--- |
| `ci` | VARCHAR(20) | NO | **PK, FK** | Hereda de `personas.ci` (CASCADE) |
| `preferencia_talla`| VARCHAR(10) | SÍ | | Talla habitual del cliente (XS, S, M, L, XL) |
| `preferencia_estilo`| VARCHAR(100) | SÍ | | Preferencia para IA de recomendación |
| `fecha_registro`| DATE | NO | | Fecha de alta como cliente |

### 1.4. Tabla: `roles`
| Campo | Tipo de Dato | Nulo | Clave | Restricciones / Descripción |
| :--- | :--- | :---: | :---: | :--- |
| `id` | SERIAL | NO | **PK** | Identificador autonumérico |
| `nombre` | VARCHAR(50) | NO | **UQ** | Nombre del rol (Administrador, Cajero, etc.) |
| `descripcion` | VARCHAR(255) | SÍ | | Alcance del rol en el sistema |
| `activo` | BOOLEAN | NO | | Habilitación del rol |

### 1.5. Tabla: `usuarios`
| Campo | Tipo de Dato | Nulo | Clave | Restricciones / Descripción |
| :--- | :--- | :---: | :---: | :--- |
| `id` | SERIAL | NO | **PK** | Identificador del usuario |
| `persona_ci` | VARCHAR(20) | NO | **FK, UQ**| Vinculado a `personas.ci` |
| `rol_id` | INT | NO | **FK** | Rol asignado (`roles.id`) |
| `username` | VARCHAR(50) | NO | **UQ** | Nombre de usuario para login |
| `password_hash`| VARCHAR(255)| NO | | Hash seguro de la contraseña |
| `activo` | BOOLEAN | NO | | Estado de la cuenta |
| `ultimo_login`| TIMESTAMP | SÍ | | Fecha y hora del último acceso |

### 1.6. Tabla: `bitacoras` (Pista de Auditoría)
| Campo | Tipo de Dato | Nulo | Clave | Restricciones / Descripción |
| :--- | :--- | :---: | :---: | :--- |
| `id` | BIGSERIAL | NO | **PK** | Identificador de evento |
| `usuario_id` | INT | SÍ | **FK** | Usuario causante (`usuarios.id`) |
| `accion` | VARCHAR(100) | NO | | INSERT, UPDATE, DELETE, LOGIN, LOGOUT |
| `tabla_afectada`| VARCHAR(100)| SÍ | | Nombre de la entidad modificada |
| `registro_id` | VARCHAR(50) | SÍ | | Clave del registro afectado |
| `ip_origen` | VARCHAR(45) | SÍ | | Dirección IP cliente |
| `detalles` | TEXT | SÍ | | Payload o JSON del cambio |
| `fecha_hora` | TIMESTAMP | NO | | Marca temporal del evento |

---

## 2. MÓDULO DE CATÁLOGO, 3D AR Y PROMOCIONES

### 2.1. Tabla: `categorias`
`id` (PK, SERIAL), `nombre` (UQ, VARCHAR), `descripcion` (TEXT), `activo` (BOOLEAN).

### 2.2. Tabla: `temporadas`
`id` (PK, SERIAL), `nombre` (UQ, VARCHAR), `fec_inicio` (DATE), `fec_fin` (DATE), `activo` (BOOLEAN).

### 2.3. Tabla: `proveedores`
`id` (PK, SERIAL), `razon_social` (VARCHAR), `nit` (UQ, VARCHAR), `contacto` (VARCHAR), `telefono` (VARCHAR), `correo` (VARCHAR), `direccion` (VARCHAR), `activo` (BOOLEAN).

### 2.4. Tabla: `ropa` (Con soporte AR 3D)
| Campo | Tipo de Dato | Nulo | Clave | Restricciones / Descripción |
| :--- | :--- | :---: | :---: | :--- |
| `id` | SERIAL | NO | **PK** | Identificador de la prenda base |
| `categoria_id`| INT | NO | **FK** | Vinculado a `categorias.id` |
| `temporada_id`| INT | SÍ | **FK** | Vinculado a `temporadas.id` |
| `proveedor_id`| INT | SÍ | **FK** | Vinculado a `proveedores.id` |
| `nombre` | VARCHAR(150) | NO | | Nombre comercial de la prenda |
| `descripcion` | TEXT | SÍ | | Ficha técnica y características |
| `precio_base` | NUMERIC(10,2)| NO | | `CHECK (precio_base >= 0)` |
| `costo_estandar`| NUMERIC(10,2)| NO | | Costo unitario para cálculo de margen |
| `genero` | VARCHAR(20) | NO | | `CHECK (genero IN ('Hombre','Mujer','Unisex','Niños'))` |
| `imagen_uri` | VARCHAR(500) | SÍ | | URL de fotografía de alta resolución |
| `modelo_3d_uri`| VARCHAR(500)| SÍ | | URL del modelo 3D (.glb) para probador AR |
| `activo` | BOOLEAN | NO | | Estado en catálogo |

### 2.5. Tabla: `tallas`
`id` (PK, SERIAL), `nombre` (UQ, VARCHAR), `tipo` (VARCHAR), `orden` (INT).

### 2.6. Tabla: `colores`
`id` (PK, SERIAL), `nombre` (UQ, VARCHAR), `codigo_hex` (VARCHAR).

### 2.7. Tabla: `variantes_prenda` (SKU Físico)
`id` (PK, SERIAL), `ropa_id` (FK), `talla_id` (FK), `color_id` (FK), `sku` (UQ, VARCHAR), `cod_barra` (UQ, VARCHAR), `precio_ajustado` (NUMERIC), `activo` (BOOLEAN).  
*Restricción de unicidad:* `UNIQUE (ropa_id, talla_id, color_id)`.

### 2.8. Tabla: `promociones`
`id` (PK, SERIAL), `nombre` (VARCHAR), `porcentaje_descuento` (NUMERIC, 1-100), `fec_inicio` (TIMESTAMP), `fec_fin` (TIMESTAMP), `activo` (BOOLEAN).

### 2.9. Tabla: `promocion_ropa` (Asociativa N:M)
`id` (PK, SERIAL), `promocion_id` (FK), `ropa_id` (FK), `fec_asignacion` (TIMESTAMP).

### 2.10. Tabla: `resenas`
`id` (PK, SERIAL), `ropa_id` (FK), `cliente_ci` (FK), `calificacion` (INT, 1-5), `comentario` (TEXT), `fec_publicacion` (TIMESTAMP).

---

## 3. MÓDULO DE SUCURSALES, INVENTARIO Y LOGÍSTICA

### 3.1. Tabla: `sucursales`
`id` (PK, SERIAL), `nombre` (UQ, VARCHAR), `direccion` (VARCHAR), `ciudad` (VARCHAR), `telefono` (VARCHAR), `latitud` (NUMERIC), `longitud` (NUMERIC), `es_almacen_central` (BOOLEAN), `activo` (BOOLEAN).

### 3.2. Tabla: `inventario_sucursal` (Cálculo Atómico de Stock)
| Campo | Tipo de Dato | Nulo | Clave | Restricciones / Descripción |
| :--- | :--- | :---: | :---: | :--- |
| `id` | SERIAL | NO | **PK** | Identificador de inventario |
| `sucursal_id` | INT | NO | **FK** | Tienda física (`sucursales.id`) |
| `variante_id` | INT | NO | **FK** | Variante física (`variantes_prenda.id`) |
| `stock_fisico` | INT | NO | | Existencias físicas en estante |
| `stock_reservado`| INT | NO | | Unidades apartadas por reservas/carrito |
| `stock_disponible`| INT | NO | **GEN** | `GENERATED ALWAYS AS (stock_fisico - stock_reservado) STORED` |
| `stock_minimo` | INT | NO | | Umbral de alerta para reabastecimiento |

### 3.3. Tabla: `traspasos`
`id` (PK, SERIAL), `sucursal_origen_id` (FK), `sucursal_destino_id` (FK), `solicitado_por_ci` (FK), `estado` (PENDIENTE/EN_TRANSITO/RECIBIDO/CANCELADO), `observacion` (TEXT), `fec_solicitud` (TIMESTAMP), `fec_recepcion` (TIMESTAMP).

### 3.4. Tabla: `detalles_traspaso`
`id` (PK, SERIAL), `traspaso_id` (FK), `variante_id` (FK), `cantidad` (INT > 0).

---

## 4. MÓDULO DE EXPERIENCIA E-COMMERCE Y OMNICANALIDAD

### 4.1. Tabla: `carritos_compra`
`id` (PK, SERIAL), `cliente_ci` (UQ, FK), `fec_creacion` (TIMESTAMP), `fec_actualizacion` (TIMESTAMP).

### 4.2. Tabla: `detalles_carrito_compra`
`id` (PK, SERIAL), `carrito_id` (FK), `variante_id` (FK), `cantidad` (INT > 0), `fec_agregado` (TIMESTAMP).

### 4.3. Tabla: `reservas` (Web-to-Store 48h)
| Campo | Tipo de Dato | Nulo | Clave | Restricciones / Descripción |
| :--- | :--- | :---: | :---: | :--- |
| `id` | SERIAL | NO | **PK** | Código de reserva |
| `cliente_ci` | VARCHAR(20) | NO | **FK** | Cliente titular |
| `sucursal_id` | INT | NO | **FK** | Tienda física asignada para retiro |
| `fec_reserva` | TIMESTAMP | NO | | Momento de la creación |
| `fec_limite` | TIMESTAMP | NO | | Plazo de 48 horas para retiro |
| `estado` | VARCHAR(30) | NO | | PENDIENTE, RETIRADA, EXPIRADA, CANCELADA |
| `observacion` | TEXT | SÍ | | Notas de retiro o motivo de cancelación |

### 4.4. Tabla: `detalles_reserva`
`id` (PK, SERIAL), `reserva_id` (FK), `variante_id` (FK), `cantidad` (INT > 0), `precio_unitario` (NUMERIC).

---

## 5. MÓDULO DE VENTAS Y FACTURACIÓN FISCAL

### 5.1. Tabla: `metodos_pago`
`id` (PK, SERIAL), `nombre` (UQ, VARCHAR), `tipo` (EFECTIVO, TARJETA_POS, QR_CAJA, PASARELA_DIGITAL), `activo` (BOOLEAN).

### 5.2. Tabla: `tipos_venta`
`id` (PK, SERIAL), `nombre` (UQ, VARCHAR: Presencial POS, Digital Web, Digital Móvil), `descripcion` (VARCHAR).

### 5.3. Tabla: `ventas` (Transacción Omnicanal)
| Campo | Tipo de Dato | Nulo | Clave | Restricciones / Descripción |
| :--- | :--- | :---: | :---: | :--- |
| `id` | SERIAL | NO | **PK** | Número de orden / venta |
| `cliente_ci` | VARCHAR(20) | SÍ | **FK** | Cliente comprador |
| `empleado_ci` | VARCHAR(20) | SÍ | **FK** | Cajero responsable (Venta física) |
| `sucursal_id` | INT | NO | **FK** | Tienda física de origen |
| `tipo_venta_id`| INT | NO | **FK** | Canal de venta |
| `metodo_pago_id`| INT | NO | **FK** | Método de liquidación |
| `monto_total` | NUMERIC(10,2)| NO | | Suma bruta de ítems |
| `descuento_total`| NUMERIC(10,2)| NO | | Descuento aplicado por promociones |
| `monto_neto` | NUMERIC(10,2)| NO | | Total a pagar |
| `monto_recibido`| NUMERIC(10,2)| SÍ | | Efectivo entregado en caja |
| `cambio_devuelto`| NUMERIC(10,2)| SÍ | | Vuelto entregado al cliente |
| `estado` | VARCHAR(30) | NO | | COMPLETADA, ANULADA, FALLIDA, PENDIENTE |
| `referencia_pago`| VARCHAR(150)| SÍ | | Token de Stripe / Libélula / Nro Voucher |
| `fec_venta` | TIMESTAMP | NO | | Fecha y hora de transacción |

### 5.4. Tabla: `detalles_venta`
`id` (PK, SERIAL), `venta_id` (FK), `variante_id` (FK), `cantidad` (INT > 0), `precio_unitario` (NUMERIC), `subtotal` (NUMERIC), `descuento` (NUMERIC).

### 5.5. Tabla: `facturas` (Comprobante Fiscal 1:1)
| Campo | Tipo de Dato | Nulo | Clave | Restricciones / Descripción |
| :--- | :--- | :---: | :---: | :--- |
| `id` | SERIAL | NO | **PK** | Identificador de factura |
| `venta_id` | INT | NO | **FK, UQ**| Relación estricta 1:1 con `ventas.id` |
| `nro_factura` | VARCHAR(50) | NO | **UQ** | Número correlativo fiscal |
| `nro_autorizacion`| VARCHAR(100)| NO | | Autorización del SIN |
| `nit_emisor` | VARCHAR(30) | NO | | NIT de FashionStore S.R.L. |
| `razon_social_emisor`| VARCHAR(150)| NO | | Razón social emisor |
| `nit_cliente` | VARCHAR(30) | NO | | NIT o CI del comprador |
| `razon_social_cliente`| VARCHAR(150)| NO | | Nombre / Razón Social del comprador |
| `codigo_control`| VARCHAR(50) | SÍ | | Código de control fiscal |
| `fecha_emision`| TIMESTAMP | NO | | Fecha y hora de emisión |
| `fec_limite_emision`| DATE | NO | | Fecha límite de dosificación |
| `total_literal`| VARCHAR(255)| NO | | Monto expresado en palabras |
| `estado` | VARCHAR(30) | NO | | VALIDA / ANULADA |
