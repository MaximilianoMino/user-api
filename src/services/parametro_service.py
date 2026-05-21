from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.parametro import Parametro
from src.models.otros import PlantillaParametro

PRODUCTO_PRINCIPAL_PARAMETRO_ID = 46


async def get_parametros_by_variedad(db: AsyncSession, variedad_id: int) -> list:
    """Obtener parámetros relevantes para una variedad específica.

    Si no hay parámetros configurados en plantilla_parametro para la variedad,
    devuelve todos los parámetros activos como fallback.
    """
    stmt = (
        select(Parametro)
        .join(PlantillaParametro, Parametro.parametro_id == PlantillaParametro.parametro_id)
        .where(
            PlantillaParametro.variedad_id == variedad_id,
            PlantillaParametro.aplica == True,
            Parametro.parametro_id != PRODUCTO_PRINCIPAL_PARAMETRO_ID,
            Parametro.activo == True,
        )
        .order_by(Parametro.codigo)
    )
    result = await db.execute(stmt)
    parametros = list(result.scalars().all())

    if not parametros:
        fallback_stmt = (
            select(Parametro)
            .where(
                Parametro.activo == True,
                Parametro.parametro_id != PRODUCTO_PRINCIPAL_PARAMETRO_ID,
            )
            .order_by(Parametro.codigo)
        )
        fallback_result = await db.execute(fallback_stmt)
        parametros = list(fallback_result.scalars().all())

    return parametros
