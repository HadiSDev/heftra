"""The kinds and states of items' specifications and their alternatives."""
from __future__ import annotations

from enum import Enum


class ItemClass(str, Enum):
    """Bought to be processed or by measure, or bought to be used as it is."""

    MATERIAL = "material"
    FINISHED_GOOD = "finished_good"


class PricingUnit(str, Enum):
    KG = "kg"
    M = "m"
    M2 = "m2"
    M3 = "m3"
    L = "l"
    PIECE = "piece"
    SHEET = "sheet"
    ROLL = "roll"
    PACK = "pack"


class SpecSource(str, Enum):
    AI = "ai"
    HUMAN = "human"


class AlternativeSource(str, Enum):
    """Where an alternative was found: the organization's purchases, other organizations'
    prices, or a marketplace."""

    HISTORY = "history"
    BENCHMARK = "benchmark"
    MARKETPLACE = "marketplace"


class AlternativeMatch(str, Enum):
    EXACT = "exact"
    EQUIVALENT = "equivalent"


class AlternativeReviewStatus(str, Enum):
    OPEN = "open"
    DISMISSED = "dismissed"
    SWITCHED = "switched"


class DismissReason(str, Enum):
    NOT_EQUIVALENT = "not_equivalent"
    SUPPLIER_NOT_APPROVED = "supplier_not_approved"
    PRICE_WRONG = "price_wrong"
    OTHER = "other"
