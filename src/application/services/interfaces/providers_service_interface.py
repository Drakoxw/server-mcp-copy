

from abc import ABC, abstractmethod
from typing import List
from src.application.dtos.providers.provider_response_dto import ProviderResponseDto


class ProvidersServiceInterface(ABC):

    @abstractmethod
    async def list(self, enterprise_id:int, token: str) -> List[ProviderResponseDto]:
        """ Lista los proveedores """
        pass