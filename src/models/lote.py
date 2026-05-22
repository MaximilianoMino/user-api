import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models import Muestra, Organizacion, SubVariedad, Temporada, Variedad


class EstadoMercaderiaTipo(str, Enum):
    NATURAL = "natural"
    PRELIMPIADA = "prelimpiada"
    PROCESADA = "procesada"


class LoteStatus(str, Enum):
    BORRADOR = "borrador"
    MUESTREO_TOMADO = "muestreo_tomado"
    ANALISIS_COMPLETO = "analisis_completo"
    LISTO_PARA_COMPARTIR = "listo_para_compartir"


class Lote(Base):
    """Lote model - maps to 'lote' table"""

    __tablename__ = "lote"

    lote_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lote_anterior_id = Column(UUID(as_uuid=True), ForeignKey("lote.lote_id"), nullable=True)
    volumen_estimado = Column(Numeric, nullable=True)
    volumen_disponible = Column(Numeric, nullable=True)
    status = Column(
        SQLEnum("borrador", "muestreo_tomado", "analisis_completo", "listo_para_compartir",
             name="lote_status", create_type=False),
        nullable=False, default="borrador"
    )
    estado_mercaderia = Column(
        SQLEnum("natural", "prelimpiada", "procesada",
             name="estado_mercaderia_tipo", create_type=False),
        nullable=False
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    org_id = Column(Integer, ForeignKey("organizacion.org_id"), nullable=False)
    variedad_id = Column(Integer, ForeignKey("variedad.variedad_id"), nullable=False)
    created_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=False)
    sub_variedad_id = Column(Integer, ForeignKey("sub_variedad.sub_variedad_id"), nullable=True)
    temporada_id = Column(Integer, ForeignKey("temporada.temporada_id"), nullable=True)
    imagen_principal = Column(String, nullable=True)
    view_count = Column(Integer, nullable=False, default=0)
    gps_lat = Column(Numeric, nullable=True)
    gps_lng = Column(Numeric, nullable=True)
    gps_accuracy_m = Column(Numeric, nullable=True)
    gps_captured_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    organizacion = relationship("Organizacion", foreign_keys=[org_id])
    variedad = relationship("Variedad", foreign_keys=[variedad_id])
    sub_variedad = relationship("SubVariedad", foreign_keys=[sub_variedad_id])
    temporada = relationship("Temporada", foreign_keys=[temporada_id])
    muestras = relationship("Muestra", back_populates="lote", foreign_keys="Muestra.lote_id")

    def __repr__(self):
        return f"<Lote(lote_id={self.lote_id}, status={self.status})>"


from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


class LoteBase(BaseModel):
    org_id: Optional[int] = None
    variedad_id: int
    sub_variedad_id: Optional[int] = None
    temporada_id: Optional[int] = None
    volumen_estimado: Optional[float] = None
    volumen_disponible: Optional[float] = None
    estado_mercaderia: str
    status: str = "borrador"
    imagen_principal: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    gps_accuracy_m: Optional[float] = None
    gps_captured_at: Optional[datetime] = None


class LoteCreate(LoteBase):
    pass


class LoteUpdate(BaseModel):
    variedad_id: Optional[int] = None
    sub_variedad_id: Optional[int] = None
    temporada_id: Optional[int] = None
    volumen_estimado: Optional[float] = None
    volumen_disponible: Optional[float] = None
    estado_mercaderia: Optional[str] = None
    status: Optional[str] = None
    imagen_principal: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    gps_accuracy_m: Optional[float] = None
    gps_captured_at: Optional[datetime] = None


class LoteResponse(LoteBase):
    lote_id: UUID
    view_count: int = 0
    evidencias_count: int = 0
    documentos_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    variedad: Optional[Dict[str, Any]] = None
    sub_variedad: Optional[Dict[str, Any]] = None
    temporada: Optional[Dict[str, Any]] = None
    muestras: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True


class LoteDetailResponse(BaseModel):
    data: LoteResponse


class LoteListResponse(BaseModel):
    lotes: List[LoteResponse]
    total: int
    page: int
    page_size: int


class EstadoMercaderia(Enum):
    NATURAL = "natural"
    PRELIMPIADA = "prelimpiada"
    PROCESADA = "procesada"


class LoteStatusSchema(Enum):
    BORRADOR = "borrador"
    MUESTREO_TOMADO = "muestreo_tomado"
    ANALISIS_COMPLETO = "analisis_completo"
    LISTO_PARA_COMPARTIR = "listo_para_compartir"