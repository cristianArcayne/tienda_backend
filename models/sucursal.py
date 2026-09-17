"""
Módulo de Sucursales, Inventario Omnicanal y Traspasos entre Tiendas.
Estructura correspondiente al Diagrama de Clases UML de FashionStore.
"""
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship

from database import Base


class Sucursal(Base):
    """
    Entidad SUCURSAL
    Atributos: ID (PK), Nombre, Direccion, Ciudad, Telefono
    """
    __tablename__ = "sucursales"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False, unique=True, index=True)
    direccion = Column(String(200), nullable=False)
    ciudad = Column(String(50), nullable=False, default="Santa Cruz")
    telefono = Column(String(30), nullable=True)
    activo = Column(Boolean, default=True, nullable=False)

    # Relaciones
    inventarios = relationship("InventarioSucursal", back_populates="sucursal", cascade="all, delete-orphan")
    reservas = relationship("Reserva", back_populates="sucursal")
    ventas = relationship("Venta", back_populates="sucursal")
    traspasos_origen = relationship("Traspaso", foreign_keys="[Traspaso.sucursal_origen_id]", back_populates="sucursal_origen")
    traspasos_destino = relationship("Traspaso", foreign_keys="[Traspaso.sucursal_destino_id]", back_populates="sucursal_destino")
    empleados = relationship("Empleado", backref="sucursal")


class InventarioSucursal(Base):
    """
    Entidad INVENTARIO_SUCURSAL
    Atributos: ID (PK), Stock_Fisico, Stock_Reservado, Stock_Disponible, Stock_Minimo
    Llaves Foráneas: Sucursal_ID, Variante_ID
    Constraint: Unique(Sucursal_ID, Variante_ID)
    """
    __tablename__ = "inventario_sucursal"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_fisico = Column(Integer, nullable=False, default=0)
    stock_reservado = Column(Integer, nullable=False, default=0)
    stock_minimo = Column(Integer, nullable=False, default=5)
    fec_actualizacion = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    sucursal_id = Column(Integer, ForeignKey("sucursales.id", ondelete="CASCADE"), nullable=False, index=True)
    variante_id = Column(Integer, ForeignKey("variantes_prenda.id", ondelete="CASCADE"), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("sucursal_id", "variante_id", name="uq_inventario_sucursal_variante"),
    )

    # Relaciones
    sucursal = relationship("Sucursal", back_populates="inventarios")
    variante = relationship("VariantePrenda", back_populates="inventarios_sucursal")

    @property
    def stock_disponible(self) -> int:
        return max(0, (self.stock_fisico or 0) - (self.stock_reservado or 0))


class MovimientoInventario(Base):
    """
    Entidad MOVIMIENTO_INVENTARIO (CU09: Kardex / Control de Existencias)
    Registra entradas por mercadería/compra, ajustes por mermas, daños o conteo físico.
    """
    __tablename__ = "movimientos_inventario"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sucursal_id = Column(Integer, ForeignKey("sucursales.id", ondelete="CASCADE"), nullable=False, index=True)
    variante_id = Column(Integer, ForeignKey("variantes_prenda.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo_movimiento = Column(String(30), nullable=False)  # 'ENTRADA', 'MERMA', 'DANIO', 'CONTEO_FISICO', 'TRASPASO_SALIDA', 'TRASPASO_ENTRADA'
    cantidad = Column(Integer, nullable=False)
    stock_anterior = Column(Integer, nullable=False, default=0)
    stock_nuevo = Column(Integer, nullable=False, default=0)
    motivo = Column(String(255), nullable=True)
    fecha = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    usuario_ci = Column(String(50), nullable=True)

    # Relaciones
    sucursal = relationship("Sucursal")
    variante = relationship("VariantePrenda")


class Traspaso(Base):
    """
    Entidad TRASPASO
    Atributos: ID (PK), Fecha, Estado
    Llaves Foráneas: Empleado_ID, Sucursal_Origen_ID, Sucursal_Destino_ID
    """
    __tablename__ = "traspasos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column("fec_solicitud", DateTime(timezone=True), nullable=True, default=datetime.utcnow)
    estado = Column(String(30), nullable=False, default="PENDIENTE")  # 'PENDIENTE', 'EN_TRANSITO', 'RECIBIDO', 'CANCELADO'
    observacion = Column(String, nullable=True)
    fecha_recepcion = Column("fec_recepcion", DateTime(timezone=True), nullable=True)

    sucursal_origen_id = Column(Integer, ForeignKey("sucursales.id", ondelete="RESTRICT"), nullable=False)
    sucursal_destino_id = Column(Integer, ForeignKey("sucursales.id", ondelete="RESTRICT"), nullable=False)
    empleado_id = Column("solicitado_por_ci", String(20), ForeignKey("empleados.ci", ondelete="RESTRICT"), nullable=True)

    # Relaciones
    empleado = relationship("Empleado", back_populates="traspasos_registrados")
    sucursal_origen = relationship("Sucursal", foreign_keys=[sucursal_origen_id], back_populates="traspasos_origen")
    sucursal_destino = relationship("Sucursal", foreign_keys=[sucursal_destino_id], back_populates="traspasos_destino")
    detalles = relationship("DetalleTraspaso", back_populates="traspaso", cascade="all, delete-orphan")


class DetalleTraspaso(Base):
    """
    Entidad DETALLE_TRASPASO
    Atributos: ID (PK), Cantidad
    Llaves Foráneas: Traspaso_ID, Variante_ID
    """
    __tablename__ = "detalles_traspaso"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cantidad = Column(Integer, nullable=False, default=1)

    traspaso_id = Column(Integer, ForeignKey("traspasos.id", ondelete="CASCADE"), nullable=False)
    variante_id = Column(Integer, ForeignKey("variantes_prenda.id", ondelete="RESTRICT"), nullable=False)

    # Relaciones
    traspaso = relationship("Traspaso", back_populates="detalles")
    variante = relationship("VariantePrenda", back_populates="detalles_traspaso")
