from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FolioSequence
from app.services.exceptions import BusinessConflictError, EntityNotFoundError


def generate_folio(db: Session, sequence_key: str) -> str:
    """Reserva y devuelve el siguiente folio sin confirmar la transacción.

    La secuencia se incrementa y se hace ``flush`` para que el cambio participe
    en la transacción del llamador. El endpoint o proceso superior conserva la
    responsabilidad de hacer ``commit`` o ``rollback``.
    """
    sequence = db.execute(
        select(FolioSequence).where(FolioSequence.sequence_key == sequence_key)
    ).scalar_one_or_none()

    if sequence is None:
        raise EntityNotFoundError(f"No existe la secuencia de folios {sequence_key}.")
    if not sequence.active:
        raise BusinessConflictError(
            f"La secuencia de folios {sequence_key} está inactiva."
        )

    folio = f"{sequence.prefix}{sequence.next_number:0{sequence.padding}d}"
    sequence.next_number += 1
    db.flush()
    return folio
