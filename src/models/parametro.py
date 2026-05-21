from datetime import datetime

from sqlalchemy import Column, Boolean, DateTime, Enum, ForeignKey, Identity, Integer, String
from sqlalchemy.orm import relationship

from src.models.base import Base


class ParametroValueType(str, Enum):
    PORCENTAJE = "porcentaje"
    CONTEO = "conteo"
    PESO = "peso"
    PPM = "ppm"


class Parametro(Base):
    """Parametro model - maps to 'parametro' table"""

    __tablename__ = "parametro"

    codigo = Column(String, nullable=False, unique=True)
    value_type = Column(
        Enum("porcentaje", "conteo", "peso", "ppm", name="parametro_value_type", create_type=False),
        nullable=False, default="porcentaje"
    )
    unidad_default = Column(String, nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    parametro_id = Column(Integer, Identity(), primary_key=True)
    created_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=False)

    # Relationships
    analisis_resultados = relationship("AnalisisResultado", back_populates="parametro")

    def __repr__(self):
        return f"<Parametro(parametro_id={self.parametro_id}, codigo={self.codigo})>"