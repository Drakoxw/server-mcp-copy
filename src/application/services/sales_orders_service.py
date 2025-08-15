import requests
from typing import Dict, Any

from src.application.dtos.sales_and_orders.pedidos_response_dto import BodegaDTO, OperadorDTO, PedidosResponseDTO
from src.application.services.interfaces.sales_orders_service_interface import SalesOrdersServiceInterface
from src.infrastructure.api.http.ave_http_client import AveHttpClient
from src.tools.logger_config import LoggerSetup

logger = LoggerSetup(file_name="SalesOrder.log").create_module_logger("order")

class SalesOrdersService(SalesOrdersServiceInterface):

    def __init__(self, token: str):
        super().__init__()
        self.token = token
        self.BASE_URL = "https://app.aveonline.co/avestock/api/createOrder.php"

    async def create_order(self, payload: Dict[str, Any]) -> PedidosResponseDTO:
        try:
            logger.info(f"⚠️⚠️⚠️  payload  ⚠️⚠️⚠️ {payload}")
            client = AveHttpClient(self.token, 30)
            status, response = await client.post(self.BASE_URL, json=payload)

            logger.info(f"⚠️⚠️⚠️ response ⚠️⚠️⚠️ {response}")
            print("✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅")

            if status != 200:
                raise Exception(response)

            return self._map_to_dto(response)
        except Exception as e:
            return PedidosResponseDTO(success=False, messages=str(e))

    def _map_to_dto(self, data: Dict[str, Any]) -> PedidosResponseDTO:
        """
        Convierte el diccionario JSON en un ResponseDTO con subclases.
        """
        bodegas = None
        if "databodegas" in data and isinstance(data["databodegas"], list):
            bodegas = [
                BodegaDTO(
                    bodega_id=b.get("bodega_id"),
                    bodega_nombre=b.get("bodega_nombre"),
                    dataoperadores=[
                        OperadorDTO(**op) for op in b.get("dataoperadores", [])
                    ] if "dataoperadores" in b else None
                )
                for b in data["databodegas"]
            ]

        return PedidosResponseDTO(
            success=data.get("success", False),
            order_id=data.get("order_id"),
            messages=data.get("messages"),
            valortransporte=data.get("valortransporte"),
            id=data.get("id"),
            diasEntrega=data.get("diasEntrega"),
            kilosenvios=data.get("kilosenvios"),
            operador=data.get("operador"),
            bodegaContact=data.get("bodegaContact"),
            bodegaId=data.get("bodegaId"),
            bodegaTel=data.get("bodegaTel"),
            bodegaDir=data.get("bodegaDir"),
            bodegaEmail=data.get("bodegaEmail"),
            bodega_usuario=data.get("bodega_usuario"),
            bodega_id=data.get("bodega_id"),
            bodegaOrigen=data.get("bodegaOrigen"),
            # databodegas=bodegas
        )
