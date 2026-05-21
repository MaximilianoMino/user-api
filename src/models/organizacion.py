from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Identity, Integer, String
from sqlalchemy.orm import relationship

from src.models.base import Base


class OrganizacionTipo(str, Enum):
    PRODUCTOR = "productor"
    ACOPIADOR = "acopiador"
    INTERMEDIARIO = "intermediario"
    EXPORTADOR = "exportador"
    COMPRADOR = "comprador"


class Organizacion(Base):
    """Organizacion model - maps to 'organizacion' table"""

    __tablename__ = "organizacion"

    nombre = Column(String, nullable=False)
    tipo = Column(
        Enum("productor", "acopiador", "intermediario", "exportador", "comprador",
             name="organizacion_tipo", create_type=False),
        nullable=False
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    org_id = Column(Integer, Identity(), primary_key=True)
    created_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=False)

    def __repr__(self):
        return f"<Organizacion(org_id={self.org_id}, nombre={self.nombre})>"