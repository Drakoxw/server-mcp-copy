
from typing import List
from src.application.dtos.agents.agents_response_dto import AgentsResponseDto
from src.application.services.interfaces.agents_service_interface import AgentsServiceInterface
from src.infrastructure.api.http.ave_http_client import AveHttpClient


class AgentsService(AgentsServiceInterface):
    
    def __init__(self, client: AveHttpClient) -> None:
        super().__init__()
        self.client = client

    async def list(self, enterprise_id:int, token: str) -> List[AgentsResponseDto]:

        url = "https://app.aveonline.co/api/comunes/v1.0/agentes.php"

        json = {
            "tipo": "listarAgentesPorEmpresaAuth",
            "token": token,
            "idempresa": enterprise_id
        }

        _, response = await self.client.post(url, json=json)

        if response.get("status") == "ok" and isinstance(response["agentes"], list):
            return [AgentsResponseDto(**item) for item in response["agentes"]]

        return []