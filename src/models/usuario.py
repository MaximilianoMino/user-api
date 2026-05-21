import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Identity, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models import Organizacion


class Usuario(Base):
    """Usuario model - maps to 'usuario' table"""

    __tablename__ = "usuario"

    user_id = Column(Integer, Identity(), primary_key=True)
    auth_user_id = Column(UUID(as_uuid=True), unique=True, nullable=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    telefono = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=True)

    # Relationships
    organizaciones = relationship(
        "UsuarioOrganizacionRol",
        back_populates="usuario",
        foreign_keys="UsuarioOrganizacionRol.user_id",
    )

    def __repr__(self):
        return f"<Usuario(user_id={self.user_id}, email={self.email})>"