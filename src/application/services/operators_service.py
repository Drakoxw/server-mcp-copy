
from typing import List
from src.application.dtos.operators.operator_dto import OperatorResponseDto
from src.application.services.interfaces.operators_service_interface import OperatorsServiceInterface
from src.infrastructure.api.http.ave_http_client import AveHttpClient
class OperatorsService(OperatorsServiceInterface):

    def __init__(self, client: AveHttpClient) -> None:
        super().__init__()
        self.client = client

    async def list(self, token: str, enterprise_id: int) -> List[OperatorResponseDto]:
        url = "https://app.aveonline.co/api/box/v1.0/transportadora.php"
        path = "https://app.aveonline.co/app/temas/imagen_transpo/"
        operators = []

        json = {
            "tipo":"listarTransportadorasPorEmpresa",
            "token":token,
            "id": enterprise_id
        }

        _, response = await self.client.post(url, json=json)

        if response.get("status") == "ok" and isinstance(response["transportadoras"], list):
            for item in response["transportadoras"]:
                operators.append(OperatorResponseDto(id=item["id"], nombre=item["text"], imagen=path + item["imagen"], imagen2=path + item["imagen2"]))

        return operators