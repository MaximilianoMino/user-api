import logging
import uuid
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from supabase import Client

from src.core.messages import ErrorMessages
from src.models.evidencia import CONTENT_TYPES_PERMITIDOS, TIPOS_VALIDOS
from src.repositories.evidencia_repository import EvidenciaRepository
from src.repositories.lote_repository import LoteRepository

logger = logging.getLogger(__name__)

STORAGE_BUCKET = "evidencias"


def _validate_tipo(tipo: str) -> None:
    if tipo not in TIPOS_VALIDOS:
        raise ValueError("TIPO_INVALIDO")


def _validate_content_type(content_type: str) -> None:
    if content_type not in CONTENT_TYPES_PERMITIDOS:
        raise ValueError("CONTENT_TYPE_INVALIDO")


def _get_extension(content_type: str) -> str:
    extensions = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "video/mp4": "mp4",
    }
    return extensions.get(content_type, "bin")


async def generate_upload_url(
    lote_id: str,
    tipo: str,
    content_type: str,
    supabase_client: Client,
) -> Dict[str, Any]:
    _validate_tipo(tipo)
    _validate_content_type(content_type)

    extension = _get_extension(content_type)
    file_key = f"lotes/{lote_id}/evidencias/{uuid.uuid4()}.{extension}"

    try:
        upload_result = supabase_client.storage.from_(STORAGE_BUCKET).create_signed_upload_url(
            file_key,
        )
    except Exception as e:
        logger.error(f"Error generating upload URL: {e}")
        raise ValueError("BUCKET_NOT_FOUND")

    upload_url = upload_result.get("url") or upload_result.get("signed_url")

    return {
        "data": {
            "upload_url": upload_url,
            "file_key": file_key,
        }
    }


async def confirm_upload(
    repo: EvidenciaRepository,
    db: AsyncSession,
    lote_repo: LoteRepository,
    lote_id: str,
    file_key: str,
    tipo: str,
    muestra_id: Optional[str],
    user_id: int,
    org_id: int,
    supabase_client: Client,
) -> Dict[str, Any]:
    _validate_tipo(tipo)

    lote = await lote_repo.get_by_id(lote_id)
    if not lote or lote.org_id != org_id:
        raise ValueError("LOTE_NOT_FOUND")

    if muestra_id:
        muestra = await lote_repo.get_muestra_by_id(lote_id, muestra_id)
        if not muestra:
            raise ValueError("MUESTRA_NOT_FOUND")

    try:
        url_result = supabase_client.storage.from_(STORAGE_BUCKET).get_public_url(file_key)
        url = url_result.get("publicUrl") or url_result.get("url") or f"{supabase_client.storage_url}/object/public/{STORAGE_BUCKET}/{file_key}"
    except Exception:
        url = f"{supabase_client.storage_url}/object/public/{STORAGE_BUCKET}/{file_key}"

    evidencia = await repo.create(
        evidencia_id=uuid.uuid4(),
        muestra_id=uuid.UUID(muestra_id) if muestra_id else None,
        tipo=tipo,
        url=url,
        created_by=user_id,
        metadatos={"file_key": file_key, "lote_id": lote_id},
    )

    return {
        "data": repo.to_response_dict(evidencia)
    }


async def list_evidencias(
    repo: EvidenciaRepository,
    db: AsyncSession,
    lote_repo: LoteRepository,
    lote_id: str,
    org_id: int,
) -> Dict[str, Any]:
    lote = await lote_repo.get_by_id(lote_id)
    if not lote or lote.org_id != org_id:
        raise ValueError("LOTE_NOT_FOUND")

    evidencias = await repo.list_by_lote(uuid.UUID(lote_id))

    return {
        "data": [repo.to_list_item_dict(e) for e in evidencias]
    }


async def delete_evidencia(
    repo: EvidenciaRepository,
    db: AsyncSession,
    lote_repo: LoteRepository,
    evidencia_id: str,
    user_id: int,
    org_id: int,
    supabase_client: Client,
) -> Dict[str, Any]:
    evidencia = await repo.get_by_id(uuid.UUID(evidencia_id))
    if not evidencia:
        raise ValueError("EVIDENCIA_NOT_FOUND")

    lote_id = None
    if evidencia.muestra and evidencia.muestra.lote_id:
        lote_id = str(evidencia.muestra.lote_id)
    else:
        lote_id = (evidencia.metadatos or {}).get("lote_id")

    if not lote_id:
        raise ValueError("EVIDENCIA_NOT_FOUND")

    lote = await lote_repo.get_by_id(lote_id)
    if not lote or lote.org_id != org_id:
        raise ValueError("EVIDENCIA_NOT_FOUND")

    updated = await repo.soft_delete(uuid.UUID(evidencia_id), user_id)
    if not updated:
        raise ValueError("EVIDENCIA_NOT_FOUND")

    return {
        "message": "Evidencia eliminada correctamente"
    }
