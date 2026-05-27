import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.core.database import get_db
from src.models.catalogo import VariedadResponse, SubVariedadResponse, TemporadaResponse, ParametroResponse, VariedadListResponse, SubVariedadListResponse, TemporadaListResponse, ParametroListResponse
from src.models.variedad import Variedad
from src.models.sub_variedad import SubVariedad
from src.models.temporada import Temporada
from src.models.parametro import Parametro
from src.models.otros import PlantillaParametro
from src.services.parametro_service import get_parametros_by_variedad

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/variedades", response_model=VariedadListResponse)
async def listar_variedades(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> dict:
    result = await db.execute(
        select(Variedad)
        .where(Variedad.activo == True)
        .order_by(Variedad.codigo)
    )
    variedades = result.scalars().all()
    return VariedadListResponse(data=[VariedadResponse.model_validate(v) for v in variedades])


@router.get("/subvariedades", response_model=SubVariedadListResponse)
async def listar_subvariedades(
    variedad_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> dict:
    query = select(SubVariedad).where(SubVariedad.activo == True)
    if variedad_id is not None:
        query = query.where(SubVariedad.variedad_id == variedad_id)
    query = query.order_by(SubVariedad.codigo)
    result = await db.execute(query)
    subvariedades = result.scalars().all()
    return SubVariedadListResponse(data=[SubVariedadResponse.model_validate(s) for s in subvariedades])


@router.get("/temporadas", response_model=TemporadaListResponse)
async def listar_temporadas(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> dict:
    current_year = datetime.now().year

    entries = []
    for offset in range(-2, 2):
        y = current_year + offset
        entries.append({"codigo": str(y), "anio_inicio": y, "anio_fin": y})
        entries.append({"codigo": f"{y}/{y + 1}", "anio_inicio": y, "anio_fin": y + 1})

    stmt = text(
        "INSERT INTO public.temporada (codigo, anio_inicio, anio_fin) "
        "VALUES (:codigo, :anio_inicio, :anio_fin) "
        "ON CONFLICT (codigo) DO NOTHING"
    )
    for e in entries:
        await db.execute(stmt, e)
    await db.commit()

    codigos = [e["codigo"] for e in entries]
    result = await db.execute(
        select(Temporada)
        .where(Temporada.codigo.in_(codigos))
        .order_by(Temporada.codigo)
    )
    temporadas = result.scalars().all()

    return TemporadaListResponse(data=[TemporadaResponse.model_validate(t) for t in temporadas])


@router.get("/variedades/{variedad_id}/parametros", response_model=ParametroListResponse)
async def listar_parametros_por_variedad(
    variedad_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Devolver parámetros relevantes para una variedad específica."""
    parametros = await get_parametros_by_variedad(db, variedad_id)
    return ParametroListResponse(data=[ParametroResponse.model_validate(p) for p in parametros])
