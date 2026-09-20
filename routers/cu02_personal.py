"""
CU02: Gestion de Personal (Usuarios) y Roles
Endpoints compatibles con el frontend Angular de FashionStore.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
import hashlib, uuid

from database import get_db
from models.seguridad_persona import Usuario, Persona, Cliente, Rol, Empleado, Permiso
from routers.bitacora import registrar_bitacora

router = APIRouter(tags=["CU02 - Usuarios y Roles"])

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def usuario_to_dict(u: Usuario) -> dict:
    persona = u.persona
    return {
        "id": u.id,
        "username": u.nombre_usuario,
        "email": persona.correo if persona else "",
        "nombre": persona.nombre if persona else "",
        "apellido": persona.apellido_pat if persona else "",
        "telefono": persona.telefono if persona else "",
        "is_superuser": u.rol.nombre.lower() in ["administrador", "admin"] if u.rol else False,
        "activo": u.estado,
        "grupos": [u.rol.nombre] if u.rol else [],
        "rol_id": u.rol_id,
    }

def rol_to_dict(r: Rol) -> dict:
    permisos = r.permisos if r.permisos else []
    return {
        "id": r.id,
        "name": r.nombre,
        "nombre": r.nombre,
        "descripcion": r.descripcion or "",
        "activo": r.activo,
        "permisos": [{"id": p.id, "nombre": p.nombre, "name": p.nombre, "codename": p.codename} for p in permisos],
        "permisos_ids": [p.id for p in permisos],
    }

def paginar(query, page: int, page_size: int):
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return total, items

# === USUARIOS ===

@router.get("/api/usuarios")
@router.get("/api/usuarios/")
@router.get("/api/v1/usuarios")
@router.get("/api/v1/usuarios/")
def listar_usuarios(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=5000), db: Session = Depends(get_db)):
    query = db.query(Usuario).order_by(Usuario.id)
    total, usuarios = paginar(query, page, page_size)
    base = "/api/v1/usuarios"
    return {
        "count": total,
        "next": f"{base}?page={page+1}&page_size={page_size}" if page * page_size < total else None,
        "previous": f"{base}?page={page-1}&page_size={page_size}" if page > 1 else None,
        "results": [usuario_to_dict(u) for u in usuarios]
    }

@router.get("/api/usuarios/{usuario_id}")
@router.get("/api/usuarios/{usuario_id}/")
@router.get("/api/v1/usuarios/{usuario_id}")
@router.get("/api/v1/usuarios/{usuario_id}/")
def obtener_usuario(usuario_id: int, db: Session = Depends(get_db)):
    u = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario_to_dict(u)

@router.post("/api/usuarios", status_code=201)
@router.post("/api/usuarios/", status_code=201)
@router.post("/api/v1/usuarios", status_code=201)
@router.post("/api/v1/usuarios/", status_code=201)
def crear_usuario(body: dict, request: Request, db: Session = Depends(get_db)):
    username = body.get("username", "").strip()
    password = body.get("password", "")
    email    = body.get("email", "").strip()
    grupo_id = body.get("grupo_id")
    nombre   = body.get("nombre", username).strip() or username
    apellido = body.get("apellido", "").strip()

    if not username:
        raise HTTPException(status_code=400, detail="El username es requerido")
    if not password:
        raise HTTPException(status_code=400, detail="La contrasena es requerida")
    if grupo_id is None:
        raise HTTPException(status_code=400, detail="El rol (grupo_id) es requerido")
    if db.query(Usuario).filter(Usuario.nombre_usuario == username).first():
        raise HTTPException(status_code=400, detail="El nombre de usuario ya esta en uso")

    rol = db.query(Rol).filter(Rol.id == grupo_id).first()
    if not rol:
        raise HTTPException(status_code=400, detail="El rol seleccionado no existe")

    correo_final = email if email else f"{username}@sin-correo.com"
    if db.query(Persona).filter(Persona.correo == correo_final).first():
        correo_final = f"{username}_{uuid.uuid4().hex[:6]}@sin-correo.com"

    fake_ci = str(uuid.uuid4().int)[:8]
    
    # Determinar si es Empleado o Cliente según el rol
    if rol.nombre.lower() == 'cliente':
        nueva_persona = Cliente(
            ci=fake_ci,
            nombre=nombre,
            apellido_pat=apellido if apellido else username,
            apellido_mat="",
            correo=correo_final,
            preferencia_talla="M"
        )
    else:
        # Es personal interno (Empleado)
        nueva_persona = Empleado(
            ci=fake_ci,
            nombre=nombre,
            apellido_pat=apellido if apellido else username,
            apellido_mat="",
            correo=correo_final,
            sucursal_id=body.get("sucursal_id"),
            cargo=rol.nombre
        )
        
    db.add(nueva_persona)
    db.commit()
    db.refresh(nueva_persona)

    nuevo_usuario = Usuario(
        nombre_usuario=username,
        contrasena=hash_password(password),
        persona_ci=nueva_persona.ci,
        rol_id=rol.id
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    
    registrar_bitacora(db, "INSERT", "usuarios", str(nuevo_usuario.id), f"Usuario creado: {username}", request=request)
    
    return usuario_to_dict(nuevo_usuario)

@router.put("/api/usuarios/{usuario_id}")
@router.put("/api/usuarios/{usuario_id}/")
@router.put("/api/v1/usuarios/{usuario_id}")
@router.put("/api/v1/usuarios/{usuario_id}/")
def actualizar_usuario(usuario_id: int, body: dict, request: Request, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    rol_id_target = body.get("grupo_id") or body.get("rol_id")
    if rol_id_target:
        rol = db.query(Rol).filter(Rol.id == rol_id_target).first()
        if not rol:
            raise HTTPException(status_code=400, detail="El rol no existe")
        usuario.rol_id = rol.id

    if body.get("password"):
        usuario.contrasena = hash_password(body["password"])

    if usuario.persona:
        if body.get("email"):
            existente = db.query(Persona).filter(Persona.correo == body["email"], Persona.ci != usuario.persona_ci).first()
            if existente:
                raise HTTPException(status_code=400, detail="El correo ya esta en uso")
            usuario.persona.correo = body["email"]
        if body.get("nombre"):
            usuario.persona.nombre = body["nombre"]
        if body.get("apellido"):
            usuario.persona.apellido_pat = body["apellido"]
    else:
        if body.get("email") or body.get("nombre"):
            fake_ci = str(uuid.uuid4().int)[:8]
            nueva_p = Persona(
                ci=fake_ci,
                nombre=body.get("nombre", usuario.nombre_usuario),
                apellido_pat=body.get("apellido", ""),
                correo=body.get("email") or f"{usuario.nombre_usuario}@fashionstore.bo"
            )
            db.add(nueva_p)
            db.flush()
            usuario.persona_ci = nueva_p.ci

    db.commit()
    db.refresh(usuario)
    
    registrar_bitacora(db, "UPDATE", "usuarios", str(usuario.id), f"Usuario actualizado: {usuario.nombre_usuario}", request=request)
    
    return usuario_to_dict(usuario)

@router.delete("/api/usuarios/{usuario_id}", status_code=204)
@router.delete("/api/usuarios/{usuario_id}/", status_code=204)
@router.delete("/api/v1/usuarios/{usuario_id}", status_code=204)
@router.delete("/api/v1/usuarios/{usuario_id}/", status_code=204)
def eliminar_usuario(usuario_id: int, request: Request, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if usuario.nombre_usuario.lower() == "admin" or usuario.id == 1:
        raise HTTPException(status_code=400, detail="No se puede eliminar el usuario administrador principal")
    
    nombre_usu = usuario.nombre_usuario
    persona = usuario.persona
    db.delete(usuario)
    if persona:
        db.delete(persona)
    db.commit()
    
    registrar_bitacora(db, "DELETE", "usuarios", str(usuario_id), f"Usuario eliminado: {nombre_usu}", request=request)
    
    return None

# === ROLES ===

@router.get("/api/roles/permisos_disponibles")
@router.get("/api/roles/permisos_disponibles/")
@router.get("/api/v1/roles/permisos_disponibles")
@router.get("/api/v1/roles/permisos_disponibles/")
def permisos_disponibles(db: Session = Depends(get_db)):
    """Retorna todos los permisos disponibles del sistema para asignar a roles."""
    permisos = db.query(Permiso).order_by(Permiso.codename).all()
    return [{"id": p.id, "nombre": p.nombre, "codename": p.codename} for p in permisos]

@router.get("/api/roles")
@router.get("/api/roles/")
@router.get("/api/v1/roles")
@router.get("/api/v1/roles/")
def listar_roles(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=5000), db: Session = Depends(get_db)):
    query = db.query(Rol).order_by(Rol.id)
    total, roles = paginar(query, page, page_size)
    base = "/api/v1/roles"
    return {
        "count": total,
        "next": f"{base}?page={page+1}&page_size={page_size}" if page * page_size < total else None,
        "previous": f"{base}?page={page-1}&page_size={page_size}" if page > 1 else None,
        "results": [rol_to_dict(r) for r in roles]
    }

@router.get("/api/roles/{rol_id}")
@router.get("/api/roles/{rol_id}/")
@router.get("/api/v1/roles/{rol_id}")
@router.get("/api/v1/roles/{rol_id}/")
def obtener_rol(rol_id: int, db: Session = Depends(get_db)):
    r = db.query(Rol).filter(Rol.id == rol_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return rol_to_dict(r)

@router.post("/api/roles", status_code=201)
@router.post("/api/roles/", status_code=201)
@router.post("/api/v1/roles", status_code=201)
@router.post("/api/v1/roles/", status_code=201)
def crear_rol(body: dict, request: Request, db: Session = Depends(get_db)):
    nombre = (body.get("name") or body.get("nombre") or "").strip()
    if not nombre:
        raise HTTPException(status_code=400, detail="El nombre del rol es requerido")
    if db.query(Rol).filter(Rol.nombre == nombre).first():
        raise HTTPException(status_code=400, detail="Ya existe un rol con ese nombre")
    nuevo = Rol(nombre=nombre, descripcion=body.get("descripcion", ""), activo=True)
    db.add(nuevo)
    db.flush()  # Para obtener el ID antes de asignar permisos
    
    # Asignar permisos si se proporcionaron
    permisos_ids = body.get("permisos_ids", [])
    if permisos_ids:
        permisos = db.query(Permiso).filter(Permiso.id.in_(permisos_ids)).all()
        nuevo.permisos = permisos
    
    db.commit()
    db.refresh(nuevo)
    
    registrar_bitacora(db, "INSERT", "roles", str(nuevo.id), f"Rol creado: {nuevo.nombre}", request=request)
    
    return rol_to_dict(nuevo)

@router.put("/api/roles/{rol_id}")
@router.put("/api/roles/{rol_id}/")
@router.put("/api/v1/roles/{rol_id}")
@router.put("/api/v1/roles/{rol_id}/")
def actualizar_rol(rol_id: int, body: dict, request: Request, db: Session = Depends(get_db)):
    rol = db.query(Rol).filter(Rol.id == rol_id).first()
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    nombre = (body.get("name") or body.get("nombre") or "").strip()
    if nombre and nombre != rol.nombre:
        if db.query(Rol).filter(Rol.nombre == nombre).first():
            raise HTTPException(status_code=400, detail="Ya existe un rol con ese nombre")
        rol.nombre = nombre
    if "descripcion" in body:
        rol.descripcion = body["descripcion"]
    if "activo" in body:
        rol.activo = body["activo"]
    
    # Sincronizar permisos si se proporcionaron
    if "permisos_ids" in body:
        permisos_ids = body["permisos_ids"]
        permisos = db.query(Permiso).filter(Permiso.id.in_(permisos_ids)).all()
        rol.permisos = permisos
    
    db.commit()
    db.refresh(rol)
    
    registrar_bitacora(db, "UPDATE", "roles", str(rol.id), f"Rol actualizado: {rol.nombre}", request=request)
    
    return rol_to_dict(rol)

@router.delete("/api/roles/{rol_id}", status_code=204)
@router.delete("/api/roles/{rol_id}/", status_code=204)
@router.delete("/api/v1/roles/{rol_id}", status_code=204)
@router.delete("/api/v1/roles/{rol_id}/", status_code=204)
def eliminar_rol(rol_id: int, request: Request, db: Session = Depends(get_db)):
    rol = db.query(Rol).filter(Rol.id == rol_id).first()
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    if db.query(Usuario).filter(Usuario.rol_id == rol_id).first():
        raise HTTPException(status_code=400, detail="No se puede eliminar: hay usuarios asignados a este rol")
    nombre_rol = rol.nombre
    db.delete(rol)
    db.commit()
    
    registrar_bitacora(db, "DELETE", "roles", str(rol_id), f"Rol eliminado: {nombre_rol}", request=request)
    
    return None
