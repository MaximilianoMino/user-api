import logging
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_org_id, get_lote_repository
from src.core.database import get_db
from src.core.messages import ErrorMessages
from src.core.supabase_client import get_supabase_client
from src.models.documento import DocumentoConfirmRequest, DocumentoUploadUrlRequest
from src.repositories.documento_repository import DocumentoRepository
from src.repositories.lote_repository import LoteRepository
from src.services import documento_service
from supabase import Client

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_documento_repository(
    db: "AsyncSession" = Depends(get_db),
) -> DocumentoRepository:
    return DocumentoRepository(db)


@router.post(
    "/lotes/{lote_id}/documentos/upload-url",
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
async def generate_upload_url_endpoint(
    lote_id: UUID,
    data: DocumentoUploadUrlRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_id: int = Depends(get_org_id),
    supabase: Client = Depends(get_supabase_client),
) -> dict:
    try:
        return await documento_service.generate_upload_url(
            lote_id=str(lote_id),
            nombre_original=data.nombre_original,
            tipo_mime=data.tipo_mime,
            tamano_bytes=data.tamano_bytes,
            supabase_client=supabase,
        )
    except ValueError as e:
        error_code = str(e)
        if error_code == "CONTENT_TYPE_INVALIDO":
            raise HTTPException(status_code=400, detail=ErrorMessages.CONTENT_TYPE_INVALIDO)
        if error_code == "TAMANO_EXCEDIDO":
            raise HTTPException(status_code=400, detail=ErrorMessages.TAMANO_EXCEDIDO)
        if error_code == "BUCKET_NOT_FOUND":
            raise HTTPException(status_code=500, detail="Error al generar URL de subida")
        raise HTTPException(status_code=400, detail=error_code)


@router.post(
    "/lotes/{lote_id}/documentos",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
)
async def confirm_upload_endpoint(
    lote_id: UUID,
    data: DocumentoConfirmRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_id: int = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    supabase: Client = Depends(get_supabase_client),
    repo: DocumentoRepository = Depends(get_documento_repository),
    lote_repo: LoteRepository = Depends(get_lote_repository),
) -> dict:
    try:
        return await documento_service.confirm_upload(
            repo=repo,
            db=db,
            lote_repo=lote_repo,
            lote_id=str(lote_id),
            file_key=data.file_key,
            nombre_original=data.nombre_original,
            tipo_mime=data.tipo_mime,
            tamano_bytes=data.tamano_bytes,
            user_id=current_user["user_id"],
            org_id=org_id,
            supabase_client=supabase,
            categoria=data.categoria,
            descripcion=data.descripcion,
        )
    except ValueError as e:
        error_code = str(e)
        if error_code == "CONTENT_TYPE_INVALIDO":
            raise HTTPException(status_code=400, detail=ErrorMessages.CONTENT_TYPE_INVALIDO)
        if error_code == "TAMANO_EXCEDIDO":
            raise HTTPException(status_code=400, detail=ErrorMessages.TAMANO_EXCEDIDO)
        if error_code == "LOTE_NOT_FOUND":
            raise HTTPException(status_code=404, detail=ErrorMessages.LOTE_NOT_FOUND)
        raise HTTPException(status_code=400, detail=error_code)


@router.get(
    "/lotes/{lote_id}/documentos",
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
async def list_documentos_endpoint(
    lote_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_id: int = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    repo: DocumentoRepository = Depends(get_documento_repository),
    lote_repo: LoteRepository = Depends(get_lote_repository),
) -> dict:
    try:
        return await documento_service.list_documentos(
            repo=repo,
            db=db,
            lote_repo=lote_repo,
            lote_id=str(lote_id),
            org_id=org_id,
        )
    except ValueError as e:
        error_code = str(e)
        if error_code == "LOTE_NOT_FOUND":
            raise HTTPException(status_code=404, detail=ErrorMessages.LOTE_NOT_FOUND)
        raise HTTPException(status_code=400, detail=error_code)


@router.delete(
    "/documentos/{documento_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
async def delete_documento_endpoint(
    documento_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_id: int = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    repo: DocumentoRepository = Depends(get_documento_repository),
    lote_repo: LoteRepository = Depends(get_lote_repository),
) -> dict:
    try:
        return await documento_service.delete_documento(
            repo=repo,
            db=db,
            lote_repo=lote_repo,
            documento_id=str(documento_id),
            user_id=current_user["user_id"],
            org_id=org_id,
        )
    except ValueError as e:
        error_code = str(e)
        if error_code == "DOCUMENTO_NOT_FOUND":
            raise HTTPException(status_code=404, detail=ErrorMessages.DOCUMENTO_NOT_FOUND)
        raise HTTPException(status_code=400, detail=error_code)
