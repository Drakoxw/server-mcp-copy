from pydantic import BaseModel, EmailStr
from typing import Optional, Union, Literal

class AgentsResponseDto(BaseModel):
    id: int
    nombre: str
    identificacion: Union[int, str] 
    email: EmailStr
    direccion: str
    comentarios: Optional[str] = ""
    comentario_direccion: Optional[str] = ""
    telefono: str
    idordenrecogida: int
    idciudad: str
    principal: Literal["SI", "NO"]
    nombrecontacto: Optional[str] = None
    tienevalorminimo: bool
