from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship

from src.models.base import Base


class UsuarioRol(str, Enum):
    ADMINISTRADOR_GLOBAL = "administrador_global"
    ADMINISTRADOR = "administrador"
    INVITADO = "invitado"
    LABORATORISTA = "laboratorista"


class UsuarioOrganizacionRol(Base):
    """UsuarioOrganizacionRol model - maps to 'usuario_organizacion_rol' table"""

    __tablename__ = "usuario_organizacion_rol"

    user_id = Column(Integer, ForeignKey("usuario.user_id"), nullable=False, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizacion.org_id"), nullable=False, primary_key=True)
    rol = Column(
        Enum("administrador_global", "administrador", "invitado", "laboratorista",
             name="usuario_rol", create_type=False),
        nullable=False, primary_key=True
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=False)

    # Relationships
    usuario = relationship("Usuario", foreign_keys=[user_id])
    organizacion = relationship("Organizacion", foreign_keys=[org_id])

    def __repr__(self):
        return f"<UsuarioOrganizacionRol(user_id={self.user_id}, org_id={self.org_id}, rol={self.rol})>"