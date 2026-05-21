import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.muestra import Muestra, MuestraEstado


class MuestraRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, muestra_id: str) -> Optional[Muestra]:
        """Obtener una muestra por ID."""
        result = await self.db.execute(
            select(Muestra)
            .options(selectinload(Muestra.lote))
            .where(Muestra.muestra_id == muestra_id)
        )
        return result.scalar_one_or_none()

    async def get_by_lote(self, lote_id: str) -> list[Muestra]:
        """Obtener todas las muestras de un lote."""
        result = await self.db.execute(
            select(Muestra)
            .where(Muestra.lote_id == lote_id)
            .order_by(Muestra.created_at.desc())
        )
        return result.scalars().all()

    async def count_muestras_tomadas_by_lote(self, lote_id: str) -> int:
        """Contar muestras en estado 'tomada' de un lote."""
        result = await self.db.execute(
            select(func.count(Muestra.muestra_id))
            .where(
                Muestra.lote_id == lote_id,
                Muestra.estado == "tomada"
            )
        )
        return result.scalar()

    async def create(
        self,
        lote_id: str,
        peso_muestra: float,
        unidad_peso: str,
        contexto: str,
        observaciones: Optional[str],
        user_id: int,
    ) -> Muestra:
        """Crear una nueva muestra."""
        muestra = Muestra(
            muestra_id=uuid.uuid4(),
            lote_id=lote_id,
            peso_muestra=peso_muestra,
            unidad_peso=unidad_peso,
            contexto=contexto,
            observaciones=observaciones,
            estado=MuestraEstado.TOMADA,
            created_by=user_id,
            updated_by=user_id,
        )
        self.db.add(muestra)
        await self.db.commit()
        await self.db.refresh(muestra)
        return muestra

    async def update_observaciones(
        self,
        muestra_id: str,
        observaciones: Optional[str],
        user_id: int,
    ) -> Muestra:
        """Actualizar observaciones de una muestra."""
        muestra = await self.get_by_id(muestra_id)
        if muestra:
            muestra.observaciones = observaciones
            muestra.updated_by = user_id
            await self.db.commit()
            await self.db.refresh(muestra)
        return muestra

    def to_dict(self, muestra: Muestra) -> Dict[str, Any]:
        """Convertir modelo Muestra a dict."""
        return {
            "muestra_id": muestra.muestra_id,
            "lote_id": muestra.lote_id,
            "contexto": muestra.contexto,
            "peso_muestra": float(muestra.peso_muestra) if muestra.peso_muestra else None,
            "unidad_peso": muestra.unidad_peso,
            "estado": muestra.estado,
            "observaciones": muestra.observaciones,
            "created_at": muestra.created_at.isoformat() if muestra.created_at else None,
            "updated_at": muestra.updated_at.isoformat() if muestra.updated_at else None,
        }

    def to_dict_with_lote(self, muestra: Muestra) -> Dict[str, Any]:
        """Convertir modelo Muestra a dict con información del lote."""
        result = self.to_dict(muestra)
        if muestra.lote:
            result["lote"] = {
                "lote_id": str(muestra.lote.lote_id),
                "variedad": {
                    "variedad_id": muestra.lote.variedad_id,
                    "codigo": None
                } if muestra.lote.variedad_id else None,
                "status": muestra.lote.status
            }
        result["sugerencias_ia"] = []
        return result