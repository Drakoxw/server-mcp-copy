from typing import Optional
from pydantic import BaseModel

class OrderDto(BaseModel):
    idagente: int
    ordencompra: str
    idproveedor: int
    idtransportador: int
    modoenvio: int
    pedido: str  # Número del pedido
    fecha_min: str  # Fecha mínima despacho orden de compra (DD/MM/AAAA)
    fecha_max: str  # Fecha máxima despacho orden de compra (DD/MM/AAAA)
    plu: str  # Código interno de la orden de compra por cliente
    ean: int  # Código EAN del producto
    referencia: str  # Código referencia del producto
    nombre_articulo: str  # Nombre del producto
    descripcion: Optional[str] = None  # Descripción del producto (opcional)
    cantidad_solicitada: str  # Cantidad del producto
    precio: int  # Valor unitario del producto (sin puntos ni decimales)
    total: int  # Valor total del producto (sin puntos ni decimales)
    valoracion: int  # Valoración total del pedido (sin puntos ni decimales)
    cliente: str  # Cliente destino
    ciudad: str  # Ciudad destino (sin tildes ni ñ)
    departamento: str  # Departamento destino (sin tildes ni ñ)
    direccion: str  # Dirección destino
    tel: str  # Teléfono destino
    correo: str  # Correo electrónico destino
    observaciones: str  # Observaciones pedido
    peso: int  # Peso en kilogramos del pedido (sin puntos ni decimales)
    codigo_dane: str  # Código DANE (8 posiciones)
