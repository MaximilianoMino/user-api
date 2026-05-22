from typing import List, Optional

from pydantic import BaseModel


class ParametroSugerido(BaseModel):
    nombre: str
    valor: float
    unidad: str
    parametro_id: Optional[int] = None
    codigo_db: Optional[str] = None


class IAResponse(BaseModel):
    parametros: List[ParametroSugerido]
    texto_original: str
    mensaje: Optional[str] = None

    class Config:
        from_attributes = True
