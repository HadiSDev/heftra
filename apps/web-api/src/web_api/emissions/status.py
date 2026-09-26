"""Whether a voucher's emissions could be estimated, and if not, why."""
from __future__ import annotations

from enum import Enum


class EmissionsStatus(str, Enum):
    ESTIMATED = "estimated"
    PARTIAL = "partial"
    NO_SPEND = "no_spend"
    NO_LINES = "no_lines"
    UNMATCHED = "unmatched"
    NO_FACTOR = "no_factor"
    UNCONVERTED = "unconverted"
    NO_FACTOR_SET = "no_factor_set"
