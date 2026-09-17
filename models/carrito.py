"""
Módulo de Carrito de Compras y Detalle de Carrito.
Estructura correspondiente al Diagrama de Clases UML de FashionStore.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class CarritoCompra(Base):
    """
    Entidad CARRITO_COMPRA
    Atributos: ID (PK), Fecha_Creacion, Fecha_Actualizacion
    Llave Foránea: Cliente_ID (1 a 1 / 1 a 0..1)
    """
    __tablename__ = "carritos_compra"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha_creacion = Column("fec_creacion", DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    fecha_actualizacion = Column("fec_actualizacion", DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    cliente_id = Column("cliente_ci", String(20), ForeignKey("clientes.ci", ondelete="CASCADE"), unique=True, nullable=False)

    # Relaciones
    cliente = relationship("Cliente", back_populates="carrito")
    detalles = relationship("DetalleCarritoCompra", back_populates="carrito", cascade="all, delete-orphan")


class DetalleCarritoCompra(Base):
    """
    Entidad DETALLE_CARRITO_COMPRA
    Atributos: ID (PK), Cantidad, Fecha_Agregado
    Llaves Foráneas: Carrito_ID, Variante_ID
    """
    __tablename__ = "detalles_carrito_compra"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cantidad = Column(Integer, nullable=False, default=1)
    fecha_agregado = Column("fec_agregado", DateTime(timezone=True), default=datetime.utcnow, nullable=True)

    carrito_id = Column(Integer, ForeignKey("carritos_compra.id", ondelete="CASCADE"), nullable=False)
    variante_id = Column(Integer, ForeignKey("variantes_prenda.id", ondelete="RESTRICT"), nullable=False)

    # Relaciones
    carrito = relationship("CarritoCompra", back_populates="detalles")
    variante = relationship("VariantePrenda", back_populates="detalles_carrito")
