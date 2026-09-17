from typing import List, Optional, Union
from datetime import date
from pydantic import BaseModel

class ClienteRegistroRequest(BaseModel):
    username: str
    password: str
    nombre: str
    apellido: str
    fecha_nacimiento: Optional[Union[date, str]] = None
    email: Optional[str] = None

class ClienteRegistroResponse(BaseModel):
    id: int
    username: str
    mensaje: str

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    access: str
    refresh: str
    usuario_id: int
    username: str
    nombre_completo: str
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    is_superuser: bool
    roles: List[str]
    permisos: List[str]
    
class RecuperarPasswordRequest(BaseModel):
    username_or_email: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None

class RecuperarPasswordResponse(BaseModel):
    success: bool
    mensaje: str

class EnviarCodigoRequest(BaseModel):
    username_or_email: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None

class VerificarCodigoRequest(BaseModel):
    username_or_email: Optional[str] = None
    username: Optional[str] = None
    codigo: str

class CambiarContrasenaRequest(BaseModel):
    username_or_email: Optional[str] = None
    username: Optional[str] = None
    codigo: str
    nueva_contrasena: Optional[str] = None
    nueva_password: Optional[str] = None
