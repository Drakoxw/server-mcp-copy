"""
main.py - Servidor MCP con herramientas de AveOnline
"""

import os
import threading
from typing import Optional
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
from dotenv import load_dotenv

from src.application.dtos.sales_and_orders.pedidos_dto import ItemDTO, PedidoDTO
from src.application.services.sales_orders_service import SalesOrdersService
from src.application.use_cases.create_order import CreateOrder
load_dotenv()

from src.application.dtos.quote.shipment_request_dto import ShipmentRequestDTO
from src.infrastructure.session.user_session import AveSession

from callback_server import start_callback_server
from src.application.auth.oauth_service import create_oauth_url
from src.infrastructure.session.session_service import session_service
# Cargar variables de entorno

# Importar las herramientas
from src.application.auth.ave_online_auth import AveOnlineAuth
from src.application.services.agents_service import AgentsService
from src.application.services.cities_service import CitiesService
from src.application.services.operators_service import OperatorsService
from src.application.services.quotation_service import QuotationService
from src.application.use_cases.create_massive_quote import CreateMasiveQuote
from src.application.use_cases.search_cities import SearchCities
from src.infrastructure.api.http.ave_http_client import AveHttpClient
from src.tools.base.ip import IpTool
from src.tools.logger_config import LoggerSetup
from src.tools.informational.ave_online_tool import AveOnlineInfoTool
from src.application.use_cases.list_agents import GetListAgents
from src.application.use_cases.list_operators import ListOperators
from src.application.use_cases.list_providers import ListProviders
from src.application.use_cases.pursache_order import PursacheOrder
from src.application.dtos.orders.order_dto import OrderDto
from src.application.services.providers_service import ProvidersService
from src.application.services.purchase_order_service import PurchaseOrderService

start_callback_server()

# Crear el servidor MCP
mcp = FastMCP(
    name="AveOnline MCP Server",
)

HOST_URI = "0.0.0.0"
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# Loggers específicos para diferentes módulos
auth_logger = LoggerSetup(file_name="auth_logger.log").get_logger()
api_logger = LoggerSetup(file_name="api_logger.log").get_logger()
oauth_logger = LoggerSetup(file_name="oauth_logger.log").get_logger()

# Inicializar el gestor de sesiones

CUSTOM_SESSION_HEADERS = "x_session_token"

# Crear instancia de la herramienta
aveonline_info = AveOnlineInfoTool()
aveonline_auth = AveOnlineAuth()
http_client = AveHttpClient("")


ip_tool = IpTool()

# ============================================================================
# HERRAMIENTAS INFORMATIVAS DE AVEONLINE
# ============================================================================
@mcp.tool()
def aveonline_info_tool(
    query_type: str,
    service_name: str = "",
    category: str = ""
) -> dict:
    """
    Proporciona información detallada sobre servicios y ventajas de AveOnline
    
    Args:
        query_type: Tipo de consulta (overview, services, service_detail, benefits, integration_info, pricing_info, contact_info)
        service_name: Servicio específico (shipping_quotes, tracking_system, api_integration, smart_logistics, customer_support)
        category: Filtrar por categoría (logistics, technology, customer_service, tracking, integration)
    
    Returns:
        dict: Información solicitada sobre AveOnline
    """
    params = {"query_type": query_type}
    
    if service_name:
        params["service_name"] = service_name
    
    if category:
        params["category"] = category
    
    return aveonline_info.execute(params)

@mcp.tool()
def company_quick_info() -> dict:
    """
    Información rápida y básica sobre AveOnline
    
    Returns:
        dict: Información básica de la empresa
    """
    return aveonline_info.company_quick_info()

