from pydantic import BaseModel, HttpUrl
from typing import Optional, Union


class ShippingQuoteResponse(BaseModel):
    uuid: str
    numbererror: Optional[str] = ""
    dataerror: Optional[str] = ""
    codTransportadora: str
    nombreTransportadora: str
    logoTransportadora: Optional[HttpUrl]
    logoTransportadora2: Optional[HttpUrl]
    origen: str
    destino: str
    unidades: Union[int, str]  # Puede venir como string
    kilos: float
    pesovolumen: float
    valoracion: Union[int, float, str]
    porcentajeValoracion: Union[float, str]
    codigoTrayecto: Union[int, str]
    trayecto: Optional[str]
    tipoEnvio: Optional[str]
    fletexkilo: float
    fletexunidad: float
    fletetotal: float
    diasentrega: Union[int, str]
    costoManejo: float
    valorTotal: float
    valorOtrosRecaudos: float
    total: float
    valorTransRecaudoUrbano: float
    fleteUrbano: float
    costoRecaudoUrbano: float
    tipoServicio: Optional[str]
    categoria: Optional[str]
    recogidaEstimada: Optional[str]
    entregaEstimada: Optional[str]
