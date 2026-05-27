import logging
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_org_id
from src.core.database import get_db
from src.core.messages import ErrorMessages
from src.models.analisis import AnalisisCreate, AnalisisUpdate
from src.repositories.analisis_repository import AnalisisRepository
from src.services import analisis_service

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_analisis_repository(
    db: "AsyncSession" = Depends(get_db),
) -> AnalisisRepository:
    """Dependency to get AnalisisRepository instance."""
    return AnalisisRepository(db)


@router.post(
    "/muestras/{muestra_id}/analisis",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
)
async def create_analisis_endpoint(
    muestra_id: UUID,
    data: AnalisisCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_id: int = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    repo: AnalisisRepository = Depends(get_analisis_repository),
) -> dict:
    """Crear un nuevo análisis para la muestra especificada."""
    try:
        result = await analisis_service.create_analisis(
            repo=repo,
            db=db,
            muestra_id=str(muestra_id),
            org_id=org_id,
            user_id=current_user["user_id"],
            data=data,
        )
        await db.commit()
        return result
    except ValueError as e:
        error_code = str(e)
        if error_code.startswith("PARAMETRO_NOT_FOUND:"):
            param_id = error_code.split(":")[1]
            raise HTTPException(
                status_code=400,
                detail=f"El parámetro con ID {param_id} no existe"
            )
        if error_code.startswith("VALOR_NEGATIVO:"):
            param_id = error_code.split(":")[1]
            raise HTTPException(
                status_code=400,
                detail=f"El valor para el parámetro {param_id} debe ser mayor o igual a 0"
            )
        if error_code.startswith("VALOR_FUERA_DE_RANGO:"):
            parts = error_code.split(":")
            param_id = parts[1]
            peso = parts[2]
            raise HTTPException(
                status_code=400,
                detail=f"El valor para el parámetro {param_id} debe estar entre 0 y el peso de la muestra ({peso} g)"
            )
        if error_code.startswith("SUMA_EXCEDE_PESO:"):
            parts = error_code.split(":")
            suma = parts[1]
            peso = parts[2]
            raise HTTPException(
                status_code=400,
                detail=f"La suma de los valores ({suma}) supera el peso de la muestra ({peso})"
            )
        if error_code == "ANALISIS_YA_EXISTE":
            raise HTTPException(
                status_code=400,
                detail=ErrorMessages.ANALISIS_YA_EXISTE
            )
        if error_code == "MUESTRA_NOT_FOUND":
            raise HTTPException(status_code=404, detail=ErrorMessages.MUESTRA_NOT_FOUND)
        if error_code == "MUESTRA_NO_TOMADA":
            raise HTTPException(
                status_code=409,
                detail="La muestra no está en estado 'tomada'"
            )
        if error_code == "PARAMETRO_PRODUCTO_PRINCIPAL_NO_EXISTE":
            raise HTTPException(
                status_code=500,
                detail="El parámetro 'producto_principal' no existe en la tabla parametro"
            )
        raise HTTPException(status_code=400, detail=error_code)


@router.get(
    "/muestras/{muestra_id}/analisis",
    response_model=dict,
)
async def get_analisis_by_muestra_endpoint(
    muestra_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_id: int = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    repo: AnalisisRepository = Depends(get_analisis_repository),
) -> dict:
    """Obtener el análisis asociado a una muestra."""
    try:
        return await analisis_service.get_analisis_by_muestra(
            repo=repo,
            db=db,
            muestra_id=str(muestra_id),
            org_id=org_id,
        )
    except ValueError as e:
        error_code = str(e)
        if error_code == "MUESTRA_NOT_FOUND":
            raise HTTPException(status_code=404, detail=ErrorMessages.MUESTRA_NOT_FOUND)
        if error_code == "ANALISIS_NOT_FOUND":
            raise HTTPException(status_code=404, detail=ErrorMessages.ANALISIS_NOT_FOUND)
        raise HTTPException(status_code=404, detail="Análisis no encontrado")


@router.get(
    "/analisis/{analisis_id}",
    response_model=dict,
)
async def get_analisis_endpoint(
    analisis_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_id: int = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    repo: AnalisisRepository = Depends(get_analisis_repository),
) -> dict:
    """Obtener el detalle de un análisis."""
    try:
        return await analisis_service.get_analisis(
            repo=repo,
            db=db,
            analisis_id=str(analisis_id),
            org_id=org_id,
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")


@router.patch(
    "/analisis/{analisis_id}",
    response_model=dict,
)
async def update_analisis_endpoint(
    analisis_id: UUID,
    data: AnalisisUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_id: int = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    repo: AnalisisRepository = Depends(get_analisis_repository),
) -> dict:
    """Actualizar observaciones de un análisis."""
    try:
        return await analisis_service.update_analisis(
            repo=repo,
            db=db,
            analisis_id=str(analisis_id),
            org_id=org_id,
            user_id=current_user["user_id"],
            data=data,
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")