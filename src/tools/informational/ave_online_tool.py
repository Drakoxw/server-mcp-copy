"""
Herramienta MCP informativa sobre AveOnline
Esta herramienta proporciona información sobre servicios, ventajas y características de AveOnline
No requiere autenticación - Es una herramienta informativa
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class ServiceCategory(Enum):
    LOGISTICS = "logistics"
    TECHNOLOGY = "technology"
    CUSTOMER_SERVICE = "customer_service"
    TRACKING = "tracking"
    INTEGRATION = "integration"

@dataclass
class ServiceInfo:
    name: str
    description: str
    category: ServiceCategory
    benefits: List[str]
    features: List[str]
    target_audience: List[str]

class AveOnlineInfoTool:
    """
    Herramienta MCP que proporciona información completa sobre AveOnline
    """
    
    def __init__(self):
        self.tool_name = "aveonline_info"
        self.description = "Proporciona información detallada sobre servicios y ventajas de AveOnline"
        self.version = "1.0.0"
        self._services_data = self._initialize_services_data()
    
    def _initialize_services_data(self) -> Dict[str, ServiceInfo]:
        """Inicializa la base de datos de servicios de AveOnline"""
        return {
            "shipping_quotes": ServiceInfo(
                name="Cotizaciones de Envío Inteligentes",
                description="Sistema avanzado de cotizaciones que compara múltiples transportadoras en tiempo real",
                category=ServiceCategory.LOGISTICS,
                benefits=[
                    "Ahorro hasta 30% en costos de envío",
                    "Comparación automática de tarifas",
                    "Cotizaciones en tiempo real",
                    "Optimización de rutas",
                    "Transparencia total en precios"
                ],
                features=[
                    "API REST para integración",
                    "Dashboard web intuitivo",
                    "Múltiples transportadoras",
                    "Cálculo automático de dimensiones",
                    "Histórico de cotizaciones",
                    "Alertas de cambios de precio"
                ],
                target_audience=[
                    "E-commerce",
                    "Pequeñas y medianas empresas",
                    "Grandes corporaciones",
                    "Desarrolladores",
                    "Startups"
                ]
            ),
            
            "tracking_system": ServiceInfo(
                name="Sistema de Seguimiento Unificado",
                description="Plataforma centralizada para rastrear envíos de múltiples transportadoras",
                category=ServiceCategory.TRACKING,
                benefits=[
                    "Visibilidad completa del envío",
                    "Notificaciones proactivas",
                    "Reducción de consultas de clientes",
                    "Mayor satisfacción del cliente",
                    "Control total de la cadena logística"
                ],
                features=[
                    "Tracking en tiempo real",
                    "Notificaciones por email/SMS",
                    "Dashboard unificado",
                    "API de consulta",
                    "Reportes detallados",
                    "Integración con e-commerce"
                ],
                target_audience=[
                    "Retailers online",
                    "Operadores logísticos",
                    "Departamentos de customer service",
                    "Empresas de manufactura"
                ]
            ),
            
            "api_integration": ServiceInfo(
                name="Plataforma de Integración API",
                description="Suite completa de APIs para integrar servicios logísticos en cualquier sistema",
                category=ServiceCategory.INTEGRATION,
                benefits=[
                    "Integración rápida y sencilla",
                    "Reducción de tiempo de desarrollo",
                    "Escalabilidad garantizada",
                    "Soporte técnico especializado",
                    "Documentación completa"
                ],
                features=[
                    "RESTful APIs",
                    "Webhooks para eventos",
                    "SDKs en múltiples lenguajes",
                    "Rate limiting inteligente",
                    "Autenticación y registro OAuth 2.0"
                ],
                target_audience=[
                    "Equipos de IT",
                    "Integradores de sistemas",
                    "Empresas tech"
                ]
            ),
            
            "smart_logistics": ServiceInfo(
                name="Logística Inteligente",
                description="Soluciones logísticas impulsadas por IA para optimizar operaciones",
                category=ServiceCategory.TECHNOLOGY,
                benefits=[
                    "Optimización automática de rutas",
                    "Predicción de demanda",
                    "Reducción de costos operativos",
                    "Mejora en tiempos de entrega",
                    "Analytics avanzados"
                ],
                features=[
                    "Machine Learning integrado",
                    "Predicción de tiempos de entrega",
                    "Optimización de inventarios",
                    "Análisis predictivo",
                    "Reportes automáticos",
                    "Dashboard ejecutivo"
                ],
                target_audience=[
                    "Directores de logística",
                    "Supply chain managers",
                    "CFOs",
                    "Empresas de retail"
                ]
            ),
            
            "customer_support": ServiceInfo(
                name="Soporte al Cliente 24/7",
                description="Servicio de atención especializado en logística con soporte multicanal",
                category=ServiceCategory.CUSTOMER_SERVICE,
                benefits=[
                    "Atención 24/7 los 365 días",
                    "Especialistas en logística",
                    "Múltiples canales de contacto",
                    "Resolución proactiva de problemas",
                    "SLA garantizado"
                ],
                features=[
                    "Chat en vivo",
                    "Email support",
                    "Teléfono especializado",
                    "Portal de autoservicio",
                    "Base de conocimientos",
                    "Ticketing system"
                ],
                target_audience=[
                    "Todas las empresas usuarias",
                    "Equipos de customer service",
                    "Gerentes de operaciones"
                ]
            )
        }
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """Retorna la definición de la herramienta para MCP"""
        return {
            "name": self.tool_name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query_type": {
                        "type": "string",
                        "enum": [
                            "overview",
                            "services",
                            "service_detail",
                            "benefits",
                            "integration_info",
                            "pricing_info",
                            "contact_info"
                        ],
                        "description": "Tipo de información solicitada sobre AveOnline"
                    },
                    "service_name": {
                        "type": "string",
                        "enum": [
                            "shipping_quotes",
                            "tracking_system", 
                            "api_integration",
                            "smart_logistics",
                            "customer_support"
                        ],
                        "description": "Servicio específico para consulta detallada"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["logistics", "technology", "customer_service", "tracking", "integration"],
                        "description": "Filtrar servicios por categoría"
                    }
                },
                "required": ["query_type"]
            }
        }
    
    def coverage_data(self, country: str = "") -> dict:
        """Verifica la cobertura de AveOnline en países y ciudades"""
        
        coverage_data = {
            "countries": {
                "colombia": {
                    "available": True,
                    "cities": ["Todas las ciudades"],
                    "services": ["full"]
                },
                "ecuador": {
                    "available": True,
                    "cities": ["Todas las ciudades"],
                    "services": ["full"]
                }
            }
        }

        if country:
            country_lower = country.lower()
            if country_lower in coverage_data["countries"]:
                result = coverage_data["countries"][country_lower].copy()
                result["country"] = country
                
                return result
            else:
                return {
                    "country": country,
                    "available": False,
                    "message": "AveOnline no tiene cobertura en este país aún",
                    "available_countries": list(coverage_data["countries"].keys())
                }
    
        return {
            "total_countries": len(coverage_data["countries"]),
            "available_countries": list(coverage_data["countries"].keys()),
            "coverage_summary": coverage_data["countries"]
        }
    
    def company_quick_info(self) -> dict:
        return {
        "company": "AveOnline",
        "tagline": "Revolucionando la Logística con Tecnología Inteligente",
        "services": [
            "Cotizaciones de envío inteligentes",
            "Sistema de seguimiento unificado",
            "APIs de integración",
            "Logística con IA",
            "Transporte Nacional",
            "Transporte Internacional",
            "Anticipo de Recaudo",
            "Pago Contraentrega",
            "Ave Chat",
            "Dropshipping",
            "Automatización Shopify",
            "Plugin WooCommerce",
            "Sistema contable Alegra",
            "Ave CRM",
            "Ave Metrics",
            "Bodegaje",
        ],
        "coverage": ["Colombia", "Ecuador"],
        "contact": {
            "sales": "pqr@aveonline.co",
            "support": "desarrollo1@aveonline.co",
            "website": "https://aveonline.co/"
        }
    }

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta la herramienta y retorna información sobre AveOnline"""
        query_type = params.get("query_type")
        service_name = params.get("service_name")
        category = params.get("category")
        
        try:
            if query_type == "overview":
                return self._get_company_overview()
            elif query_type == "services":
                return self._get_services_list(category)
            elif query_type == "service_detail":
                return self._get_service_detail(service_name)
            elif query_type == "benefits":
                return self._get_general_benefits()
            elif query_type == "integration_info":
                return self._get_integration_info()
            elif query_type == "pricing_info":
                return self._get_pricing_info()
            elif query_type == "contact_info":
                return self._get_contact_info()
            else:
                return {"error": "Tipo de consulta no válido"}
                
        except Exception as e:
            return {"error": f"Error al procesar la consulta: {str(e)}"}
    
    def _get_company_overview(self) -> Dict[str, Any]:
        """Información general de la empresa"""
        return {
            "company_name": "AveOnline",
            "tagline": "Transporte, logística, cadena de suministro y almacenamiento con Tecnología Inteligente",
            "mission": "Simplificar y optimizar las operaciones logísticas de empresas de todos los tamaños mediante tecnología de vanguardia",
            "vision": "Ser la plataforma logística más confiable y eficiente de América Latina",
            "founded": "2013",
            "specialties": "Seguimiento a entregas de ordenes de compra a clientes finales, Alto nivel de servicio en el seguimiento y correcciones de las guías de envio, Consultoria transporte terrestre de mercancias en Colombia, Recaudo del costo del producto al momento de la entrega y Appi,s para Prestashop y woo commerce - (Word Press) que cotizan el transporte.",
            "headquarters": "Medellín, Colombia",
            "coverage": "Colombia, Ecuador",
            "key_differentiators": [
                "Tecnología de IA aplicada a logística",
                "Integración con múltiples transportadoras",
                "Sistema de seguimiento unificado",
                "Cotizaciones de envío inteligentes",
                "APIs de integración",
                "Servicios en varios paises de origen",
                "Envios internacionales a todo el mundo",
                "Soporte especializado y personalizado",
            ],
            "statistics": {
                "active_clients": "5000+",
                "monthly_shipments": "1.000,000+",
                "average_savings": "30%",
                "uptime_guarantee": "99.9%",
                "api_response_time": "<200ms"
            }
        }
    
    def _get_services_list(self, category_filter: Optional[str] = None) -> Dict[str, Any]:
        """Lista todos los servicios, opcionalmente filtrados por categoría"""
        services = {}
        
        for service_id, service_info in self._services_data.items():
            if not category_filter or service_info.category.value == category_filter:
                services[service_id] = {
                    "name": service_info.name,
                    "description": service_info.description,
                    "category": service_info.category.value
                }
        
        return {
            "services": services,
            "total_services": len(services),
            "filter_applied": category_filter or "none"
        }
    
    def _get_service_detail(self, service_name: Optional[str]) -> Dict[str, Any]:
        """Información detallada de un servicio específico"""
        if not service_name or service_name not in self._services_data:
            return {
                "error": "Servicio no encontrado",
                "available_services": list(self._services_data.keys())
            }
        
        service = self._services_data[service_name]
        return {
            "service_name": service.name,
            "description": service.description,
            "category": service.category.value,
            "benefits": service.benefits,
            "features": service.features,
            "target_audience": service.target_audience,
            "implementation_time": "1-3 días",
            "support_level": "24/7 especializado"
        }
    
    def _get_general_benefits(self) -> Dict[str, Any]:
        """Beneficios generales de usar AveOnline"""
        return {
            "cost_benefits": [
                "Ahorro promedio del 30% en costos de envío",
                "Reducción de tiempo operativo hasta 50%",
                "Eliminación de costos ocultos",
                "ROI positivo en menos de 3 meses"
            ],
            "operational_benefits": [
                "Automatización completa del proceso logístico",
                "Visibilidad en tiempo real de todos los envíos",
                "Reducción de errores humanos",
                "Integración sin interrupciones"
            ],
            "strategic_benefits": [
                "Escalabilidad garantizada",
                "Ventaja competitiva sostenible",
                "Mejor experiencia del cliente final",
                "Data-driven decision making"
            ],
            "technical_benefits": [
                "APIs robustas y documentadas",
                "Seguridad de nivel empresarial",
                "Uptime del 99.9%",
                "Soporte técnico especializado"
            ]
        }
    
    def _get_integration_info(self) -> Dict[str, Any]:
        """Información sobre integración técnica"""
        return {
            "integration_methods": [
                "REST APIs",
                "Webhooks",
                "Plugins para e-commerce"
            ],
            "supported_platforms": [
                "Shopify",
                "WooCommerce", 
                "PrestaShop",
                "Sistemas custom"
            ],
            "implementation": {
                "setup_time": "1-3 días",
                "documentation": "Completa y actualizada",
            },
            "security": [
                "OAuth 2.0",
                "SSL/TLS encryption",
                "Rate limiting",
                "IP whitelisting",
                "Audit logs"
            ],
            "getting_started": {
                "step_1": "Definir negociacion con AveOnline",
                "step_2": "Guiarse de la documentación: https://integraciones.aveonline.co/docs/introduccion/",
                "step_3": "Autenticacion: https://integraciones.aveonline.co/docs/nacional/autenticacion",
                "step_4": "Analisis y Validación de que servicios se desean implementar",
                "step_5": "Migración a producción"
            }
        }
    
    def _get_pricing_info(self) -> Dict[str, Any]:
        """Información sobre precios y planes"""
        return {
            "pricing_model": "Pay-per-use y planes mensuales",
            "plans": {
                "starter": {
                    "name": "Plan Starter",
                    "price": "Gratis hasta 100 envíos/mes",
                    "features": [
                        "Cotizaciones básicas",
                        "Tracking básico",
                        "Soporte por email"
                    ],
                    "ideal_for": "Pequeñas empresas y startups"
                },
                "professional": {
                    "name": "Plan Professional", 
                    "price": "Desde $99 USD/mes",
                    "features": [
                        "Cotizaciones avanzadas",
                        "Tracking en tiempo real",
                        "APIs completas",
                        "Soporte prioritario",
                        "Analytics básicos"
                    ],
                    "ideal_for": "Empresas en crecimiento"
                },
                "enterprise": {
                    "name": "Plan Enterprise",
                    "price": "Precio personalizado",
                    "features": [
                        "Todas las funcionalidades",
                        "SLA personalizado",
                        "Soporte dedicado",
                        "Analytics avanzados",
                        "Integraciones custom"
                    ],
                    "ideal_for": "Grandes corporaciones"
                }
            },
            "additional_info": {
                "setup_fee": "Sin costo de setup",
                "contract_terms": "Sin permanencia mínima",
                "payment_methods": ["Tarjeta de crédito", "ACH", "Wire transfer"],
                "currency_support": ["USD", "COP"]
            }
        }
    
    def _get_contact_info(self) -> Dict[str, Any]:
        """Información de contacto y soporte"""
        return {
            "sales_contact": {
                "email": "sales@aveonline.com",
                "phone": "+57 (4) 444-5555",
                "whatsapp": "+57 300 123 4567"
            },
            "technical_support": {
                "email": "support@aveonline.com",
                "phone": "+57 (4) 444-5556",
                "chat": "Disponible en portal web 24/7"
            },
            "business_hours": {
                "sales": "Lunes a Sabado 7:00 AM - 5:00 PM (COT)",
                "support": "24/7 los 365 días del año"
            },
            "office_locations": {
                "headquarters": {
                    "city": "Medellín, Colombia",
                    "address": "Carrera 43A #1-50, El Poblado",
                    "postal_code": "050021"
                },
            },
            "online_resources": {
                "website": "https://aveonline.com",
                "developer_portal": "https://developers.aveonline.com",
                "status_page": "https://status.aveonline.com",
                "blog": "https://blog.aveonline.com"
            },
            "social_media": {
                "linkedin": "@aveonline-oficial",
                "twitter": "@AveOnline",
                "youtube": "AveOnline Channel"
            }
        }
    

# Función helper para usar la herramienta en un servidor MCP
def create_aveonline_info_tool():
    """Factory function para crear la herramienta"""
    return AveOnlineInfoTool()

# Ejemplo de uso
if __name__ == "__main__":
    # Crear instancia de la herramienta
    tool = AveOnlineInfoTool()
    
    # Ejemplos de consultas
    print("=== OVERVIEW DE AVEONLINE ===")
    overview = tool.execute({"query_type": "overview"})
    print(json.dumps(overview, indent=2, ensure_ascii=False))
    x = json.dumps(overview, indent=2, ensure_ascii=False)
    
    print("\n=== LISTA DE SERVICIOS ===")
    services = tool.execute({"query_type": "services"})
    print(json.dumps(services, indent=2, ensure_ascii=False))
    
    print("\n=== DETALLE DEL SERVICIO DE COTIZACIONES ===")
    detail = tool.execute({
        "query_type": "service_detail", 
        "service_name": "shipping_quotes"
    })
    print(json.dumps(detail, indent=2, ensure_ascii=False))