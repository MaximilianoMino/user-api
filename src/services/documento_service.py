import logging
import uuid
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from supabase import Client

from src.core.messages import ErrorMessages
from src.models.documento import (
    TIPO_MAX_SIZE_BYTES,
    es_content_type_valido,
    get_extension,
)
from src.repositories.documento_repository import DocumentoRepository
from src.repositories.lote_repository import LoteRepository

logger = logging.getLogger(__name__)

STORAGE_BUCKET = "documentos"


def _validate_content_type(content_type: str) -> None:
    if not es_content_type_valido(content_type):
        raise ValueError("CONTENT_TYPE_INVALIDO")


def _validate_tamano(tamano_bytes: int) -> None:
    if tamano_bytes > TIPO_MAX_SIZE_BYTES:
        raise ValueError("TAMANO_EXCEDIDO")


async def generate_upload_url(
    lote_id: str,
    nombre_original: str,
    tipo_mime: str,
    tamano_bytes: int,
    supabase_client: Client,
) -> Dict[str, Any]:
    _validate_content_type(tipo_mime)
    _validate_tamano(tamano_bytes)

    extension = get_extension(tipo_mime)
    file_key = f"lotes/{lote_id}/documentos/{uuid.uuid4()}.{extension}"

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
    repo: DocumentoRepository,
    db: AsyncSession,
    lote_repo: LoteRepository,
    lote_id: str,
    file_key: str,
    nombre_original: str,
    tipo_mime: str,
    tamano_bytes: int,
    user_id: int,
    org_id: int,
    supabase_client: Client,
    categoria: Optional[str] = None,
    descripcion: Optional[str] = None,
) -> Dict[str, Any]:
    _validate_content_type(tipo_mime)
    _validate_tamano(tamano_bytes)

    lote = await lote_repo.get_by_id(lote_id)
    if not lote or lote.org_id != org_id:
        raise ValueError("LOTE_NOT_FOUND")

    try:
        url_result = supabase_client.storage.from_(STORAGE_BUCKET).get_public_url(file_key)
        url = url_result.get("publicUrl") or url_result.get("url") or f"{supabase_client.storage_url}/object/public/{STORAGE_BUCKET}/{file_key}"
    except Exception:
        url = f"{supabase_client.storage_url}/object/public/{STORAGE_BUCKET}/{file_key}"

    extension = get_extension(tipo_mime)
    nombre_archivo = file_key.split("/")[-1]

    documento = await repo.create(
        lote_documento_id=uuid.uuid4(),
        lote_id=uuid.UUID(lote_id),
        nombre_original=nombre_original,
        nombre_archivo=nombre_archivo,
        tipo_mime=tipo_mime,
        extension=extension,
        url=url,
        tamano_bytes=tamano_bytes,
        created_by=user_id,
        categoria=categoria,
        descripcion=descripcion,
    )

    return {
        "data": repo.to_response_dict(documento)
    }


async def list_documentos(
    repo: DocumentoRepository,
    db: AsyncSession,
    lote_repo: LoteRepository,
    lote_id: str,
    org_id: int,
) -> Dict[str, Any]:
    lote = await lote_repo.get_by_id(lote_id)
    if not lote or lote.org_id != org_id:
        raise ValueError("LOTE_NOT_FOUND")

    documentos = await repo.list_by_lote(uuid.UUID(lote_id))

    return {
        "data": [repo.to_list_item_dict(d) for d in documentos]
    }


async def delete_documento(
    repo: DocumentoRepository,
    db: AsyncSession,
    lote_repo: LoteRepository,
    documento_id: str,
    user_id: int,
    org_id: int,
) -> Dict[str, Any]:
    documento = await repo.get_by_id(uuid.UUID(documento_id))
    if not documento:
        raise ValueError("DOCUMENTO_NOT_FOUND")

    lote_id = str(documento.lote_id)
    lote = await lote_repo.get_by_id(lote_id)
    if not lote or lote.org_id != org_id:
        raise ValueError("DOCUMENTO_NOT_FOUND")

    updated = await repo.soft_delete(uuid.UUID(documento_id), user_id)
    if not updated:
        raise ValueError("DOCUMENTO_NOT_FOUND")

    return {
        "message": "Documento eliminado correctamente"
    }
