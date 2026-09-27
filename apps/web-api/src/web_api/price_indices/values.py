"""A month's value of a price index series."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import NamedTuple


class IndexValue(NamedTuple):
    month: date
    value: Decimal
