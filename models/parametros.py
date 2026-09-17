from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Talla(Base):
    """
    Entidad Talla (CU05: Gestionar parámetros de moda)
    Almacena los valores de tallas textiles o de calzado (ej. XS, S, M, L, 38, 40).
    """
    __tablename__ = "tallas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    medida = Column(String(20), unique=True, nullable=False, index=True)
    tipo = Column(String(30), nullable=False, default="Textil")  # 'Textil', 'Calzado', 'Accesorio'
    guia_medida = Column(String(150), nullable=True)

    # Relación de integridad: Una talla puede estar vinculada a múltiples variantes de prendas
    variantes = relationship(
        "VariantePrenda",
        back_populates="talla",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self):
        return f"<Talla id={self.id} medida='{self.medida}' tipo='{self.tipo}'>"


class VariantePrenda(Base):
    """
    Entidad VariantePrenda (Catálogo e Inventario FashionStore)
    Representa una SKU específica que combina Prenda + Talla + Color.
    Permite validar dependencias relacionales al intentar borrar una Talla
    y mapear disponibilidad por sucursal en tiempo real (CU11, CU12, CU13).
    """
    __tablename__ = "variantes_prenda"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sku = Column(String(60), unique=True, nullable=False, index=True)
    nombre_prenda = Column(String(120), nullable=False)
    precio = Column(Numeric(10, 2), nullable=False, default=0.0)

    # Llave foránea que referencia al Producto base del catálogo (CU07 / CU11)
    producto_id = Column(
        Integer,
        ForeignKey("productos.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # Color asignado a la variante para el catálogo y vestidor AR
    color = Column(String(50), nullable=False, default="Estándar", index=True)

    # Llave foránea que referencia a la entidad Talla
    talla_id = Column(
        Integer,
        ForeignKey("tallas.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Relaciones
    producto = relationship("Producto", back_populates="variantes")
    talla = relationship("Talla", back_populates="variantes")

    # Relación con inventario físico por sucursal
    stocks = relationship("InventarioStock", back_populates="variante", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<VariantePrenda id={self.id} sku='{self.sku}' talla_id={self.talla_id} color='{self.color}'>"
