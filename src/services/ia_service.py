import json
import logging
from typing import Any, Dict

from google import genai
from google.genai import types

from src.core.config import settings

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-flash"

IA_PROMPT = """Esta es una foto de un análisis de calidad de granos escrito a mano. Extraé todos los valores numéricos que encuentres y devolvé UNICAMENTE un JSON con este formato:
{
  "parametros": [
    {"nombre": "Humedad", "valor": 14.5, "unidad": "%"},
    {"nombre": "Impurezas", "valor": 1.2, "unidad": "%"}
  ],
  "texto_original": "..."
}
Si no podés leer nada, devolvé {"parametros": [], "texto_original": ""}"""


async def process_analysis_image(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Procesar una imagen de análisis manuscrito con Gemini 2.5 Flash.

    Args:
        file_bytes: Contenido binario de la imagen
        filename: Nombre original del archivo (para logging)

    Returns:
        Dict con "parametros" (lista de dicts), "texto_original" (str),
        y opcionalmente "mensaje" si hubo un error.
    """
    try:
        if not settings.GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY no configurada")
            return {
                "parametros": [],
                "texto_original": "",
                "mensaje": "El servicio de IA no está configurado. Contactá al administrador.",
            }

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        image_part = types.Part.from_bytes(
            data=file_bytes,
            mime_type="image/jpeg",
        )

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[IA_PROMPT, image_part],
        )

        text = response.text.strip()

        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        parsed = json.loads(text)

        return {
            "parametros": parsed.get("parametros", []),
            "texto_original": parsed.get("texto_original", ""),
        }

    except json.JSONDecodeError as e:
        logger.error(f"IA: respuesta JSON inválida de Gemini: {e}")
        return {
            "parametros": [],
            "texto_original": "",
            "mensaje": "No se pudo interpretar la respuesta de la IA.",
        }
    except Exception as e:
        logger.error(f"IA: error procesando imagen {filename}: {e}")
        return {
            "parametros": [],
            "texto_original": "",
            "mensaje": "No se pudo procesar la imagen. Intentá con una foto más clara.",
        }
