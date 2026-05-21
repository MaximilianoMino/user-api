import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models import Lote, Muestra


class AnalisisEstado(str, Enum):
    PARCIAL = "parcial"
    COMPLETO = "completo"
    INVALIDADA = "invalidada"


class Analisis(Base):
    """Analisis model - maps to 'analisis' table"""

    __tablename__ = "analisis"

    analisis_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    muestra_id = Column(UUID(as_uuid=True), ForeignKey("muestra.muestra_id"), nullable=False)
    metodo = Column(Text, nullable=True)
    estado = Column(
        Enum("parcial", "completo", "invalidada", name="analisis_estado", create_type=False),
        nullable=False, default="parcial"
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=False)
    plantilla_id = Column(Integer, ForeignKey("plantilla_analisis.plantilla_id"), nullable=True)
    observaciones_generales = Column(Text, nullable=True)
    fecha_completado = Column(DateTime, nullable=True)

    # Relationships
    muestra = relationship("Muestra", foreign_keys=[muestra_id])
    resultados = relationship("AnalisisResultado", back_populates="analisis", foreign_keys="AnalisisResultado.analisis_id")

    def __repr__(self):
        return f"<Analisis(analisis_id={self.analisis_id}, estado={self.estado})>"


class ParametroCreate(BaseModel):
    parametro_id: int
    valor: float = Field(..., ge=0)
    comentario: Optional[str] = None


class AnalisisCreate(BaseModel):
    parametros: List[ParametroCreate]

    @field_validator("parametros")
    @classmethod
    def al_menos_un_parametro(cls, v: List[ParametroCreate]) -> List[ParametroCreate]:
        if len(v) == 0:
            raise ValueError("Debe enviar al menos un parámetro")
        return v


class ParametroResponse(BaseModel):
    parametro_id: int
    nombre: str
    valor: float
    unidad: str
    comentario: Optional[str] = None

    class Config:
        from_attributes = True


class AnalisisResponse(BaseModel):
    analisis_id: UUID
    muestra_id: UUID
    estado: str
    fecha_completado: Optional[datetime] = None
    parametros: List[ParametroResponse] = []
    producto_principal: float = 0.0
    total_parametros: int = 0
    suma_valores: float = 0.0
    peso_muestra: float = 0.0
    muestra: Optional[Dict[str, Any]] = None
    lote: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True, "arbitrary_types_allowed": True}


class AnalisisUpdate(BaseModel):
    observaciones_generales: Optional[str] = None