# Herramienta para obtener información de contacto específica
@mcp.tool()
def get_contact_info(department: str = "general") -> dict:
    """
    Obtiene información de contacto de AveOnline
    
    Args:
        department: Departamento específico (sales, general)
    
    Returns:
        dict: Información de contacto
    """
    contacts = {
        "sales": {
            "email": "pqr@aveonline.co",
            "phone": "+57 3054202125",
            "whatsapp": "+57 3054202125",
            "hours": "Lunes a Viernes 7:00 AM - 5:00 PM (COT)"
        },
        "general": {
            "website": "https://aveonline.co/",
            "headquarters": "Medellín, Colombia",
            "address": "Calle 37 sur # 28C 60 Envigado - Antioquia",
            "social": {
                "facebook": "https://web.facebook.com/aveonlineoficial",
                "linkedin": "https://co.linkedin.com/company/ave-online",
                "twitter": "@AveOnline"
            }
        }
    }
    
    return contacts.get(department, contacts["general"])

# Herramienta para verificar cobertura geográfica
@mcp.tool()
def check_coverage(country: str = "") -> dict:
    """
    Verifica la cobertura de AveOnline en países y ciudades
    
    Args:
        country: País a verificar (opcional)
    
    Returns:
        dict: Información de cobertura
    """
    return aveonline_info.coverage_data(country)

@mcp.tool
async def request_header_info() -> dict:
    """Permite validar los headers de las solicitudes incluyendo información de IP"""

    headers = get_http_headers()
    
    auth_header = headers.get("authorization", "")
    is_bearer = auth_header.startswith("Bearer ")
    
    # Obtener información de IP del cliente
    client_ip = ip_tool.get_ip()
    
    # Información adicional de IP
    proxy_ips = []
    if "x-forwarded-for" in headers:
        proxy_ips = [ip.strip() for ip in headers["x-forwarded-for"].split(",")]
    
    return {
        "user-ip": headers.get("x-user-ip", "Unknown"),
        "user_agent": headers.get("user-agent", "Unknown"),
        "content_type": headers.get("content-type", "Unknown"),
        "has_auth": bool(auth_header),
        "auth_type": "Bearer" if is_bearer else "Other" if auth_header else "None",
        "headers_count": len(headers),
        "client_ip": client_ip,
        "proxy_chain": proxy_ips if len(proxy_ips) > 1 else None,
        "is_proxied": bool(headers.get("x-forwarded-for") or headers.get("x-real-ip")),
        "cloudflare_ip": headers.get("cf-connecting-ip"),
        "headers": headers
    }

# ============================================================================
# HERRAMIENTAS DE AUTENTICACIÓN
# ============================================================================

# @mcp.tool()
# async def login_in_ave(username: str, password: str) -> dict:
#     """
#     Inicia sesión de usuario en AveOnline, requiere un username y password
    
#     Returns:
#          dict: Información de la sesión creada, El 'session_token' es el token de sesión generado y se usara para autenticación futuras solicitudes
#     """
#     try:
#         headers = get_http_headers()
#         response = await aveonline_auth.login(username=username, password=password)

#         if response.get("error"):
#             response["code"] = "AVE_LOGIN_ERROR"
#             return response
        
#         session = await session_manager.create_session_ave(response["data"], headers)
#         return {
#             "error": False,
#             "message": "Login successful",
#             "session_token": session.session_token,
#             "user_info": {
#                 "user_id": session.user_id,
#                 "username": session.username,
#                 "email": session.email,
#                 "permissions": session.permissions
#             },
#         }
#     except Exception as e:
#         return {
#             "error": True,
#             "message": str(e),
#             "code": "LOGIN_ERROR_UKN"
#         }

