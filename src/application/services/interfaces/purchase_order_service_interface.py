
from abc import ABC, abstractmethod

from src.application.dtos.orders.order_dto import OrderDto
from src.application.dtos.orders.order_response_dto import OrderResponseDto
from src.infrastructure.session.user_session import AveSession

class PurchaseOrderServiceInterface(ABC): 

    @abstractmethod
    async def generate(self, session: AveSession, data: OrderDto) -> OrderResponseDto:
        """ Generar una orden de compra con uno o mas detalles """
        pass