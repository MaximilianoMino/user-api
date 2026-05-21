import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models import Lote


class MuestraContexto(str, Enum):
    BIG_BAGS = "big_bags"
    BOLSAS = "bolsas"
    GRANEL = "granel"
    SILO_METALICO = "silo_metalico"
    SILOBOLSA = "silobolsa"


class MuestraEstado(str, Enum):
    INICIADA = "iniciada"
    TOMADA = "tomada"
    OMITIDA = "omitida"
    INVALIDADA = "invalidada"


class Muestra(Base):
    """Muestra model - maps to 'muestra' table"""

    __tablename__ = "muestra"

    muestra_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lote_id = Column(UUID(as_uuid=True), ForeignKey("lote.lote_id"), nullable=False)
    contexto = Column(
        Enum("big_bags", "bolsas", "granel", "silo_metalico", "silobolsa", name="muestra_contexto", create_type=False),
        nullable=False
    )
    sop_version = Column(String, nullable=True)
    checklist_sop = Column(JSONB, nullable=True)
    observaciones = Column(Text, nullable=True)
    estado = Column(
        Enum("iniciada", "tomada", "omitida", "invalidada", name="muestra_estado", create_type=False),
        nullable=False, default="iniciada"
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=False)
    peso_muestra = Column(Numeric, nullable=False)
    unidad_peso = Column(String, nullable=False, default="g")

    # Relationships
    lote = relationship("Lote", back_populates="muestras", foreign_keys=[lote_id])

    def __repr__(self):
        return f"<Muestra(muestra_id={self.muestra_id}, contexto={self.contexto})>"


from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime


CONTEXTOS_VALIDOS = {"big_bags", "bolsas", "granel", "silo_metalico", "silobolsa"}
UNIDADES_PESO_VALIDAS = {"g", "kg"}


class MuestraCreate(BaseModel):
    peso_muestra: float = Field(..., gt=0)
    unidad_peso: str = Field(default="g")
    contexto: Optional[str] = Field(default="bolsas")
    observaciones: Optional[str] = None

    @field_validator("unidad_peso")
    @classmethod
    def validar_unidad(cls, v: str) -> str:
        if v not in UNIDADES_PESO_VALIDAS:
            raise ValueError("UNIDAD_PESO_INVALIDA")
        return v

    @field_validator("contexto")
    @classmethod
    def validar_contexto(cls, v: str) -> str:
        if v not in CONTEXTOS_VALIDOS:
            raise ValueError("CONTEXTO_INVALIDO")
        return v


class MuestraUpdate(BaseModel):
    observaciones: Optional[str] = None


class MuestraResponse(BaseModel):
    muestra_id: UUID
    lote_id: UUID
    contexto: str
    peso_muestra: float
    unidad_peso: str
    estado: str
    observaciones: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MuestraDetalleResponse(BaseModel):
    muestra_id: UUID
    lote_id: UUID
    contexto: str
    peso_muestra: float
    unidad_peso: str
    estado: str
    observaciones: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    lote: dict
    sugerencias_ia: List = Field(default_factory=list)

    class Config:
        from_attributes = True