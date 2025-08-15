from abc import ABC, abstractmethod

from src.application.dtos.quote.shipment_request_dto import ShipmentRequestDTO
from src.application.dtos.quote.shipping_quote_response_dto import ShippingQuoteResponse
from src.infrastructure.api.http.ave_http_client import AveHttpClient

class QuotationServiceInterface(ABC):  
    @abstractmethod  
    async def quote_masive(self, payload: ShipmentRequestDTO) -> list[ShippingQuoteResponse]:
        """ METODO PARA GENERAR LA COTIZACION MASIVA """
        pass

    @abstractmethod  
    async def quote(self, payload: ShipmentRequestDTO, operatorId: int) -> ShippingQuoteResponse:
        """ METODO PARA GENERAR LA COTIZACION A UNA SOLA TRANSPORTADORA"""
        pass

    
    