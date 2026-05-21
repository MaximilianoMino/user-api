import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.ficha_repository import FichaRepository
from src.services import ficha_service

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_ficha_repository(
    db: "AsyncSession" = Depends(get_db),
) -> FichaRepository:
    """Dependency to get FichaRepository instance."""
    return FichaRepository(db)


@router.get(
    "/public/ficha/{token}",
    response_model=dict,
)
async def get_ficha_publica_endpoint(
    token: str,
    db: AsyncSession = Depends(get_db),
    repo: FichaRepository = Depends(get_ficha_repository),
) -> dict:
    """Vista pública de una ficha - sin autenticación."""
    try:
        return await ficha_service.get_ficha_publica(
            repo=repo,
            token=token,
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Ficha no encontrada o expirada")