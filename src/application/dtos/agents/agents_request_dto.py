from typing import Literal
from pydantic import BaseModel


class AgentsRequestDto(BaseModel):
    tipo: str = "listarAgentesPorEmpresaAuth"
    token: str
    idempresa: int
