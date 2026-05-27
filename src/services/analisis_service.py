import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.analisis import Analisis, AnalisisCreate, AnalisisUpdate
from src.models.lote import Lote
from src.models.muestra import Muestra, MuestraEstado
from src.models.parametro import Parametro
from src.repositories.analisis_repository import AnalisisRepository

logger = logging.getLogger(__name__)

PRODUCTO_PRINCIPAL_CODIGO = "producto_principal"


async def validate_muestra_for_analisis(
    db: AsyncSession,
    muestra_id: str,
    org_id: int,
) -> Muestra:
    """Validar que la muestra exista, pertenezca a la org, esté en estado tomada y no tenga análisis."""
    result = await db.execute(
        select(Muestra)
        .options(selectinload(Muestra.lote))
        .where(Muestra.muestra_id == muestra_id)
    )
    muestra = result.scalar_one_or_none()

    if not muestra:
        raise ValueError("MUESTRA_NOT_FOUND")

    if not muestra.lote or muestra.lote.org_id != org_id:
        raise ValueError("MUESTRA_NOT_FOUND")

    if muestra.estado != MuestraEstado.TOMADA:
        raise ValueError("MUESTRA_NO_TOMADA")

    return muestra


async def validate_parametros(
    repo: AnalisisRepository,
    parametros: list,
    peso_muestra: float,
) -> list:
    """Validar que los parámetros existan y sus valores estén en rango [0, peso_muestra]."""
    validated_results = []
    parametro_ids = []

    for param in parametros:
        parametro_ids.append(param.parametro_id)

    existing_parametros = {}
    for pid in set(parametro_ids):
        parametro = await repo.get_parametro_by_id(pid)
        if not parametro:
            raise ValueError(f"PARAMETRO_NOT_FOUND:{pid}")
        existing_parametros[pid] = parametro

    for param in parametros:
        if param.valor < 0:
            raise ValueError(f"VALOR_NEGATIVO:{param.parametro_id}")
        if param.valor > peso_muestra:
            raise ValueError(f"VALOR_FUERA_DE_RANGO:{param.parametro_id}:{peso_muestra}")

        parametro = existing_parametros[param.parametro_id]

        valor = param.valor
        if parametro.value_type == "porcentaje" and valor <= 100:
            valor = round((valor / 100) * peso_muestra, 2)

        validated_results.append({
            "parametro_id": param.parametro_id,
            "valor": valor,
            "unidad": parametro.unidad_default,
            "comentario": param.comentario,
        })

    return validated_results


async def create_analisis(
    repo: AnalisisRepository,
    db: AsyncSession,
    muestra_id: str,
    org_id: int,
    user_id: int,
    data: AnalisisCreate,
) -> Dict[str, Any]:
    """Crear un análisis completo con sus parámetros."""
    muestra = await validate_muestra_for_analisis(db, muestra_id, org_id)

    peso_muestra = float(muestra.peso_muestra)

    if await repo.has_analisis_for_muestra(muestra_id):
        raise ValueError("ANALISIS_YA_EXISTE")

    validated_results = await validate_parametros(repo, data.parametros, peso_muestra)

    suma_valores = sum(r["valor"] for r in validated_results)

    if suma_valores > peso_muestra:
        raise ValueError(f"SUMA_EXCEDE_PESO:{suma_valores}:{peso_muestra}")

    if suma_valores <= peso_muestra:
        producto_principal_param = await repo.get_parametro_by_codigo(PRODUCTO_PRINCIPAL_CODIGO)
        if not producto_principal_param:
            raise ValueError("PARAMETRO_PRODUCTO_PRINCIPAL_NO_EXISTE")

        diferencia = peso_muestra - suma_valores
        validated_results.append({
            "parametro_id": producto_principal_param.parametro_id,
            "valor": diferencia,
            "unidad": producto_principal_param.unidad_default or "g",
            "comentario": "Ajuste automático",
        })
        suma_valores += diferencia

    async with db.begin_nested():
        analisis = await repo.create(
            muestra_id=muestra_id,
            estado="completo",
            created_by=user_id,
            updated_by=user_id,
            resultados=validated_results,
            observaciones_generales=None,
            fecha_completado=datetime.utcnow(),
        )

        result_lote = await db.execute(
            select(Lote).where(Lote.lote_id == str(muestra.lote_id))
        )
        lote = result_lote.scalar_one_or_none()
        if lote:
            lote.status = "analisis_completo"
            lote.updated_by = user_id

    return {"data": await repo.to_response_dict(analisis, peso_muestra)}


async def get_analisis_by_muestra(
    repo: AnalisisRepository,
    db: AsyncSession,
    muestra_id: str,
    org_id: int,
) -> Dict[str, Any]:
    """Obtener el análisis asociado a una muestra."""
    result_muestra = await db.execute(
        select(Muestra)
        .options(selectinload(Muestra.lote))
        .where(Muestra.muestra_id == muestra_id)
    )
    muestra = result_muestra.scalar_one_or_none()

    if not muestra or not muestra.lote or muestra.lote.org_id != org_id:
        raise ValueError("MUESTRA_NOT_FOUND")

    peso_muestra = float(muestra.peso_muestra) if muestra.peso_muestra else 0.0

    analisis = await repo.get_by_muestra_id(muestra_id)
    if not analisis:
        raise ValueError("ANALISIS_NOT_FOUND")

    return {"data": await repo.to_response_dict(analisis, peso_muestra)}


async def get_analisis(
    repo: AnalisisRepository,
    db: AsyncSession,
    analisis_id: str,
    org_id: int,
) -> Dict[str, Any]:
    """Obtener el detalle de un análisis."""
    analisis = await repo.get_by_id(analisis_id)

    if not analisis:
        raise ValueError("ANALISIS_NOT_FOUND")

    result_muestra = await db.execute(
        select(Muestra)
        .options(selectinload(Muestra.lote))
        .where(Muestra.muestra_id == str(analisis.muestra_id))
    )
    muestra = result_muestra.scalar_one_or_none()

    if not muestra or not muestra.lote or muestra.lote.org_id != org_id:
        raise ValueError("ANALISIS_NOT_FOUND")

    peso_muestra = float(muestra.peso_muestra) if muestra.peso_muestra else 0.0

    return {"data": await repo.to_response_dict(analisis, peso_muestra)}


async def update_analisis(
    repo: AnalisisRepository,
    db: AsyncSession,
    analisis_id: str,
    org_id: int,
    user_id: int,
    data: AnalisisUpdate,
) -> Dict[str, Any]:
    """Actualizar observaciones de un análisis."""
    analisis = await repo.get_by_id(analisis_id)

    if not analisis:
        raise ValueError("ANALISIS_NOT_FOUND")

    result_muestra = await db.execute(
        select(Muestra)
        .options(selectinload(Muestra.lote))
        .where(Muestra.muestra_id == str(analisis.muestra_id))
    )
    muestra = result_muestra.scalar_one_or_none()

    if not muestra or not muestra.lote or muestra.lote.org_id != org_id:
        raise ValueError("ANALISIS_NOT_FOUND")

    peso_muestra = float(muestra.peso_muestra) if muestra.peso_muestra else 0.0

    updated_analisis = await repo.update(
        analisis_id=analisis_id,
        observaciones_generales=data.observaciones_generales,
        updated_by=user_id,
    )

    return {"data": await repo.to_response_dict(updated_analisis, peso_muestra)}