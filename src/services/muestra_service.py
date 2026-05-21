import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.lote import Lote
from src.models.muestra import Muestra, MuestraCreate, MuestraUpdate
from src.repositories.muestra_repository import MuestraRepository

logger = logging.getLogger(__name__)


async def validate_lote_for_muestra(
    db: AsyncSession,
    lote_id: str,
    org_id: int,
) -> Lote:
    """Validar que el lote existe, pertenece a la org y está en estado editable."""
    result = await db.execute(
        select(Lote).where(
            Lote.lote_id == lote_id,
            Lote.org_id == org_id,
            Lote.deleted_at.is_(None)
        )
    )
    lote = result.scalar_one_or_none()

    if not lote:
        raise ValueError("LOTE_NOT_FOUND")

    if lote.status not in ("borrador", "muestreo_tomado"):
        raise ValueError("LOTE_NO_EDITABLE")

    return lote


async def create_muestra(
    repo: MuestraRepository,
    db: AsyncSession,
    lote_id: str,
    org_id: int,
    user_id: int,
    data: MuestraCreate,
) -> Dict[str, Any]:
    """Crear una nueva muestra y transicionar el estado del lote."""
    lote = await validate_lote_for_muestra(db, lote_id, org_id)

    muestra = await repo.create(
        lote_id=lote_id,
        peso_muestra=data.peso_muestra,
        unidad_peso=data.unidad_peso,
        contexto=data.contexto,
        observaciones=data.observaciones,
        user_id=user_id,
    )

    if lote.status == "borrador":
        lote.status = "muestreo_tomado"
        lote.updated_by = user_id
        await db.commit()

    return {"data": repo.to_dict_with_lote(muestra)}


async def get_muestra(
    repo: MuestraRepository,
    db: AsyncSession,
    muestra_id: str,
    org_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Obtener el detalle de una muestra."""
    muestra = await repo.get_by_id(muestra_id)

    if not muestra:
        raise ValueError("MUESTRA_NOT_FOUND")

    if org_id is not None:
        result_lote = await db.execute(
            select(Lote).where(Lote.lote_id == str(muestra.lote_id))
        )
        lote = result_lote.scalar_one_or_none()
        if not lote or lote.org_id != org_id:
            raise ValueError("MUESTRA_NOT_FOUND")

    return {"data": repo.to_dict_with_lote(muestra)}


async def update_muestra(
    repo: MuestraRepository,
    db: AsyncSession,
    muestra_id: str,
    org_id: int,
    user_id: int,
    data: MuestraUpdate,
) -> Dict[str, Any]:
    """Actualizar una muestra (solo observaciones)."""
    muestra = await repo.get_by_id(muestra_id)

    if not muestra:
        raise ValueError("MUESTRA_NOT_FOUND")

    result_lote = await db.execute(
        select(Lote).where(Lote.lote_id == str(muestra.lote_id))
    )
    lote = result_lote.scalar_one_or_none()
    if not lote or lote.org_id != org_id:
        raise ValueError("MUESTRA_NOT_FOUND")

    updated_muestra = await repo.update_observaciones(
        muestra_id=muestra_id,
        observaciones=data.observaciones,
        user_id=user_id,
    )

    return {"data": repo.to_dict_with_lote(updated_muestra)}