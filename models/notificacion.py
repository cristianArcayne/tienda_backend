"""
Modelo para suscripciones push y notificaciones.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from database import Base


class SuscripcionPushModel(Base):
    """
    Suscripción de navegador para Notificaciones Push Web.
    """
    __tablename__ = "suscripciones_push"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, nullable=True)
    endpoint = Column(Text, unique=True, nullable=False)
    p256dh = Column(Text, nullable=False)
    auth = Column(Text, nullable=False)
    user_agent = Column(String(255), nullable=True)
    activa = Column(Boolean, default=True, nullable=False)
    ultima_promocion_id = Column(Integer, nullable=True)
    ultimo_envio = Column(DateTime, nullable=True)
    ultimo_error = Column(Text, nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)
