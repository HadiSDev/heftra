"""A human choosing a line's emission sector, and edits that make an AI's choice stale."""
from __future__ import annotations

from sqlmodel import Session

from ..db.models import EmissionSector, EmissionSectorSource, InvoiceLine
from .factors import active_factor_set

EMISSION_SECTOR_FIELDS = (
    "emission_sector_id", "emission_sector_source", "emission_sector_confidence",
    "emission_sector_rationale",
)
DESCRIBING_FIELDS = ("item_name", "description", "spend_category_id")


class SectorNotOffered(ValueError):
    """The sector is not one of the active factor set's."""


def choose_sector(session: Session, line: InvoiceLine, sector_id: str | None) -> None:
    """Set the line's sector as a human's choice, or clear it so the matcher may try again."""
    if sector_id is None:
        _clear(line)
        return
    factor_set = active_factor_set(session)
    sector = session.get(EmissionSector, sector_id)
    if factor_set is None or sector is None or sector.classification != factor_set.classification:
        raise SectorNotOffered("That emission sector is not in the active factor set.")
    line.emission_sector_id = sector.id
    line.emission_sector_source = EmissionSectorSource.HUMAN
    line.emission_sector_confidence = None
    line.emission_sector_rationale = None


def forget_stale_ai_sector(line: InvoiceLine, changed_fields: set[str]) -> None:
    """Clear an AI's sector when what the line says it bought has changed."""
    if line.emission_sector_source != EmissionSectorSource.AI:
        return
    if changed_fields & set(DESCRIBING_FIELDS):
        _clear(line)


def _clear(line: InvoiceLine) -> None:
    line.emission_sector_id = None
    line.emission_sector_source = None
    line.emission_sector_confidence = None
    line.emission_sector_rationale = None
