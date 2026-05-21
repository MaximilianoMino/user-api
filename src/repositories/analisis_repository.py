import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.analisis import Analisis
from src.models.analisis_resultado import AnalisisResultado
from src.models.parametro import Parametro
from src.models.muestra import Muestra
from src.models.lote import Lote


class AnalisisRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_parametro_by_id(self, parametro_id: int) -> Optional[Parametro]:
        """Obtener un parámetro por ID."""
        result = await self.db.execute(
            select(Parametro).where(Parametro.parametro_id == parametro_id)
        )
        return result.scalar_one_or_none()

    async def get_parametro_by_codigo(self, codigo: str) -> Optional[Parametro]:
        """Obtener un parámetro por código."""
        result = await self.db.execute(
            select(Parametro).where(Parametro.codigo == codigo)
        )
        return result.scalar_one_or_none()

    async def has_analisis_for_muestra(self, muestra_id: str) -> bool:
        """Verificar si ya existe un análisis para la muestra."""
        result = await self.db.execute(
            select(func.count(Analisis.analisis_id))
            .where(
                Analisis.muestra_id == muestra_id,
                Analisis.estado == "completo"
            )
        )
        count = result.scalar()
        return count > 0

    async def create(
        self,
        muestra_id: str,
        estado: str,
        created_by: int,
        updated_by: int,
        resultados: List[Dict[str, Any]],
        observaciones_generales: Optional[str] = None,
        fecha_completado: Optional[datetime] = None,
    ) -> Analisis:
        """Crear un análisis con sus resultados."""
        analisis = Analisis(
            analisis_id=uuid.uuid4(),
            muestra_id=muestra_id,
            estado=estado,
            created_by=created_by,
            updated_by=updated_by,
            observaciones_generales=observaciones_generales,
            fecha_completado=fecha_completado,
        )
        self.db.add(analisis)

        for resultado in resultados:
            analisis_resultado = AnalisisResultado(
                resultado_id=uuid.uuid4(),
                analisis_id=analisis.analisis_id,
                parametro_id=resultado["parametro_id"],
                valor=resultado["valor"],
                unidad=resultado.get("unidad"),
                comentario=resultado.get("comentario"),
            )
            self.db.add(analisis_resultado)

        await self.db.commit()
        await self.db.refresh(analisis)
        return analisis

    async def get_by_muestra_id(self, muestra_id: str) -> Optional[Analisis]:
        """Obtener un análisis por muestra_id con sus resultados y relaciones."""
        result = await self.db.execute(
            select(Analisis)
            .options(
                selectinload(Analisis.resultados).selectinload(AnalisisResultado.parametro),
                selectinload(Analisis.muestra)
                    .selectinload(Muestra.lote)
                    .selectinload(Lote.variedad),
            )
            .where(Analisis.muestra_id == muestra_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, analisis_id: str) -> Optional[Analisis]:
        """Obtener un análisis por ID con sus resultados y relaciones."""
        result = await self.db.execute(
            select(Analisis)
            .options(
                selectinload(Analisis.resultados).selectinload(AnalisisResultado.parametro),
                selectinload(Analisis.muestra)
                    .selectinload(Muestra.lote)
                    .selectinload(Lote.variedad),
            )
            .where(Analisis.analisis_id == analisis_id)
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        analisis_id: str,
        observaciones_generales: Optional[str],
        updated_by: int,
    ) -> Optional[Analisis]:
        """Actualizar observaciones de un análisis."""
        analisis = await self.get_by_id(analisis_id)
        if analisis:
            analisis.observaciones_generales = observaciones_generales
            analisis.updated_by = updated_by
            await self.db.commit()
            await self.db.refresh(analisis)
        return analisis

    async def to_response_dict(self, analisis: Analisis, peso_muestra: float) -> Dict[str, Any]:
        """Convertir modelo Analisis a dict para response."""
        stmt = (
            select(AnalisisResultado)
            .options(selectinload(AnalisisResultado.parametro))
            .where(AnalisisResultado.analisis_id == analisis.analisis_id)
        )
        result = await self.db.execute(stmt)
        resultados = result.scalars().all()

        stmt_m = (
            select(Muestra)
            .options(selectinload(Muestra.lote).selectinload(Lote.variedad))
            .where(Muestra.muestra_id == analisis.muestra_id)
        )
        result_m = await self.db.execute(stmt_m)
        muestra = result_m.scalar_one_or_none()

        parametros = []
        suma_valores = 0.0
        producto_principal = 0.0

        for resultado in resultados:
            if resultado.parametro and resultado.parametro.codigo == "producto_principal":
                producto_principal = float(resultado.valor) if resultado.valor else 0.0
                continue

            param_dict = {
                "parametro_id": resultado.parametro_id,
                "nombre": resultado.parametro.codigo if resultado.parametro else "Desconocido",
                "valor": float(resultado.valor) if resultado.valor else 0.0,
                "unidad": resultado.unidad or "",
                "comentario": resultado.comentario,
            }
            parametros.append(param_dict)
            suma_valores += float(resultado.valor) if resultado.valor else 0.0

        muestra_dict = None
        lote_dict = None
        if muestra:
            muestra_dict = {
                "muestra_id": str(muestra.muestra_id),
                "contexto": muestra.contexto,
                "peso_muestra": float(muestra.peso_muestra) if muestra.peso_muestra else 0.0,
            }
            if muestra.lote:
                variedad_info = None
                if muestra.lote.variedad:
                    variedad_info = {
                        "variedad_id": muestra.lote.variedad_id,
                        "codigo": muestra.lote.variedad.codigo,
                    }
                lote_dict = {
                    "lote_id": str(muestra.lote.lote_id),
                    "variedad": variedad_info
                }

        return {
            "analisis_id": str(analisis.analisis_id),
            "muestra_id": str(analisis.muestra_id),
            "estado": analisis.estado,
            "fecha_completado": analisis.fecha_completado.isoformat() if analisis.fecha_completado else None,
            "parametros": parametros,
            "producto_principal": producto_principal,
            "total_parametros": len(parametros),
            "suma_valores": round(suma_valores, 2),
            "peso_muestra": peso_muestra,
            "muestra": muestra_dict,
            "lote": lote_dict,
        }