from src.application.dtos.cities.city_response_dto import CityResponseDto
from src.application.services.interfaces.cities_service_interface import CitiesServiceInterface
from src.infrastructure.api.http.ave_http_client import AveHttpClient

class CitiesService(CitiesServiceInterface):

    def __init__(self, client: AveHttpClient) -> None:
        super().__init__()
        self.client = client

    async def search(self, query: str, quantity: int = 5):
        url = "https://app.aveonline.co/api/box/v1.0/ciudad.php"

        json = {
            "tipo": "listar",
            "data": query,
            "registros": quantity
        }

        _, response = await self.client.post(url, json=json)

        if response.get("status") == "ok" and isinstance(response["ciudades"], list):
            return [CityResponseDto(**item) for item in response["ciudades"]]

        return []