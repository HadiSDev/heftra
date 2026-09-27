"""Making one factor set the one estimates use."""
from __future__ import annotations

from typing import NamedTuple

from sqlmodel import Session, select

from ..audit import record_audit
from ..db.models import EmissionFactorSet
from ..db.models.audit_log import SYSTEM_ACTOR

AUDIT_ENTITY = "emission_factor_set"


class Activation(NamedTuple):
    """The set now active, the one it replaced, and whether lines need matching again."""

    factor_set: EmissionFactorSet
    previous: EmissionFactorSet | None
    rematch_needed: bool


def activate_factor_set(session: Session, factor_set: EmissionFactorSet, *,
                        actor: str = SYSTEM_ACTOR) -> Activation:
    """Deactivate every other set and activate `factor_set`, audited; the caller commits."""
    previous = session.exec(
        select(EmissionFactorSet).where(EmissionFactorSet.active == True)  # noqa: E712
    ).first()
    if previous is not None and previous.id == factor_set.id:
        return Activation(factor_set, None, rematch_needed=False)

    others = session.exec(
        select(EmissionFactorSet).where(EmissionFactorSet.active == True,  # noqa: E712
                                        EmissionFactorSet.id != factor_set.id)
    ).all()
    for other in others:
        other.active = False
        session.add(other)
    session.flush()
    factor_set.active = True
    session.add(factor_set)
    record_audit(
        session, entity_type=AUDIT_ENTITY, entity_id=factor_set.id, action="activate",
        actor=actor, changes=[
            {"field": "active", "old": False, "new": True},
            {"field": "active_set", "old": previous.version if previous else None,
             "new": factor_set.version},
        ],
    )
    session.flush()
    return Activation(
        factor_set, previous,
        rematch_needed=previous is not None
        and previous.classification != factor_set.classification,
    )