@mcp.tool()
async def oauth_login() -> dict:
    """
    Genera una url para realizar la autenticación OAuth con Google y tambien un session_id para el callback.
    Se debe abrir la url en el navegador para iniciar el flujo de autenticación.
    Al completar el OAuth se podra usar el session_id para usar las herramientas que requieran autenticación.

    Returns:
        dict: Un diccionario con las claves:
            - `session_token` (str): Token de sesión activo. Usa este mismo token para futuras solicitudes que requieran autenticación.
            - `oauth_url` (str): URL para realizar la autenticación OAuth con Google.
    """
    try:
        oauth = await create_oauth_url()

        return {
            "error": False,
            "message": "Abre este enlace en tu navegador para iniciar el flujo de autenticación OAuth",
            "session_token": oauth.get("session_id", ""),
            "oauth_url": oauth.get("auth_url", "")
        }

    except Exception as e:
        return {
            "error": True,
            "message": str(e),
            "code": "LOGIN_ERROR"
        }

# ============================================================================
# HERRAMIENTAS CON MUTACIONES EN LOS DATOS DE AVEONLINE (AUTH REQUIRED)
# ============================================================================
@mcp.tool()
async def create_shipping_quote(
    city_of_origin: str,
    city_of_destination: str,
    weight: Optional[int], 
    declared_value: Optional[int] = 10000, 
    value_to_be_collected: Optional[int] = 0, 
    units: Optional[int] = 1, 
    width: Optional[int] = 1, 
    height: Optional[int] = 1, 
    length: Optional[int] = 1, 
    agent_id: Optional[int] = 0, 
    description: Optional[str] ="No info",
    session_token: Optional[str] = ""
):
    """
    Realiza una cotización de envío a través de la plataforma Aveonline.

    Esta herramienta permite obtener un listado de cotizaciones de envío (mensajería o paquetería) basado en los parámetros físicos y económicos del paquete, 
    como ciudades, peso, dimensiones, valor declarado y forma de pago. Las cotizaciones se obtienen desde Aveonline y pueden incluir múltiples operadores logísticos.

    ⚠️ La autenticación puede realizarse de las siguientes maneras (en orden de prioridad):
    - Si no se proporciona ningún token, se forzará el flujo de autenticación OAuth.
    - A través del argumento `session_token`
    - Vía header HTTP personalizado: `x_session_token`
    - Alternativamente, también se puede usar el token `meteor_token` como parámetro o encabezado (`x-meteor-header`)
    
    Si no se proporciona ningún token, se forzará el flujo de autenticación OAuth.

    Args:
        city_of_origin (str): Ciudad de origen (ej: "MEDELLIN(ANTIOQUIA)")
        city_of_destination (str): Ciudad de destino (misma convención que origen)
        weight (int): Peso del envío en kilogramos
        declared_value (int, optional): Valor declarado del envío en pesos, minimo 10000. Defaults to 10000.
        value_to_be_collected (int, optional): Valor a recaudar en destino (contraentrega). Defaults to 0.
        units (int, optional): Número de unidades o bultos del envío. Defaults to 1.
        width (int, optional): Ancho del paquete en centímetros. Defaults to 1.
        height (int, optional): Alto del paquete en centímetros. Defaults to 1.
        length (int, optional): Largo del paquete en centímetros. Defaults to 1.
        agent_id (int, optional): ID del agente autorizado para cotizar. Si no se especifica, se tomará el agente principal del usuario. Defaults to 0.
        description (str, optional): Descripción general del envío. Defaults to "".
        session_token (str, optional): Token de sesión activo generado por Aveonline. Si se omite, se espera que esté presente en el header `x_session_token`.

    Returns:
        dict: Un diccionario con las claves:
            - `session_token` (str): Token de sesión activo. Usa este mismo token para futuras solicitudes que requieran autenticación.
            - `data` (list[dict]): Lista de cotizaciones por operador logístico. Cada item incluye costos y detalles donde el campo `total` representa el valor a pagar.

    """
    session_data = await session_service.get_session(session_token or "")
    if session_token == "" or session_data == None:
        oauth = await create_oauth_url()
        return {
            "error": True,
            "message": "Abre este enlace en tu navegador para iniciar el flujo de autenticación OAuth y vuelve a intertarlo cuando se complete el flujo",
            "session_token": oauth.get("session_id", ""),
            "oauth_url": oauth.get("auth_url", "")
        }
    
    if not city_of_origin or not city_of_destination:
        return {
            "error": True,
            "message": "Debe proporcionar ciudad de origen y destino",
            "code": "MISSING_CITY"
        }
    # headers = get_http_headers()
    ave_session = AveSession(**session_data["ave_session"])

    quote_service = QuotationService(AveHttpClient(ave_session.token, 60))
    service_agent = AgentsService(AveHttpClient(ave_session.token, 15))

    if (agent_id == 0):
        agent_id = await GetListAgents(service_agent).look_for_main(ave_session.idEnterprise, ave_session.tokenBody)

    payload = {
        "idAgente": agent_id,
        "idtransportador": 0,
        "idempresa": ave_session.idEnterprise,
        "origen": city_of_origin,
        "destino": city_of_destination,
        "valorrecaudo": value_to_be_collected,
        "valorMinimo": 1,
        "idasumecosto": 0,
        "contraentrega": 0,
        "productos": [
            {
                "alto": height,
                "largo": length,
                "ancho": width,
                "peso": str(weight),
                "unidades": units,
                "nombre": description,
                "valorDeclarado": str(declared_value)
            }
        ]
    }
    quotes = await CreateMasiveQuote(quote_service).execute(ShipmentRequestDTO(**payload))
    return {
        "session_token": session_token,
        "data": quotes
    }

