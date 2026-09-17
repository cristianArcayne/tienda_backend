from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base


class Permiso(Base):
    __tablename__ = 'permisos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(200), nullable=False)
    codename = Column(String(150), nullable=False, unique=True, index=True)
    app = Column(String(50), nullable=False)
    modelo = Column(String(50), nullable=False)
    roles_asignados = relationship('RolPermiso', back_populates='permiso', cascade='all, delete-orphan')


class RolPermiso(Base):
    __tablename__ = 'rol_permisos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    rol_id = Column(Integer, ForeignKey('roles.id', ondelete='CASCADE'), nullable=False)
    permiso_id = Column(Integer, ForeignKey('permisos.id', ondelete='CASCADE'), nullable=False)
    __table_args__ = (
        UniqueConstraint('rol_id', 'permiso_id', name='uq_rol_permiso'),
    )
    rol = relationship('Rol', back_populates='permisos_asignados')
    permiso = relationship('Permiso', back_populates='roles_asignados')
