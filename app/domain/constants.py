"""Canonical persisted domain values. Never persist the attribute names."""


class TicketStatus:
    OPEN = "Abierto"
    IN_PAYMENT = "En cobro"
    PAID = "Cobrado"
    CANCELLED = "Cancelado"


class TicketPaymentStatus:
    UNPAID = "Sin pagar"
    PAID = "Pagado"
    CANCELLED = "Cancelado"


class TicketLineStatus:
    CAPTURED = "Capturado"
    SENT_TO_KITCHEN = "Enviado a comanda"
    PRINTED = "Impreso"
    CANCELLED = "Cancelado"


class TicketLineType:
    SIMPLE = "Simple"
    PACKAGE_PARENT = "Paquete padre"
    PACKAGE_COMPONENT = "Componente de paquete"


class PriceMode:
    NORMAL = "Normal"
    PACKAGE_PRICE = "Precio de paquete"
    INCLUDED_IN_PACKAGE = "Incluido en paquete"


class CommandValue:
    ORDER = "Pedido"
    QUEUED = "En cola"
    ADD = "Agregar"


class PrintJobType:
    COMMAND = "Comanda"
    TICKET = "Ticket"
    CASH_SHIFT = "Corte"
    COMMAND_CANCELLATION = "Cancelacion comanda"


class PrintStatus:
    PENDING = "Pendiente"
    CLAIMED = "Tomado"
    PRINTED = "Impreso"
    FAILED = "Fallido"
    CANCELLED = "Cancelado"


class CashShiftStatus:
    OPEN = "Abierto"
    CLOSED = "Cerrado"


class ActiveStatus:
    ACTIVE = "Activo"
    CANCELLED = "Cancelado"


class PaymentMethodValue:
    CASH = "Efectivo"
    CARD = "Tarjeta"
    TRANSFER = "Transferencia"


class InventoryMovementType:
    PURCHASE = "Compra"
    ADJUSTMENT_IN = "Ajuste entrada"
    ADJUSTMENT_OUT = "Ajuste salida"
    WASTE = "Merma"
    SALE_CONSUMPTION = "Consumo venta"


class StockStatus:
    OK = "Correcto"
    LOW = "Stock bajo"
    OUT = "Sin stock"


class StockAlertStatus:
    OPEN = "Abierta"
    RESOLVED = "Resuelta"


class ReceiptStatus:
    DRAFT = "Borrador"
    PENDING = "Pendiente"
    PROCESSED = "Procesada"


class TableStatus:
    FREE = "Libre"
    OCCUPIED = "Ocupada"
    OPEN = "Abierto"
    IN_PAYMENT = "En cobro"


class ProductType:
    SIMPLE = "Simple"
    PACKAGE = "Paquete"


class CatalogStatus:
    ACTIVE = "Activo"


class PackageValue:
    FIXED_COMPONENTS = "Componentes fijos"
    PRINT_COMPONENTS = "Imprimir componentes"
    CONSUME_COMPONENT_RECIPES = "Consumir recetas de componentes"


class UnitFamily:
    MASS = "Masa"
    VOLUME = "Volumen"
    COUNT = "Conteo"


class ItemType:
    OTHER = "Otro"


class ConnectionType:
    LOGICAL = "Logica"
    USB = "USB"


class AuthorizationStatus:
    APPROVED = "Aprobada"


class SyncStatus:
    PENDING = "Pendiente"
    IDLE = "Inactivo"


class InventorySourceType:
    TICKET_LINE = "Linea ticket"
    PACKAGE_COMPONENT = "Componente de paquete"
    MANUAL = "Manual"


AUDIT_EVENT_VALUES = {
    "CASH_SHIFT_OPENED": "Corte abierto",
    "CASH_SHIFT_CLOSED": "Corte cerrado",
    "CASH_EXPENSE_CREATED": "Gasto de caja creado",
    "TICKET_OPENED": "Ticket abierto",
    "TICKET_LINE_ADDED": "Linea de ticket agregada",
    "PACKAGE_LINE_ADDED": "Paquete agregado",
    "ROUND_SENT": "Ronda enviada",
    "PAYMENT_STARTED": "Cobro iniciado",
    "PAYMENT_CREATED": "Pago creado",
    "PAYMENT_REGISTERED": "Pago registrado",
    "TICKET_PAID": "Ticket cobrado",
    "TICKET_LINE_CANCELLED": "Linea de ticket cancelada",
    "TICKET_CANCELLED": "Ticket cancelado",
    "INVENTORY_MOVEMENT_CREATED": "Movimiento de inventario creado",
    "PURCHASE_RECEIPT_PROCESSED": "Recepcion procesada",
    "STOCK_ALERT_OPENED": "Alerta de stock abierta",
    "STOCK_ALERT_RESOLVED": "Alerta de stock resuelta",
}


def audit_event(technical_key: str) -> str:
    """Resolve a stable technical code to its persisted Spanish label."""
    return AUDIT_EVENT_VALUES[technical_key]