@mcp.tool()
async def list_agents(session_token: Optional[str] = ""):
    """ 
        Lista los agentes disponibles en la empresa, el id del agente se usara en otras Tools como `agent_id` 

        Args:
            session_token (str): Token de sesión activo.
        Returns:
            dict: Un diccionario con las claves:
                - `session_token` (str): Token de sesión activo. Usa este mismo token para futuras solicitudes que requieran autenticación.
                - `data`  List[dict]:  Retorna un listado de agentes disponibles, cada agente tiene un campo `principal`: ('SI', 'NO'), donde define si el agente principal
           
    """
    session_data = await session_service.get_session(session_token or "")
    if session_token == "" or session_data == None:
        oauth = await create_oauth_url()
        return {
            "error": True,
            "message": "Abre este enlace en tu navegador para iniciar el flujo de autenticación OAuth y vuelve a intertarlo cuando se complete el flujo",
            "session_token": oauth.get("session_id", ""),
            "oauth_url": oauth.get("auth_url", "")
        }
    ave_session = AveSession(**session_data["ave_session"])

    agents = []

    service = AgentsService(AveHttpClient(ave_session.token, 15))
    agents = await GetListAgents(service).execute(ave_session.idEnterprise, ave_session.tokenBody)

    return {
        "session_token": session_token,
        "data": agents
    }

@mcp.tool()
async def find_cities(city: str, quantity: int,  session_token: Optional[str] = ""):
    """ 
    Busca una ciudad en el formato correcto, tambien se puede usar para validar si existe esa ciudad y el codigo Dane

    Args:
        session_token (str): Token de sesión activo.
    
    Returns:
        dict: Un diccionario con las claves:
            - `session_token` (str): Token de sesión activo. Usa este mismo token para futuras solicitudes que requieran autenticación.
            - `data`  List[dict]:  Retorna un listado ciudades
    """
    session_data = await session_service.get_session(session_token or "")
    if session_token == "" or session_data == None:
        oauth = await create_oauth_url()
        return {
            "error": True,
            "message": "Abre este enlace en tu navegador para iniciar el flujo de autenticación OAuth y vuelve a intertarlo cuando se complete el flujo",
            "session_token": oauth.get("session_id", ""),
            "oauth_url": oauth.get("auth_url", "")
        }
    ave_session = AveSession(**session_data["ave_session"])
    
    service = CitiesService(AveHttpClient(ave_session.token, 15))
    cities = await SearchCities(service).execute(city, quantity)

    return {
        "session_token": session_token,
        "data": cities
    }

