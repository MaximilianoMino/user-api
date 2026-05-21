from datetime import datetime

from sqlalchemy import Column, DateTime, Identity, Integer, String

from src.models.base import Base


class Temporada(Base):
    """Temporada model - maps to 'temporada' table"""

    __tablename__ = "temporada"

    codigo = Column(String, nullable=False, unique=True)
    anio_inicio = Column(Integer, nullable=False)
    anio_fin = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    temporada_id = Column(Integer, Identity(), primary_key=True)

    def __repr__(self):
        return f"<Temporada(temporada_id={self.temporada_id}, codigo={self.codigo})>"