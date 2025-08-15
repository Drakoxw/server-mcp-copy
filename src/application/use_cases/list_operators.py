
from typing import List
from src.application.dtos.operators.operator_dto import OperatorResponseDto
from src.application.services.interfaces.operators_service_interface import OperatorsServiceInterface


class ListOperators:

    def __init__(self, service: OperatorsServiceInterface) -> None:
        self._service = service

    async def execute(self, token: str, enterprise_id: int) -> List[OperatorResponseDto]:
        return await self._service.list(token, enterprise_id)