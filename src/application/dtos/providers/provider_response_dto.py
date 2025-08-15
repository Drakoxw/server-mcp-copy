

from pydantic import BaseModel

class ProviderResponseDto(BaseModel):
    idproveedor: int
    nombreproveedor: str
    telefonoproveedor: str
    direccionproveedor: str
    ciudadproveedor: str