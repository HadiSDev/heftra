"""The demo company read back through the functions behind the web app's pages."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlmodel import Session

from web_api.agreements.reads import list_agreements
from web_api.alternatives.listing import AlternativeFilters, list_items
from web_api.auth.deps import TenantScope
from web_api.compliance.dashboard import agreement_compliance
from web_api.compliance.report import agreement_report
from web_api.db.models import Agreement
from web_api.db.session import engine
from web_api.routers.vendor_overview import vendor_overview
from web_api.spend_analytics.breakdown import spend_breakdown
from web_api.spend_analytics.emissions import spend_emissions
from web_api.spend_analytics.overview import spend_overview
from web_api.spend_analytics.periods import Period

from ..settings import LAST_DAY, ORGANIZATION_ID
from .counts import table_counts

LAST_TWELVE_MONTHS = Period(date(2025, 10, 1), LAST_DAY)
YEAR_TO_DATE = Period(date(2026, 1, 1), date(2026, 10, 3))
TOP = 6


def print_report(company_id: str) -> None:
    ids = [company_id]
    with Session(engine) as session:
        print("\nRows:", table_counts(session, company_id))
        _spend(session, ids)
        _emissions(session, ids)
        _alternatives(session, ids)
        _agreements(session, ids)
        _suppliers(session, ids)


def _spend(session: Session, ids: list[str]) -> None:
    for label, period in (("Last 12 months", LAST_TWELVE_MONTHS), ("Year to date", YEAR_TO_DATE)):
        (row,) = spend_overview(session, ids, period).rows
        print(f"\n{label}: spend {_eur(row.spend)} against {_eur(row.comparison_spend)}, "
              f"categorized {_eur(row.categorized_spend)}, {row.active_suppliers} suppliers")
    overview = spend_overview(session, ids, LAST_TWELVE_MONTHS)
    print("  Months:", ", ".join(f"{month.month:%b %y} {_eur(month.amount)}"
                                 for month in overview.rows[0].months))
    print("  Needs review:", overview.attention.needs_review_lines, "lines")
    (breakdown,) = spend_breakdown(session, ids, LAST_TWELVE_MONTHS, limit=TOP).rows
    print("  Top categories:", ", ".join(f"{category.name} {_eur(category.spend)}"
                                         for category in breakdown.categories[:TOP]))
    print("  Top suppliers:", ", ".join(f"{supplier.name} {_eur(supplier.spend)}"
                                        for supplier in breakdown.suppliers[:TOP]))


def _emissions(session: Session, ids: list[str]) -> None:
    emissions = spend_emissions(session, ids, LAST_TWELVE_MONTHS)
    tonnes = (emissions.kg_co2e or Decimal(0)) / 1000
    print(f"\nEmissions, last 12 months: {tonnes:,.0f} t CO2e; top sectors: "
          + ", ".join(f"{sector.name} {sector.kg_co2e / 1000:,.0f} t"
                      for sector in emissions.top_sectors[:4]))


def _alternatives(session: Session, ids: list[str]) -> None:
    page = list_items(session, ids, AlternativeFilters(), 1, 50)
    print(f"\nAlternatives: {page.total} items, best yearly savings {_eur(page.total_saving)}, "
          f"{page.searched_items} items searched")
    for item in page.items:
        print(f"  {item.name} ({item.supplier_name}): {item.best.source} "
              f"{item.best.saving_percent}% = {_eur(item.best.saving_yearly)}/year")


def _agreements(session: Session, ids: list[str]) -> None:
    today = date.today()
    for summary in list_agreements(session, ids, today):
        agreement = session.get(Agreement, summary.id)
        report = agreement_report(session, agreement, today, kinds=None, review_statuses=None,
                                  sort="amount", order="desc", page=1, page_size=5)
        print(f"\nAgreement {summary.title}: {summary.open_rule_breaks} open rule breaks "
              f"{_eur(summary.rule_break_amount)}, in scope {_eur(report.in_scope_spend)} "
              f"({_eur(report.supplier_spend)} with the supplier), "
              f"{report.findings.total} findings")
        for total in report.totals:
            print(f"  {total.kind}: {total.count} = {_eur(total.amount)}")
        for commitment in report.commitments:
            print(f"  Commitment {commitment.scope}: {_eur(commitment.spent)} of "
                  f"{_eur(commitment.committed)}, target to date "
                  f"{_eur(commitment.target_to_date)}")
    compliance = agreement_compliance(session, ids, YEAR_TO_DATE)
    print(f"Compliance this year: {compliance.open_rule_breaks} open rule breaks "
          f"{_eur(compliance.rule_break_amount)}; off contract "
          + ", ".join(f"{supplier.name} {_eur(supplier.amount)}"
                      for supplier in compliance.top_suppliers))


def _suppliers(session: Session, ids: list[str]) -> None:
    scope = TenantScope(organization_id=ORGANIZATION_ID, user_id="demo-report", role="admin",
                        company_ids=ids, active_company_ids=ids)
    page = vendor_overview(q=None, company_id=None, sort=None, order=None, page=1, page_size=5,
                           scope=scope, session=session)
    print(f"\nSupplier directory: {page.total} suppliers; first: "
          + ", ".join(vendor.name for vendor in page.items))


def _eur(amount: Decimal | None) -> str:
    if amount is None:
        return "n/a"
    return f"€{amount:,.0f}"
