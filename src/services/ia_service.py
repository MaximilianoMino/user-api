import json
import logging
import re
from typing import Any, Dict

from google import genai
from google.genai import types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.models.parametro import Parametro

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

MAPEO_GEMINI_DB = {
    "manchado x maquina": "MANCHA_MECANICA",
    "manchado leve ojo negro": "MANCHADOS_LEVES_OJO_NEGRO",
    "ojos negros": "MANCHADOS_LEVES_OJO_NEGRO",
    "ojo negro": "MANCHADOS_LEVES_OJO_NEGRO",
    "manchado leve": "MANCHADOS_LEVES",
    "manchado fuerte": "MANCHADOS_FUERTES",
    "mancha mecanica": "MANCHA_MECANICA",
    "mancha": "MANCHADOS",
    "manchado": "MANCHADOS",
    "arrugado leve": "ARRUGADOS_LEVES",
    "arrugado": "ARRUGADOS",
    "descolorido oscuro": "DESCOLORIDOS_OSCUROS",
    "descolorido violaceo": "DESCOLORIDOS_VIOLACEO",
    "descolorido amarronado": "DESCOLORIDO_AMARRONADOS",
    "descolorido": "DESCOLORIDOS",
    "decolorido": "DESCOLORIDOS",
    "helado venoso": "HELADOS_VENOSO",
    "helado": "HELADOS",
    "partido": "PARTIDOS",
    "quebrado": "QUEBRADOS",
    "brotado": "BROTADOS",
    "ardido": "GRANOS_NEGROS_ARDIDOS",
    "cascado": "DANIOS_MECANICOS",
    "roido": "ROIDOS",
    "picado": "PICADOS",
    "pelado": "PELADOS",
    "oxidado": "OXIDADOS",
    "lavado": "LAVADOS",
    "revolcado": "REVOLCADOS",
    "decorado": "DESCORTICADOS",
    "chuzo": "CHUZOS",
    "bolita": "BOLITA",
    "terron": "TERRON",
    "paja": "MATERIA_EXTRANIA",
    "chala": "MATERIA_EXTRANIA",
    "tierra": "TIERRA",
    "piedra": "MATERIA_EXTRANIA",
    "palos": "GRANOS_CON_PALOS",
    "alergeno": "MATERIA_EXTRANIA",
    "otra variedad": "OTRA_VARIEDAD",
    "hongos": "HONGOS",
    "huevo de tero": "HUEVO_DE_TERO",
    "caida de zaranda": "CAIDA_ZARANDA",
    "boca de pescado": "BOCA_DE_PESCADO",
    "danios mecanicos": "DANIOS_MECANICOS",
    "piel de vaina": "PIEL_DE_VAINA",
}

SUFIJOS_IGNORAR = [
    "total", "rinde aproximado", "zaranda", "peso de muestra", "producto_principal",
]


def _extraer_base(nombre: str) -> str:
    """Elimina sufijos entre paréntesis y espacios extra."""
    return re.sub(r"\s*\(.*?\)", "", nombre).strip()


def _puntaje_prioridad(nombre: str) -> int:
    """Menor puntaje = mayor prioridad."""
    nombre_lower = nombre.lower()
    score = 0
    if "calidad final" in nombre_lower:
        score += 0
    elif "simulacion" in nombre_lower or "simulación" in nombre_lower:
        score += 100
    elif "original" in nombre_lower:
        score += 200
    else:
        score += 300

    if "porcentaje" in nombre_lower:
        score += 0
    elif "gramos" in nombre_lower:
        score += 10
    else:
        score += 20

    return score


def _limpiar_parametros(parametros: list) -> list:
    """Filtra irrelevantes, agrupa por nombre base y conserva solo el de mayor prioridad por grupo."""
    filtrados = [p for p in parametros if not any(
        sufijo in p.get("nombre", "").lower() for sufijo in SUFIJOS_IGNORAR
    )]

    grupos: dict[str, dict] = {}
    for p in filtrados:
        base = _extraer_base(p.get("nombre", ""))
        if not base:
            continue
        mejor = grupos.get(base)
        puntaje = _puntaje_prioridad(p.get("nombre", ""))
        if mejor is None or puntaje < _puntaje_prioridad(mejor.get("nombre", "")):
            grupos[base] = p

    return list(grupos.values())


async def process_analysis_image(file_bytes: bytes, filename: str, db: AsyncSession) -> Dict[str, Any]:
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

        parametros = _limpiar_parametros(parsed.get("parametros", []))

        try:
            result = await db.execute(select(Parametro.parametro_id, Parametro.codigo))
            todos_parametros = result.all()
            codigo_a_id = {row.codigo: row.parametro_id for row in todos_parametros}
            codigos_lower = {row.codigo.lower(): row.codigo for row in todos_parametros}
        except Exception as e:
            logger.warning(f"IA: error cargando parámetros de DB: {e}")
            codigo_a_id = {}
            codigos_lower = {}

        try:
            for p in parametros:
                nombre = p.get("nombre", "")
                if not nombre:
                    continue

                nombre_lower = nombre.lower()
                codigo_db = None

                for clave, codigo in sorted(MAPEO_GEMINI_DB.items(), key=lambda x: len(x[0]), reverse=True):
                    if clave in nombre_lower:
                        codigo_db = codigo
                        break

                match_id = None
                if codigo_db and codigo_db in codigo_a_id:
                    match_id = codigo_db

                if not match_id:
                    for codigo_lower, codigo_real in codigos_lower.items():
                        if nombre_lower in codigo_lower:
                            match_id = codigo_real
                            break

                if match_id:
                    p["parametro_id"] = codigo_a_id[match_id]
                    p["codigo_db"] = match_id
        except Exception as e:
            logger.warning(f"IA: error mapeando parámetros a DB: {e}")

        return {
            "parametros": parametros,
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
