"""A person accepting a finding as an exception, ruling it out of scope, or reopening it."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Session

from ..audit import diff_changes, record_audit
from ..db.models import AgreementFinding, FindingReviewStatus
from ..schemas.agreements import FindingReview
from .constants import AUDIT_FINDING

REVIEW_FIELDS = ("review_status", "review_note")


def review_finding(session: Session, finding: AgreementFinding, body: FindingReview,
                   actor: str) -> AgreementFinding:
    before = {field: getattr(finding, field) for field in REVIEW_FIELDS}
    reopened = body.review_status == FindingReviewStatus.OPEN
    finding.review_status = body.review_status.value
    finding.review_note = None if reopened else body.note
    finding.reviewed_by = None if reopened else actor
    finding.reviewed_at = None if reopened else datetime.now(timezone.utc)
    session.add(finding)
    changes = diff_changes(before, {field: getattr(finding, field) for field in REVIEW_FIELDS},
                           REVIEW_FIELDS)
    if changes:
        record_audit(session, entity_type=AUDIT_FINDING, entity_id=finding.id, action="review",
                     actor=actor, changes=changes)
    return finding
