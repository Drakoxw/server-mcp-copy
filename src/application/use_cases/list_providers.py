from typing import List
from src.application.dtos.providers.provider_response_dto import ProviderResponseDto
from src.application.services.providers_service import ProvidersService


class ListProviders:

    def __init__(self, service: ProvidersService) -> None:
        self._service = service

    async def execute(self, token: str, enterprise_id: int) -> List[ProviderResponseDto]:
        return await self._service.list(enterprise_id, token)