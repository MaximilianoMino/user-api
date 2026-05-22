import logging
import os
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_org_id
from src.core.database import get_db
from src.core.messages import ErrorMessages
from src.repositories.ficha_repository import FichaRepository
from src.services import ficha_service

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_ficha_repository(
    db: "AsyncSession" = Depends(get_db),
) -> FichaRepository:
    """Dependency to get FichaRepository instance."""
    return FichaRepository(db)


@router.post(
    "/lotes/{lote_id}/ficha",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
)
async def create_ficha_endpoint(
    lote_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_id: int = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    repo: FichaRepository = Depends(get_ficha_repository),
) -> dict:
    """Generar una ficha compartible para el lote."""
    try:
        return await ficha_service.generar_ficha(
            repo=repo,
            db=db,
            lote_id=str(lote_id),
            org_id=org_id,
            user_id=current_user["user_id"],
            base_url=os.getenv("BASE_URL", "https://agryflow-app.vercel.app"),
        )
    except ValueError as e:
        error_code = str(e)
        if error_code == "LOTE_NOT_FOUND":
            raise HTTPException(status_code=404, detail=ErrorMessages.LOTE_NOT_FOUND)
        if error_code == "FICHA_ESTADO_NO_VALIDO":
            raise HTTPException(status_code=400, detail=ErrorMessages.FICHA_ESTADO_NO_VALIDO)
        if error_code == "FICHA_MUESTRA_NO_TOMADA":
            raise HTTPException(status_code=400, detail=ErrorMessages.FICHA_MUESTRA_NO_TOMADA)
        if error_code == "FICHA_ANALISIS_NO_COMPLETO":
            raise HTTPException(status_code=400, detail=ErrorMessages.FICHA_ANALISIS_NO_COMPLETO)
        if error_code == "FICHA_SIN_EVIDENCIAS":
            raise HTTPException(status_code=400, detail=ErrorMessages.FICHA_SIN_EVIDENCIAS)
        if error_code == "FICHA_SIN_VARIEDAD":
            raise HTTPException(status_code=400, detail=ErrorMessages.FICHA_SIN_VARIEDAD)
        if error_code == "FICHA_SIN_SUBVARIEDAD":
            raise HTTPException(status_code=400, detail=ErrorMessages.FICHA_SIN_SUBVARIEDAD)
        raise HTTPException(status_code=400, detail=error_code)


@router.get(
    "/fichas/{ficha_id}",
    response_model=dict,
)
async def get_ficha_endpoint(
    ficha_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_id: int = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    repo: FichaRepository = Depends(get_ficha_repository),
) -> dict:
    """Consultar una ficha existente."""
    try:
        return await ficha_service.get_ficha_autenticada(
            repo=repo,
            db=db,
            ficha_id=str(ficha_id),
            org_id=org_id,
            base_url=os.getenv("BASE_URL", "https://agryflow-app.vercel.app"),
        )
    except ValueError:
        raise HTTPException(status_code=404, detail=ErrorMessages.FICHA_NOT_FOUND)