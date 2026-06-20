class BusinessError(Exception):
    """Error esperado causado por una regla de negocio."""


class InvalidBusinessDataError(BusinessError):
    """Indica que un valor válido sintácticamente no cumple el dominio."""


class EntityNotFoundError(BusinessError):
    """Indica que una entidad necesaria no existe."""


class BusinessConflictError(BusinessError):
    """Indica que el estado actual impide ejecutar la operación."""
