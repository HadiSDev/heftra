"""Items and alternatives as the API returns them."""
from __future__ import annotations

from collections.abc import Iterable

from sqlmodel import Session, col, select

from ..db.models import (
    CompanyItem,
    ItemAlternative,
    PipelineRun,
    PipelineRunKind,
    PipelineRunStatus,
    SpendCategory,
    User,
    Vendor,
)
from ..schemas.alternatives import AlternativeRead, ItemRead
from ..specs.specification import read_spec

IN_FLIGHT = (PipelineRunStatus.QUEUED.value, PipelineRunStatus.RUNNING.value)


def alternative_reads(session: Session,
                      alternatives: Iterable[ItemAlternative]) -> list[AlternativeRead]:
    alternatives = list(alternatives)
    reviewers = _names(session, User, {entry.reviewed_by for entry in alternatives
                                       if entry.reviewed_by})
    return [AlternativeRead.model_validate(
        {**entry.model_dump(), "reviewed_by_name": reviewers.get(entry.reviewed_by)})
        for entry in alternatives]


def item_read(session: Session, item: CompanyItem) -> ItemRead:
    alternatives = session.exec(select(ItemAlternative).where(
        ItemAlternative.item_id == item.id)).all()
    ranked = sorted(alternatives, key=lambda entry: (entry.review_status != "open",
                                                     -(entry.saving_yearly or 0)))
    category = session.get(SpendCategory, item.category_id) if item.category_id else None
    vendor = session.get(Vendor, item.vendor_id) if item.vendor_id else None
    return ItemRead(
        id=item.id, company_id=item.company_id, item_name=item.item_name,
        description=item.description, unit=item.unit, vendor_id=item.vendor_id,
        supplier_name=vendor.name if vendor else None,
        category_path=[level for level in (category.level_1, category.level_2, category.level_3,
                                           category.level_4) if level] if category else [],
        spec=read_spec(item.spec), spec_source=item.spec_source, spend=item.spend,
        lines=item.lines, last_bought_on=item.last_bought_on, quantity=item.quantity,
        unit_price=item.unit_price, currency=item.base_currency, price_note=item.price_note,
        searched_at=item.searched_at, searching=searching(session, item) is not None,
        alternatives=alternative_reads(session, ranked))


def searching(session: Session, item: CompanyItem) -> PipelineRun | None:
    """The item's search that is queued or running."""
    runs = session.exec(select(PipelineRun).where(
        PipelineRun.company_id == item.company_id,
        PipelineRun.kind == PipelineRunKind.FIND_ALTERNATIVES.value,
        col(PipelineRun.status).in_(IN_FLIGHT))).all()
    return next((run for run in runs if (run.params or {}).get("item_id") == item.id), None)


def _names(session: Session, model, ids: set[str]) -> dict[str, str]:
    if not ids:
        return {}
    return dict(session.exec(select(model.id, model.name).where(col(model.id).in_(ids))).all())


def vendor_names(session: Session, ids: set[str]) -> dict[str, str]:
    return _names(session, Vendor, ids)
