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


class TicketLineNoteType:
    MODIFICATION = "Modificacion"


class PermissionKey:
    DISCOUNT_AUTHORIZE = "DISCOUNT_AUTHORIZE"
    REPRINT = "REPRINT"
    SMS_SEND = "SMS_SEND"
    SUPPORT_ACCESS = "SUPPORT_ACCESS"
    ADMIN_READ = "ADMIN_READ"


class EmployeeSessionStatus:
    ACTIVE = "Activa"
    CLOSED = "Cerrada"
    EXPIRED = "Expirada"


class TicketSplitStatus:
    OPEN = "Abierta"
    PAID = "Pagada"
    CANCELLED = "Cancelada"


class TicketSplitType:
    EQUAL = "Partes iguales"
    BY_LINES = "Por lineas"


class NotificationChannelKey:
    SMS = "SMS"


class SmsStatus:
    PENDING = "Pendiente"
    SENT = "Enviada"
    FAILED = "Fallida"
    SIMULATED = "Simulada"
    CANCELLED = "Cancelada"


class PriceMode:
    NORMAL = "Normal"
    PACKAGE_PRICE = "Precio de paquete"
    INCLUDED_IN_PACKAGE = "Incluido en paquete"


class DiscountType:
    AMOUNT = "Monto"
    PERCENT = "Porcentaje"
    COURTESY = "Cortesia"


class CommandValue:
    ORDER = "Pedido"
    QUEUED = "En cola"
    ADD = "Agregar"


class ProductionOrderStatus:
    QUEUED = "En cola"
    RECEIVED = "Recibida"
    IN_PREPARATION = "En preparacion"
    COMPLETED = "Terminada"
    DELIVERED = "Entregada"
    CANCELLED = "Cancelada"


class PrintJobType:
    COMMAND = "Comanda"
    TICKET = "Ticket"
    CASH_SHIFT = "Corte"
    COMMAND_CANCELLATION = "Cancelacion comanda"
    MODIFICATION = "Modificacion"


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
    VARIANT_OPTION = "Opcion variante"


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
    "PRODUCTION_ORDER_RECEIVED": "Orden de produccion recibida",
    "PRODUCTION_ORDER_STARTED": "Orden de produccion iniciada",
    "PRODUCTION_ORDER_COMPLETED": "Orden de produccion terminada",
    "PRODUCTION_ORDER_DELIVERED": "Orden de produccion entregada",
    "TICKET_LINE_MODIFIED": "Modificacion de linea",
    "DISCOUNT_APPLIED": "Descuento aplicado",
    "COURTESY_APPLIED": "Cortesia aplicada",
    "REPRINT_REQUESTED": "Reimpresion solicitada",
    "TICKET_SPLIT_CREATED": "Division de cuenta creada",
    "TICKET_SPLIT_PAYMENT": "Pago de division registrado",
    "SMS_FAILED": "Notificacion SMS fallida",
}


def audit_event(technical_key: str) -> str:
    """Resolve a stable technical code to its persisted Spanish label."""
    return AUDIT_EVENT_VALUES[technical_key]
