import logging
from typing import Any, Dict
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.analisis import Analisis
from src.models.evidencia import Evidencia
from src.models.lote import Lote, LoteStatus
from src.models.muestra import Muestra
from src.repositories.ficha_repository import FichaRepository

logger = logging.getLogger(__name__)


async def validar_requisitos_lote(
    db: AsyncSession,
    lote_id: str,
    org_id: int,
) -> Muestra:
    """Validar que el lote cumple los requisitos mínimos para generar una ficha."""
    result_lote = await db.execute(
        select(Lote).where(Lote.lote_id == lote_id)
    )
    lote = result_lote.scalar_one_or_none()

    if not lote:
        raise ValueError("LOTE_NOT_FOUND")

    if lote.org_id != org_id:
        raise ValueError("LOTE_NOT_FOUND")

    if lote.deleted_at is not None:
        raise ValueError("LOTE_NOT_FOUND")

    if lote.status not in (LoteStatus.ANALISIS_COMPLETO, LoteStatus.LISTO_PARA_COMPARTIR):
        raise ValueError("FICHA_ESTADO_NO_VALIDO")

    if not lote.variedad_id:
        raise ValueError("FICHA_SIN_VARIEDAD")

    if not lote.sub_variedad_id:
        raise ValueError("FICHA_SIN_SUBVARIEDAD")

    result_muestra = await db.execute(
        select(Muestra)
        .where(
            and_(
                Muestra.lote_id == lote_id,
                Muestra.estado == "tomada"
            )
        )
    )
    muestra = result_muestra.scalar_one_or_none()

    if not muestra:
        raise ValueError("FICHA_MUESTRA_NO_TOMADA")

    result_analisis = await db.execute(
        select(Analisis)
        .where(
            and_(
                Analisis.muestra_id == str(muestra.muestra_id),
                Analisis.estado == "completo"
            )
        )
    )
    analisis = result_analisis.scalar_one_or_none()

    if not analisis:
        raise ValueError("FICHA_ANALISIS_NO_COMPLETO")

    result_evidencias = await db.execute(
        select(func.count(Evidencia.evidencia_id))
        .where(
            Evidencia.metadatos['lote_id'].astext == str(lote_id),
            Evidencia.estado == 'activa'
        )
    )
    evidencias_count = result_evidencias.scalar() or 0

    if evidencias_count == 0:
        raise ValueError("FICHA_SIN_EVIDENCIAS")

    return muestra


async def generar_ficha(
    repo: FichaRepository,
    db: AsyncSession,
    lote_id: str,
    org_id: int,
    user_id: int,
    base_url: str = "https://agryflow.app",
) -> Dict[str, Any]:
    """Generar una ficha compartible para el lote."""
    existing_ficha = await repo.get_ficha_activa_por_lote(lote_id)
    if existing_ficha:
        link_publico = f"{base_url}/ficha/{existing_ficha.link_token}"
        return {"data": repo.to_response_dict(existing_ficha, link_publico)}

    muestra = await validar_requisitos_lote(db, lote_id, org_id)

    ficha = await repo.create(
        lote_id=lote_id,
        muestra_id=str(muestra.muestra_id),
        user_id=user_id,
    )

    result_lote = await db.execute(
        select(Lote).where(Lote.lote_id == lote_id)
    )
    lote = result_lote.scalar_one_or_none()
    if lote:
        lote.status = LoteStatus.LISTO_PARA_COMPARTIR
        lote.updated_by = user_id
        await db.commit()

    link_publico = f"{base_url}/ficha/{ficha.link_token}"
    return {"data": repo.to_response_dict(ficha, link_publico)}


async def get_ficha_publica(
    repo: FichaRepository,
    token: str,
) -> Dict[str, Any]:
    """Obtener datos públicos de una ficha por token."""
    ficha = await repo.get_por_token(token)

    if not ficha or ficha.estado != "activa":
        raise ValueError("FICHA_NOT_FOUND")

    datos = await repo.get_datos_publicos(str(ficha.lote_id))

    if not datos:
        raise ValueError("FICHA_NOT_FOUND")

    return {"data": datos}


async def get_ficha_autenticada(
    repo: FichaRepository,
    db: AsyncSession,
    ficha_id: str,
    org_id: int,
) -> Dict[str, Any]:
    """Obtener una ficha por ID (autenticado)."""
    ficha = await repo.get_por_id(ficha_id)

    if not ficha:
        raise ValueError("FICHA_NOT_FOUND")

    if not ficha.muestra or not ficha.muestra.lote:
        raise ValueError("FICHA_NOT_FOUND")

    if ficha.muestra.lote.org_id != org_id:
        raise ValueError("FICHA_NOT_FOUND")

    datos = await repo.get_datos_publicos(str(ficha.lote_id))
    link_publico = f"https://agryflow.app/ficha/{ficha.link_token}"

    return {
        "data": repo.to_response_dict(ficha, link_publico),
        "lote": datos.get("lote", {}),
        "muestra": datos.get("muestra", {})
    }