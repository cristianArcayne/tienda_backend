"""
Esquemas Pydantic para los Módulos de Innovación Tecnológica, IA, AR y Reportes por Voz.
Alineados a CU16, CU17, CU18 y CU19.
"""
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict


# =========================================================================
# CU16: VESTIDOR VIRTUAL (AR)
# =========================================================================

class TexturaVarianteAR(BaseModel):
    variante_id: int
    talla: str
    color_nombre: str
    color_hex: Optional[str] = None
    cod_barra: str


class MetadatosARResponse(BaseModel):
    ropa_id: int
    nombre: str
    categoria: str
    precio: float
    precio_promocional: Optional[float] = None
    imagen_uri: Optional[str] = None
    modelo_3d_uri: str
    formato_3d: str = "glb"  # glb / gltf / usdz
    posicion_anclaje: str = "TORSO"  # TORSO, LEGS, FEET, HEAD, FULL_BODY
    escala_recomendada: List[float] = [1.0, 1.0, 1.0]
    dimensiones_aprox_cm: Dict[str, float] = {"ancho": 45.0, "alto": 70.0, "profundidad": 20.0}
    texturas_disponibles: List[TexturaVarianteAR] = []
    soporta_ar_flutter: bool = True

    model_config = ConfigDict(from_attributes=True)


class ValidarAjusteCorporalRequest(BaseModel):
    ropa_id: int
    altura_cm: float = Field(..., gt=50, lt=250, description="Altura en cm")
    pecho_cm: float = Field(..., gt=30, lt=200, description="Contorno de pecho en cm")
    cintura_cm: float = Field(..., gt=30, lt=200, description="Contorno de cintura en cm")
    cadera_cm: float = Field(..., gt=30, lt=200, description="Contorno de cadera en cm")


class AjusteCorporalResponse(BaseModel):
    ropa_id: int
    talla_recomendada: str
    porcentaje_calce: float
    mensaje_ajuste: str
    escala_avatar_sugerida: List[float]


# =========================================================================
# CU17: RECOMENDADOR INTELIGENTE (IA)
# =========================================================================

class PrendaSugeridaItem(BaseModel):
    ropa_id: int
    nombre: str
    categoria: str
    precio: float
    imagen_uri: Optional[str] = None
    modelo_3d_uri: Optional[str] = None
    motivo_sugerencia: str


class GenerarOutfitRequest(BaseModel):
    cliente_id: Optional[Union[str, int]] = Field(None, description="CI o ID del cliente para personalizar con su historial")
    ropa_principal_id: Optional[int] = Field(None, description="Prenda base seleccionada")
    ocasion: Optional[str] = Field("Casual", description="Casual, Formal, Fiesta, Deportivo, Trabajo")
    estilo_preferido: Optional[str] = None


class OutfitRecomendadoResponse(BaseModel):
    id: Optional[int] = None
    outfit_nombre: str
    descripcion_estilo: str
    ocasion: str
    score_afinidad: float  # Ej: 96.5%
    tipo_algoritmo: str
    prenda_principal: Optional[PrendaSugeridaItem] = None
    prendas_complementarias: List[PrendaSugeridaItem] = []
    precio_total_outfit: float
    descuento_combo_aplicable: float = 0.0
    precio_final_con_descuento: float


class FeedbackRecomendacionRequest(BaseModel):
    recomendacion_id: int
    aceptada: bool
    comentario: Optional[str] = None


class ChatMessageRequest(BaseModel):
    mensaje: str = Field(..., description="Mensaje de texto del usuario")
    cliente_id: Optional[Union[str, int]] = None
    historial: Optional[List[Dict[str, str]]] = Field(default=[], description="Historial de mensajes previos")


class ChatMessageResponse(BaseModel):
    respuesta_texto: str
    outfit_recomendado: Optional[OutfitRecomendadoResponse] = None

# =========================================================================
# CU18: REPORTES MEDIANTE COMANDOS DE VOZ & ANALÍTICA
# =========================================================================

class ComandoVozTextoRequest(BaseModel):
    comando_voz: Optional[str] = Field(None, description="Texto transcrito del comando de voz")
    comando_texto: Optional[str] = Field(None, description="Texto transcrito alternativo")
    comando: Optional[str] = Field(None, description="Texto alternativo del comando de voz")
    usuario_id: Optional[int] = None


class AudioBase64Request(BaseModel):
    audio_base64: str = Field(..., description="Cadena de audio codificada en Base64")
    formato: str = Field("audio/webm", description="Formato MIME del audio (audio/webm, audio/wav, audio/mp3)")
    usuario_id: Optional[int] = None


class SerieDatosGrafico(BaseModel):
    name: str
    data: List[float]


class DatosGrafico(BaseModel):
    tipo_grafico: str  # 'bar', 'pie', 'donut', 'line', 'radialBar'
    labels: List[str]
    series: List[Any]  # Puede ser lista de números o lista de SerieDatosGrafico


class ReporteVozResponse(BaseModel):
    comando_reconocido: str
    intencion_detectada: str
    resumen_ejecutivo: str  # Texto en lenguaje natural apto para Text-to-Speech (TTS)
    metricas_kpi: Dict[str, Any]
    datos_grafico: DatosGrafico
    datos_tabla: Optional[List[Dict[str, Any]]] = None
    columnas_tabla: Optional[List[Dict[str, str]]] = None
    sugerencias_siguientes_comandos: List[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =========================================================================
# CU19: RESEÑAS Y CALIFICACIONES
# =========================================================================

class ResenaCreateRequest(BaseModel):
    ropa_id: Optional[int] = None
    producto_id: Optional[int] = None
    cliente_ci: Optional[Union[str, int]] = "admin"
    cliente_nombre: Optional[str] = None
    puntuacion_estrellas: Optional[int] = None
    calificacion: Optional[int] = None
    comentario: Optional[str] = Field(None, max_length=1000)


class ResenaUpdateRequest(BaseModel):
    puntuacion_estrellas: Optional[int] = None
    calificacion: Optional[int] = None
    comentario: Optional[str] = Field(None, max_length=1000)


class ResenaItemResponse(BaseModel):
    id: int
    ropa_id: int
    producto: Optional[int] = None
    cliente_ci: Union[str, int]
    cliente_nombre: Optional[str] = None
    usuario_username: Optional[str] = None
    usuario: Optional[int] = None
    puntuacion_estrellas: int
    calificacion: Optional[int] = None
    comentario: Optional[str] = None
    fecha: date
    fecha_creacion: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DesgloseEstrellas(BaseModel):
    estrella_5: int = 0
    estrella_4: int = 0
    estrella_3: int = 0
    estrella_2: int = 0
    estrella_1: int = 0


class ResumenCalificacionesRopaResponse(BaseModel):
    ropa_id: int
    ropa_nombre: str
    promedio_calificacion: float  # Ej: 4.8 / 5.0
    total_resenas: int
    porcentaje_recomendacion: float  # Ej: 92.0%
    desglose_estrellas: DesgloseEstrellas
    ultimas_resenas: List[ResenaItemResponse]
