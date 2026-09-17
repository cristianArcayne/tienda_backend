"""
Modelo para la configuración de fidelización de clientes.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Numeric, Boolean, DateTime
from database import Base


class ConfiguracionFidelizacionModel(Base):
    """
    Configuración global de fidelización:
    Monto mínimo acumulado de compras para recibir beneficio,
    monto de descuento a otorgar, y estado activo.
    """
    __tablename__ = "configuraciones_fidelizacion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    monto_minimo_acumulado = Column(Numeric(10, 2), default=100.0, nullable=False)
    monto_descuento = Column(Numeric(10, 2), default=15.0, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
