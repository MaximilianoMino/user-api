import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy import Boolean
from sqlalchemy.dialects.postgresql import JSON, JSONB, UUID
from sqlalchemy.orm import relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models import Muestra, Lote


# === Tablas del DDL ===

class EvidenciaEspecial(Base):
    """EvidenciaEspecial model - maps to 'evidencia_especial' table"""
    __tablename__ = "evidencia_especial"

    evidencia_especial_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analisis_especial_id = Column(UUID(as_uuid=True), ForeignKey("analisis_especial.analisis_especial_id"), nullable=False)
    tipo = Column(Enum("foto", "video", "documento", name="evidencia_especial_tipo", create_type=False), nullable=False)
    url = Column(String, nullable=False)
    metadatos = Column(JSONB, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=True)


class AnalisisEspecialStatus(str, Enum):
    SOLICITADO = "solicitado"
    INICIADO = "iniciado"
    REALIZADO = "realizado"
    INVALIDADO = "invalidado"
    RECHAZADO = "rechazado"


class AnalisisEspecialTipo(str, Enum):
    TRAZABILIDAD_AGROQUIMICOS = "trazabilidad_agroquimicos"
    ANALISIS_GERMINATIVO = "analisis_germinativo"
    HIDRATACION_COCcion = "hidratacion_coccion"
    OTROS = "otros"


class AnalisisEspecial(Base):
    """AnalisisEspecial model - maps to 'analisis_especial' table"""
    __tablename__ = "analisis_especial"

    analisis_especial_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lote_id = Column(UUID(as_uuid=True), ForeignKey("lote.lote_id"), nullable=False)
    tipo = Column(
        Enum("trazabilidad_agroquimicos", "analisis_germinativo", "hidratacion_coccion", "otros",
             name="analisis_especial_tipo", create_type=False),
        nullable=False
    )
    tipo_descripcion = Column(String, nullable=True)
    status = Column(
        Enum("solicitado", "iniciado", "realizado", "invalidado", "rechazado",
             name="analisis_especial_status", create_type=False),
        nullable=False, default="solicitado"
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=True)


class AnalisisFuenteImagen(Base):
    """AnalisisFuenteImagen model - maps to 'analisis_fuente_imagen' table"""
    __tablename__ = "analisis_fuente_imagen"

    analisis_fuente_imagen_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analisis_id = Column(UUID(as_uuid=True), ForeignKey("analisis.analisis_id"), nullable=False)
    nombre_original = Column(String, nullable=False)
    nombre_archivo = Column(String, nullable=False)
    tipo_mime = Column(String, nullable=False)
    extension = Column(String, nullable=True)
    url = Column(String, nullable=False)
    tamano_bytes = Column(Integer, nullable=True)
    origen = Column(String, nullable=True)
    estado_lectura_ia = Column(
        Enum("pendiente", "procesando", "procesada", "revisada", "rechazada", "error",
             name="lectura_ia_status", create_type=False),
        nullable=False, default="pendiente"
    )
    texto_crudo_ocr = Column(Text, nullable=True)
    respuesta_ia_json = Column(JSON, nullable=True)
    confianza_global = Column(Numeric, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=True)


class AnalisisResultadoIa(Base):
    """AnalisisResultadoIa model - maps to 'analisis_resultado_ia' table"""
    __tablename__ = "analisis_resultado_ia"

    resultado_ia_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analisis_fuente_imagen_id = Column(UUID(as_uuid=True), ForeignKey("analisis_fuente_imagen.analisis_fuente_imagen_id"), nullable=False)
    analisis_id = Column(UUID(as_uuid=True), ForeignKey("analisis.analisis_id"), nullable=False)
    parametro_id = Column(Integer, ForeignKey("parametro.parametro_id"), nullable=False)
    valor_leido = Column(Numeric, nullable=True)
    unidad_leida = Column(String, nullable=True)
    texto_original = Column(String, nullable=True)
    out_of_range_detectado = Column(Boolean, nullable=False, default=False)
    confianza = Column(Numeric, nullable=True)
    comentario_ia = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=True)


class LecturaIaStatus(str, Enum):
    PENDIENTE = "pendiente"
    PROCESANDO = "procesando"
    PROCESADA = "procesada"
    REVISADA = "revisada"
    RECHAZADA = "rechazada"
    ERROR = "error"


