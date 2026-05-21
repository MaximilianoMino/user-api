from datetime import datetime

from sqlalchemy import Column, Boolean, DateTime, ForeignKey, Identity, Integer, String

from src.models.base import Base


class SubVariedad(Base):
    """SubVariedad model - maps to 'sub_variedad' table"""

    __tablename__ = "sub_variedad"

    codigo = Column(String, nullable=False, unique=True)
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    variedad_id = Column(Integer, ForeignKey("variedad.variedad_id"), nullable=False)
    sub_variedad_id = Column(Integer, Identity(), primary_key=True)

    def __repr__(self):
        return f"<SubVariedad(sub_variedad_id={self.sub_variedad_id}, codigo={self.codigo})>"