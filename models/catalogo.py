"""
Módulo de Catálogo, Ropa, Parámetros de Moda, Promociones y Reseñas.
Estructura correspondiente al Diagrama de Clases UML de FashionStore.
"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Text, Numeric, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from database import Base


class Categoria(Base):
    """
    Entidad CATEGORIA
    Atributos: ID (PK), Nombre
    """
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False, unique=True, index=True)

    # Relación 1 a N con ROPA
    ropas = relationship("Ropa", back_populates="categoria")


class Temporada(Base):
    """
    Entidad TEMPORADA
    Atributos: ID (PK), Nombre
    """
    __tablename__ = "temporadas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), nullable=False, unique=True)

    # Relación 1 a N con ROPA
    ropas = relationship("Ropa", back_populates="temporada")


class Proveedor(Base):
    """
    Entidad PROVEEDOR
    Atributos: ID (PK), Razon_Social, Telefono, Contacto
    """
    __tablename__ = "proveedores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    razon_social = Column(String(150), nullable=False, unique=True)
    nit = Column(String(50), nullable=True, unique=True)
    correo = Column(String(150), nullable=True)
    direccion = Column(String(255), nullable=True)
    telefono = Column(String(30), nullable=True)
    contacto = Column(String(100), nullable=True)

    # Relación 1 a N con ROPA
    ropas = relationship("Ropa", back_populates="proveedor")


class Ropa(Base):
    """
    Entidad ROPA (Prenda Base del Catálogo)
    Atributos: ID (PK), Nombre, Descripcion, Precio, Imagen_URI, Modelo_3D_URI
    Llaves Foráneas: Categoria_ID, Temporada_ID, Proveedor_ID
    """
    __tablename__ = "ropa"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(120), nullable=False, index=True)
    descripcion = Column(Text, nullable=True)
    precio = Column(Numeric(10, 2), nullable=False)
    costo_estandar = Column(Numeric(10, 2), nullable=True, default=0.0)
    imagen_uri = Column(String(255), nullable=True)
    modelo_3d_uri = Column(String(255), nullable=True)  # Archivo .glb / .gltf para Realidad Aumentada
    activo = Column(Boolean, nullable=False, default=True)

    categoria_id = Column(Integer, ForeignKey("categorias.id", ondelete="RESTRICT"), nullable=True)
    temporada_id = Column(Integer, ForeignKey("temporadas.id", ondelete="SET NULL"), nullable=True)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id", ondelete="SET NULL"), nullable=True)

    # Relaciones
    categoria = relationship("Categoria", back_populates="ropas")
    temporada = relationship("Temporada", back_populates="ropas")
    proveedor = relationship("Proveedor", back_populates="ropas")
    variantes = relationship("VariantePrenda", back_populates="ropa", cascade="all, delete-orphan")
    promociones_asociadas = relationship("PromocionRopa", back_populates="ropa", cascade="all, delete-orphan")
    resenas = relationship("Resena", back_populates="ropa", cascade="all, delete-orphan")


class Talla(Base):
    """
    Entidad TALLA
    Atributos: ID (PK), Medida
    """
    __tablename__ = "tallas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    medida = Column(String(20), nullable=False, unique=True, index=True)  # Ej: 'XS', 'S', 'M', 'L', 'XL', '40'
    tipo = Column(String(30), nullable=False, default="Textil")
    guia_medida = Column(String(150), nullable=True)

    # Relación 1 a N con VARIANTE_PRENDA
    variantes = relationship("VariantePrenda", back_populates="talla")

    @property
    def nombre(self):
        return self.medida


class Color(Base):
    """
    Entidad COLOR
    Atributos: ID (PK), Nombre, Codigo_Hex
    """
    __tablename__ = "colores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), nullable=False, unique=True)
    codigo_hex = Column(String(10), nullable=True)  # Ej: '#0000FF', '#000000'

    # Relación 1 a N con VARIANTE_PRENDA
    variantes = relationship("VariantePrenda", back_populates="color")


class VariantePrenda(Base):
    """
    Entidad VARIANTE_PRENDA (SKU Físico por Talla y Color)
    Atributos: ID (PK), cod_Barra
    Llaves Foráneas: Ropa_ID, Talla_ID, Color_ID
    """
    __tablename__ = "variantes_prenda"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String(50), nullable=True)
    cod_barra = Column(String(60), nullable=False, unique=True, index=True)
    precio_ajustado = Column(Numeric(10, 2), nullable=True)
    activo = Column(Boolean, default=True)

    ropa_id = Column(Integer, ForeignKey("ropa.id", ondelete="CASCADE"), nullable=False)
    talla_id = Column(Integer, ForeignKey("tallas.id", ondelete="RESTRICT"), nullable=False)
    color_id = Column(Integer, ForeignKey("colores.id", ondelete="RESTRICT"), nullable=False)

    # Relaciones
    ropa = relationship("Ropa", back_populates="variantes")
    talla = relationship("Talla", back_populates="variantes")
    color = relationship("Color", back_populates="variantes")

    # Relaciones con Inventario, Carrito, Reserva, Venta, Traspaso
    inventarios_sucursal = relationship("InventarioSucursal", back_populates="variante", cascade="all, delete-orphan")
    detalles_carrito = relationship("DetalleCarritoCompra", back_populates="variante")
    detalles_reserva = relationship("DetalleReserva", back_populates="variante")
    detalles_venta = relationship("DetalleVenta", back_populates="variante")
    detalles_traspaso = relationship("DetalleTraspaso", back_populates="variante")


class Promocion(Base):
    """
    Entidad PROMOCION (CU08: Gestionar promociones y descuentos)
    Atributos: ID (PK), Nombre, Descripcion, Porcentaje_Descuento, Fecha_Inicio, Fecha_Fin, Activo
    """
    __tablename__ = "promociones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=True)
    porcentaje_descuento = Column(Numeric(5, 2), nullable=False)  # Ej: 15.00 (%)
    fecha_inicio = Column("fec_inicio", DateTime(timezone=True), nullable=False)
    fecha_fin = Column("fec_fin", DateTime(timezone=True), nullable=False)
    activo = Column(Boolean, default=True, nullable=False)

    # Relación N a M con ROPA mediante PROMOCION_ROPA
    ropas_asociadas = relationship("PromocionRopa", back_populates="promocion", cascade="all, delete-orphan")


class PromocionRopa(Base):
    """
    Entidad PROMOCION_ROPA (Tabla Intermedia)
    Atributos: ID (PK), Estado, Fec_Asignacion
    Llaves Foráneas: Promocion_ID, Ropa_ID
    """
    __tablename__ = "promocion_ropa"

    id = Column(Integer, primary_key=True, autoincrement=True)
    promocion_id = Column(Integer, ForeignKey("promociones.id", ondelete="CASCADE"), nullable=False)
    ropa_id = Column(Integer, ForeignKey("ropa.id", ondelete="CASCADE"), nullable=False)
    fec_asignacion = Column("fec_asignacion", DateTime(timezone=True), default=datetime.utcnow, nullable=True)
    estado = Column(String(20), default="ACTIVA", nullable=False)  # 'ACTIVA', 'INACTIVA'

    # Relaciones
    promocion = relationship("Promocion", back_populates="ropas_asociadas")
    ropa = relationship("Ropa", back_populates="promociones_asociadas")


class Resena(Base):
    """
    Entidad RESEÑA
    Atributos: ID (PK), Puntuacion_Estrellas, Comentario, Fecha
    Llaves Foráneas: Cliente_ID, Ropa_ID
    """
    __tablename__ = "resenas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    puntuacion_estrellas = Column("calificacion", Integer, nullable=False)  # 1 a 5 estrellas
    comentario = Column(Text, nullable=True)
    fecha = Column("fec_publicacion", Date, default=date.today, nullable=False)

    cliente_id = Column("cliente_ci", String(20), ForeignKey("clientes.ci", ondelete="CASCADE"), nullable=False)
    ropa_id = Column(Integer, ForeignKey("ropa.id", ondelete="CASCADE"), nullable=False)

    # Relaciones
    cliente = relationship("Cliente", back_populates="resenas")
    ropa = relationship("Ropa", back_populates="resenas")
