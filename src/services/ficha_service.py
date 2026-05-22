import logging
import os
from typing import Any, Dict
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.analisis import Analisis
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

    return muestra


async def generar_ficha(
    repo: FichaRepository,
    db: AsyncSession,
    lote_id: str,
    org_id: int,
    user_id: int,
    base_url: str = os.getenv("BASE_URL", "https://agryflow-app.vercel.app"),
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

    return datos


def _render_ficha_html(datos: dict) -> str:
    lote = datos.get("lote", {})
    org = datos.get("organizacion", {})
    muestra = datos.get("muestra", {})
    analisis = datos.get("analisis", {})
    evidencias = datos.get("evidencias", [])
    trazabilidad = datos.get("trazabilidad", {})

    params_rows = ""
    for p in analisis.get("parametros", []):
        params_rows += f"""<tr><td>{p['nombre']}</td><td class="val">{p['valor']}</td><td>{p['unidad']}</td></tr>"""

    evidencia_imgs = ""
    for e in evidencias:
        if e.get("tipo") == "foto":
            evidencia_imgs += f"""<img src="{e['url']}" alt="Evidencia" loading="lazy">"""

    variedad = lote.get("variedad", {}) or {}
    sub_variedad = lote.get("sub_variedad", {}) or {}
    temporada = lote.get("temporada", {}) or {}

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ficha de Análisis - {org.get("nombre", "AgryFlow")}</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #F4F1EC; color: #1a1a1a; line-height: 1.6; }}
  .container {{ max-width: 640px; margin: 0 auto; padding: 16px; }}
  .header {{ background: #0f5238; color: #fff; padding: 24px 16px; text-align: center; border-radius: 12px 12px 0 0; }}
  .header h1 {{ font-size: 1.25rem; font-weight: 600; }}
  .header p {{ font-size: 0.85rem; opacity: 0.85; margin-top: 4px; }}
  .card {{ background: #fff; border-radius: 12px; padding: 20px; margin-top: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }}
  .card h2 {{ font-size: 1rem; color: #0f5238; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #e8e4de; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px 16px; }}
  .grid .label {{ font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }}
  .grid .value {{ font-size: 0.95rem; font-weight: 500; }}
  .grid .full {{ grid-column: 1 / -1; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
  th {{ text-align: left; font-size: 0.7rem; color: #888; text-transform: uppercase; letter-spacing: 0.5px; padding: 6px 8px; border-bottom: 1px solid #e8e4de; }}
  td {{ padding: 8px; border-bottom: 1px solid #f0ece6; }}
  td.val {{ font-weight: 600; text-align: right; font-variant-numeric: tabular-nums; }}
  tr:last-child td {{ border-bottom: none; }}
  .summary {{ display: flex; justify-content: space-between; margin-top: 12px; padding-top: 12px; border-top: 2px solid #0f5238; font-weight: 600; }}
  .evidencias {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
  .evidencias img {{ width: 100%; border-radius: 8px; aspect-ratio: 4/3; object-fit: cover; }}
  .footer {{ text-align: center; padding: 20px; font-size: 0.8rem; color: #888; }}
  .footer span {{ color: #0f5238; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>{org.get("nombre", "AgryFlow")}</h1>
    <p>{org.get("tipo", "")}</p>
  </div>

  <div class="card">
    <h2>Lote</h2>
    <div class="grid">
      <div><div class="label">Variedad</div><div class="value">{variedad.get("codigo", "-")}</div></div>
      <div><div class="label">Subvariedad</div><div class="value">{sub_variedad.get("codigo", "-")}</div></div>
      <div><div class="label">Temporada</div><div class="value">{temporada.get("codigo", "-")}</div></div>
      <div><div class="label">Estado</div><div class="value">{lote.get("estado_mercaderia", "-")}</div></div>
      <div class="full"><div class="label">Volumen Estimado</div><div class="value">{lote.get("volumen_estimado", "-")} kg</div></div>
      <div class="full"><div class="label">Volumen Disponible</div><div class="value">{lote.get("volumen_disponible", "-")} kg</div></div>
    </div>
  </div>

  <div class="card">
    <h2>Muestra</h2>
    <div class="grid">
      <div><div class="label">Peso</div><div class="value">{muestra.get("peso_muestra", "-")} {muestra.get("unidad_peso", "g")}</div></div>
      <div><div class="label">Contexto</div><div class="value">{muestra.get("contexto", "-")}</div></div>
      <div class="full"><div class="label">Observaciones</div><div class="value">{muestra.get("observaciones", "Sin observaciones") or "Sin observaciones"}</div></div>
    </div>
  </div>

  <div class="card">
    <h2>Análisis</h2>
    <table>
      <thead><tr><th>Parámetro</th><th style="text-align:right">Valor</th><th>Unidad</th></tr></thead>
      <tbody>{params_rows}</tbody>
    </table>
    <div class="summary">
      <span>Subtotal daños: {analisis.get("subtotal_danos", "-")}%</span>
      <span>Total analizado: {analisis.get("total_analizado", "-")}%</span>
    </div>
    <div style="text-align:right;font-weight:600;color:#0f5238;margin-top:4px">
      Producto principal: {analisis.get("producto_principal", "-")}%
    </div>
  </div>
  {"<div class='card'><h2>Evidencias</h2><div class='evidencias'>" + evidencia_imgs + "</div></div>" if evidencia_imgs else ""}

  <div class="card">
    <h2>Trazabilidad</h2>
    <div class="grid">
      <div><div class="label">Creación del lote</div><div class="value">{_fmt_fecha(trazabilidad.get("fecha_creacion_lote"))}</div></div>
      <div><div class="label">Toma de muestra</div><div class="value">{_fmt_fecha(trazabilidad.get("fecha_muestra"))}</div></div>
      <div><div class="label">Análisis completado</div><div class="value">{_fmt_fecha(trazabilidad.get("fecha_analisis"))}</div></div>
    </div>
  </div>

  <div class="footer">
    Ficha generada por <span>🌱 AgryFlow</span>
  </div>
</div>
</body>
</html>"""


def _fmt_fecha(iso: str | None) -> str:
    if not iso:
        return "-"
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return iso


def _render_ficha_404_html() -> str:
    return """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ficha no encontrada - AgryFlow</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #F4F1EC; color: #1a1a1a; display: flex; align-items: center; justify-content: center; min-height: 100vh; }}
  .card {{ background: #fff; border-radius: 12px; padding: 40px 24px; margin: 16px; max-width: 400px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }}
  h1 {{ font-size: 1.25rem; color: #0f5238; margin-bottom: 8px; }}
  p {{ color: #888; font-size: 0.9rem; }}
  .icon {{ font-size: 3rem; margin-bottom: 16px; }}
</style>
</head>
<body>
<div class="card">
  <div class="icon">🔍</div>
  <h1>Ficha no encontrada</h1>
  <p>El link ha expirado o la ficha no está disponible.</p>
</div>
</body>
</html>"""


async def get_ficha_autenticada(
    repo: FichaRepository,
    db: AsyncSession,
    ficha_id: str,
    org_id: int,
    base_url: str = os.getenv("BASE_URL", "https://agryflow-app.vercel.app"),
) -> Dict[str, Any]:
    """Obtener una ficha por ID (autenticado)."""
    ficha = await repo.get_por_id(ficha_id)

    if not ficha:
        raise ValueError("FICHA_NOT_FOUND")

    if not ficha.muestra or not ficha.lote:
        raise ValueError("FICHA_NOT_FOUND")

    if ficha.lote.org_id != org_id:
        raise ValueError("FICHA_NOT_FOUND")

    datos = await repo.get_datos_publicos(str(ficha.lote_id))
    link_publico = f"{base_url}/ficha/{ficha.link_token}"

    return {
        "data": repo.to_response_dict(ficha, link_publico),
        "lote": datos.get("lote", {}),
        "muestra": datos.get("muestra", {})
    }