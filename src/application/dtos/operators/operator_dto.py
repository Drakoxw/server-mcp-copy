from pydantic import BaseModel


class OperatorResponseDto(BaseModel):
    id: int
    nombre: str
    imagen: str
    imagen2: str
