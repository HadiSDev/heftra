"""What the demo company's books span and the constants they are written with."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

ORGANIZATION_ID = "35156cc7-fb21-4b93-9b06-9fb0356e8457"

FIRST_DAY = date(2024, 10, 1)
LAST_DAY = date(2026, 9, 30)

CURRENCY = "EUR"
VAT_RATE = Decimal("0.25")
SEED = 20261003

MONEY = Decimal("0.01")
