
import asyncio
import requests
import httpx
from typing import List
from src.application.dtos.quote.shipment_request_dto import ShipmentRequestDTO
from src.application.dtos.quote.shipping_quote_response_dto import ShippingQuoteResponse
from src.application.services.interfaces.quotation_service_interface import QuotationServiceInterface
from src.infrastructure.api.http.ave_http_client import AveHttpClient
from src.tools.logger_config import LoggerSetup

logger = LoggerSetup(file_name="QuotationService.log").create_module_logger("quotation")

class QuotationService(QuotationServiceInterface):

    def __init__(self, client: AveHttpClient) -> None:
        super().__init__()
        self.client = client
        self.endpoint = "https://logistic.api.aveonline.co/api/guides/quote/v1/operator-quote-shipping"
        self.operators = [1028, 1009, 1026, 29, 1031, 1016, 1027, 33, 1010]

    async def quote_masive(self, payload: ShipmentRequestDTO) -> List[ShippingQuoteResponse]:
        tasks = [self._quote_for_operator(payload, operator_id) for operator_id in self.operators]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        quotes = []
        for result in results:
            if isinstance(result, ShippingQuoteResponse):
                quotes.append(result)
            elif isinstance(result, list):
                quotes.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Error during concurrent request: {result}")

        return quotes

    async def _quote_for_operator(self, base_payload: ShipmentRequestDTO, operator_id: int):
        payload_copy = base_payload.model_copy(deep=True)
        payload_copy.idtransportador = operator_id

        try:
            _, response = await self.client.post(self.endpoint, json=payload_copy.model_dump())

            if response.get("status") == "ok" and isinstance(response["data"], dict):
                return ShippingQuoteResponse(**response["data"])

            elif isinstance(response.get("data"), list):  # fallback for list-style data
                return [ShippingQuoteResponse(**item) for item in response["data"]]

        except httpx.RequestError as e:
            logger.warning(f"Request error for operator {operator_id}: {e}")
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP status error for operator {operator_id}: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error for operator {operator_id}: {e}")
        return None
    
    async def quote(self, payload: ShipmentRequestDTO, operatorId: int) -> List[ShippingQuoteResponse]:
        url = "https://logistic.api.aveonline.co/api/guides/quote/v1/operator-quote-shipping"

        try:
            json = payload.model_dump()
            json["idtransportador"] = operatorId
            status, response = await self.client.post(url, json=json)

            if (status != 200):
                logger.warning(f"Bad Request Ave: {response}")

            if response.get("status") == "ok":
                return [ShippingQuoteResponse(**response.get("data"))]

            return []

        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

        return []

