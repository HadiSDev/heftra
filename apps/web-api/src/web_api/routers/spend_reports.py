"""The dashboard's spend reports: overview, trend, breakdown and insights over a period."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from ..auth.deps import TenantScope, get_session, resolve_company_ids, tenant_scope
from ..compliance.dashboard import agreement_compliance
from ..schemas import SpendBreakdown, SpendEmissions, SpendInsights, SpendOverview, SpendTrend
from ..schemas.agreements import AgreementCompliance
from ..spend_analytics.emissions import spend_emissions
from ..spend_analytics.breakdown import DEFAULT_SUPPLIERS, MAX_SUPPLIERS, spend_breakdown
from ..spend_analytics.insights import spend_insights
from ..spend_analytics.overview import spend_overview
from ..spend_analytics.periods import Period
from ..spend_analytics.trend import spend_trend

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


class ReportScope:
    """The companies and period a spend report is asked for, validated."""

    def __init__(
        self,
        date_from: date = Query(alias="from"),
        date_to: date = Query(alias="to"),
        company_id: str | None = Query(default=None),
        scope: TenantScope = Depends(tenant_scope),
    ) -> None:
        if date_from > date_to:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="The period cannot end before it starts.",
            )
        self.period = Period(date_from, date_to)
        self.company_ids = resolve_company_ids(scope, company_id)


@router.get("/spend-overview", response_model=SpendOverview)
def get_spend_overview(
    report: ReportScope = Depends(), session: Session = Depends(get_session)
) -> SpendOverview:
    """The period's spend and its comparison, the categorized spend, suppliers and work waiting."""
    return spend_overview(session, report.company_ids, report.period)


@router.get("/spend-trend", response_model=SpendTrend)
def get_spend_trend(
    report: ReportScope = Depends(), session: Session = Depends(get_session)
) -> SpendTrend:
    """Twelve months of spend ending with the period, by the top categories."""
    return spend_trend(session, report.company_ids, report.period)


@router.get("/spend-breakdown", response_model=SpendBreakdown)
def get_spend_breakdown(
    report: ReportScope = Depends(),
    limit: int = Query(default=DEFAULT_SUPPLIERS, ge=1, le=MAX_SUPPLIERS),
    session: Session = Depends(get_session),
) -> SpendBreakdown:
    """Spend by category and the top suppliers, in the period and the comparison period."""
    return spend_breakdown(session, report.company_ids, report.period, limit=limit)


@router.get("/spend-insights", response_model=SpendInsights)
def get_spend_insights(
    report: ReportScope = Depends(), session: Session = Depends(get_session)
) -> SpendInsights:
    """New suppliers, the biggest rises, recurring spend and the largest uncategorized vouchers."""
    return spend_insights(session, report.company_ids, report.period)


@router.get("/spend-emissions", response_model=SpendEmissions)
def get_spend_emissions(
    report: ReportScope = Depends(), session: Session = Depends(get_session)
) -> SpendEmissions:
    """The period's estimated emissions against its comparison, twelve months, the top sectors."""
    return spend_emissions(session, report.company_ids, report.period)


@router.get("/agreement-compliance", response_model=AgreementCompliance)
def get_agreement_compliance(
    report: ReportScope = Depends(), session: Session = Depends(get_session)
) -> AgreementCompliance:
    """The period's open contract rule breaks and the suppliers bought from off-contract."""
    return agreement_compliance(session, report.company_ids, report.period)
