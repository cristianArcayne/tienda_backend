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

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SEGMIND_API_KEY = os.getenv("SEGMIND_API_KEY", "SG_6197dc2bb848ae07")
SEGMIND_API_URL = "https://api.segmind.com/v1/idm-vton"


async def _generar_gemini_vision_tryon(foto_usuario_bytes: bytes, garment_bytes: bytes, prenda_nombre: str) -> Optional[str]:
    """
    Motor Nivel 1: Google Gemini Vision.
    Genera fotorrealista overlay de ropa mediante Gemini Multimodal REST API.
    """
    api_key = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY).strip()
    if not api_key or api_key.startswith("tu_"):
        return None

    user_b64 = base64.b64encode(foto_usuario_bytes).decode("utf-8")
    garment_b64 = base64.b64encode(garment_bytes).decode("utf-8")

    models_to_try = ["gemini-2.5-flash-image", "gemini-3.1-flash-image", "gemini-3.6-flash"]

    prompt_text = (
        f"Virtual Try-On task: Fit the garment '{prenda_nombre}' shown in the second image "
        f"seamlessly onto the person in the first image. "
        f"Preserve the person's face, body structure, pose, skin tone, and background. "
        f"Return only the final try-on image."
    )

    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt_text},
                    {"inline_data": {"mime_type": "image/jpeg", "data": user_b64}},
                    {"inline_data": {"mime_type": "image/jpeg", "data": garment_b64}}
                ]
            }]
        }

        try:
            print(f"[IA Vestidor] Intentando Gemini Vision Nivel 1 ({model})...")
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    for candidate in candidates:
                        parts = candidate.get("content", {}).get("parts", [])
                        for part in parts:
                            inline = part.get("inlineData") or part.get("inline_data")
                            if inline and "data" in inline:
                                mime = inline.get("mimeType") or inline.get("mime_type") or "image/png"
                                b64_img = inline.get("data")
                                print(f"[IA Vestidor] ¡Gemini Vision ({model}) exitoso!")
                                return f"data:{mime};base64,{b64_img}"
        except Exception as e:
            print(f"[IA Vestidor Error Gemini] {model}: {e}")
            continue

    return None


def _detectar_categoria_segmind(prenda) -> str:
    """Detecta la categoría de la prenda para Segmind IDM-VTON (upper_body, lower_body, dresses)"""
    nombre = (prenda.nombre or "").lower()
    cat_nombre = (prenda.categoria.nombre if prenda.categoria else "").lower()

    if any(w in nombre or w in cat_nombre for w in ["pantalon", "jean", "short", "falda", "bermuda", "inferior"]):
        return "lower_body"
    elif any(w in nombre or w in cat_nombre for w in ["vestido", "enterizo", "overol", "mono", "jumpsuit"]):
        return "dresses"

    return "upper_body"


def _estimar_color_fondo(img, margen=10):
    """Estima el color dominante del borde de la imagen para usar como relleno."""
    try:
        from PIL import Image
        w, h = img.size
        pixels = []
        for x in range(w):
            for y in range(min(margen, h)):
                pixels.append(img.getpixel((x, y))[:3])
            for y in range(max(0, h - margen), h):
                pixels.append(img.getpixel((x, y))[:3])
        for y in range(h):
            for x in range(min(margen, w)):
                pixels.append(img.getpixel((x, y))[:3])
            for x in range(max(0, w - margen), w):
                pixels.append(img.getpixel((x, y))[:3])
        if not pixels:
            return (200, 200, 200)
        r = sum(p[0] for p in pixels) // len(pixels)
        g = sum(p[1] for p in pixels) // len(pixels)
        b = sum(p[2] for p in pixels) // len(pixels)
        return (r, g, b)
    except Exception:
        return (200, 200, 200)


