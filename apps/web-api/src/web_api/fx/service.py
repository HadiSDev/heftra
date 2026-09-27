"""Converting money into a company's base currency at a historical rate."""
from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from ..db.models import ErpEntry, FxRate, Invoice, InvoiceLine
from .provider import RateProvider, RateSet, default_provider

logger = logging.getLogger(__name__)

EUR = "EUR"
_ONE = Decimal(1)
_RATE_SCALE = Decimal("0.00000001")
_MONEY_SCALE = Decimal("0.01")

CONVERTED = "converted"
UNCONVERTED = "unconverted"
UNCHANGED = "unchanged"


def normalize_currency(code: str | None) -> str | None:
    """Uppercase a currency code, or None if it isn't one."""
    if not code:
        return None
    code = code.strip().upper()
    return code if len(code) == 3 and code.isalpha() else None


def convert(amount: Decimal | None, rate: Decimal) -> Decimal | None:
    """Apply a rate to an amount, rounded half-up to the money scale."""
    if amount is None:
        return None
    return (Decimal(amount) * rate).quantize(_MONEY_SCALE, rounding=ROUND_HALF_UP)


class FxService:
    """Resolves historical rates for one unit of work.

    Rates fetched from the provider are added to `session`, for the caller to commit with its
    own writes. A service made with `for_reads` commits them itself, in a session of their own,
    so a read-only request keeps what it fetched instead of fetching it again next time.
    """

    def __init__(self, session: Session, provider: RateProvider | None = None, *,
                 commit_fetched: bool = False) -> None:
        self.session = session
        self.provider = provider if provider is not None else default_provider()
        self._commit_fetched = commit_fetched
        self._memo: dict[date, Optional[tuple[date, dict[str, Decimal]]]] = {}

    @classmethod
    def for_reads(cls, session: Session, provider: RateProvider | None = None) -> FxService:
        """A service for a request that writes nothing else, keeping the rates it fetches."""
        return cls(session, provider, commit_fetched=True)

    def prefetch(self, dates: Iterable[date]) -> None:
        """Load the stored rates of every date in `dates` in one query."""
        wanted = {day for day in dates if day not in self._memo}
        if not wanted:
            return
        rows = self.session.exec(
            select(FxRate).where(col(FxRate.rate_date).in_(wanted))
        ).all()
        by_date: dict[date, list[FxRate]] = {}
        for row in rows:
            by_date.setdefault(row.rate_date, []).append(row)
        for day, day_rows in by_date.items():
            self._memo[day] = (day_rows[0].published_date,
                               {row.quote_currency: row.rate for row in day_rows})

    def get_rate(
        self, from_currency: str | None, to_currency: str | None, on_date: date | None
    ) -> tuple[Decimal, date] | None:
        """Return ``(rate, published_date)`` for ``from → to`` on ``on_date``."""
        source = normalize_currency(from_currency)
        target = normalize_currency(to_currency)
        if source is None or target is None or on_date is None:
            return None
        if source == target:
            return _ONE, on_date

        resolved = self._eur_rates(on_date)
        if resolved is None:
            return None
        published, rates = resolved
        if source not in rates or target not in rates or not rates[source]:
            logger.warning(
                "FX: no published rate for %s→%s on %s", source, target, on_date
            )
            return None

        rate = (rates[target] / rates[source]).quantize(_RATE_SCALE, rounding=ROUND_HALF_UP)
        return rate, published

    def _eur_rates(self, on_date: date) -> tuple[date, dict[str, Decimal]] | None:
        """The EUR-based rate set for a date, from memo, then cache, then source."""
        if on_date in self._memo:
            return self._memo[on_date]

        cached = self._read_cache(on_date)
        if cached is None:
            cached = self._fetch_and_cache(on_date)
        self._memo[on_date] = cached
        return cached

    def _read_cache(self, on_date: date) -> tuple[date, dict[str, Decimal]] | None:
        rows = self.session.exec(select(FxRate).where(FxRate.rate_date == on_date)).all()
        if not rows:
            return None
        return rows[0].published_date, {r.quote_currency: r.rate for r in rows}

    def _fetch_and_cache(self, on_date: date) -> tuple[date, dict[str, Decimal]] | None:
        fetched: RateSet | None = self.provider.fetch(on_date)
        if fetched is None:
            return None
        published, rates = fetched

        if self._commit_fetched:
            self._commit_cache(on_date, published, rates)
        else:
            self._write_cache(self.session, on_date, published, rates)
            if published != on_date:
                self._write_cache(self.session, published, published, rates)
        return published, rates

    def _commit_cache(self, on_date: date, published: date, rates: dict[str, Decimal]) -> None:
        """Store a fetched rate set in its own transaction; another request storing it first is fine."""
        with Session(self.session.get_bind()) as cache:
            self._write_cache(cache, on_date, published, rates)
            if published != on_date:
                self._write_cache(cache, published, published, rates)
            try:
                cache.commit()
            except IntegrityError:
                cache.rollback()
                logger.info("FX: rates for %s were stored by another request", on_date)

    def _write_cache(
        self, session: Session, rate_date: date, published: date, rates: dict[str, Decimal]
    ) -> None:
        existing = {
            r.quote_currency
            for r in session.exec(
                select(FxRate).where(FxRate.rate_date == rate_date)
            ).all()
        }
        source = type(self.provider).__name__
        for currency, rate in rates.items():
            if currency in existing:
                continue
            session.add(
                FxRate(
                    quote_currency=currency,
                    rate_date=rate_date,
                    published_date=published,
                    rate=rate,
                    source=source,
                )
            )

    def convert_row(
        self,
        row,
        *,
        base_currency: str,
        source_currency: str | None,
        on_date: date | None,
        amount_fields: Iterable[tuple[str, str]],
    ) -> str:
        """Write a row's base amounts, rate and rate date."""
        amount_fields = tuple(amount_fields)
        if (
            row.fx_rate is not None
            and row.base_currency == base_currency
            and all(
                getattr(row, base_field) == convert(getattr(row, source_field), row.fx_rate)
                for source_field, base_field in amount_fields
            )
        ):
            return UNCHANGED

        resolved = self.get_rate(source_currency, base_currency, on_date)
        if resolved is None:
            self._clear(row, amount_fields)
            return UNCONVERTED

        rate, published = resolved
        for source_field, base_field in amount_fields:
            setattr(row, base_field, convert(getattr(row, source_field), rate))
        row.base_currency = base_currency
        row.fx_rate = rate
        row.fx_rate_date = published
        return CONVERTED

    @staticmethod
    def _clear(row, amount_fields: Iterable[tuple[str, str]]) -> None:
        """Leave a row unmistakably unconverted rather than half-converted."""
        for _, base_field in amount_fields:
            setattr(row, base_field, None)
        row.base_currency = None
        row.fx_rate = None
        row.fx_rate_date = None

    def convert_invoice(self, invoice: Invoice, base_currency: str) -> str:
        return self.convert_row(
            invoice,
            base_currency=base_currency,
            source_currency=invoice.currency,
            on_date=invoice.invoice_date,
            amount_fields=(("total", "base_total"), ("tax", "base_tax")),
        )

    def convert_line(
        self,
        line: InvoiceLine,
        base_currency: str,
        *,
        currency: str | None,
        invoice_date: date | None,
    ) -> str:
        """Convert a line using its invoice's date and currency."""
        return self.convert_row(
            line,
            base_currency=base_currency,
            source_currency=currency,
            on_date=invoice_date,
            amount_fields=(("amount", "base_amount"),),
        )

    def convert_entry(self, entry: ErpEntry, base_currency: str) -> str:
        return self.convert_row(
            entry,
            base_currency=base_currency,
            source_currency=entry.currency,
            on_date=entry.accounting_date,
            amount_fields=(
                ("debit_amount", "base_debit_amount"),
                ("credit_amount", "base_credit_amount"),
            ),
        )
