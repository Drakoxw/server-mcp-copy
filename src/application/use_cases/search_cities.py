
from typing import List
from src.application.dtos.cities.city_response_dto import CityResponseDto
from src.application.services.cities_service import CitiesService


class SearchCities: 
    def __init__(self, service: CitiesService) -> None:
        self._service = service

    async def execute(self, query: str, quantity: int = 5) -> List[CityResponseDto]:
        return await self._service.search(query, quantity)