class LoteMuestraFuenteImagenIa(Base):
    """LoteMuestraFuenteImagenIa model - maps to 'lote_muestra_fuente_imagen_ia' table"""
    __tablename__ = "lote_muestra_fuente_imagen_ia"

    lote_muestra_fuente_imagen_ia_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lote_id = Column(UUID(as_uuid=True), ForeignKey("lote.lote_id"), nullable=False)
    muestra_id = Column(UUID(as_uuid=True), ForeignKey("muestra.muestra_id"), nullable=True)
    nombre_original = Column(String, nullable=False)
    nombre_archivo = Column(String, nullable=False)
    tipo_mime = Column(String, nullable=False)
    extension = Column(String, nullable=True)
    url = Column(String, nullable=False)
    tamano_bytes = Column(Integer, nullable=True)
    estado_lectura_ia = Column(
        Enum("pendiente", "procesando", "procesada", "revisada", "rechazada", "error",
             name="lectura_ia_status", create_type=False),
        nullable=False, default="pendiente"
    )
    variedad_id_sugerida = Column(Integer, ForeignKey("variedad.variedad_id"), nullable=True)
    sub_variedad_id_sugerida = Column(Integer, ForeignKey("sub_variedad.sub_variedad_id"), nullable=True)
    observaciones_sugeridas = Column(Text, nullable=True)
    peso_muestra_sugerido = Column(Numeric, nullable=True)
    unidad_peso_sugerida = Column(String, nullable=True)
    texto_crudo_ocr = Column(Text, nullable=True)
    respuesta_ia_json = Column(JSON, nullable=True)
    confianza_global = Column(Numeric, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=True)


class LoteDocumentoStatus(str, Enum):
    ACTIVO = "activo"
    ARCHIVADO = "archivado"
    ELIMINADO = "eliminado"


class LoteDocumento(Base):
    """LoteDocumento model - maps to 'lote_documento' table"""
    __tablename__ = "lote_documento"

    lote_documento_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lote_id = Column(UUID(as_uuid=True), ForeignKey("lote.lote_id"), nullable=False)
    nombre_original = Column(String, nullable=False)
    nombre_archivo = Column(String, nullable=False)
    tipo_mime = Column(String, nullable=False)
    extension = Column(String, nullable=True)
    url = Column(String, nullable=False)
    tamano_bytes = Column(Integer, nullable=True)
    categoria = Column(String, nullable=True)
    descripcion = Column(Text, nullable=True)
    estado = Column(
        Enum("activo", "archivado", "eliminado", name="lote_documento_status", create_type=False),
        nullable=False, default="activo"
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=True)


class FichaEstado(str, Enum):
    ACTIVA = "activa"
    REVOCADA = "revocada"


class FichaPermiso(str, Enum):
    PUBLIC_LINK = "public_link"
    INVITED_ONLY = "invited_only"


class FichaReporte(Base):
    """FichaReporte model - maps to 'ficha_reporte' table"""
    __tablename__ = "ficha_reporte"

    ficha_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    muestra_id = Column(UUID(as_uuid=True), ForeignKey("muestra.muestra_id"), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    link_token = Column(String, nullable=False, unique=True)
    permisos = Column(
        Enum("public_link", "invited_only", name="ficha_permiso", create_type=False),
        nullable=False
    )
    estado = Column(
        Enum("activa", "revocada", name="ficha_estado", create_type=False),
        nullable=False, default="activa"
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=True)
    lote_id = Column(UUID(as_uuid=True), ForeignKey("lote.lote_id"), nullable=False)

    # Relationships
    muestra = relationship("Muestra", foreign_keys=[muestra_id])
    lote = relationship("Lote", foreign_keys=[lote_id])


class FichaReporteInvitado(Base):
    """FichaReporteInvitado model - maps to 'ficha_reporte_invitado' table"""
    __tablename__ = "ficha_reporte_invitado"

    ficha_id = Column(UUID(as_uuid=True), ForeignKey("ficha_reporte.ficha_id"), nullable=False, primary_key=True)
    invited_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("usuario.user_id"), nullable=False, primary_key=True)


class PlantillaAnalisis(Base):
    """PlantillaAnalisis model - maps to 'plantilla_analisis' table"""
    __tablename__ = "plantilla_analisis"

    nombre = Column(String, nullable=False)
    version = Column(String, nullable=True)
    descripcion = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=False)
    plantilla_id = Column(Integer, primary_key=True, autoincrement=True)


class PlantillaParametro(Base):
    """PlantillaParametro model - maps to 'plantilla_parametro' table"""
    __tablename__ = "plantilla_parametro"

    rubro = Column(Enum("defectos_graves", "defectos_intensos", "defectos_leves", name="rubro_tipo", create_type=False), nullable=True)
    aplica = Column(Boolean, nullable=False, default=True)
    obligatorio = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    parametro_id = Column(Integer, ForeignKey("parametro.parametro_id"), nullable=False, primary_key=True)
    variedad_id = Column(Integer, ForeignKey("variedad.variedad_id"), nullable=False, primary_key=True)
    created_by = Column(Integer, ForeignKey("usuario.user_id"), nullable=False, primary_key=True)
    plantilla_id = Column(Integer, ForeignKey("plantilla_analisis.plantilla_id"), nullable=False, primary_key=True)


# === Tablas i18n (no están en el DDL pero podrían existir) ===
# Estas tablas no están en el DDL proporcionado, las omito por ahora