@mcp.tool()
async def list_transporters(session_token: Optional[str] = ""):
    """ 
    Listar las transportadoras logísticos disponibles que estan asociados al usuario

    Args:
        session_token (str): Token de sesión activo.
    
    Returns:
        dict: Un diccionario con las claves:
            - `session_token` (str): Token de sesión activo. Usa este mismo token para futuras solicitudes que requieran autenticación.
            - `data` List[dict]: 
                - `id`: Identificador del operador logistico
                - `nombre`: Nombre del operador logistico
                - `imagen`: Imagen principal de la imagen
                - `imagen2`: Imagen segundaria de la imagen
    """
    session_data = await session_service.get_session(session_token or "")
    if session_token == "" or session_data == None:
        oauth = await create_oauth_url()
        return {
            "error": True,
            "message": "Abre este enlace en tu navegador para iniciar el flujo de autenticación OAuth y vuelve a intertarlo cuando se complete el flujo",
            "session_token": oauth.get("session_id", ""),
            "oauth_url": oauth.get("auth_url", "")
        }
    ave_session = AveSession(**session_data["ave_session"])

    service = OperatorsService(AveHttpClient("", 60))
    data = await ListOperators(service).execute(ave_session.tokenBody, ave_session.idEnterprise)

    return {
        "session_token": session_token,
        "data": data
    }


@mcp.tool()
async def generate_order(
    city_of_destination: str,
    paymentClient: int,
    clientContact: str,
    clientId: str,
    weight: float,
    quantity: int,
    productRef: str,
    total_order_value: int,
    operator_id: Optional[int] = 0, 
    agent_id: Optional[int] = 0, 
    session_token: Optional[str] = ""
) -> dict:
    """
    Genera un pedido en AveCRM.
    Los productos deben estar previamente registrados en el sistema.
    Si no pasa el operador logístico, se calculará el envío automáticamente.

    Args:
        city_of_destination (str): Ciudad de destino (ej: "MEDELLIN(ANTIOQUIA)").
        paymentClient (int): Método de pago del cliente (1=Cliente paga pedido, 2=No)
        clientContact (str): Contacto del cliente - nombre del destinatario.
        clientId (str): ID del cliente en el sistema.
        weight (int): Peso del envío en kilogramos
        quantity (int): Cantidad de productos.
        productRef (str): Referencia del producto.
        total_order_value (int): valor total del pedido.
        operator_id (int, optional): ID del operador logistico o transportadora
        agent_id (int, optional): ID del agente o Bodega en AveCRM.
        session_token (str, optional): Token de sesión activo generado por Aveonline. Si se omite, se espera que esté presente en el header `x_session_token`.

    Returns:
        dict: Un diccionario con las claves:
            - `session_token` (str): Token de sesión activo. Usa este mismo token para futuras solicitudes que requieran autenticación.
            - `data` [dict]: 
                - `id`: Identificador de la orden realizada
                - `transportation_value`: Valor estimado de transportadora. Este valor puede cambiar si en confirmar pedido se cambia de operador
                - `total_amount`: Costo total de la orden
                - `order_id`: Numero de la orden de pedido generada en el sistem
    """
    session_data = await session_service.get_session(session_token or "")
    if session_token == "" or session_data == None:
        oauth = await create_oauth_url()
        return {
            "error": True,
            "message": "Abre este enlace en tu navegador para iniciar el flujo de autenticación OAuth y vuelve a intertarlo cuando se complete el flujo",
            "session_token": oauth.get("session_id", ""),
            "oauth_url": oauth.get("auth_url", "")
        }
    ave_session = AveSession(**session_data["ave_session"])
    
    service_agent = AgentsService(AveHttpClient(ave_session.token, 15))
    if (agent_id == 0 or agent_id == None):
        agent_id = await GetListAgents(service_agent).look_for_main(ave_session.idEnterprise, ave_session.tokenBody)

    item = ItemDTO(**{
        "productRef": productRef,
        "quantity": quantity,
        "peso": weight,
    })

    # Construir el pedido
    pedido = PedidoDTO.from_minimal({
        "empresa": ave_session.idEnterprise,
        "token": ave_session.tokenBody,
        "idAgente": agent_id,
        "items": [item],
        "grandTotalPeso": weight,
        "totalAmountValue": total_order_value,
        "grandTotalValue ": total_order_value,
        "clientDestino": city_of_destination,
        "clientContact": clientContact,
        "clientId": clientId,
        "clientDir": "DIRECCIÓN PENDIENTE",
        "clientTel": "TELÉFONO PENDIENTE",
        "clientEmail": "EMAIL@PENDIENTE.COM",
        "paymentCliente": paymentClient,
        "seloperadorEnvio": operator_id
    })

    service = SalesOrdersService(ave_session.token)
    response = await CreateOrder(service).execute(pedido)

    if response.success == True:
        return {
            "session_token": session_token,
            "data": {
                "id": response.id,
                "transportation_value": response.valortransporte,
                "total_amount": response.totalAmount,
                "order_id": response.order_id,
            }
            
        }
    return {
        "error": True,
        "messages": response.messages or "Hubo un error inesperado",
        "session_token": session_token,
    }


