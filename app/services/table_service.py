from sqlalchemy.orm import Session

from app.models import DiningTable
from app.services.exceptions import BusinessConflictError, EntityNotFoundError


def get_free_active_table(db: Session, table_id: int) -> DiningTable:
    """Obtiene una mesa activa y libre o reporta la regla que lo impide."""
    table = db.get(DiningTable, table_id)
    if table is None:
        raise EntityNotFoundError("La mesa no existe.")
    if not table.active:
        raise BusinessConflictError("La mesa está inactiva.")
    if table.status_cache != "FREE":
        raise BusinessConflictError("La mesa no está libre.")
    return table
