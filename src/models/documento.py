import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

TIPO_MAX_SIZE_BYTES = 20_971_520  # 20 MB

CONTENT_TYPES_PERMITIDOS = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

CONTENT_TYPE_PREFIXES_PERMITIDOS = [
    "image/",
]


def es_content_type_valido(content_type: str) -> bool:
    if content_type in CONTENT_TYPES_PERMITIDOS:
        return True
    for prefix in CONTENT_TYPE_PREFIXES_PERMITIDOS:
        if content_type.startswith(prefix):
            return True
    return False


def get_extension(content_type: str) -> str:
    extensions = {
        "application/pdf": "pdf",
        "application/msword": "doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "application/vnd.ms-excel": "xls",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    }
    if content_type in extensions:
        return extensions[content_type]
    if content_type.startswith("image/"):
        subtype = content_type.split("/")[-1]
        subtype_map = {
            "jpeg": "jpg",
            "svg+xml": "svg",
        }
        return subtype_map.get(subtype, subtype)
    return "bin"


class DocumentoUploadUrlRequest(BaseModel):
    nombre_original: str = Field(...)
    tipo_mime: str = Field(...)
    tamano_bytes: int = Field(...)
    categoria: Optional[str] = Field(default=None)
    descripcion: Optional[str] = Field(default=None)


class DocumentoConfirmRequest(BaseModel):
    file_key: str = Field(...)
    nombre_original: str = Field(...)
    tipo_mime: str = Field(...)
    tamano_bytes: int = Field(...)
    categoria: Optional[str] = Field(default=None)
    descripcion: Optional[str] = Field(default=None)


class DocumentoResponse(BaseModel):
    lote_documento_id: uuid.UUID
    url: str
    nombre_original: str
    nombre_archivo: str
    tipo_mime: str
    extension: str
    tamano_bytes: int
    categoria: Optional[str]
    descripcion: Optional[str]
    estado: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentoListItem(BaseModel):
    lote_documento_id: uuid.UUID
    url: str
    nombre_original: str
    tipo_mime: str
    tamano_bytes: int
    categoria: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