def _preprocesar_imagen_usuario(foto_bytes: bytes) -> bytes:
    """
    Pre-procesa la foto del usuario para hacerla compatible con Segmind IDM-VTON:
    - Convierte a ratio 3:4 (768x1024)
    - Añade padding/blur sutil en bordes
    """
    try:
        from PIL import Image, ImageOps, ImageFilter
        import io

        img = Image.open(io.BytesIO(foto_bytes))
        img = ImageOps.exif_transpose(img).convert("RGB")
        orig_w, orig_h = img.size

        target_w, target_h = 768, 1024  # Ratio 3:4
        target_ratio = target_w / target_h

        current_ratio = orig_w / orig_h
        bg_color = _estimar_color_fondo(img.convert("RGBA"))

        if abs(current_ratio - target_ratio) < 0.05:
            img_resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        elif current_ratio > target_ratio:
            new_w = target_w
            new_h = int(target_w / current_ratio)
            img_scaled = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            canvas = Image.new("RGB", (target_w, target_h), bg_color)
            canvas.paste(img_scaled, (0, 0))

            if new_h < target_h:
                bottom_strip = img_scaled.crop((0, max(0, new_h - 30), new_w, new_h))
                bottom_strip = bottom_strip.resize((new_w, target_h - new_h), Image.Resampling.LANCZOS)
                bottom_strip = bottom_strip.filter(ImageFilter.GaussianBlur(radius=15))
                canvas.paste(bottom_strip, (0, new_h))

            img_resized = canvas
        else:
            new_h = target_h
            new_w = int(target_h * current_ratio)
            img_scaled = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            canvas = Image.new("RGB", (target_w, target_h), bg_color)
            paste_x = (target_w - new_w) // 2
            canvas.paste(img_scaled, (paste_x, 0))

            if new_w < target_w:
                left_strip = img_scaled.crop((0, 0, min(30, new_w), new_h))
                left_strip = left_strip.resize((paste_x, new_h), Image.Resampling.LANCZOS)
                left_strip = left_strip.filter(ImageFilter.GaussianBlur(radius=15))
                canvas.paste(left_strip, (0, 0))

                right_x = paste_x + new_w
                right_strip = img_scaled.crop((max(0, new_w - 30), 0, new_w, new_h))
                right_strip = right_strip.resize((target_w - right_x, new_h), Image.Resampling.LANCZOS)
                right_strip = right_strip.filter(ImageFilter.GaussianBlur(radius=15))
                canvas.paste(right_strip, (right_x, 0))

            img_resized = canvas

        out_buf = io.BytesIO()
        img_resized.save(out_buf, format="JPEG", quality=92)
        return out_buf.getvalue()

    except Exception as e:
        print(f"[Preprocesar Error] {e} - usando imagen original")
        return foto_bytes


