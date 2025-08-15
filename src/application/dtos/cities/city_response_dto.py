from typing import Literal
from pydantic import BaseModel


class CityResponseDto(BaseModel):
    nombre: str
    codigoDANE: str
    id: int
