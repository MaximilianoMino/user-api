import logging
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_org_id, get_lote_repository
from src.core.database import get_db
from src.core.messages import ErrorMessages
from src.core.supabase_client import get_supabase_client
from src.models.evidencia import EvidenciaConfirmRequest, EvidenciaUploadUrlRequest
from src.repositories.evidencia_repository import EvidenciaRepository
from src.repositories.lote_repository import LoteRepository
from src.services import evidencia_service
from supabase import Client

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_evidencia_repository(
    db: "AsyncSession" = Depends(get_db),
) -> EvidenciaRepository:
    return EvidenciaRepository(db)


@router.post(
    "/lotes/{lote_id}/evidencias/upload-url",
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
async def generate_upload_url_endpoint(
    lote_id: UUID,
    data: EvidenciaUploadUrlRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_id: int = Depends(get_org_id),
    supabase: Client = Depends(get_supabase_client),
) -> dict:
    try:
        return await evidencia_service.generate_upload_url(
            lote_id=str(lote_id),
            tipo=data.tipo,
            content_type=data.content_type,
            supabase_client=supabase,
        )
    except ValueError as e:
        error_code = str(e)
        if error_code == "TIPO_INVALIDO":
            raise HTTPException(status_code=400, detail=ErrorMessages.TIPO_INVALIDO)
        if error_code == "CONTENT_TYPE_INVALIDO":
            raise HTTPException(status_code=400, detail=ErrorMessages.CONTENT_TYPE_INVALIDO)
        if error_code == "BUCKET_NOT_FOUND":
            raise HTTPException(status_code=500, detail="Error al generar URL de subida")
        raise HTTPException(status_code=400, detail=error_code)


@router.post(
    "/lotes/{lote_id}/evidencias",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
)
async def confirm_upload_endpoint(
    lote_id: UUID,
    data: EvidenciaConfirmRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_id: int = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    supabase: Client = Depends(get_supabase_client),
    repo: EvidenciaRepository = Depends(get_evidencia_repository),
    lote_repo: LoteRepository = Depends(get_lote_repository),
) -> dict:
    try:
        return await evidencia_service.confirm_upload(
            repo=repo,
            db=db,
            lote_repo=lote_repo,
            lote_id=str(lote_id),
            file_key=data.file_key,
            tipo=data.tipo,
            muestra_id=str(data.muestra_id) if data.muestra_id else None,
            user_id=current_user["user_id"],
            org_id=org_id,
            supabase_client=supabase,
        )
    except ValueError as e:
        error_code = str(e)
        if error_code == "TIPO_INVALIDO":
            raise HTTPException(status_code=400, detail=ErrorMessages.TIPO_INVALIDO)
        if error_code == "LOTE_NOT_FOUND":
            raise HTTPException(status_code=404, detail=ErrorMessages.LOTE_NOT_FOUND)
        if error_code == "MUESTRA_NOT_FOUND":
            raise HTTPException(status_code=404, detail=ErrorMessages.MUESTRA_NOT_FOUND)
        raise HTTPException(status_code=400, detail=error_code)


@router.get(
    "/lotes/{lote_id}/evidencias",
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
async def list_evidencias_endpoint(
    lote_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_id: int = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    repo: EvidenciaRepository = Depends(get_evidencia_repository),
    lote_repo: LoteRepository = Depends(get_lote_repository),
) -> dict:
    try:
        return await evidencia_service.list_evidencias(
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
    "/evidencias/{evidencia_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
async def delete_evidencia_endpoint(
    evidencia_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_id: int = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    repo: EvidenciaRepository = Depends(get_evidencia_repository),
    lote_repo: LoteRepository = Depends(get_lote_repository),
    supabase: Client = Depends(get_supabase_client),
) -> dict:
    try:
        return await evidencia_service.delete_evidencia(
            repo=repo,
            db=db,
            lote_repo=lote_repo,
            evidencia_id=str(evidencia_id),
            user_id=current_user["user_id"],
            org_id=org_id,
            supabase_client=supabase,
        )
    except ValueError as e:
        error_code = str(e)
        if error_code == "EVIDENCIA_NOT_FOUND":
            raise HTTPException(status_code=404, detail=ErrorMessages.EVIDENCIA_NOT_FOUND)
        raise HTTPException(status_code=400, detail=error_code)
