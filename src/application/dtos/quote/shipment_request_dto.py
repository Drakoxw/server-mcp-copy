from pydantic import BaseModel, Field
from typing import List, Optional, Union


class ProductDTO(BaseModel):
    alto: Union[int, float, str]
    largo: Union[int, float, str]
    ancho: Union[int, float, str]
    peso: str
    unidades: int
    nombre: str
    valorDeclarado: str


class LocationDTO(BaseModel):
    address: Optional[str] = ""
    latitude: Optional[str] = ""
    longitude: Optional[str] = ""


class ShipmentRequestDTO(BaseModel):
    idAgente: int
    idtransportador: int
    idempresa: int
    origen: str
    destino: str
    valorrecaudo: Optional[int] = 0
    valorMinimo: Optional[int] = 1
    idasumecosto: Optional[int] = 0
    contraentrega: Optional[int] = 0
    productos: List[dict]
