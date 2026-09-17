"""
Módulo de Reservas Web-to-Store y Detalle de Reserva.
Estructura correspondiente al Diagrama de Clases UML de FashionStore.
"""
from datetime import date, datetime, timedelta
from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class Reserva(Base):
    """
    Entidad RESERVA (Web-to-Store)
    Atributos: ID (PK), Fecha, Fecha_Limite (48h), Hora_Estimada, Estado
    Llaves Foráneas: Cliente_ID, Sucursal_ID
    """
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column("fec_reserva", DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    fecha_limite = Column("fec_limite", DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow() + timedelta(hours=48))
    hora_estimada = Column("observacion", String(255), nullable=True)
    estado = Column(String(30), nullable=False, default="PENDIENTE")  # 'PENDIENTE', 'CONFIRMADA', 'COMPLETADA', 'CANCELADA', 'EXPIRADA'

    cliente_id = Column("cliente_ci", String(20), ForeignKey("clientes.ci", ondelete="CASCADE"), nullable=False)
    sucursal_id = Column(Integer, ForeignKey("sucursales.id", ondelete="RESTRICT"), nullable=False)

    # Relaciones
    cliente = relationship("Cliente", back_populates="reservas")
    sucursal = relationship("Sucursal", back_populates="reservas")
    detalles = relationship("DetalleReserva", back_populates="reserva", cascade="all, delete-orphan")


class DetalleReserva(Base):
    """
    Entidad DETALLE_RESERVA
    Atributos: ID (PK), Cantidad, Precio_Unitario
    Llaves Foráneas: Reserva_ID, Variante_ID
    """
    __tablename__ = "detalles_reserva"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cantidad = Column(Integer, nullable=False, default=1)
    precio_unitario = Column(Numeric(10, 2), nullable=False, default=0.0)

    reserva_id = Column(Integer, ForeignKey("reservas.id", ondelete="CASCADE"), nullable=False)
    variante_id = Column(Integer, ForeignKey("variantes_prenda.id", ondelete="RESTRICT"), nullable=False)

    # Relaciones
    reserva = relationship("Reserva", back_populates="detalles")
    variante = relationship("VariantePrenda", back_populates="detalles_reserva")
