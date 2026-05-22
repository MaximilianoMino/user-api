import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
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
)
async def get_ficha_publica_endpoint(
    token: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    repo: FichaRepository = Depends(get_ficha_repository),
):
    """Vista pública de una ficha - sin autenticación."""
    try:
        datos = await ficha_service.get_ficha_publica(
            repo=repo,
            token=token,
        )
    except ValueError:
        accept = request.headers.get("accept", "")
        if "text/html" in accept:
            return HTMLResponse(
                content=ficha_service._render_ficha_404_html(),
                status_code=404,
            )
        raise HTTPException(status_code=404, detail="Ficha no encontrada o expirada")

    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return HTMLResponse(
            content=ficha_service._render_ficha_html(datos),
            status_code=200,
        )

    return JSONResponse(content={"data": datos})
