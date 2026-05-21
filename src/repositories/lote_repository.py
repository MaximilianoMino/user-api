import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.cache import lote_cache, cache_key_lote
from src.models.lote import Lote
from src.models.variedad import Variedad
from src.models.sub_variedad import SubVariedad
from src.models.temporada import Temporada
from src.models.muestra import Muestra
from src.models.evidencia import Evidencia
from src.models.otros import LoteDocumento


class LoteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_lotes(
        self,
        org_id: int,
        status: Optional[str] = None,
        busqueda: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> Dict[str, Any]:
        """Listar lotes con filtros, paginación y ordenamiento."""
        query = (
            select(Lote)
            .options(
                selectinload(Lote.variedad),
                selectinload(Lote.sub_variedad),
                selectinload(Lote.temporada),
            )
            .where(Lote.org_id == org_id, Lote.deleted_at.is_(None))
        )

        if status:
            query = query.where(Lote.status == status)

        if busqueda:
            query = query.join(Lote.variedad).outerjoin(
                SubVariedad, Lote.sub_variedad_id == SubVariedad.sub_variedad_id
            ).where(
                or_(
                    Variedad.codigo.ilike(f"%{busqueda}%"),
                    SubVariedad.codigo.ilike(f"%{busqueda}%"),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar()

        sort_column = getattr(Lote, sort_by, Lote.created_at)
        if order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        lotes = result.scalars().all()

        return {
            "lotes": [self._to_dict(lote) for lote in lotes],
            "total": total,
            "page": skip // limit + 1,
            "page_size": limit,
        }

    def _to_dict(self, lote: Lote) -> Dict[str, Any]:
        """Convertir modelo Lote a dict para respuesta."""
        return {
            "lote_id": lote.lote_id,
            "org_id": lote.org_id,
            "variedad_id": lote.variedad_id,
            "sub_variedad_id": lote.sub_variedad_id,
            "temporada_id": lote.temporada_id,
            "variedad": {
                "variedad_id": lote.variedad.variedad_id,
                "codigo": lote.variedad.codigo,
            } if lote.variedad else None,
            "sub_variedad": {
                "sub_variedad_id": lote.sub_variedad.sub_variedad_id,
                "codigo": lote.sub_variedad.codigo,
            } if lote.sub_variedad else None,
            "temporada": {
                "temporada_id": lote.temporada.temporada_id,
                "codigo": lote.temporada.codigo,
            } if lote.temporada else None,
            "volumen_estimado": float(lote.volumen_estimado) if lote.volumen_estimado else None,
            "volumen_disponible": float(lote.volumen_disponible) if lote.volumen_disponible else None,
            "estado_mercaderia": lote.estado_mercaderia,
            "status": lote.status,
            "imagen_principal": lote.imagen_principal,
            "view_count": lote.view_count,
            "gps_lat": float(lote.gps_lat) if lote.gps_lat else None,
            "gps_lng": float(lote.gps_lng) if lote.gps_lng else None,
            "gps_accuracy_m": float(lote.gps_accuracy_m) if lote.gps_accuracy_m else None,
            "gps_captured_at": lote.gps_captured_at.isoformat() if lote.gps_captured_at else None,
            "created_at": lote.created_at.isoformat() if lote.created_at else None,
            "updated_at": lote.updated_at.isoformat() if lote.updated_at else None,
            "created_by": lote.created_by,
            "updated_by": lote.updated_by,
            "deleted_at": lote.deleted_at.isoformat() if lote.deleted_at else None,
            "muestras": [],
        }

    async def get_by_id(self, lote_id: str) -> Optional[Lote]:
        """Obtener un lote por ID sin filtrar por org (la validación la hace el caller)."""
        result = await self.db.execute(
            select(Lote)
            .options(
                selectinload(Lote.variedad),
                selectinload(Lote.sub_variedad),
                selectinload(Lote.temporada),
            )
            .where(
                Lote.lote_id == lote_id,
                Lote.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def get_muestra_by_id(self, lote_id: str, muestra_id: str) -> Optional[Muestra]:
        """Obtener una muestra por ID perteneciente a un lote."""
        result = await self.db.execute(
            select(Muestra)
            .where(
                Muestra.muestra_id == muestra_id,
                Muestra.lote_id == lote_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_lote(self, org_id: int, lote_id: str) -> Lote:
        """Obtener un lote por ID con sus relaciones."""
        result = await self.db.execute(
            select(Lote)
            .options(
                selectinload(Lote.variedad),
                selectinload(Lote.sub_variedad),
                selectinload(Lote.temporada),
                selectinload(Lote.muestras),
            )
            .where(
                Lote.lote_id == lote_id,
                Lote.org_id == org_id,
                Lote.deleted_at.is_(None)
            )
        )
        lote = result.scalar_one_or_none()
        if not lote:
            raise ValueError("LOTE_NOT_FOUND")
        return lote

    async def get_lote_dict(self, org_id: int, lote_id: str) -> Dict[str, Any]:
        """Obtener lote como dict con cache."""
        cache_key = cache_key_lote(org_id, lote_id)
        cached = lote_cache.get(cache_key)
        if cached is not None:
            return cached

        lote = await self.get_lote(org_id, lote_id)
        result = await self._to_dict_with_muestras(lote)

        lote_cache.set(cache_key, result)
        return result

    def invalidate_lote_cache(self, org_id: int, lote_id: str) -> None:
        """Invalidar cache de un lote específico."""
        lote_cache.invalidate(cache_key_lote(org_id, lote_id))

    def invalidate_org_lotes_cache(self, org_id: int) -> None:
        """Invalidar todos los caches de lotes de una organización."""
        keys_to_delete = [
            key for key in lote_cache._cache
            if key.startswith(f"lote:{org_id}:")
        ]
        for key in keys_to_delete:
            lote_cache.invalidate(key)

    async def _to_dict_with_muestras(self, lote: Lote) -> Dict[str, Any]:
        """Convertir modelo Lote a dict con muestras y conteos."""
        result = self._to_dict(lote)
        counts = await self.count_evidencias_and_documentos(str(lote.lote_id))
        result["evidencias_count"] = counts["evidencias_count"]
        result["documentos_count"] = counts["documentos_count"]
        result["muestras"] = [
            {
                "muestra_id": m.muestra_id,
                "lote_id": m.lote_id,
                "contexto": m.contexto,
                "peso_muestra": float(m.peso_muestra) if m.peso_muestra else None,
                "unidad_peso": m.unidad_peso,
                "estado": m.estado,
                "checklist_sop": m.checklist_sop,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "updated_at": m.updated_at.isoformat() if m.updated_at else None,
            }
            for m in lote.muestras
        ]
        return result

    async def create_lote(self, org_id: int, user_id: int, data: Dict[str, Any]) -> Lote:
        """Crear un nuevo lote."""
        lote = Lote(
            lote_id=uuid.uuid4(),
            org_id=org_id,
            variedad_id=data["variedad_id"],
            sub_variedad_id=data.get("sub_variedad_id"),
            temporada_id=data.get("temporada_id"),
            volumen_estimado=data.get("volumen_estimado"),
            volumen_disponible=data.get("volumen_estimado"),
            estado_mercaderia=data["estado_mercaderia"],
            status="borrador",
            imagen_principal=data.get("imagen_principal"),
            gps_lat=data.get("gps_lat"),
            gps_lng=data.get("gps_lng"),
            gps_accuracy_m=data.get("gps_accuracy_m"),
            gps_captured_at=datetime.utcnow() if data.get("gps_lat") and data.get("gps_lng") else None,
            created_by=user_id,
            updated_by=user_id,
        )
        self.db.add(lote)
        await self.db.commit()
        await self.db.refresh(lote)
        return await self.get_lote(org_id, str(lote.lote_id))

    async def update_lote(self, org_id: int, lote_id: str, user_id: int, data: Dict[str, Any]) -> Lote:
        """Actualizar un lote."""
        result = await self.db.execute(
            select(Lote)
            .options(
                selectinload(Lote.variedad),
                selectinload(Lote.sub_variedad),
                selectinload(Lote.temporada),
                selectinload(Lote.muestras),
            )
            .where(Lote.lote_id == lote_id, Lote.org_id == org_id)
        )
        lote = result.scalar_one_or_none()

        if not lote:
            raise ValueError("LOTE_NOT_FOUND")

        for field, value in data.items():
            if hasattr(lote, field) and value is not None:
                setattr(lote, field, value)

        lote.updated_by = user_id

        if "volumen_estimado" in data and data["volumen_estimado"] is not None:
            lote.volumen_disponible = data["volumen_estimado"]

        await self.db.commit()
        await self.db.refresh(lote)

        self.invalidate_lote_cache(org_id, lote_id)
        return lote

    async def delete_lote(self, lote_id: str) -> None:
        """Soft delete de un lote."""
        lote = await self.db.get(Lote, lote_id)
        if not lote:
            raise ValueError("LOTE_NOT_FOUND")
        lote.deleted_at = datetime.utcnow()
        await self.db.commit()

        self.invalidate_lote_cache(lote.org_id, lote_id)

    async def check_variedad_exists(self, variedad_id: int) -> bool:
        """Verificar que existe la variedad."""
        result = await self.db.execute(
            select(Variedad).where(Variedad.variedad_id == variedad_id)
        )
        return result.scalar_one_or_none() is not None

    async def check_subvariedad_valid(self, sub_variedad_id: int, variedad_id: int) -> bool:
        """Verificar que la subvariedad pertenece a la variedad."""
        result = await self.db.execute(
            select(SubVariedad).where(
                SubVariedad.sub_variedad_id == sub_variedad_id,
                SubVariedad.variedad_id == variedad_id
            )
        )
        return result.scalar_one_or_none() is not None

    async def check_temporada_exists(self, temporada_id: int) -> bool:
        """Verificar que existe la temporada."""
        result = await self.db.execute(
            select(Temporada).where(Temporada.temporada_id == temporada_id)
        )
        return result.scalar_one_or_none() is not None

    async def count_muestras(self, lote_id: str) -> int:
        """Contar muestras asociadas a un lote."""
        result = await self.db.execute(
            select(func.count(Muestra.muestra_id))
            .where(Muestra.lote_id == lote_id)
        )
        return result.scalar()

    async def count_evidencias(self, lote_id: str) -> int:
        """Contar evidencias activas asociadas a un lote."""
        result = await self.db.execute(
            select(func.count(Evidencia.evidencia_id))
            .where(
                Evidencia.metadatos['lote_id'].astext == str(lote_id),
                Evidencia.estado == 'activa'
            )
        )
        return result.scalar() or 0

    async def count_documentos(self, lote_id: str) -> int:
        """Contar documentos asociados a un lote."""
        result = await self.db.execute(
            select(func.count(LoteDocumento.lote_documento_id))
            .where(LoteDocumento.lote_id == lote_id)
        )
        return result.scalar() or 0

    async def count_evidencias_and_documentos(self, lote_id: str) -> Dict[str, int]:
        """Contar evidencias activas y documentos en un solo query."""
        evidencias_subq = (
            select(func.count(Evidencia.evidencia_id).label("ec"))
            .where(
                Evidencia.metadatos['lote_id'].astext == str(lote_id),
                Evidencia.estado == 'activa'
            )
            .scalar_subquery()
        )
        documentos_subq = (
            select(func.count(LoteDocumento.lote_documento_id).label("dc"))
            .where(LoteDocumento.lote_id == lote_id)
            .scalar_subquery()
        )
        result = await self.db.execute(
            select(evidencias_subq, documentos_subq)
        )
        row = result.one()
        return {
            "evidencias_count": row[0] or 0,
            "documentos_count": row[1] or 0,
        }

    async def get_lote_for_update(self, org_id: int, lote_id: str) -> Lote:
        """Obtener lote para actualizar (con validaciones)."""
        result = await self.db.execute(
            select(Lote)
            .options(
                selectinload(Lote.muestras),
            )
            .where(
                Lote.lote_id == lote_id,
                Lote.org_id == org_id,
                Lote.deleted_at.is_(None)
            )
        )
        lote = result.scalar_one_or_none()
        if not lote:
            raise ValueError("LOTE_NOT_FOUND")
        return lote
