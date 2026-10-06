"""Planning every invoice of the demo company's books, the same on every run."""
from __future__ import annotations

import hashlib
import math
import random
from datetime import date

from ..catalog.milestones import MILESTONES
from ..catalog.shapes import Billing, MilestoneSpec, OfferSpec, SupplierSpec
from ..catalog.suppliers import SUPPLIERS
from ..settings import SEED
from .lines import LinePlanner
from .planned import PlannedInvoice, PlannedLine
from .season import activity
from .working_days import months, working_days

MONTHLY_BILLING_DAY = 2
FIRST_NUMBER = 10_000
NUMBER_RANGE = 80_000


class PurchasePlanner:
    def __init__(self, seed: int = SEED) -> None:
        self._rng = random.Random(seed)
        self._lines = LinePlanner(self._rng)

    def plan(self) -> list[PlannedInvoice]:
        """Every invoice from the first day to the last, oldest first, numbered per supplier."""
        drafts: list[tuple[SupplierSpec, date, tuple[PlannedLine, ...]]] = []
        for month in months():
            for supplier in SUPPLIERS:
                drafts += self._month(supplier, month)
            drafts += [self._milestone(milestone) for milestone in MILESTONES
                       if milestone.on.replace(day=1) == month]
        drafts.sort(key=lambda draft: (draft[1], draft[0].key))
        return self._numbered(drafts)

    def _month(self, supplier: SupplierSpec,
               month: date) -> list[tuple[SupplierSpec, date, tuple[PlannedLine, ...]]]:
        days = working_days(month, supplier.first_day)
        if not days:
            return []
        busy = activity(month) if supplier.seasonal else 1.0
        if supplier.billing == Billing.MONTHLY:
            on = days[min(MONTHLY_BILLING_DAY, len(days) - 1)]
            lines = tuple(self._lines.order(offer, on, sequence, busy)
                          for sequence, offer in enumerate(supplier.offers))
            return [(supplier, on, lines)]
        share = len(days) / len(working_days(month))
        count = self._count(supplier.invoices_per_month * busy * share)
        scale = math.sqrt(busy)
        drafts = []
        for _ in range(count):
            on = self._rng.choice(days)
            offers = self._pick(supplier)
            lines = tuple(self._lines.order(offer, on, sequence, scale)
                          for sequence, offer in enumerate(offers))
            drafts.append((supplier, on, lines))
        return drafts

    def _milestone(self, milestone: MilestoneSpec
                   ) -> tuple[SupplierSpec, date, tuple[PlannedLine, ...]]:
        supplier = next(spec for spec in SUPPLIERS if spec.key == milestone.supplier)
        return supplier, milestone.on, (self._lines.lump_sum(milestone.product, 0,
                                                             milestone.amount),)

    def _count(self, expected: float) -> int:
        whole = math.floor(expected)
        return whole + (1 if self._rng.random() < expected - whole else 0)

    def _pick(self, supplier: SupplierSpec) -> list[OfferSpec]:
        """Distinct offers for one invoice, the heavier ones more often."""
        low, high = supplier.lines_per_invoice
        wanted = min(self._rng.randint(low, high), len(supplier.offers))
        remaining = list(supplier.offers)
        picked = []
        while len(picked) < wanted:
            choice = self._rng.choices(remaining, weights=[offer.weight for offer in remaining])[0]
            remaining.remove(choice)
            picked.append(choice)
        return picked

    @staticmethod
    def _numbered(drafts: list[tuple[SupplierSpec, date, tuple[PlannedLine, ...]]]
                  ) -> list[PlannedInvoice]:
        counters: dict[str, int] = {}
        invoices = []
        for supplier, on, lines in drafts:
            if supplier.key not in counters:
                digest = int(hashlib.sha256(supplier.key.encode()).hexdigest(), 16)
                counters[supplier.key] = FIRST_NUMBER + digest % NUMBER_RANGE
            counters[supplier.key] += 1
            number = f"{supplier.invoice_prefix}-{counters[supplier.key]}"
            invoices.append(PlannedInvoice(key=f"{supplier.key}:{number}", supplier=supplier,
                                           number=number, on=on, lines=lines))
        return invoices
