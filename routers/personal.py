from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import exists
import hashlib

from database import get_db
from models.seguridad_persona import Empleado, Rol, Usuario
from schemas.personal_auditoria import (
    EmpleadoCreate, EmpleadoUpdate, EmpleadoResponse,
    RolCreate, RolResponse
)
from routers.bitacora import registrar_bitacora

router = APIRouter(
    prefix="/api/v1",
    tags=["CU02. Gestionar personal y asignación de roles"]
)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ==========================================
# ROLES
# ==========================================
@router.get("/roles", response_model=List[RolResponse])
def listar_roles(db: Session = Depends(get_db)):
    return db.query(Rol).order_by(Rol.id.asc()).all()

@router.post("/roles", response_model=RolResponse, status_code=status.HTTP_201_CREATED)
def crear_rol(rol_in: RolCreate, db: Session = Depends(get_db)):
    if db.query(exists().where(Rol.nombre == rol_in.nombre)).scalar():
        raise HTTPException(status_code=400, detail="El rol ya existe")
    nuevo = Rol(nombre=rol_in.nombre, descripcion=rol_in.descripcion)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    registrar_bitacora(db, accion="INSERT", tabla="roles", registro_id=str(nuevo.id), detalles=f"Rol creado: {nuevo.nombre}")
    return nuevo

# ==========================================
# EMPLEADOS
# ==========================================
@router.get("/personal", response_model=List[EmpleadoResponse])
def listar_personal(db: Session = Depends(get_db)):
    empleados = db.query(Empleado).all()
    res = []
    for emp in empleados:
        usuario = db.query(Usuario).filter(Usuario.persona_ci == emp.ci).first()
        res.append(EmpleadoResponse(
            ci=emp.ci,
            nombre=emp.nombre,
            apellido_pat=emp.apellido_pat,
            apellido_mat=emp.apellido_mat,
            correo=emp.correo,
            telefono=emp.telefono,
            direccion=emp.direccion,
            cargo=emp.cargo,
            fec_contratacion=emp.fec_contratacion,
            activo=emp.activo,
            usuario_id=usuario.id if usuario else None,
            username=usuario.nombre_usuario if usuario else None,
            rol_id=usuario.rol_id if usuario else None,
            rol_nombre=usuario.rol.nombre if (usuario and usuario.rol) else None
        ))
    return res

@router.post("/personal", response_model=EmpleadoResponse, status_code=status.HTTP_201_CREATED)
def registrar_empleado(emp_in: EmpleadoCreate, db: Session = Depends(get_db)):
    if db.query(exists().where(Empleado.ci == emp_in.ci)).scalar():
        raise HTTPException(status_code=400, detail="El CI ya está registrado")
    if db.query(exists().where(Empleado.correo == emp_in.correo)).scalar():
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    if db.query(exists().where(Usuario.nombre_usuario == emp_in.username)).scalar():
        raise HTTPException(status_code=400, detail="El username ya está en uso")
    
    nuevo_emp = Empleado(
        ci=emp_in.ci,
        nombre=emp_in.nombre,
        apellido_pat=emp_in.apellido_pat,
        apellido_mat=emp_in.apellido_mat,
        correo=emp_in.correo,
        telefono=emp_in.telefono,
        direccion=emp_in.direccion,
        cargo=emp_in.cargo,
        fec_contratacion=emp_in.fec_contratacion or date.today()
    )
    db.add(nuevo_emp)
    
    nuevo_usu = Usuario(
        nombre_usuario=emp_in.username,
        contrasena=hash_password(emp_in.password),
        persona_ci=emp_in.ci,
        rol_id=emp_in.rol_id
    )
    db.add(nuevo_usu)
    db.commit()
    db.refresh(nuevo_emp)
    db.refresh(nuevo_usu)
    
    registrar_bitacora(db, accion="INSERT", tabla="empleados", registro_id=emp_in.ci, detalles=f"Empleado creado: {emp_in.nombre}")
    
    return EmpleadoResponse(
        **nuevo_emp.__dict__,
        usuario_id=nuevo_usu.id,
        username=nuevo_usu.nombre_usuario,
        rol_id=nuevo_usu.rol_id
    )

@router.put("/personal/{ci}", response_model=EmpleadoResponse)
def actualizar_empleado(ci: str, emp_in: EmpleadoUpdate, db: Session = Depends(get_db)):
    emp = db.query(Empleado).filter(Empleado.ci == ci).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    if emp_in.nombre is not None: emp.nombre = emp_in.nombre
    if emp_in.apellido_pat is not None: emp.apellido_pat = emp_in.apellido_pat
    if emp_in.apellido_mat is not None: emp.apellido_mat = emp_in.apellido_mat
    if emp_in.telefono is not None: emp.telefono = emp_in.telefono
    if emp_in.direccion is not None: emp.direccion = emp_in.direccion
    if emp_in.cargo is not None: emp.cargo = emp_in.cargo
    if emp_in.activo is not None: emp.activo = emp_in.activo
    
    usuario = db.query(Usuario).filter(Usuario.persona_ci == emp.ci).first()
    if emp_in.rol_id is not None and usuario:
        usuario.rol_id = emp_in.rol_id
        
    db.commit()
    db.refresh(emp)
    if usuario: db.refresh(usuario)
    
    registrar_bitacora(db, accion="UPDATE", tabla="empleados", registro_id=ci, detalles=f"Empleado actualizado")
    
    return EmpleadoResponse(
        **emp.__dict__,
        usuario_id=usuario.id if usuario else None,
        username=usuario.nombre_usuario if usuario else None,
        rol_id=usuario.rol_id if usuario else None,
        rol_nombre=usuario.rol.nombre if (usuario and usuario.rol) else None
    )
