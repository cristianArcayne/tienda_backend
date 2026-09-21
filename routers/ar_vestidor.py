"""
Router para CU16: Utilizar Vestidor Virtual (AR).
Alineado a endpoints de alto rendimiento para clientes móviles (Flutter / ARCore / SceneKit).
Incluye Virtual Try-On con IA mediante Fashn.ai.
"""
import os
import base64
import httpx
import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
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


# ============================================================
# VIRTUAL TRY-ON CON IA (Segmind IDM-VTON)
# ============================================================

SEGMIND_API_KEY = os.getenv("SEGMIND_API_KEY", "SG_6197dc2bb848ae07")
SEGMIND_API_URL = "https://api.segmind.com/v1/idm-vton"


def _detectar_categoria_segmind(prenda) -> str:
    """Detecta la categoría de la prenda para Segmind IDM-VTON (upper_body, lower_body, dresses)"""
    nombre = (prenda.nombre or "").lower()
    cat_nombre = (prenda.categoria.nombre if prenda.categoria else "").lower()

    if any(w in nombre or w in cat_nombre for w in ["pantalon", "jean", "short", "falda", "bermuda", "inferior"]):
        return "lower_body"
    elif any(w in nombre or w in cat_nombre for w in ["vestido", "enterizo", "overol", "mono", "jumpsuit"]):
        return "dresses"

    return "upper_body"


@router.post(
    "/try-on-ia",
    summary="Probador virtual con IA: sube tu foto y pruébate la ropa",
    description="Envía una foto personal y el ID de la prenda. La IA genera una imagen con la ropa puesta sobre tu cuerpo usando Segmind IDM-VTON."
)
async def try_on_ia(
    foto_usuario: UploadFile = File(..., description="Foto del usuario (JPG/PNG)"),
    ropa_id: int = Form(..., description="ID de la prenda a probar"),
    db: Session = Depends(get_db)
):
    api_key = os.getenv("SEGMIND_API_KEY", SEGMIND_API_KEY).strip()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de prueba virtual con IA no está configurado. Agregue SEGMIND_API_KEY en las variables de entorno."
        )

    # Obtener prenda de la base de datos
    prenda = db.query(Ropa).filter(Ropa.id == ropa_id).first()
    if not prenda:
        raise HTTPException(status_code=404, detail="Prenda no encontrada.")

    if not prenda.imagen_uri:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La prenda seleccionada no tiene imagen disponible para la prueba virtual."
        )

    # Leer la foto del usuario y convertir a base64 data URI
    contenido_foto = await foto_usuario.read()
    content_type = foto_usuario.content_type or "image/jpeg"
    foto_base64 = f"data:{content_type};base64,{base64.b64encode(contenido_foto).decode('utf-8')}"

    # Preparar imagen de la prenda (Base64 data URI o URL absoluta)
    imagen_prenda_path = prenda.imagen_uri
    garment_data_url = None

    if imagen_prenda_path.startswith("http://") or imagen_prenda_path.startswith("https://"):
        garment_data_url = imagen_prenda_path
    else:
        # Intentar cargar desde el sistema de archivos local
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        relative_clean = imagen_prenda_path.lstrip("/").replace("/", os.sep)
        local_path = os.path.join(backend_dir, relative_clean)

        if os.path.exists(local_path):
            try:
                with open(local_path, "rb") as img_f:
                    prenda_bytes = img_f.read()
                    mime_type = "image/png" if local_path.lower().endswith(".png") else "image/jpeg"
                    garment_data_url = f"data:{mime_type};base64,{base64.b64encode(prenda_bytes).decode('utf-8')}"
            except Exception:
                pass

        if not garment_data_url:
            garment_data_url = f"https://tienda-backend-kvfk.onrender.com{imagen_prenda_path}"

    category = _detectar_categoria_segmind(prenda)

    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "human_img": foto_base64,
        "garm_img": garment_data_url,
        "category": category,
        "crop": False,
        "seed": 42,
        "steps": 20,
        "garment_des": prenda.nombre or "clothing item"
    }

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                SEGMIND_API_URL,
                headers=headers,
                json=payload
            )

            if response.status_code >= 200 and response.status_code < 300:
                c_type = response.headers.get("content-type", "").lower()
                body_bytes = response.content

                # Si el servidor responde directamente con la imagen binaria
                if "image" in c_type or (len(body_bytes) > 100 and (body_bytes.startswith(b"\xff\xd8") or body_bytes.startswith(b"\x89PNG"))):
                    mime = "image/png" if body_bytes.startswith(b"\x89PNG") else "image/jpeg"
                    b64_result = f"data:{mime};base64,{base64.b64encode(body_bytes).decode('utf-8')}"
                    return {
                        "success": True,
                        "imagen_resultado": b64_result,
                        "prenda_nombre": prenda.nombre,
                        "mensaje": f"¡Así te queda {prenda.nombre}! Generado con Segmind IDM-VTON."
                    }

                # Si responde en formato JSON
                try:
                    result = response.json()
                    out_img = result.get("image") or result.get("output") or result.get("output_url")
                    if isinstance(out_img, list) and len(out_img) > 0:
                        out_img = out_img[0]

                    if out_img:
                        return {
                            "success": True,
                            "imagen_resultado": out_img,
                            "prenda_nombre": prenda.nombre,
                            "mensaje": f"¡Así te queda {prenda.nombre}! Generado con Segmind IDM-VTON."
                        }
                except Exception:
                    pass

                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Segmind respondió correctamente pero no entregó una imagen válida."
                )

            else:
                # Error de la API de Segmind
                error_msg = response.text
                try:
                    err_json = response.json()
                    error_msg = err_json.get("error") or err_json.get("message") or error_msg
                except Exception:
                    pass

                if "No human detected" in str(error_msg):
                    error_msg = "No se detectó una persona clara en la foto. Toma una foto con buena luz mostrando tu cuerpo o torso."
                elif "Invalid Garment" in str(error_msg):
                    error_msg = "La imagen de esta prenda no pudo ser procesada. Intenta con otra prenda del catálogo."
                elif "credit" in str(error_msg).lower() or "balance" in str(error_msg).lower():
                    error_msg = "Saldo o créditos insuficientes en la cuenta de Segmind."

                print(f"[Segmind ERROR] Status {response.status_code}: {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Error del servicio Segmind IA: {error_msg}"
                )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="El servicio de IA de Segmind tardó demasiado en responder (Tiempo de espera agotado). Intenta de nuevo."
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Segmind ERROR] Exception: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al procesar la prueba virtual: {str(e)}"
        )

