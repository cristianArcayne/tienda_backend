"""
Módulo de SaaS Multitenant y Suscripciones para FashionStore.
Implementa el modelo exigido por la docente (MSc. Ing. Angélica Garzón Cuéllar)
para el Segundo Examen Parcial de Sistemas de Información 2 (S2-2026).
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship

from database import Base


class Empresa(Base):
    """
    Entidad EMPRESA (Tenant)
    Representa a cada organización o cadena comercial independiente suscrita al SaaS.
    Aislamiento lógico de datos en esquema compartido.
    """
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    razon_social = Column(String(150), nullable=False, unique=True, index=True)
    nit = Column(String(30), nullable=False, unique=True, index=True)
    slug = Column(String(80), nullable=False, unique=True, index=True)
    logo_url = Column(String(255), nullable=True)
    color_marca = Column(String(10), nullable=True, default="#1e293b")
    descripcion = Column(String(500), nullable=True)
    direccion = Column(String(200), nullable=True)
    ciudad = Column(String(60), nullable=True, default="Santa Cruz")
    telefono = Column(String(30), nullable=True)
    correo_contacto = Column(String(150), nullable=True)
    estado = Column(String(20), nullable=False, default="ACTIVA")  # ACTIVA, SUSPENDIDA, CANCELADA
    creada_en = Column(DateTime, default=datetime.utcnow, nullable=False)
    actualizada_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    suscripciones = relationship("SuscripcionEmpresa", back_populates="empresa", cascade="all, delete-orphan")
    usuarios = relationship("Usuario", back_populates="empresa")
    sucursales = relationship("Sucursal", back_populates="empresa")
    prendas = relationship("Ropa", back_populates="empresa")

    @property
    def suscripcion_activa(self):
        """Retorna la suscripción vigente actual de la empresa."""
        for s in self.suscripciones:
            if s.estado in ("ACTIVA", "activa", "TRIAL", "trial"):
                return s
        return self.suscripciones[0] if self.suscripciones else None


class PlanSuscripcion(Base):
    """
    Entidad PLAN_SUSCRIPCION
    Catálogo de planes que define las cuotas y funcionalidades permitidas:
    - BÁSICO: Hasta 2 sucursales, sin IA generativa.
    - PROFESIONAL: Hasta 10 sucursales, con IA generativa y analítica.
    """
    __tablename__ = "planes_suscripcion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(30), nullable=False, unique=True, index=True)  # BASICO, PROFESIONAL
    nombre = Column(String(80), nullable=False)
    descripcion = Column(String(255), nullable=True)
    precio_mensual = Column(Float, nullable=False, default=0.0)
    precio_anual = Column(Float, nullable=False, default=0.0)
    duracion_dias = Column(Integer, nullable=False, default=30)
    limite_sucursales = Column(Integer, nullable=False, default=2)
    limite_usuarios = Column(Integer, nullable=False, default=5)
    soporta_ar = Column(Boolean, nullable=False, default=True)
    soporta_ia = Column(Boolean, nullable=False, default=False)
    soporta_offline = Column(Boolean, nullable=False, default=True)
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)

    suscripciones = relationship("SuscripcionEmpresa", back_populates="plan")


class SuscripcionEmpresa(Base):
    """
    Entidad SUSCRIPCION_EMPRESA
    Vínculo entre la Empresa (Tenant) y su Plan contratado.
    """
    __tablename__ = "suscripciones_empresa"

    id = Column(Integer, primary_key=True, autoincrement=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("planes_suscripcion.id", ondelete="RESTRICT"), nullable=False, index=True)
    estado = Column(String(20), nullable=False, default="ACTIVA")  # ACTIVA, VENCIDA, SUSPENDIDA, CANCELADA
    ciclo = Column(String(20), nullable=False, default="mensual")  # mensual, anual
    fecha_inicio = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_fin = Column(DateTime, nullable=True)
    auto_renovar = Column(Boolean, nullable=False, default=True)
    ultima_renovacion = Column(DateTime, default=datetime.utcnow, nullable=True)
    cancelada_en = Column(DateTime, nullable=True)
    cancelada_por = Column(String(100), nullable=True)
    creada_en = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    empresa = relationship("Empresa", back_populates="suscripciones")
    plan = relationship("PlanSuscripcion", back_populates="suscripciones")
    historial_cambios = relationship("HistorialCambioPlan", back_populates="suscripcion", cascade="all, delete-orphan")


class HistorialCambioPlan(Base):
    """
    Entidad HISTORIAL_CAMBIO_PLAN
    Auditoría inmutable de upgrades y downgrades de suscripciones.
    """
    __tablename__ = "historial_cambios_plan"

    id = Column(Integer, primary_key=True, autoincrement=True)
    suscripcion_id = Column(Integer, ForeignKey("suscripciones_empresa.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_anterior_id = Column(Integer, ForeignKey("planes_suscripcion.id", ondelete="SET NULL"), nullable=True)
    plan_nuevo_id = Column(Integer, ForeignKey("planes_suscripcion.id", ondelete="RESTRICT"), nullable=False)
    cambiado_en = Column(DateTime, default=datetime.utcnow, nullable=False)
    motivo = Column(String(255), nullable=True)

    suscripcion = relationship("SuscripcionEmpresa", back_populates="historial_cambios")
    plan_anterior = relationship("PlanSuscripcion", foreign_keys=[plan_anterior_id])
    plan_nuevo = relationship("PlanSuscripcion", foreign_keys=[plan_nuevo_id])
