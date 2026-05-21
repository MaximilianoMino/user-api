import logging
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_org_id
from src.core.database import get_db
from src.core.messages import ErrorMessages
from src.models.muestra import MuestraCreate, MuestraUpdate
from src.repositories.muestra_repository import MuestraRepository
from src.services.muestra_service import create_muestra, get_muestra, update_muestra

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_muestra_repository(
    db: "AsyncSession" = Depends(get_db),
) -> MuestraRepository:
    """Dependency to get MuestraRepository instance."""
    return MuestraRepository(db)


@router.post(
    "/lotes/{lote_id}/muestras",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
)
async def create_muestra_endpoint(
    lote_id: UUID,
    data: MuestraCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_id: int = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    repo: MuestraRepository = Depends(get_muestra_repository),
) -> dict:
    """Registrar una nueva muestra para el lote especificado."""
    try:
        return await create_muestra(
            repo=repo,
            db=db,
            lote_id=str(lote_id),
            org_id=org_id,
            user_id=current_user["user_id"],
            data=data,
        )
    except ValueError as e:
        error_code = str(e)
        if error_code == "LOTE_NOT_FOUND":
            raise HTTPException(status_code=404, detail=ErrorMessages.LOTE_NOT_FOUND)
        if error_code == "LOTE_NO_EDITABLE":
            raise HTTPException(status_code=409, detail=ErrorMessages.LOTE_NO_EDITABLE)
        if error_code == "CONTEXTO_INVALIDO":
            raise HTTPException(
                status_code=400,
                detail="El contexto debe ser uno de: big_bags, bolsas, granel, silo_metalico, silobolsa"
            )
        if error_code == "UNIDAD_PESO_INVALIDA":
            raise HTTPException(
                status_code=400,
                detail="La unidad de peso solo puede ser 'g' o 'kg'"
            )
        raise HTTPException(status_code=400, detail=error_code)


@router.get(
    "/muestras/{muestra_id}",
    response_model=dict,
)
async def get_muestra_endpoint(
    muestra_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_id: int = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    repo: MuestraRepository = Depends(get_muestra_repository),
) -> dict:
    """Obtener el detalle de una muestra."""
    try:
        return await get_muestra(
            repo=repo,
            db=db,
            muestra_id=str(muestra_id),
            org_id=org_id,
        )
    except ValueError:
        raise HTTPException(status_code=404, detail=ErrorMessages.MUESTRA_NOT_FOUND)


@router.patch(
    "/muestras/{muestra_id}",
    response_model=dict,
)
async def update_muestra_endpoint(
    muestra_id: UUID,
    data: MuestraUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_id: int = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    repo: MuestraRepository = Depends(get_muestra_repository),
) -> dict:
    """Actualizar campos editables de una muestra."""
    try:
        return await update_muestra(
            repo=repo,
            db=db,
            muestra_id=str(muestra_id),
            org_id=org_id,
            user_id=current_user["user_id"],
            data=data,
        )
    except ValueError as e:
        error_code = str(e)
        if error_code == "MUESTRA_NOT_FOUND":
            raise HTTPException(status_code=404, detail=ErrorMessages.MUESTRA_NOT_FOUND)
        raise HTTPException(status_code=400, detail=error_code)