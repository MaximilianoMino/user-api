import logging
from typing import Any, Dict, Optional

from src.models.lote import LoteCreate, LoteUpdate
from src.repositories.lote_repository import LoteRepository

logger = logging.getLogger(__name__)


async def list_lotes(
    repo: LoteRepository,
    org_id: int,
    status: Optional[str] = None,
    busqueda: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    sort_by: str = "created_at",
    order: str = "desc",
) -> Dict[str, Any]:
    """Listar lotes con filtros y paginación"""
    return await repo.list_lotes(
        org_id=org_id,
        status=status,
        busqueda=busqueda,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        order=order,
    )


async def create_lote(
    repo: LoteRepository,
    org_id: int,
    user_id: int,
    data: LoteCreate,
) -> Dict[str, Any]:
    """Crear un nuevo lote"""
    if not await repo.check_variedad_exists(data.variedad_id):
        raise ValueError("VARIEDAD_NOT_FOUND")

    if data.sub_variedad_id:
        if not await repo.check_subvariedad_valid(data.sub_variedad_id, data.variedad_id):
            raise ValueError("SUBVARIEDAD_INVALIDA")

    if data.temporada_id:
        if not await repo.check_temporada_exists(data.temporada_id):
            raise ValueError("TEMPORADA_NOT_FOUND")

    data_dict = data.model_dump()
    data_dict["estado_mercaderia"] = data.estado_mercaderia.value if hasattr(data.estado_mercaderia, 'value') else data.estado_mercaderia

    lote = await repo.create_lote(org_id, user_id, data_dict)

    return await repo._to_dict_with_muestras(lote)


async def get_lote(
    repo: LoteRepository,
    org_id: int,
    lote_id: str,
) -> Dict[str, Any]:
    """Obtener detalle de un lote"""
    return await repo.get_lote_dict(org_id, lote_id)


async def update_lote(
    repo: LoteRepository,
    org_id: int,
    user_id: int,
    lote_id: str,
    data: LoteUpdate,
) -> Dict[str, Any]:
    """Actualizar un lote"""
    lote = await repo.get_lote_for_update(org_id, lote_id)

    if lote.status != "borrador":
        raise ValueError("LOTE_NO_EDITABLE")

    muestras_count = await repo.count_muestras(lote_id)
    update_data = data.model_dump(exclude_none=True)

    if update_data.get("volumen_estimado") is not None and muestras_count > 0:
        raise ValueError("LOTE_TIENE_MUESTRAS")

    if update_data.get("sub_variedad_id"):
        if not await repo.check_subvariedad_valid(update_data["sub_variedad_id"], lote.variedad_id):
            raise ValueError("SUBVARIEDAD_INVALIDA")

    if update_data.get("temporada_id"):
        if not await repo.check_temporada_exists(update_data["temporada_id"]):
            raise ValueError("TEMPORADA_NOT_FOUND")

    if update_data.get("estado_mercaderia"):
        update_data["estado_mercaderia"] = update_data["estado_mercaderia"].value if hasattr(update_data["estado_mercaderia"], 'value') else update_data["estado_mercaderia"]

    updated_lote = await repo.update_lote(org_id, lote_id, user_id, update_data)

    return await repo._to_dict_with_muestras(updated_lote)


async def delete_lote(
    repo: LoteRepository,
    org_id: int,
    lote_id: str,
) -> Dict[str, Any]:
    """Soft delete de un lote"""
    lote = await repo.get_lote_for_update(org_id, lote_id)

    muestras_count = await repo.count_muestras(lote_id)
    if muestras_count > 0:
        raise ValueError("LOTE_DELETE_HAS_MUESTRAS")

    await repo.delete_lote(lote_id)
    return {"message": "Lote eliminado correctamente"}