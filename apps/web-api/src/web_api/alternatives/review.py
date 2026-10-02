"""A person dismissing an alternative with a reason, marking a switch, or reopening it."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Session

from ..audit import diff_changes, record_audit
from ..db.models import AlternativeReviewStatus, ItemAlternative
from ..schemas.alternatives import AlternativeReview
from .access import AUDIT_ALTERNATIVE

REVIEW_FIELDS = ("review_status", "dismiss_reason", "review_note")


def review_alternative(session: Session, alternative: ItemAlternative, body: AlternativeReview,
                       actor: str) -> ItemAlternative:
    before = {field: getattr(alternative, field) for field in REVIEW_FIELDS}
    reopened = body.review_status == AlternativeReviewStatus.OPEN
    dismissed = body.review_status == AlternativeReviewStatus.DISMISSED
    alternative.review_status = body.review_status.value
    alternative.dismiss_reason = body.dismiss_reason.value if dismissed else None
    alternative.review_note = None if reopened else body.note
    alternative.reviewed_by = None if reopened else actor
    alternative.reviewed_at = None if reopened else datetime.now(timezone.utc)
    session.add(alternative)
    changes = diff_changes(before, {field: getattr(alternative, field)
                                    for field in REVIEW_FIELDS}, REVIEW_FIELDS)
    if changes:
        record_audit(session, entity_type=AUDIT_ALTERNATIVE, entity_id=alternative.id,
                     action="review", actor=actor, changes=changes)
    return alternative
