from src.application.dtos.sales_and_orders.pedidos_dto import PedidoDTO
from src.application.dtos.sales_and_orders.pedidos_response_dto import PedidosResponseDTO
from src.application.services.sales_orders_service import SalesOrdersService

class CreateOrder:
    """Caso de uso para generar una orden"""
    def __init__(self, service: SalesOrdersService):
        self.service = service

    async def execute(self, payload: PedidoDTO) -> PedidosResponseDTO:
        return await self.service.create_order(payload.model_dump())
    
    def test(self, payload: PedidoDTO):
        return payload.model_dump()