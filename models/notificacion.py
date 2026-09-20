"""
Modelo para suscripciones push y notificaciones in-app/push.
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


class NotificacionModel(Base):
    """
    Historial centralizado de notificaciones (promociones, compras, reservas, alertas).
    Consultable por la app móvil y el frontend web.
    """
    __tablename__ = "notificaciones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(200), nullable=False)
    mensaje = Column(Text, nullable=False)
    tipo = Column(String(50), default="PROMOCION")  # PROMOCION, COMPRA, RESERVA, BROADCAST, SISTEMA
    leida = Column(Boolean, default=False, nullable=False)
    usuario_id = Column(Integer, nullable=True)
    datos_adicionales = Column(Text, nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)
