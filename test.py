
import asyncio
import time
from dotenv import load_dotenv

from src.application.dtos.sales_and_orders.pedidos_dto import ItemDTO, PedidoDTO
from src.application.dtos.sales_and_orders.pedidos_response_dto import PedidosResponseDTO
from src.application.use_cases.create_order import CreateOrder
load_dotenv()
import traceback
import sys

from fastapi import HTTPException


from src.application.services.sales_orders_service import SalesOrdersService
from src.infrastructure.session.session_service import session_service
from src.infrastructure.session.user_session import AveSession


async def test():
    try:
        session_data = await session_service.get_session('4fb89e40-e07c-4efe-9453-7346a62072ff')
        if session_data == None:
            raise HTTPException(status_code=404, detail="Sesión no encontrada o expirada")
        ave_session = AveSession(**session_data["ave_session"] or {})

        
        item = ItemDTO(**{
            "productRef": "dddd",
            "quantity": 1,
            "peso": 2,
        })

        # Construir el pedido
        pedido = PedidoDTO.from_minimal({
            "tipo": "authave",
            "empresa": ave_session.idEnterprise,
            "token": ave_session.tokenBody,
            "idAgente": 666,
            "items": [item],
            "clientDestino": "cali",
            "clientContact": "clientContact",
            "clientId": "25",
            "clientDir": "DIRECCIÓN PENDIENTE",
            "clientTel": "TELÉFONO PENDIENTE",
            "clientEmail": "EMAIL@PENDIENTE.COM",
            "paymentCliente": 1,
            "seloperadorEnvio": 123
        })

        print(f"Payload : {pedido}")

        service = SalesOrdersService(ave_session.token)
        response = CreateOrder(service).test(pedido)

        print(pedido)
        print('responseresponseresponseresponseresponseresponse')
        print(response)
 
    except Exception as e:
        # exc_type, exc_value, exc_tb = sys.exc_info()
        # filename = exc_tb.tb_frame.f_code.co_filename
        # line_no = exc_tb.tb_lineno
        # print(f"Error: {e} en {filename}, línea {line_no}")
        print(e)


if __name__ == "__main__":
    asyncio.run(test())