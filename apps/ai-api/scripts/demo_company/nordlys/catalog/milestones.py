"""The large one-off invoices that make some months stand out: stage payments, switchboards and
the yearly audit."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from .products import office_services as o
from .products import site_services as s
from .shapes import MilestoneSpec

MILESTONES: tuple[MilestoneSpec, ...] = (
    MilestoneSpec(date(2024, 11, 28), "jord-kloak-vest", s.GROUNDWORKS_STAGE, Decimal("88000.00")),
    MilestoneSpec(date(2025, 3, 20), "kjaer-partnere", o.ANNUAL_AUDIT, Decimal("14500.00")),
    MilestoneSpec(date(2025, 6, 26), "jord-kloak-vest", s.GROUNDWORKS_STAGE, Decimal("118000.00")),
    MilestoneSpec(date(2025, 10, 30), "jord-kloak-vest", s.GROUNDWORKS_STAGE, Decimal("96500.00")),
    MilestoneSpec(date(2025, 11, 27), "elinstallator-holm", s.ELECTRICAL_MATERIALS,
                  Decimal("48200.00")),
    MilestoneSpec(date(2026, 3, 19), "kjaer-partnere", o.ANNUAL_AUDIT, Decimal("15200.00")),
    MilestoneSpec(date(2026, 3, 27), "jord-kloak-vest", s.GROUNDWORKS_STAGE, Decimal("142000.00")),
    MilestoneSpec(date(2026, 4, 29), "elinstallator-holm", s.ELECTRICAL_MATERIALS,
                  Decimal("64000.00")),
    MilestoneSpec(date(2026, 9, 24), "jord-kloak-vest", s.GROUNDWORKS_STAGE, Decimal("168000.00")),
    MilestoneSpec(date(2026, 9, 29), "elinstallator-holm", s.ELECTRICAL_MATERIALS,
                  Decimal("72500.00")),
)
