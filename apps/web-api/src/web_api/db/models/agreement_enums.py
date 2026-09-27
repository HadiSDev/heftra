"""The states and kinds of agreements, their terms and their findings."""
from __future__ import annotations

from enum import Enum


class AgreementStatus(str, Enum):
    """Where an agreement is between upload and being analysed."""

    PENDING = "pending"
    READING = "reading"
    REVIEW = "review"
    ACTIVE = "active"
    FAILED = "failed"


class AgreementTermKind(str, Enum):
    PREFERRED_SUPPLIER = "preferred_supplier"
    AGREED_PRICE = "agreed_price"
    DISCOUNT = "discount"
    VOLUME_COMMITMENT = "volume_commitment"


class AgreementTermStatus(str, Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class AgreementTermSource(str, Enum):
    AI = "ai"
    HUMAN = "human"


class FindingKind(str, Enum):
    COMPLIANT = "compliant"
    OFF_CONTRACT = "off_contract"
    OVERCHARGE = "overcharge"
    MISSED_DISCOUNT = "missed_discount"
    POTENTIAL_SAVING = "potential_saving"
    PRICE_UNVERIFIABLE = "price_unverifiable"


class FindingSeverity(str, Enum):
    RULE_BREAK = "rule_break"
    WARNING = "warning"
    INFO = "info"


class FindingReviewStatus(str, Enum):
    OPEN = "open"
    EXCEPTION = "exception"
    NOT_IN_SCOPE = "not_in_scope"
