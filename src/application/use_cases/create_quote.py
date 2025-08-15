

from src.application.dtos.quote.shipment_request_dto import ShipmentRequestDTO
from src.application.dtos.quote.shipping_quote_response_dto import ShippingQuoteResponse
from src.application.services.interfaces.quotation_service_interface import QuotationServiceInterface


class CreateQuote:
    """ CASO DE USO PARA LA COTIZACION SIMPLE """
    def __init__(self, shipping_service: QuotationServiceInterface):
        self._shipping_service = shipping_service

    async def execute(self, payload: ShipmentRequestDTO, operatorId: int) -> ShippingQuoteResponse:
        return await self._shipping_service.quote(payload, operatorId)