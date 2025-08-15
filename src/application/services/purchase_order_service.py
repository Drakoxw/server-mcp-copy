
import httpx
from src.application.dtos.orders.order_dto import OrderDto
from src.application.dtos.orders.order_response_dto import OrderResponseDto
from src.application.services.interfaces.purchase_order_service_interface import PurchaseOrderServiceInterface
from src.infrastructure.api.http.ave_http_client import AveHttpClient
from src.infrastructure.session.user_session import AveSession
from src.tools.logger_config import LoggerSetup

logger = LoggerSetup(file_name="order_compra.log").create_module_logger("list")

class PurchaseOrderService(PurchaseOrderServiceInterface): 

    async def generate(self, session: AveSession, data: OrderDto) -> OrderResponseDto:
        try:
            url = "https://app.aveonline.co/api/nal/v2.0/ordendeCompra.php"
            provider_id = 0

            json = {
                    "tipo":"generarorden",
                    "token": session.tokenBody,
                    "idempresa": session.idEnterprise,
                    "idagente": data.idagente,
                    "idproveedor": data.idproveedor,
                    "ordencompra": data.ordencompra,
                    "idtransportador": None,
                    "detalle" : [
                    {
                        "pedido": data.pedido,
                        "fecha_min": data.fecha_min,
                        "fecha_max": data.fecha_max,
                        "plu": data.plu, 
                        "ean": data.ean,
                        "referencia": data.referencia,
                        "nombre_articulo": data.nombre_articulo,
                        "descripcion": data.descripcion,
                        "cantidad_solicitada": data.cantidad_solicitada,
                        "precio": data.precio,
                        "total": data.total,
                        "valoracion": data.valoracion,
                        "cliente": data.cliente, 
                        "puntoventa": "",
                        "ciudad": data.ciudad, 
                        "departamento": data.departamento,
                        "direccion": data.direccion,
                        "tel": data.tel,
                        "correo": data.correo,
                        "observaciones": data.observaciones,
                        "peso": data.peso,
                        "alto": "1",
                        "largo": "2",
                        "ancho": "3",
                        "cartaporte": "",
                        "campana": "",
                        "guia": "",
                        "factura": "",
                        "fecha_redencion": "",
                        "codigo_dane": data.codigo_dane
                    }
                ]
            }

            client = AveHttpClient("", 30)
            _, response = await client.post(url, json=json)

            if response.get("status") == "ok":
                return OrderResponseDto(**response)

            return OrderResponseDto(codigo=[], message="No se pudo procesar la peticion", status="error")
        
        except httpx.RequestError as e:
            logger.warning(f"Request error for operator {provider_id}: {e}")
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP status error for operator {provider_id}: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error for operator {provider_id}: {e}")

        return OrderResponseDto(codigo=[], message="Hubo un error inesperado", status="error")