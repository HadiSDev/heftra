"""The dashboard's tiles: spend and its change, the categorized share, suppliers, work waiting."""
from __future__ import annotations

from sqlmodel import Session

from web_api.schemas import MonthSpend, SpendOverview, SpendOverviewRow

from .allocation import allocate
from .figures import attention_counts, by_currency, first_invoice_dates, report_periods, total, within
from .periods import Period, month_start, trailing_months


def spend_overview(session: Session, company_ids: list[str], period: Period) -> SpendOverview:
    comparison = period.comparison()
    months = trailing_months(period.end)
    window = Period(min(comparison.start, months[0]), period.end)
    allocation = allocate(session, company_ids, window)
    first_invoices = first_invoice_dates(session, company_ids)

    rows = []
    for currency, spend in by_currency(allocation.spend).items():
        in_period = within(spend, period)
        suppliers = {row.vendor_id for row in in_period if row.vendor_id}
        rows.append(SpendOverviewRow(
            currency=currency,
            spend=total(in_period),
            comparison_spend=total(within(spend, comparison)),
            categorized_spend=total(row for row in in_period if row.categorized),
            unconverted_vouchers=sum(
                1 for voucher in allocation.unconverted
                if voucher.currency == currency and period.contains(voucher.spent_on)
            ),
            months=[
                MonthSpend(month=month, amount=total(
                    row for row in spend if month_start(row.spent_on) == month
                ))
                for month in months
            ],
            active_suppliers=len(suppliers),
            new_suppliers=sum(
                1 for vendor_id in suppliers
                if vendor_id in first_invoices and period.contains(first_invoices[vendor_id])
            ),
        ))

    return SpendOverview(
        **report_periods(period).model_dump(),
        rows=rows,
        attention=attention_counts(session, company_ids),
    )
