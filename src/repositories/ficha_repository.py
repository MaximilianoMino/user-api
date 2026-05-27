import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.analisis import Analisis
from src.models.analisis_resultado import AnalisisResultado
from src.models.evidencia import Evidencia
from src.models.lote import Lote
from src.models.muestra import Muestra
from src.models.organizacion import Organizacion
from src.models.otros import FichaReporte
from src.models.parametro import Parametro


class FichaRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_ficha_activa_por_lote(self, lote_id: str) -> Optional[FichaReporte]:
        """Obtener la ficha activa de un lote."""
        result = await self.db.execute(
            select(FichaReporte)
            .where(
                and_(
                    FichaReporte.lote_id == lote_id,
                    FichaReporte.estado == "activa"
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_por_token(self, token: str) -> Optional[FichaReporte]:
        """Obtener una ficha por link_token."""
        result = await self.db.execute(
            select(FichaReporte)
            .options(
                selectinload(FichaReporte.muestra),
                selectinload(FichaReporte.lote),
            )
            .where(FichaReporte.link_token == token)
        )
        return result.scalar_one_or_none()

    async def get_por_id(self, ficha_id: str) -> Optional[FichaReporte]:
        """Obtener una ficha por ID."""
        result = await self.db.execute(
            select(FichaReporte)
            .options(
                selectinload(FichaReporte.muestra),
                selectinload(FichaReporte.lote),
            )
            .where(FichaReporte.ficha_id == ficha_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        lote_id: str,
        muestra_id: str,
        user_id: int,
    ) -> FichaReporte:
        """Crear una nueva ficha."""
        link_token = str(uuid.uuid4())
        ficha = FichaReporte(
            ficha_id=uuid.uuid4(),
            lote_id=lote_id,
            muestra_id=muestra_id,
            link_token=link_token,
            permisos="public_link",
            estado="activa",
            version=1,
            created_by=user_id,
            updated_by=user_id,
        )
        self.db.add(ficha)
        await self.db.commit()
        await self.db.refresh(ficha)
        return ficha

    async def get_datos_publicos(self, lote_id: str) -> Dict[str, Any]:
        """Obtener todos los datos públicos de un lote para la ficha."""
        result_lote = await self.db.execute(
            select(Lote)
            .options(
                selectinload(Lote.variedad),
                selectinload(Lote.sub_variedad),
                selectinload(Lote.temporada),
                selectinload(Lote.organizacion)
            )
            .where(Lote.lote_id == lote_id)
        )
        lote = result_lote.scalar_one_or_none()

        if not lote:
            return {}

        result_muestra = await self.db.execute(
            select(Muestra)
            .where(
                and_(
                    Muestra.lote_id == lote_id,
                    Muestra.estado == "tomada"
                )
            )
            .order_by(Muestra.created_at.desc())
        )
        muestra = result_muestra.scalars().first()

        analisis_data = {}
        if muestra:
            result_analisis = await self.db.execute(
                select(Analisis)
                .options(
                    selectinload(Analisis.resultados).selectinload(AnalisisResultado.parametro)
                )
                .where(
                    and_(
                        Analisis.muestra_id == str(muestra.muestra_id),
                        Analisis.estado == "completo"
                    )
                )
            )
            analisis = result_analisis.scalars().first()

            if analisis:
                parametros = []
                subtotal_danos = 0.0
                producto_principal = 0.0

                for resultado in analisis.resultados:
                    nombre = resultado.parametro.codigo if resultado.parametro else "Desconocido"
                    parametros.append({
                        "nombre": nombre,
                        "valor": float(resultado.valor) if resultado.valor else 0.0,
                        "unidad": resultado.unidad or ""
                    })

                    if nombre in ["impurezas", "granos_partidos"]:
                        subtotal_danos += float(resultado.valor) if resultado.valor else 0.0
                    elif nombre == "producto_principal":
                        producto_principal = float(resultado.valor) if resultado.valor else 0.0

                analisis_data = {
                    "parametros": parametros,
                    "subtotal_danos": round(subtotal_danos, 2),
                    "producto_principal": producto_principal,
                    "total_analizado": sum(p["valor"] for p in parametros)
                }

        evidencias = []
        if muestra:
            result_evidencias = await self.db.execute(
                select(Evidencia)
                .where(
                    and_(
                        Evidencia.muestra_id == str(muestra.muestra_id),
                        Evidencia.estado == "activa"
                    )
                )
            )
            for ev in result_evidencias.scalars().all():
                evidencias.append({
                    "url": ev.url,
                    "tipo": ev.tipo
                })

        trazabilidad = {
            "fecha_creacion_lote": lote.created_at.isoformat() if lote.created_at else None,
            "fecha_muestra": muestra.created_at.isoformat() if muestra and muestra.created_at else None,
            "fecha_analisis": analisis.fecha_completado.isoformat() if analisis and analisis.fecha_completado else None
        }

        return {
            "lote": {
                "lote_id": str(lote.lote_id),
                "variedad": {"codigo": lote.variedad.codigo} if lote.variedad else None,
                "sub_variedad": {"codigo": lote.sub_variedad.codigo} if lote.sub_variedad else None,
                "temporada": {"codigo": lote.temporada.codigo} if lote.temporada else None,
                "volumen_estimado": float(lote.volumen_estimado) if lote.volumen_estimado else None,
                "volumen_disponible": float(lote.volumen_disponible) if lote.volumen_disponible else None,
                "estado_mercaderia": lote.estado_mercaderia,
                "imagen_principal": lote.imagen_principal,
                "created_at": lote.created_at.isoformat() if lote.created_at else None,
            },
            "organizacion": {
                "nombre": lote.organizacion.nombre if lote.organizacion else "",
                "tipo": lote.organizacion.tipo if lote.organizacion else ""
            },
            "muestra": {
                "peso_muestra": float(muestra.peso_muestra) if muestra and muestra.peso_muestra else 0.0,
                "unidad_peso": muestra.unidad_peso if muestra else "g",
                "contexto": muestra.contexto if muestra else "",
                "observaciones": muestra.observaciones if muestra else None,
            } if muestra else {},
            "analisis": analisis_data,
            "evidencias": evidencias,
            "trazabilidad": trazabilidad
        }

    def to_response_dict(self, ficha: FichaReporte, link_publico: str = None) -> Dict[str, Any]:
        """Convertir modelo FichaReporte a dict."""
        return {
            "ficha_id": str(ficha.ficha_id),
            "lote_id": str(ficha.lote_id),
            "link_token": ficha.link_token,
            "link_publico": link_publico,
            "estado": ficha.estado,
            "version": ficha.version,
            "created_at": ficha.created_at.isoformat() if ficha.created_at else None,
            "muestra_id": str(ficha.muestra_id) if ficha.muestra_id else None
        }