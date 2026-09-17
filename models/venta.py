"""
Módulo de Ventas, Facturación Fiscal, Métodos de Pago y Tipos de Venta.
Estructura correspondiente al Diagrama de Clases UML de FashionStore.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class MetodoPago(Base):
    """
    Entidad METODO_PAGO
    Atributos: ID (PK), Nombre
    Ejemplos: 'Efectivo', 'Tarjeta POS', 'QR Caja', 'Stripe', 'Libélula QR', 'PayPal'
    """
    __tablename__ = "metodos_pago"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), nullable=False, unique=True)

    # Relación 1 a N con VENTA
    ventas = relationship("Venta", back_populates="metodo_pago")


class TipoVenta(Base):
    """
    Entidad TIPO_VENTA
    Atributos: ID (PK), Nombre
    Ejemplos: 'Presencial POS', 'Digital E-commerce Web', 'Digital App Móvil'
    """
    __tablename__ = "tipos_venta"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), nullable=False, unique=True)

    # Relación 1 a N con VENTA
    ventas = relationship("Venta", back_populates="tipo_venta")


class Venta(Base):
    """
    Entidad VENTA
    Atributos: ID (PK), Fecha, Total, Codigo_Transaccion, Estado_Pago
    Llaves Foráneas: Empleado_CI (atiende), Cliente_CI (pertenece), Sucursal_ID (factura_en),
                     Metodo_Pago_ID (paga), Tipo_Venta_ID (tiene)
    """
    __tablename__ = "ventas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column("fec_venta", DateTime, nullable=False, default=datetime.utcnow)
    total = Column("monto_total", Numeric(10, 2), nullable=False)
    descuento_total = Column(Numeric(10, 2), default=0.0, nullable=True)
    monto_neto = Column(Numeric(10, 2), nullable=True)
    monto_recibido = Column(Numeric(10, 2), nullable=True)
    cambio_devuelto = Column(Numeric(10, 2), nullable=True)
    codigo_transaccion = Column("referencia_pago", String(100), nullable=True, index=True)
    estado_pago = Column("estado", String(30), nullable=False, default="COMPLETADA")  # 'COMPLETADA', 'PENDIENTE', 'ANULADA', 'FALLIDA'

    # Llaves Foráneas
    cliente_id = Column("cliente_ci", String(20), ForeignKey("clientes.ci", ondelete="SET NULL"), nullable=True)
    empleado_ci = Column(String(20), ForeignKey("empleados.ci", ondelete="SET NULL"), nullable=True)
    sucursal_id = Column(Integer, ForeignKey("sucursales.id", ondelete="RESTRICT"), nullable=False)
    metodo_pago_id = Column(Integer, ForeignKey("metodos_pago.id", ondelete="RESTRICT"), nullable=False)
    tipo_venta_id = Column(Integer, ForeignKey("tipos_venta.id", ondelete="RESTRICT"), nullable=False)

    # Relaciones
    empleado = relationship("Empleado", back_populates="ventas_atendidas")
    cliente = relationship("Cliente", back_populates="ventas")
    sucursal = relationship("Sucursal", back_populates="ventas")
    metodo_pago = relationship("MetodoPago", back_populates="ventas")
    tipo_venta = relationship("TipoVenta", back_populates="ventas")

    detalles = relationship("DetalleVenta", back_populates="venta", cascade="all, delete-orphan")
    factura = relationship("Factura", back_populates="venta", uselist=False, cascade="all, delete-orphan")

    @property
    def empleado_id(self):
        return self.empleado_ci

    @property
    def cliente_ci(self):
        return self.cliente_id


class DetalleVenta(Base):
    """
    Entidad DETALLE_VENTA
    Atributos: ID (PK), Cantidad, Precio_Unitario, SubTotal, Descuento
    Llaves Foráneas: Venta_ID, Variante_ID
    """
    __tablename__ = "detalles_venta"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cantidad = Column(Integer, nullable=False, default=1)
    precio_unitario = Column(Numeric(10, 2), nullable=False, default=0.0)
    subtotal = Column(Numeric(10, 2), nullable=False)
    descuento = Column(Numeric(10, 2), default=0.0, nullable=True)

    venta_id = Column(Integer, ForeignKey("ventas.id", ondelete="CASCADE"), nullable=False)
    variante_id = Column(Integer, ForeignKey("variantes_prenda.id", ondelete="RESTRICT"), nullable=False)

    # Relaciones
    venta = relationship("Venta", back_populates="detalles")
    variante = relationship("VariantePrenda", back_populates="detalles_venta")


class Factura(Base):
    """
    Entidad FACTURA (Comprobante Fiscal)
    Atributos: ID (PK), Nro_Factura, Nro_Autorizacion, NIT_Cliente, Razon_Social, Fecha_Emision, etc.
    Llave Foránea: Venta_ID (Relación 1 a 1 con VENTA)
    """
    __tablename__ = "facturas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nro_factura = Column(String(50), nullable=False, unique=True, index=True)
    nro_autorizacion = Column(String(100), nullable=True)
    nit_emisor = Column(String(50), nullable=True, default="1029384025")
    razon_social_emisor = Column(String(150), nullable=True, default="FashionStore Bolivia S.R.L.")
    nit_cliente = Column(String(30), nullable=False, default="0")
    razon_social = Column("razon_social_cliente", String(120), nullable=False, default="Sin Nombre")
    codigo_control = Column(String(50), nullable=True)
    fecha_emision = Column(DateTime, nullable=False, default=datetime.utcnow)
    fec_limite_emision = Column(DateTime, nullable=True)
    total_literal = Column(String(255), nullable=True)
    estado = Column(String(30), nullable=False, default="VALIDA")

    venta_id = Column(Integer, ForeignKey("ventas.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Relación 1 a 1 con VENTA
    venta = relationship("Venta", back_populates="factura")
