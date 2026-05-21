from datetime import datetime

from sqlalchemy import Column, Boolean, DateTime, Identity, Integer, String

from src.models.base import Base


class Variedad(Base):
    """Variedad model - maps to 'variedad' table"""

    __tablename__ = "variedad"

    codigo = Column(String, nullable=False, unique=True)
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    variedad_id = Column(Integer, Identity(), primary_key=True)

    def __repr__(self):
        return f"<Variedad(variedad_id={self.variedad_id}, codigo={self.codigo})>"