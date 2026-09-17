"""
Modelo para alertas generadas por Inteligencia Artificial y Reabastecimiento.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from database import Base


class AlertaIAModel(Base):
    """
    Alerta de inventario o demanda proyectada por IA.
    """
    __tablename__ = "alertas_ia"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo = Column(String(50), nullable=False, default="stock_bajo")  # 'stock_bajo', 'demanda_alta'
    variante_id = Column(Integer, ForeignKey("variantes_prenda.id", ondelete="CASCADE"), nullable=False)
    stock_actual = Column(Integer, nullable=False, default=0)
    limite_minimo = Column(Integer, nullable=False, default=5)
    demanda_proyectada = Column(Integer, nullable=True)
    dias_proyectados = Column(Integer, nullable=True, default=7)
    deficit = Column(Integer, nullable=False, default=0)
    leida = Column(Boolean, nullable=False, default=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)

    variante = relationship("VariantePrenda")
