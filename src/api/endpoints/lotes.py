import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

logger = logging.getLogger(__name__)

from src.api.dependencies import get_current_user, get_org_id, get_lote_repository
from src.core.messages import ErrorMessages, SuccessMessages
from src.models.lote import (
    LoteCreate,
    LoteUpdate,
    LoteListResponse,
    LoteResponse,
    LoteDetailResponse,
)
from src.repositories.lote_repository import LoteRepository
from src.services.lote_service import (
    delete_lote,
    get_lote,
    list_lotes,
    create_lote,
    update_lote,
)

router = APIRouter()


@router.get("/lotes", response_model=LoteListResponse)
async def list_lotes_endpoint(
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_id: int = Depends(get_org_id),
    repo: LoteRepository = Depends(get_lote_repository),
    status: str = None,
    busqueda: str = None,
    skip: int = 0,
    limit: int = 20,
    sort_by: str = "created_at",
    order: str = "desc",
) -> LoteListResponse:
    """Listar lotes de la organización activa"""
    try:
        return await list_lotes(
            repo, org_id, status, busqueda, skip, limit, sort_by, order
        )
    except Exception as e:
        logger.warning(f"Error listing lotes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lotes", response_model=LoteResponse, status_code=201)
async def create_lote_endpoint(
    data: LoteCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_id: int = Depends(get_org_id),
    repo: LoteRepository = Depends(get_lote_repository),
) -> LoteResponse:
    """Crear un nuevo lote"""
    try:
        return await create_lote(repo, org_id, current_user["user_id"], data)
    except ValueError as e:
        error_code = str(e)
        if error_code == "VARIEDAD_NOT_FOUND":
            raise HTTPException(status_code=400, detail=ErrorMessages.VARIEDAD_NOT_FOUND)
        if error_code == "SUBVARIEDAD_INVALIDA":
            raise HTTPException(status_code=400, detail=ErrorMessages.SUBVARIEDAD_INVALIDA)
        if error_code == "TEMPORADA_NOT_FOUND":
            raise HTTPException(status_code=400, detail=ErrorMessages.TEMPORADA_NOT_FOUND)
        raise HTTPException(status_code=400, detail=error_code)


@router.get("/lotes/{lote_id}", response_model=LoteDetailResponse)
async def get_lote_endpoint(
    lote_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_id: int = Depends(get_org_id),
    repo: LoteRepository = Depends(get_lote_repository),
) -> LoteDetailResponse:
    """Obtener detalle de un lote"""
    try:
        lote = await get_lote(repo, org_id, lote_id)
        return {"data": lote}
    except ValueError:
        raise HTTPException(status_code=404, detail=ErrorMessages.LOTE_NOT_FOUND)


@router.patch("/lotes/{lote_id}", response_model=LoteResponse)
async def update_lote_endpoint(
    lote_id: str,
    data: LoteUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_id: int = Depends(get_org_id),
    repo: LoteRepository = Depends(get_lote_repository),
) -> LoteResponse:
    """Actualizar un lote"""
    try:
        return await update_lote(repo, org_id, current_user["user_id"], lote_id, data)
    except ValueError as e:
        error_code = str(e)
        if error_code == "LOTE_NOT_FOUND":
            raise HTTPException(status_code=404, detail=ErrorMessages.LOTE_NOT_FOUND)
        if error_code == "LOTE_NO_EDITABLE":
            raise HTTPException(status_code=409, detail=ErrorMessages.LOTE_NO_EDITABLE)
        if error_code == "LOTE_TIENE_MUESTRAS":
            raise HTTPException(status_code=409, detail=ErrorMessages.LOTE_TIENE_MUESTRAS)
        if error_code == "SUBVARIEDAD_INVALIDA":
            raise HTTPException(status_code=400, detail=ErrorMessages.SUBVARIEDAD_INVALIDA)
        if error_code == "TEMPORADA_NOT_FOUND":
            raise HTTPException(status_code=400, detail=ErrorMessages.TEMPORADA_NOT_FOUND)
        raise HTTPException(status_code=400, detail=error_code)


@router.delete("/lotes/{lote_id}")
async def delete_lote_endpoint(
    lote_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_id: int = Depends(get_org_id),
    repo: LoteRepository = Depends(get_lote_repository),
) -> Dict[str, str]:
    """Eliminar un lote (soft delete)"""
    try:
        await delete_lote(repo, org_id, lote_id)
        return {"message": SuccessMessages.LOTE_DELETED}
    except ValueError as e:
        error_code = str(e)
        if error_code == "LOTE_NOT_FOUND":
            raise HTTPException(status_code=404, detail=ErrorMessages.LOTE_NOT_FOUND)
        if error_code == "LOTE_DELETE_HAS_MUESTRAS":
            raise HTTPException(status_code=409, detail=ErrorMessages.LOTE_DELETE_HAS_MUESTRAS)