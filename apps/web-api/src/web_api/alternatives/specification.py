"""A person correcting an item's specification: kept from then on, priced at once, and the
item searched again."""
from __future__ import annotations

from sqlmodel import Session

from ..audit import diff_changes, record_audit
from ..db.models import CompanyItem, SpecSource
from ..specs.pricing import price_item
from ..specs.specification import Specification
from .access import AUDIT_ITEM
from .search_requests import request_item_search


def correct_specification(session: Session, item: CompanyItem, spec: Specification,
                          actor: str) -> CompanyItem:
    """Store the specification as a person's, price the item by it in base currency and queue
    a new search, which links its product and signature and prices it in EUR again; the caller
    commits."""
    before = item.spec
    item.spec = spec.stored()
    item.item_class = spec.item_class.value
    item.spec_source = SpecSource.HUMAN.value
    item.spec_signature = None
    item.product_id = None
    item.searched_at = None
    price_item(item, None)
    session.add(item)
    changes = diff_changes({"spec": before}, {"spec": item.spec}, ("spec",))
    if changes:
        record_audit(session, entity_type=AUDIT_ITEM, entity_id=item.id, action="update",
                     actor=actor, changes=changes)
    request_item_search(session, item, actor)
    return item
