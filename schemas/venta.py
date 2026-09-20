"""
Esquemas Pydantic para Ventas, Facturación Fiscal, Métodos de Pago y Tipos de Venta.
Alineados fielmente con el Diagrama de Clases UML de FashionStore.
"""
from typing import List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class MetodoPagoResponse(BaseModel):
    id: int
    nombre: str

    model_config = ConfigDict(from_attributes=True)


class TipoVentaResponse(BaseModel):
    id: int
    nombre: str

    model_config = ConfigDict(from_attributes=True)


class FacturaResponse(BaseModel):
    id: int
    nro_factura: str
    nit_cliente: str
    razon_social: str
    fecha_emision: datetime
    nro_autorizacion: Optional[str] = None
    codigo_control: Optional[str] = None
    total_literal: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ItemVentaCreate(BaseModel):
    variante_id: int
    cantidad: int = Field(..., gt=0)
    precio_unitario: Optional[float] = None
    descuento: Optional[float] = 0.0


class DetalleVentaResponse(BaseModel):
    id: int
    variante_id: int
    cantidad: int
    subtotal: float
    precio_unitario: Optional[float] = None
    descuento: Optional[float] = 0.0
    cod_barra: Optional[str] = None
    prenda_nombre: Optional[str] = None
    talla: Optional[str] = None
    color: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class VentaPOSCreate(BaseModel):
    sucursal_id: int = Field(..., description="ID de la tienda física emisora")
    metodo_pago_id: Optional[int] = Field(1, description="ID del método de pago (1=Efectivo, 2=Tarjeta POS, 3=QR Caja)")
    empleado_id: Optional[Union[str, int]] = Field("1001", description="CI del empleado cajero en mostrador")
    cliente_id: Optional[Union[str, int]] = Field(None, description="CI del cliente o None para venta mostrador")
    nit_cliente: Optional[str] = "0"
    razon_social: Optional[str] = "Sin Nombre"
    monto_recibido: Optional[float] = None
    descuento_total: Optional[float] = 0.0
    items: List[ItemVentaCreate]


class VentaEcommerceCreate(BaseModel):
    cliente_id: Optional[Union[str, int]] = Field(None, description="CI del cliente registrado (CU15)")
    sucursal_id: Optional[int] = Field(1, description="ID de la sucursal desde donde se despacha")
    metodo_pago_id: Optional[int] = Field(3, description="ID del método de pago (Stripe, Libélula, PayPal, QR)")
    metodo_pago: Optional[str] = "QR_SIMPLE"
    nit_cliente: Optional[str] = "0"
    razon_social: Optional[str] = "Sin Nombre"
    direccion_envio: Optional[str] = "Entrega a domicilio"
    token_pasarela: Optional[str] = "tok_simulado_aprobado"
    items: Optional[List[ItemVentaCreate]] = None
    notas: Optional[str] = None


class VentaResponse(BaseModel):
    id: int
    fecha: datetime
    total: float
    codigo_transaccion: str
    estado_pago: str
    empleado_id: Optional[Union[str, int]] = None
    cliente_id: Optional[Union[str, int]] = None
    sucursal_id: int
    metodo_pago_id: int
    tipo_venta_id: int
    reserva_id: Optional[int] = None

    sucursal_nombre: Optional[str] = None
    empleado_nombre: Optional[str] = None
    cliente_nombre: Optional[str] = None
    metodo_pago_nombre: Optional[str] = None
    tipo_venta_nombre: Optional[str] = None

    detalles: List[DetalleVentaResponse] = []
    factura: Optional[FacturaResponse] = None

    # Campos calculados POS
    monto_recibido: Optional[float] = None
    cambio_devuelto: Optional[float] = None
    descuento_total: Optional[float] = 0.0
    monto_neto: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)