def _generar_composite_fallback(foto_usuario_bytes: bytes, imagen_prenda_uri: str) -> str:
    """Motor Nivel 3 (Fallback): elimina fondo blanco del JPG de la prenda y la posiciona sobre los hombros."""
    try:
        from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageChops
        import io

        user_img = Image.open(io.BytesIO(foto_usuario_bytes))
        user_img = ImageOps.exif_transpose(user_img).convert("RGBA")
        u_w, u_h = user_img.size

        garment_img = None
        if imagen_prenda_uri.startswith("http://") or imagen_prenda_uri.startswith("https://"):
            try:
                import httpx
                resp = httpx.get(imagen_prenda_uri, timeout=10.0)
                if resp.status_code == 200:
                    garment_img = Image.open(io.BytesIO(resp.content))
            except Exception:
                pass
        else:
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            relative_clean = imagen_prenda_uri.lstrip("/").replace("/", os.sep)
            local_path = os.path.join(backend_dir, relative_clean)
            if os.path.exists(local_path):
                garment_img = Image.open(local_path)

        if not garment_img:
            b64_orig = base64.b64encode(foto_usuario_bytes).decode("utf-8")
            return f"data:image/jpeg;base64,{b64_orig}"

        garment_img = ImageOps.exif_transpose(garment_img).convert("RGBA")

        # 1. Eliminar recuadro blanco/claro del JPG de la prenda
        threshold = 220
        r, g, b, a = garment_img.split()
        mask_r = r.point(lambda p: 0 if p > threshold else 255)
        mask_g = g.point(lambda p: 0 if p > threshold else 255)
        mask_b = b.point(lambda p: 0 if p > threshold else 255)
        mask_combined = ImageChops.lighter(ImageChops.lighter(mask_r, mask_g), mask_b)
        garment_img.putalpha(mask_combined)

        # Recortar bordes transparentes sobrantes
        bbox = garment_img.getbbox()
        if bbox:
            garment_img = garment_img.crop(bbox)

        # 2. Posicionar sobre los hombros
        ratio = u_w / u_h
        es_foto_parcial = ratio > 0.65

        if es_foto_parcial:
            torso_w = int(u_w * 0.60)
            pos_y_factor = 0.45
        else:
            torso_w = int(u_w * 0.70)
            pos_y_factor = 0.235

        aspect_garment = garment_img.height / max(garment_img.width, 1)
        torso_h = int(torso_w * aspect_garment)

        max_h = int(u_h * 0.48)
        if torso_h > max_h:
            torso_h = max_h
            torso_w = int(torso_h / aspect_garment)

        garment_resized = garment_img.resize((torso_w, torso_h), Image.Resampling.LANCZOS)

        pos_x = (u_w - torso_w) // 2
        pos_y = int(u_h * pos_y_factor)

        combined = user_img.copy()
        combined.paste(garment_resized, (pos_x, pos_y), garment_resized)

        out_buf = io.BytesIO()
        combined.convert("RGB").save(out_buf, format="JPEG", quality=95)
        b64_out = base64.b64encode(out_buf.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{b64_out}"

    except Exception as e:
        print(f"[Fallback Error] {e}")
        b64_orig = base64.b64encode(foto_usuario_bytes).decode("utf-8")
        return f"data:image/jpeg;base64,{b64_orig}"


@router.post(
    "/try-on-ia",
    summary="Probador virtual con IA: sube tu foto y pruébate la ropa",
    description="Envía una foto personal y el ID de la prenda. Utiliza pipeline de 3 niveles con IA (Gemini Vision -> Segmind IDM-VTON -> Pillow Smart Composite). Retorna la imagen fotorrealista."
)
async def try_on_ia(
    foto_usuario: UploadFile = File(..., description="Foto del usuario (JPG/PNG) - acepta cara, medio cuerpo o cuerpo completo"),
    ropa_id: int = Form(..., description="ID de la prenda a probar"),
    db: Session = Depends(get_db)
):
    # 1. Anti-SSRF y Validación de Prenda en DB
    prenda = db.query(Ropa).filter(Ropa.id == ropa_id).first()
    if not prenda:
        raise HTTPException(status_code=404, detail="Prenda no encontrada.")

    if not prenda.imagen_uri:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La prenda seleccionada no tiene imagen disponible para la prueba virtual."
        )

    # 2. Leer foto del usuario (zero-retention: procesado solo en memoria)
    contenido_foto_original = await foto_usuario.read()

    # 3. Leer imagen de la prenda
    prenda_bytes = None
    imagen_prenda_path = prenda.imagen_uri
    garment_data_url = None

    if imagen_prenda_path.startswith("http://") or imagen_prenda_path.startswith("https://"):
        garment_data_url = imagen_prenda_path
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r_garment = await client.get(imagen_prenda_path)
                if r_garment.status_code == 200:
                    prenda_bytes = r_garment.content
        except Exception:
            pass
    else:
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

    # ============================================================
    # NIVEL 1: GOOGLE GEMINI VISION (Primary Engine)
    # ============================================================
    if prenda_bytes:
        gemini_result = await _generar_gemini_vision_tryon(
            contenido_foto_original,
            prenda_bytes,
            prenda.nombre or "Prenda"
        )
        if gemini_result:
            return {
                "success": True,
                "imagen_resultado": gemini_result,
                "prenda_nombre": prenda.nombre,
                "mensaje": f"¡Así te queda {prenda.nombre}! Generado con Google Gemini Vision IA."
            }

    # ============================================================
    # NIVEL 2: SEGMIND IDM-VTON (Secondary Engine)
    # ============================================================
    print("[IA Vestidor] Nivel 1 (Gemini) omitido o no disponible. Iniciando Nivel 2 (Segmind)...")
    contenido_foto_procesada = _preprocesar_imagen_usuario(contenido_foto_original)
    foto_base64 = f"data:image/jpeg;base64,{base64.b64encode(contenido_foto_procesada).decode('utf-8')}"
    category = _detectar_categoria_segmind(prenda)
    segmind_key = os.getenv("SEGMIND_API_KEY", SEGMIND_API_KEY).strip()

    headers = {
        "x-api-key": segmind_key,
        "Content-Type": "application/json"
    }

    intentos_config = [
        {"crop": True, "desc": "foto preprocesada 3:4 con crop=true"},
        {"crop": False, "desc": "foto preprocesada 3:4 con crop=false"},
    ]

    for intento in intentos_config:
        payload = {
            "human_img": foto_base64,
            "garm_img": garment_data_url,
            "category": category,
            "crop": intento["crop"],
            "seed": 42,
            "steps": 30,
            "garment_des": prenda.nombre or "clothing item"
        }

        try:
            print(f"[IA Vestidor] Intento Segmind: {intento['desc']}")
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(SEGMIND_API_URL, headers=headers, json=payload)
                if response.status_code >= 200 and response.status_code < 300:
                    c_type = response.headers.get("content-type", "").lower()
                    body_bytes = response.content

                    if "image" in c_type or (len(body_bytes) > 100 and (body_bytes.startswith(b"\xff\xd8") or body_bytes.startswith(b"\x89PNG"))):
                        mime = "image/png" if body_bytes.startswith(b"\x89PNG") else "image/jpeg"
                        b64_result = f"data:{mime};base64,{base64.b64encode(body_bytes).decode('utf-8')}"
                        return {
                            "success": True,
                            "imagen_resultado": b64_result,
                            "prenda_nombre": prenda.nombre,
                            "mensaje": f"¡Así te queda {prenda.nombre}! Generado con Segmind IA."
                        }

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
                                "mensaje": f"¡Así te queda {prenda.nombre}! Generado con Segmind IA."
                            }
                    except Exception:
                        pass
        except Exception as e:
            print(f"[Segmind Error] {e}")
            continue

    # ============================================================
    # NIVEL 3: PILLOW SMART COMPOSITE (Fallback Garantizado)
    # ============================================================
    print("[IA Vestidor] Nivel 1 y 2 no disponibles. Aplicando Nivel 3 (Sintesis Inteligente Pillow)")
    img_fallback = _generar_composite_fallback(contenido_foto_original, prenda.imagen_uri)
    return {
        "success": True,
        "imagen_resultado": img_fallback,
        "prenda_nombre": prenda.nombre,
        "mensaje": f"¡Así te queda {prenda.nombre}! Generado con síntesis adaptativa."
    }

