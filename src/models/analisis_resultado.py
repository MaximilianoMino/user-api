import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models import Analisis, Parametro


class AnalisisResultado(Base):
    """AnalisisResultado model - maps to 'analisis_resultado' table"""

    __tablename__ = "analisis_resultado"

    resultado_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analisis_id = Column(UUID(as_uuid=True), ForeignKey("analisis.analisis_id"), nullable=False)
    valor = Column(Numeric, nullable=True)
    unidad = Column(String, nullable=True)
    out_of_range = Column(Boolean, nullable=False, default=False)
    comentario = Column(Text, nullable=True)
    parametro_id = Column(Integer, ForeignKey("parametro.parametro_id"), nullable=False)

    # Relationships
    analisis = relationship("Analisis", foreign_keys=[analisis_id])
    parametro = relationship("Parametro", back_populates="analisis_resultados", foreign_keys=[parametro_id])

    def __repr__(self):
        return f"<AnalisisResultado(resultado_id={self.resultado_id})>"