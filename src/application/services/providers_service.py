

from typing import List
from src.application.dtos.providers.provider_response_dto import ProviderResponseDto
from src.application.services.interfaces.providers_service_interface import ProvidersServiceInterface
from src.infrastructure.api.http.ave_http_client import AveHttpClient
from src.tools.logger_config import LoggerSetup

logger = LoggerSetup(file_name="OperatorsService.log").create_module_logger("list")

class ProvidersService(ProvidersServiceInterface):

    def __init__(self) -> None:
        super().__init__()

    async def list(self, enterprise_id:int, token: str) -> List[ProviderResponseDto]:
        url = "https://app.aveonline.co/api/nal/v2.0/ordendeCompra.php"

        json = {
            "tipo": "listarproveedores",
            "token": token,
            "idempresa": enterprise_id
        }

        client = AveHttpClient("", 30)
        _, response = await client.post(url, json=json)

        if response.get("status") == "ok" and isinstance(response["proveedores "], list):
            return [ProviderResponseDto(**item) for item in response["proveedores "]]

        return []