# @mcp.tool()
# async def list_providers(session_token: str = ""):
#     """
#         Listado de proveedores para las ordenes de compra
        
#         Args:
#             session_token (str): Token de sesión activo.

#         Returns:
#             dict: Un diccionario con las claves:
#                 - `session_token` (str): Token de sesión activo. Usa este mismo token para futuras solicitudes que requieran autenticación.
#                 - `data` List[dict]: 
#                     - `idproveedor`: Identificador del proveedor (importante para las ordenes de compra)
#                     - `nombreproveedor`: Nombre del proveedor
#                     - `telefonoproveedor`: Telefono principal del proveedor
#                     - `direccionproveedor`: Direccion del proveedor
#                     - `ciudadproveedor`: Ciudad del proveedor
#     """
#     headers = get_http_headers()
#     data = []
#     session: UserSession
#     existing_session = session_manager.get_session_by_token(session_token)
#     if existing_session is None:
#         session_any = await some_authentication(session_token, aveonline_auth, headers)
#         if session_any is None:
#             return {
#                 "error": True,
#                 "message": "No se pudo autenticar obtener ninguna sesión",
#                 "code": "SESSION_REQUIRED"
#             }
#         session = session_any
#     else:
#         session = existing_session

#     service = ProvidersService()
#     data = await ListProviders(service).execute(session.ave_session.token, session.ave_session.idEnterprise)
#     return {
#         "session_token": session.session_token,
#         "data": data
#     }

# @mcp.tool()
# async def generate_purchase_order(
#     provider_id: int,
#     purchase_order: str,
#     operator_id: int,
#     shipping_mode: int,
#     order_number: str,
#     plu: str,
#     ean: int,
#     reference: str,
#     product_name: str,
#     requested_quantity: str,
#     unit_price: int,
#     total_price: int,
#     valuation: int,
#     customer: str,
#     city: str,
#     state: str,
#     address: str,
#     phone: str,
#     email: str,
#     notes: str,
#     weight: int,
#     dane_code: str,
#     min_dispatch_date: str ="",
#     max_dispatch_date: str = "",
#     description: str = "Nueva orden",
#     agent_id: int = 0,
#     session_token: str = "",
# ):
#     """
#     Genera una nueva orden de compra y solicitud de despacho para un proveedor determinado.

#     Esta herramienta permite crear una orden de compra formal que incluye los detalles del producto,
#     información de entrega, precios y datos de contacto del destinatario. Está diseñada para integrarse
#     con sistemas externos de logística o ERP a través del servidor MCP.

