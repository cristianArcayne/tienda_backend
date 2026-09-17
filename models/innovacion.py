"""
Módulo de Modelos para Innovación Tecnológica (IA, AR, Recomendaciones).
Alineado a CU16 (Vestidor Virtual AR) y CU17 (Recomendador Inteligente IA).
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class RecomendacionIA(Base):
    """
    Entidad RECOMENDACION_IA
    Almacena las sugerencias de venta cruzada y outfits generados para un cliente.
    """
    __tablename__ = "recomendaciones_ia"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(String(20), ForeignKey("clientes.ci", ondelete="CASCADE"), nullable=False)
    ropa_principal_id = Column(Integer, ForeignKey("ropa.id", ondelete="CASCADE"), nullable=True)
    
    outfit_nombre = Column(String(150), nullable=False)
    prendas_sugeridas_ids = Column(Text, nullable=False)  # Lista separada por comas ej: "1,2,5"
    tipo_algoritmo = Column(String(50), default="ESTILO_CRUZADO", nullable=False)  # 'ESTILO_CRUZADO', 'AFINIDAD_COLOR', 'TENDENCIA'
    score_afinidad = Column(Numeric(5, 2), default=95.00, nullable=False)  # % de compatibilidad
    aceptada = Column(Boolean, default=False, nullable=False)
    fec_generacion = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    cliente = relationship("Cliente")
    ropa_principal = relationship("Ropa")
