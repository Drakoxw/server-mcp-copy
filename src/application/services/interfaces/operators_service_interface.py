
from abc import ABC, abstractmethod
from typing import List

from src.application.dtos.operators.operator_dto import OperatorResponseDto

class OperatorsServiceInterface(ABC):

    @abstractmethod
    async def list(self, token: str, enterprise_id: int) -> List[OperatorResponseDto]:
        """ Lista de operadores logisticos asosiados a al usuario """
        pass