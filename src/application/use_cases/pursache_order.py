

from src.application.dtos.orders.order_dto import OrderDto
from src.application.services.purchase_order_service import PurchaseOrderService
from src.infrastructure.session.user_session import AveSession

class PursacheOrder:

    def __init__(self, service: PurchaseOrderService) -> None:
        self._service = service

    async def execute(self, session: AveSession, data: OrderDto):
        return await self._service.generate(session, data)