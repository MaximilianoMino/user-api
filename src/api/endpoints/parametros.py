import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.core.database import get_db
from src.models.parametro import Parametro
from src.models.catalogo import ParametroResponse, ParametroListResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/parametros", response_model=ParametroListResponse)
async def listar_parametros(
    activo: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Listar parámetros de análisis, opcionalmente filtrados por activo."""
    query = select(Parametro)
    if activo is not None:
        query = query.where(Parametro.activo == activo)
    query = query.order_by(Parametro.codigo)
    result = await db.execute(query)
    parametros = result.scalars().all()
    return ParametroListResponse(data=[ParametroResponse.model_validate(p) for p in parametros])
