"""
Módulo de Modelos de Seguridad, Personas, Roles y Auditoría.
Sincronizado con el esquema de base de datos PostgreSQL de FashionStore.
"""
from datetime import datetime, date, time
from sqlalchemy import Column, Integer, String, Date, Time, DateTime, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship

from database import Base

# Tabla de asociación M:N entre Rol y Permiso
rol_permiso = Table(
    "rol_permiso",
    Base.metadata,
    Column("rol_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permiso_id", Integer, ForeignKey("permisos.id", ondelete="CASCADE"), primary_key=True)
)


class Permiso(Base):
    """Permisos del sistema (codename + nombre descriptivo)."""
    __tablename__ = "permisos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codename = Column(String(100), nullable=False, unique=True, index=True)  # ej: 'inventario.view_producto'
    nombre = Column(String(150), nullable=False)  # ej: 'Ver Producto'

    # Relación M:N con Rol
    roles = relationship("Rol", secondary=rol_permiso, back_populates="permisos")

class Persona(Base):
    __tablename__ = "personas"

    ci = Column(String(20), primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    apellido_pat = Column(String(100), nullable=False)
    apellido_mat = Column(String(100), nullable=True)
    correo = Column(String(150), nullable=False, unique=True, index=True)
    telefono = Column(String(30), nullable=True)
    direccion = Column(String(255), nullable=True)
    tipo_persona = Column(String(20), default="PERSONA")  # 'EMPLEADO', 'CLIENTE'

    __mapper_args__ = {
        "polymorphic_identity": "PERSONA",
        "polymorphic_on": tipo_persona,
    }

    # Relación 1 a 0..1 con USUARIO
    usuario = relationship("Usuario", back_populates="persona", uselist=False, cascade="all, delete-orphan")


class Empleado(Persona):
    __tablename__ = "empleados"

    ci = Column(String(20), ForeignKey("personas.ci", ondelete="CASCADE"), primary_key=True)
    fec_contratacion = Column(Date, nullable=False, default=date.today)
    cargo = Column(String(100), nullable=False, default="Cajero POS")
    activo = Column(Boolean, nullable=False, default=True)
    sucursal_id = Column(Integer, ForeignKey("sucursales.id", ondelete="SET NULL"), nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "EMPLEADO",
    }

    # Relaciones de Empleado
    ventas_atendidas = relationship("Venta", back_populates="empleado")
    traspasos_registrados = relationship("Traspaso", back_populates="empleado")


class Cliente(Persona):
    __tablename__ = "clientes"

    ci = Column(String(20), ForeignKey("personas.ci", ondelete="CASCADE"), primary_key=True)
    preferencia_talla = Column(String(10), nullable=True)
    preferencia_estilo = Column(String(100), nullable=True)
    fecha_registro = Column(Date, nullable=False, default=date.today)

    __mapper_args__ = {
        "polymorphic_identity": "CLIENTE",
    }

    # Relaciones de Cliente
    carrito = relationship("CarritoCompra", back_populates="cliente", uselist=False, cascade="all, delete-orphan")
    reservas = relationship("Reserva", back_populates="cliente")
    ventas = relationship("Venta", back_populates="cliente")
    resenas = relationship("Resena", back_populates="cliente")


class Rol(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), nullable=False, unique=True)
    descripcion = Column(String(255), nullable=True)
    activo = Column(Boolean, nullable=False, default=True)

    # Relación 1 a N con USUARIO
    usuarios = relationship("Usuario", back_populates="rol")
    # Relación M:N con Permiso
    permisos = relationship("Permiso", secondary=rol_permiso, back_populates="roles")


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre_usuario = Column("username", String(50), nullable=False, unique=True, index=True)
    contrasena = Column("password_hash", String(255), nullable=False)
    estado = Column("activo", Boolean, nullable=False, default=True)

    persona_ci = Column(String(20), ForeignKey("personas.ci", ondelete="CASCADE"), unique=True, nullable=False)
    rol_id = Column(Integer, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)

    # Relaciones
    persona = relationship("Persona", back_populates="usuario")
    rol = relationship("Rol", back_populates="usuarios")
    bitacoras = relationship("Bitacora", back_populates="usuario", cascade="all, delete-orphan")


class Bitacora(Base):
    __tablename__ = "bitacoras"

    id = Column(Integer, primary_key=True, autoincrement=True)
    accion = Column(String(100), nullable=False)
    tabla_afectada = Column(String(100), nullable=True)
    registro_id = Column(String(50), nullable=True)
    ip_origen = Column(String(45), nullable=True)
    detalles = Column(String, nullable=True)
    fecha_hora = Column(DateTime, nullable=False)

    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)

    # Relación
    usuario = relationship("Usuario", back_populates="bitacoras")