#     Args:
#         - provider_id (int): Identificador del proveedor.
#         - purchase_order (str): Código interno de la orden de compra.
#         - operator_id (int): ID del operador logistico/ transportadora.
#         - shipping_mode (int): Modo o tipo de envío (por ejemplo: 1=por tiempo, 2=por costo).
#         - order_number (str): Número único que identifica el pedido.
#         - min_dispatch_date (str, opcional): Fecha mínima de despacho esperada (formato: DD/MM/AAAA).
#         - max_dispatch_date (str, opcional): Fecha máxima aceptada para el despacho (formato: DD/MM/AAAA).
#         - plu (str): Código interno del producto.
#         - ean (int): Código EAN del producto.
#         - reference (str): Código de referencia del producto.
#         - product_name (str): Nombre descriptivo del producto.
#         - requested_quantity (str): Cantidad solicitada del producto.
#         - unit_price (int): Precio por unidad (sin puntos ni decimales).
#         - total_price (int): Valor total de la línea del producto (sin puntos ni decimales).
#         - valuation (int): Valoración total del pedido (sin puntos ni decimales).
#         - customer (str): Nombre del cliente de destino.
#         - city (str): Ciudad del lugar de entrega.
#         - state (str): Departamento o región del lugar de entrega.
#         - address (str): Dirección completa de envío.
#         - phone (str): Número de teléfono de contacto.
#         - email (str): Correo electrónico de contacto.
#         - notes (str): Observaciones o comentarios adicionales sobre el pedido.
#         - weight (int): Peso del paquete en kilogramos.
#         - dane_code (str): Código DANE de la ciudad (Tool: find_cities) (8 dígitos).
#         - description (str, opcional): Descripción breve de la orden. Valor por defecto: "Nueva orden".
#         - agent_id (int, opcional): ID del agente encargado del pedido. Por defecto es 0.
#         - session_token (str, opcional): Token de sesión para autenticación/autorización.

#     Returns:
#         dict: Un diccionario con las claves:
#             - `session_token` (str): Token de sesión activo. Usa este mismo token para futuras solicitudes que requieran autenticación.
#             - `data` (dict): 
#                 - `status`: Estado del resultado
#                 - `message `: Mensaje de respuesta
#                 - `codigo `: Listados de `id` (Posición de lectura de cada linea) y `text` (Linea de respuesta de cada linea)

#     """
#     headers = get_http_headers()
#     data = []
#     session: UserSession
#     existing_session = session_manager.get_session_by_token(session_token)
#     if existing_session is None:
#         session_any = await some_authentication(session_token, aveonline_auth, headers)
#         if session_any is None:
#             return {
#                 "error": True,
#                 "message": "No se pudo autenticar obtener ninguna sesión",
#                 "code": "SESSION_REQUIRED"
#             }
#         session = session_any
#     else:
#         session = existing_session


#     order = OrderDto(
#         idagente=agent_id,
#         ordencompra=purchase_order,
#         idproveedor=provider_id,
#         idtransportador=operator_id,
#         modoenvio=shipping_mode,
#         pedido=order_number,
#         fecha_min=min_dispatch_date,
#         fecha_max=max_dispatch_date,
#         plu=plu,
#         ean=ean,
#         referencia=reference,
#         nombre_articulo=product_name,
#         descripcion=description,
#         cantidad_solicitada=requested_quantity,
#         precio=unit_price,
#         total=total_price,
#         valoracion=valuation,
#         cliente=customer,
#         ciudad=city,
#         departamento=state,
#         direccion=address,
#         tel=phone,
#         correo=email,
#         observaciones=notes,
#         peso=weight,
#         codigo_dane=dane_code,
#     )

#     service = PurchaseOrderService()
#     data = await PursacheOrder(service).execute(session.ave_session, order)

#     return {
#         "session_token": session.session_token,
#         "data": data
#     }
