"""
Modelo ORM para la Gestión de Devoluciones de Compras (Plazo de 24 horas).
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from database import Base


class Devolucion(Base):
    """
    Entidad DEVOLUCION
    Permite a los clientes solicitar la devolución de una compra dentro de las 24 horas.
    """
    __tablename__ = "devoluciones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    venta_id = Column(Integer, ForeignKey("ventas.id", ondelete="CASCADE"), nullable=False, unique=True)
    cliente_id = Column("cliente_ci", String(20), ForeignKey("clientes.ci", ondelete="SET NULL"), nullable=True)
    motivo = Column(Text, nullable=False)
    estado = Column(String(30), nullable=False, default="SOLICITADA")  # 'SOLICITADA', 'APROBADA', 'RECHAZADA'
    fecha_solicitud = Column(DateTime, nullable=False, default=datetime.utcnow)
    fecha_respuesta = Column(DateTime, nullable=True)
    respuesta_admin = Column(Text, nullable=True)
    monto_reembolso = Column(Numeric(10, 2), nullable=True)

    # Relaciones
    venta = relationship("Venta", backref="devolucion")
    cliente = relationship("Cliente", backref="devoluciones")
