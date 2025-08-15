from typing import List, Optional
from pydantic import BaseModel, Field


class ItemDTO(BaseModel):
    """Detalle de cada producto incluido en el pedido"""
    productRef: str = Field(..., description="Código referencia del producto")
    quantity: int = Field(..., description="Cantidad del producto")
    peso: Optional[float] = Field(0, description="Peso unitario (Kg) del producto")
    rateValue: Optional[float] = Field(0, description="Valor unitario del producto")
    ivaValue: Optional[float] = Field(0, description="Valor de IVA del producto")
    vol: Optional[float] = Field(0, description="Volumen del producto")
    declarado: Optional[float] = Field(0, description="Valor declarado unitario del producto")
    totalValue: Optional[float] = Field(0, description="Valor total del producto")


class PedidoDTO(BaseModel):
    """DTO para creación de pedido en Aveonline"""
    tipo: str = Field("authave", description="Enrutador de la API (por defecto authave)")
    empresa: int = Field(..., description="Identificador de la empresa dentro de Aveonline")
    token: str = Field(..., description="Token recibido en la autenticación")
    idAgente: int = Field(..., description="Identificador del canal de venta o agente")
    items: List[ItemDTO] = Field(..., description="Lista de productos del pedido")
    numeropedidoExterno: Optional[str] = Field("", description="Número de pedido externo")
    bodegaName: Optional[str] = Field("", description="Identificador de la bodega de despacho")

    clientDestino: str = Field(..., description="Ciudad de destino")
    clientContact: str = Field(..., description="Nombre del destinatario")
    clientId: str = Field(..., description="Identificación del destinatario")
    clientDir: str = Field(..., description="Dirección del destinatario")
    clientTel: str = Field(..., description="Teléfono del destinatario")
    clientEmail: str = Field(..., description="Correo electrónico del destinatario")

    subTotalValue: Optional[float] = Field(0, description="Subtotal antes de impuestos")
    vatValue: Optional[float] = Field(0, description="Subtotal de impuestos")
    totalAmountValue: Optional[float] = Field(0, description="Valor total del pedido")
    grandTotalValue: Optional[float] = Field(0, description="Valor total del pedido (igual a totalAmountValue)")
    grandTotalVol: Optional[float] = Field(0, description="Total volumen")
    grandTotalPeso: Optional[float] = Field(0, description="Total peso")
    grandTotalUnit: Optional[float] = Field(0, description="Total unidades")
    grandTotalDeclarado: Optional[float] = Field(0, description="Total valor declarado")
    grandTotalDeclaradoValue: Optional[float] = Field(0, description="Total valor declarado (igual a grandTotalDeclarado)")

    paymentCliente: Optional[int] = Field(2, description="1=Cliente paga pedido, 2=No")
    recaudo: Optional[float] = Field(0, description="Valor a recaudar")
    recaudoValue: Optional[float] = Field(0, description="Valor a recaudar (igual a recaudo)")
    paymentAsumecosto: Optional[int] = Field(2, description="1=Cliente asume costo recaudo, 2=No")

    valorEnvio: Optional[float] = Field(0, description="Valor del envío cotizado")
    valorEnvioValue: Optional[float] = Field(0, description="Valor del envío cotizado (igual a valorEnvio)")
    cadenaEnvio: Optional[str] = Field("", description="Variable vacía")
    seloperadorEnvio: Optional[int] = Field(0, description="Código del operador seleccionado")

    nroFactura: Optional[str] = Field("", description="Número de factura interno")
    plugin: str = Field("aveonline", description="Método de acceso (por defecto aveonline)")
    noGenerarEnvio: Optional[int] = Field(0, description="1=Generar envío asociado, 0=No")
    revisarCE: Optional[int] = Field(0, description="1=No generar por ser contraentrega")
    obs: Optional[str] = Field("", description="Observaciones del envío")
    pagado: bool = Field(False, description="Pago hecho desde ecommerce")
    enviopropio: bool = Field(False, description="Envío propio sin operador logístico")

    @classmethod
    def from_dict_with_defaults(cls, data: dict) -> "PedidoDTO":
        """
        Crea una instancia de PedidoDTO a partir de un diccionario.
        Si faltan campos, usa los valores por defecto definidos en el modelo.
        """
        defaults = {field: model_field.default
                    for field, model_field in cls.model_fields.items()
                    if model_field.default is not None}

        # Combinamos los datos recibidos con los defaults
        merged = {**defaults, **data}

        return cls(**merged)
    
    @classmethod
    def from_minimal(cls, data: dict) -> "PedidoDTO":
        """
        Crea un PedidoDTO a partir de un diccionario mínimo,
        rellenando los demás campos con valores por defecto quemados.
        """
        # Campos fijos quemados
        fixed_values = {
            "tipo": "authave",
            "numeropedidoExterno": "",
            "bodegaName": "",
            "subTotalValue": 0,
            "vatValue": 0,
            "grandTotalVol": 0,
            "grandTotalUnit": 0,
            "grandTotalDeclarado": 0,
            "grandTotalDeclaradoValue": 0,
            "recaudo": 0,
            "recaudoValue": 0,
            "paymentAsumecosto": 2,
            "valorEnvio": 0,
            "valorEnvioValue": 0,
            "cadenaEnvio": "",
            "nroFactura": "",
            "plugin": "aveonline",
            "noGenerarEnvio": 0,
            "revisarCE": 0,
            "obs": "",
            "pagado": False,
            "enviopropio": False
        }

        # Combinamos datos proporcionados con los quemados
        merged_data = {**fixed_values, **data}

        return cls(**merged_data)