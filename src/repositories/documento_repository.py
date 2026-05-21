import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.otros import LoteDocumento

logger = logging.getLogger(__name__)


class DocumentoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        lote_documento_id: UUID,
        lote_id: UUID,
        nombre_original: str,
        nombre_archivo: str,
        tipo_mime: str,
        extension: str,
        url: str,
        tamano_bytes: int,
        created_by: int,
        categoria: Optional[str] = None,
        descripcion: Optional[str] = None,
    ) -> LoteDocumento:
        documento = LoteDocumento(
            lote_documento_id=lote_documento_id,
            lote_id=lote_id,
            nombre_original=nombre_original,
            nombre_archivo=nombre_archivo,
            tipo_mime=tipo_mime,
            extension=extension,
            url=url,
            tamano_bytes=tamano_bytes,
            categoria=categoria,
            descripcion=descripcion,
            estado="activo",
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(documento)
        await self.db.commit()
        await self.db.refresh(documento)
        return documento

    async def list_by_lote(self, lote_id: UUID) -> List[LoteDocumento]:
        result = await self.db.execute(
            select(LoteDocumento)
            .where(
                LoteDocumento.lote_id == lote_id,
                LoteDocumento.estado == "activo",
            )
            .order_by(LoteDocumento.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, documento_id: UUID) -> Optional[LoteDocumento]:
        result = await self.db.execute(
            select(LoteDocumento)
            .where(LoteDocumento.lote_documento_id == documento_id)
        )
        return result.scalar_one_or_none()

    async def soft_delete(
        self,
        documento_id: UUID,
        user_id: int,
    ) -> Optional[LoteDocumento]:
        documento = await self.get_by_id(documento_id)
        if not documento:
            return None

        documento.estado = "eliminado"
        documento.updated_by = user_id

        await self.db.commit()
        await self.db.refresh(documento)
        return documento

    def to_response_dict(self, documento: LoteDocumento) -> Dict[str, Any]:
        return {
            "lote_documento_id": str(documento.lote_documento_id),
            "lote_id": str(documento.lote_id),
            "nombre_original": documento.nombre_original,
            "nombre_archivo": documento.nombre_archivo,
            "tipo_mime": documento.tipo_mime,
            "extension": documento.extension,
            "url": documento.url,
            "tamano_bytes": documento.tamano_bytes,
            "categoria": documento.categoria,
            "descripcion": documento.descripcion,
            "estado": documento.estado,
            "created_at": documento.created_at.isoformat() if documento.created_at else None,
            "updated_at": documento.updated_at.isoformat() if documento.updated_at else None,
        }

    def to_list_item_dict(self, documento: LoteDocumento) -> Dict[str, Any]:
        return {
            "lote_documento_id": str(documento.lote_documento_id),
            "url": documento.url,
            "nombre_original": documento.nombre_original,
            "tipo_mime": documento.tipo_mime,
            "tamano_bytes": documento.tamano_bytes,
            "categoria": documento.categoria,
            "created_at": documento.created_at.isoformat() if documento.created_at else None,
        }
