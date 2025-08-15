from abc import ABC, abstractmethod
from typing import List

from src.application.dtos.agents.agents_response_dto import AgentsResponseDto


class AgentsServiceInterface(ABC):

    @abstractmethod
    async def list(self, enterprise_id:int, token: str) -> List[AgentsResponseDto]:
        """ LISTADO DE LOS AGENTES """
        pass