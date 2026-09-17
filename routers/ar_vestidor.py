"""
Router para CU16: Utilizar Vestidor Virtual (AR).
Alineado a endpoints de alto rendimiento para clientes móviles (Flutter / ARCore / SceneKit).
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models.catalogo import Ropa, VariantePrenda, Categoria
from schemas.innovacion import (
    MetadatosARResponse,
    TexturaVarianteAR,
    ValidarAjusteCorporalRequest,
    AjusteCorporalResponse
)

router = APIRouter(
    prefix="/api/v1/ar",
    tags=["CU16. Utilizar vestidor virtual (AR)"]
)


@router.get(
    "/catalogo-3d",
    response_model=List[MetadatosARResponse],
    summary="Listar catálogo optimizado con soporte de Realidad Aumentada (3D)",
    description="Retorna únicamente las prendas que cuentan con recursos de modelos 3D (.glb / .gltf) activos para prueba en vestidor virtual."
)
def listar_prendas_ar(
    categoria_id: Optional[int] = Query(None, description="Filtrar por categoría"),
    db: Session = Depends(get_db)
):
    query = db.query(Ropa).filter(
        Ropa.modelo_3d_uri.isnot(None),
        Ropa.modelo_3d_uri != ""
    ).options(
        joinedload(Ropa.categoria),
        joinedload(Ropa.variantes).joinedload(VariantePrenda.talla),
        joinedload(Ropa.variantes).joinedload(VariantePrenda.color)
    )

    if categoria_id:
        query = query.filter(Ropa.categoria_id == categoria_id)

    prendas = query.all()
    resultado = []

    for p in prendas:
        cat_nom = p.categoria.nombre if p.categoria else "General"
        
        # Mapeo de anclaje corporal según categoría
        anclaje = "TORSO"
        dim = {"ancho": 45.0, "alto": 70.0, "profundidad": 20.0}
        nom_lower = p.nombre.lower()
        if "jean" in nom_lower or "pantalon" in nom_lower or "falda" in nom_lower:
            anclaje = "LEGS"
            dim = {"ancho": 40.0, "alto": 105.0, "profundidad": 25.0}
        elif "vestido" in nom_lower:
            anclaje = "FULL_BODY"
            dim = {"ancho": 45.0, "alto": 120.0, "profundidad": 25.0}
        elif "zapato" in nom_lower or "calzado" in nom_lower:
            anclaje = "FEET"
            dim = {"ancho": 25.0, "alto": 15.0, "profundidad": 30.0}

        texturas = []
        for v in (p.variantes or []):
            texturas.append(
                TexturaVarianteAR(
                    variante_id=v.id,
                    talla=v.talla.medida if v.talla else "Única",
                    color_nombre=v.color.nombre if v.color else "Estándar",
                    color_hex=v.color.codigo_hex if v.color else "#000000",
                    cod_barra=v.cod_barra
                )
            )

        resultado.append(
            MetadatosARResponse(
                ropa_id=p.id,
                nombre=p.nombre,
                categoria=cat_nom,
                precio=float(p.precio),
                imagen_uri=p.imagen_uri,
                modelo_3d_uri=p.modelo_3d_uri,
                formato_3d="glb",
                posicion_anclaje=anclaje,
                escala_recomendada=[1.0, 1.0, 1.0],
                dimensiones_aprox_cm=dim,
                texturas_disponibles=texturas,
                soporta_ar_flutter=True
            )
        )

    return resultado


@router.get(
    "/prendas/{ropa_id}",
    response_model=MetadatosARResponse,
    summary="Obtener metadatos 3D y texturas de una prenda específica para AR",
    description="Endpoint de baja latencia para que la app móvil en Flutter descargue el modelo 3D y aplique texturas dinámicas sobre el cuerpo del cliente."
)
def obtener_metadatos_ar_prenda(ropa_id: int, db: Session = Depends(get_db)):
    prenda = db.query(Ropa).filter(Ropa.id == ropa_id).options(
        joinedload(Ropa.categoria),
        joinedload(Ropa.variantes).joinedload(VariantePrenda.talla),
        joinedload(Ropa.variantes).joinedload(VariantePrenda.color)
    ).first()

    if not prenda:
        raise HTTPException(status_code=404, detail="Prenda no encontrada.")

    if not prenda.modelo_3d_uri:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La prenda solicitada aún no tiene un recurso de modelo 3D disponible para Realidad Aumentada."
        )

    cat_nom = prenda.categoria.nombre if prenda.categoria else "General"
    anclaje = "TORSO"
    dim = {"ancho": 45.0, "alto": 70.0, "profundidad": 20.0}
    nom_lower = prenda.nombre.lower()
    if "jean" in nom_lower or "pantalon" in nom_lower or "falda" in nom_lower:
        anclaje = "LEGS"
        dim = {"ancho": 40.0, "alto": 105.0, "profundidad": 25.0}
    elif "vestido" in nom_lower:
        anclaje = "FULL_BODY"
        dim = {"ancho": 45.0, "alto": 120.0, "profundidad": 25.0}

    texturas = [
        TexturaVarianteAR(
            variante_id=v.id,
            talla=v.talla.medida if v.talla else "Única",
            color_nombre=v.color.nombre if v.color else "Estándar",
            color_hex=v.color.codigo_hex if v.color else "#000000",
            cod_barra=v.cod_barra
        )
        for v in (prenda.variantes or [])
    ]

    return MetadatosARResponse(
        ropa_id=prenda.id,
        nombre=prenda.nombre,
        categoria=cat_nom,
        precio=float(prenda.precio),
        imagen_uri=prenda.imagen_uri,
        modelo_3d_uri=prenda.modelo_3d_uri,
        formato_3d="glb",
        posicion_anclaje=anclaje,
        escala_recomendada=[1.0, 1.0, 1.0],
        dimensiones_aprox_cm=dim,
        texturas_disponibles=texturas,
        soporta_ar_flutter=True
    )


@router.post(
    "/validar-ajuste",
    response_model=AjusteCorporalResponse,
    summary="Validar ajuste corporal y talla óptima para avatar 3D",
    description="Calcula la talla recomendada y escala tridimensional del avatar en base a medidas biométricas (pecho, cintura, cadera, altura)."
)
def validar_ajuste_corporal(request: ValidarAjusteCorporalRequest, db: Session = Depends(get_db)):
    prenda = db.query(Ropa).filter(Ropa.id == request.ropa_id).first()
    if not prenda:
        raise HTTPException(status_code=404, detail="Prenda no encontrada.")

    # Algoritmo de recomendación biométrica
    pecho = request.pecho_cm
    cintura = request.cintura_cm
    altura = request.altura_cm

    if pecho < 88 and cintura < 74:
        talla_rec = "S"
        calce = 95.0
        escala = [0.95, altura / 170.0, 0.95]
        msj = "Ajuste Slim perfecto en pecho y hombros para tu complexión."
    elif pecho <= 100 and cintura <= 86:
        talla_rec = "M"
        calce = 98.0
        escala = [1.0, altura / 175.0, 1.0]
        msj = "Talla M estándar ideal con caída natural y comodidad en movimiento."
    elif pecho <= 112 and cintura <= 98:
        talla_rec = "L"
        calce = 94.0
        escala = [1.08, altura / 180.0, 1.08]
        msj = "Talla L recomendada para un ajuste relajado y holgado."
    else:
        talla_rec = "XL"
        calce = 91.0
        escala = [1.15, altura / 185.0, 1.15]
        msj = "Talla XL con espacio óptimo para máxima libertad."

    return AjusteCorporalResponse(
        ropa_id=prenda.id,
        talla_recomendada=talla_rec,
        porcentaje_calce=calce,
        mensaje_ajuste=msj,
        escala_avatar_sugerida=escala
    )
