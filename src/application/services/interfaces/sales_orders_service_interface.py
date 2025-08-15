from abc import ABC, abstractmethod
import requests
from typing import Dict, Any

from src.application.dtos.sales_and_orders.pedidos_response_dto import PedidosResponseDTO

class SalesOrdersServiceInterface(ABC):  
    @abstractmethod  
    async def create_order(self, payload: Dict[str, Any]) -> PedidosResponseDTO:
        """
        Envía una solicitud para crear un pedido en Aveonline.

        :param payload: Diccionario con los datos del pedido.
        :return: Objeto ResponseDTO con la respuesta.
        """
