from pydantic import BaseModel, ConfigDict
from typing import List


class VariedadResponse(BaseModel):
    variedad_id: int
    codigo: str
    model_config = ConfigDict(from_attributes=True)


class SubVariedadResponse(BaseModel):
    sub_variedad_id: int
    codigo: str
    variedad_id: int
    model_config = ConfigDict(from_attributes=True)


class TemporadaResponse(BaseModel):
    temporada_id: int
    codigo: str
    model_config = ConfigDict(from_attributes=True)


class ParametroResponse(BaseModel):
    parametro_id: int
    codigo: str
    value_type: str
    unidad_default: str | None = None
    model_config = ConfigDict(from_attributes=True)


class VariedadListResponse(BaseModel):
    data: List[VariedadResponse]


class SubVariedadListResponse(BaseModel):
    data: List[SubVariedadResponse]


class TemporadaListResponse(BaseModel):
    data: List[TemporadaResponse]


class ParametroListResponse(BaseModel):
    data: List[ParametroResponse]
