from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class FichaResponse(BaseModel):
    ficha_id: UUID
    lote_id: UUID
    link_token: str
    link_publico: Optional[str] = None
    estado: str
    version: int
    created_at: datetime
    muestra_id: Optional[UUID] = None

    model_config = {"from_attributes": True}


class ParametroAnalisisResponse(BaseModel):
    nombre: str
    valor: float
    unidad: str


class AnalisisPublicResponse(BaseModel):
    parametros: List[ParametroAnalisisResponse]
    subtotal_danos: float = 0.0
    producto_principal: float = 0.0
    total_analizado: float = 0.0


class MuestraPublicResponse(BaseModel):
    peso_muestra: float
    unidad_peso: str
    contexto: str
    observaciones: Optional[str] = None


class LotePublicResponse(BaseModel):
    lote_id: UUID
    variedad: Optional[Dict[str, Any]] = None
    sub_variedad: Optional[Dict[str, Any]] = None
    temporada: Optional[Dict[str, Any]] = None
    volumen_estimado: Optional[float] = None
    volumen_disponible: Optional[float] = None
    estado_mercaderia: Optional[str] = None
    imagen_principal: Optional[str] = None
    created_at: Optional[datetime] = None


class OrganizacionPublicResponse(BaseModel):
    nombre: str
    tipo: str


class EvidenciaPublicResponse(BaseModel):
    url: str
    tipo: str


class TrazabilidadResponse(BaseModel):
    fecha_creacion_lote: Optional[datetime] = None
    fecha_muestra: Optional[datetime] = None
    fecha_analisis: Optional[datetime] = None


class FichaPublicResponse(BaseModel):
    lote: LotePublicResponse
    organizacion: OrganizacionPublicResponse
    muestra: MuestraPublicResponse
    analisis: AnalisisPublicResponse
    evidencias: List[EvidenciaPublicResponse] = []
    trazabilidad: TrazabilidadResponse


class FichaGenerateResponse(BaseModel):
    data: FichaResponse


class FichaDetailResponse(BaseModel):
    data: FichaResponse
    lote: Optional[Dict[str, Any]] = None
    muestra: Optional[Dict[str, Any]] = None