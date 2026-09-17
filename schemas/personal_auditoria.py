from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel, EmailStr

# ==========================================
# CU02: PERSONAL Y ROLES
# ==========================================
class RolCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class RolResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    activo: bool
    class Config:
        from_attributes = True

class EmpleadoCreate(BaseModel):
    ci: str
    nombre: str
    apellido_pat: str
    apellido_mat: Optional[str] = ""
    correo: EmailStr
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    cargo: str
    fec_contratacion: Optional[date] = None
    username: str
    password: str
    rol_id: int

class EmpleadoUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido_pat: Optional[str] = None
    apellido_mat: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    cargo: Optional[str] = None
    activo: Optional[bool] = None
    rol_id: Optional[int] = None

class EmpleadoResponse(BaseModel):
    ci: str
    nombre: str
    apellido_pat: str
    apellido_mat: Optional[str]
    correo: str
    telefono: Optional[str]
    direccion: Optional[str]
    cargo: str
    fec_contratacion: date
    activo: bool
    usuario_id: Optional[int] = None
    username: Optional[str] = None
    rol_id: Optional[int] = None
    rol_nombre: Optional[str] = None
    class Config:
        from_attributes = True

# ==========================================
# CU03: BITÁCORA
# ==========================================
class BitacoraResponse(BaseModel):
    id: int
    accion: str
    tabla_afectada: Optional[str]
    registro_id: Optional[str]
    ip_origen: Optional[str]
    detalles: Optional[str]
    fecha_hora: datetime
    usuario_id: Optional[int]
    username: Optional[str] = None
    class Config:
        from_attributes = True
