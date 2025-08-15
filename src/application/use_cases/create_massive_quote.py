

from src.application.dtos.quote.shipment_request_dto import ShipmentRequestDTO
from src.application.dtos.quote.shipping_quote_response_dto import ShippingQuoteResponse
from src.application.services.interfaces.quotation_service_interface import QuotationServiceInterface

class CreateMasiveQuote:
    """ CASO DE USO PARA LA COTIZACION MASIVA A TODOS LOS OPERADORES """
    def __init__(self, shipping_service: QuotationServiceInterface):
        self._shipping_service = shipping_service

    async def execute(self, shipping_quote: ShipmentRequestDTO) -> list[ShippingQuoteResponse]:
        return await self._shipping_service.quote_masive(shipping_quote)