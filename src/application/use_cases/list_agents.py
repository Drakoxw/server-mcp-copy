

from typing import List
from src.application.dtos.agents.agents_response_dto import AgentsResponseDto
from src.application.services.interfaces.agents_service_interface import AgentsServiceInterface


class GetListAgents:

    def __init__(self, service: AgentsServiceInterface) -> None:
        self._service = service

    async def execute(self, enterprise_id: int, token: str) -> List[AgentsResponseDto]:
        return await self._service.list(enterprise_id, token)
    
    async def look_for_main(self, enterprise_id: int, token: str) -> int:
        """ Busca el agente principal """
        list = await self._service.list(enterprise_id, token)
        for agt in list:
            if agt.principal == 'SI':
                return agt.id
        
        if list.__len__() > 0:
            return list[0].id
        else: 
            return 0