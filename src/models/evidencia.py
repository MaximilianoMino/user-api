import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from src.models.base import Base


class EvidenciaStatus(str, Enum):
    ACTIVA = "activa"
    ELIMINADA = "eliminada"


class EvidenciaTipo(str, Enum):
    FOTO = "foto"
    VIDEO = "video"


TIPOS_VALIDOS = {"foto", "video"}
CONTENT_TYPES_PERMITIDOS = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "video/mp4",
}


class Evidencia(Base):
    """Evidencia model - maps to 'evidencia' table"""

    __tablename__ = "evidencia"

    evidencia_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    muestra_id = Column(UUID(as_uuid=True), ForeignKey("muestra.muestra_id"), nullable=True)
    tipo = Column(
        Enum("foto", "video", name="evidencia_tipo", create_type=False),
        nullable=False
    )
    url = Column(String, nullable=False)
    metadatos = Column(JSONB, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    estado = Column(
        Enum("activa", "eliminada", name="evidencia_status", create_type=False),
        nullable=False, default="activa"
    )
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=True)
    created_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=True)

    # Relationships
    muestra = relationship("Muestra", foreign_keys=[muestra_id])

    def __repr__(self):
        return f"<Evidencia(evidencia_id={self.evidencia_id}, tipo={self.tipo})>"


class EvidenciaUploadUrlRequest(BaseModel):
    tipo: str = Field(...)
    content_type: str = Field(...)


class EvidenciaConfirmRequest(BaseModel):
    file_key: str = Field(...)
    tipo: str = Field(...)
    muestra_id: Optional[uuid.UUID] = Field(default=None)


class EvidenciaResponse(BaseModel):
    evidencia_id: uuid.UUID
    url: str
    tipo: str
    estado: str

    class Config:
        from_attributes = True


class EvidenciaListItem(BaseModel):
    evidencia_id: uuid.UUID
    url: str
    tipo: str
    created_at: datetime

    class Config:
        from_attributes = True