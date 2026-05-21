import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.evidencia import Evidencia
from src.models.lote import Lote
from src.models.muestra import Muestra

logger = logging.getLogger(__name__)


class EvidenciaRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        evidencia_id: UUID,
        tipo: str,
        url: str,
        created_by: int,
        muestra_id: Optional[UUID] = None,
        metadatos: Optional[Dict[str, Any]] = None,
    ) -> Evidencia:
        evidencia = Evidencia(
            evidencia_id=evidencia_id,
            muestra_id=muestra_id,
            tipo=tipo,
            url=url,
            metadatos=metadatos,
            estado="activa",
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(evidencia)
        await self.db.commit()
        await self.db.refresh(evidencia)
        return evidencia

    async def list_by_lote(self, lote_id: UUID) -> List[Evidencia]:
        result = await self.db.execute(
            select(Evidencia)
            .options(selectinload(Evidencia.muestra))
            .where(
                Evidencia.metadatos['lote_id'].astext == str(lote_id),
                Evidencia.estado == "activa",
            )
            .order_by(Evidencia.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, evidencia_id: UUID) -> Optional[Evidencia]:
        result = await self.db.execute(
            select(Evidencia)
            .options(selectinload(Evidencia.muestra))
            .where(Evidencia.evidencia_id == evidencia_id)
        )
        return result.scalar_one_or_none()

    async def soft_delete(
        self,
        evidencia_id: UUID,
        user_id: int,
    ) -> Optional[Evidencia]:
        evidencia = await self.get_by_id(evidencia_id)
        if not evidencia:
            return None

        evidencia.estado = "eliminada"
        evidencia.deleted_at = datetime.utcnow()
        evidencia.deleted_by = user_id
        evidencia.updated_by = user_id

        await self.db.commit()
        await self.db.refresh(evidencia)
        return evidencia

    def _get_lote_id(self, evidencia: Evidencia) -> Optional[str]:
        if evidencia.muestra and evidencia.muestra.lote_id:
            return str(evidencia.muestra.lote_id)
        metadatos = evidencia.metadatos or {}
        return metadatos.get("lote_id")

    def to_dict(self, evidencia: Evidencia) -> Dict[str, Any]:
        return {
            "evidencia_id": str(evidencia.evidencia_id),
            "lote_id": self._get_lote_id(evidencia),
            "muestra_id": str(evidencia.muestra_id) if evidencia.muestra_id else None,
            "tipo": evidencia.tipo,
            "url": evidencia.url,
            "estado": evidencia.estado,
            "created_at": evidencia.created_at.isoformat() if evidencia.created_at else None,
            "created_by": evidencia.created_by,
        }

    def to_response_dict(self, evidencia: Evidencia) -> Dict[str, Any]:
        file_key = (evidencia.metadatos or {}).get("file_key", "") if evidencia.metadatos else ""
        return {
            "evidencia_id": str(evidencia.evidencia_id),
            "lote_id": self._get_lote_id(evidencia),
            "file_key": file_key,
            "url": evidencia.url,
            "tipo": evidencia.tipo,
            "content_type": "",
            "estado": evidencia.estado,
            "created_at": evidencia.created_at.isoformat() if evidencia.created_at else None,
            "updated_at": evidencia.updated_at.isoformat() if evidencia.updated_at else None,
        }

    def to_list_item_dict(self, evidencia: Evidencia) -> Dict[str, Any]:
        file_key = (evidencia.metadatos or {}).get("file_key", "") if evidencia.metadatos else ""
        return {
            "evidencia_id": str(evidencia.evidencia_id),
            "lote_id": self._get_lote_id(evidencia),
            "file_key": file_key,
            "url": evidencia.url,
            "tipo": evidencia.tipo,
            "content_type": "",
            "created_at": evidencia.created_at.isoformat() if evidencia.created_at else None,
            "updated_at": evidencia.updated_at.isoformat() if evidencia.updated_at else None,
        }
