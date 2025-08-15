from pydantic import BaseModel
from typing import List

class CodigoItem(BaseModel):
    id: str
    text: str

class OrderResponseDto(BaseModel):
    status: str
    message: str
    codigo: List[CodigoItem]
