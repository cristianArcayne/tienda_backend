from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base

class Promocion(Base):
    """
    Entidad Promocion (CU08: Gestionar promociones y descuentos)
    Configura descuentos porcentuales y campañas promocionales estacionales
    para dinamizar la rotación del inventario (ej. Liquidación Invierno, Black Friday).
    """
    __tablename__ = "promociones"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(120), nullable=False, index=True)
    descuento_pct = Column(Numeric(5, 2), nullable=False)  # Ej. 25.00 para 25% de descuento
    fecha_inicio = Column(DateTime, nullable=False)
    fecha_fin = Column(DateTime, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relación con la tabla intermedia
    productos_asociados = relationship(
        "PromocionProducto",
        back_populates="promocion",
        cascade="all, delete-orphan"
    )

    def esta_vigente(self) -> bool:
        """Verifica si la campaña se encuentra temporalmente activa hoy"""
        ahora = datetime.utcnow()
        return self.activo and (self.fecha_inicio <= ahora <= self.fecha_fin)

    def __repr__(self):
        return f"<Promocion id={self.id} nombre='{self.nombre}' desc={self.descuento_pct}% activo={self.activo}>"


class PromocionProducto(Base):
    """
    Tabla intermedia PromocionProducto (CU08)
    Vincula dinámicamente las campañas promocionales con las prendas del catálogo
    que aplican para la rebaja de precio.
    """
    __tablename__ = "promocion_productos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    promocion_id = Column(
        Integer,
        ForeignKey("promociones.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    producto_id = Column(
        Integer,
        ForeignKey("productos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    asignado_en = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    promocion = relationship("Promocion", back_populates="productos_asociados")
    producto = relationship("Producto", back_populates="promociones_asociadas")

    # Restricción de unicidad para evitar duplicar el enlace de la misma prenda en una promoción
    __table_args__ = (
        UniqueConstraint('promocion_id', 'producto_id', name='uq_promocion_producto_vinculo'),
    )

    def __repr__(self):
        return f"<PromocionProducto promo_id={self.promocion_id} prod_id={self.producto_id}>"
