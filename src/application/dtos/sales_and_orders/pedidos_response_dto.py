from dataclasses import dataclass
from typing import List, Optional


@dataclass
class OperadorDTO:
    status: Optional[int] = None
    message: Optional[str] = None
    flete: Optional[float] = None
    variable: Optional[float] = None
    comision: Optional[float] = None
    total: Optional[float] = None
    campo: Optional[int] = None
    transportadora: Optional[str] = None
    diasentrega: Optional[int] = None
    stringdata: Optional[str] = None
    bodegaId: Optional[str] = None
    bodegaTel: Optional[str] = None
    bodegaDir: Optional[str] = None
    bodegaEmail: Optional[str] = None
    bodega_usuario: Optional[str] = None
    bodega_id: Optional[str] = None
    bodegaOrigen: Optional[str] = None


@dataclass
class BodegaDTO:
    bodega_id: Optional[str] = None
    bodega_nombre: Optional[str] = None
    dataoperadores: Optional[List[OperadorDTO]] = None


@dataclass
class LogDTO:
    success: bool
    errors: Optional[str] = None
    lastId: Optional[int] = None


@dataclass
class GuideDTO:
    success: bool
    message: Optional[str] = None
    status: Optional[int] = None


@dataclass
class PedidosResponseDTO:
    success: bool
    messages: Optional[str] = None
    order_id: Optional[str] = None
    valortransporte: Optional[float] = None
    arrayTransportadoras: Optional[List] = None
    id: Optional[int] = None
    log: Optional[LogDTO] = None
    diasEntrega: Optional[int] = None
    operador: Optional[str] = None
    kilosenvios: Optional[float] = None
    bodegaContact: Optional[str] = None
    bodegaId: Optional[str] = None
    bodegaTel: Optional[str] = None
    bodegaDir: Optional[str] = None
    bodegaEmail: Optional[str] = None
    bodega_usuario: Optional[str] = None
    bodega_id: Optional[int] = None
    bodegaOrigen: Optional[str] = None
    dataoperadores: Optional[List[OperadorDTO]] = None
    guide: Optional[GuideDTO] = None
    totalAmount: Optional[float] = None
