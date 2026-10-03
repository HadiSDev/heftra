"""Reviewing an agreement's terms and findings, and its report, over the API."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlmodel import Session, select

from agreement_records import agreement, finding, supplier, term, term_spend
from web_api.db.models import (
    AgreementFinding,
    AgreementScopeJudgement,
    AgreementStatus,
    AgreementTermKind,
    AgreementTermStatus,
    AuditLog,
    FindingKind,
    PipelineRun,
)
from web_api_testkit import auth


def _in_review(engine, seed, *, with_vendor=True):
    with Session(engine) as s:
        vendor = supplier(s) if with_vendor else None
        record = agreement(s, seed["comp_a"], vendor=vendor, status=AgreementStatus.REVIEW)
        draft = term(s, record.id, kind=AgreementTermKind.AGREED_PRICE,
                     status=AgreementTermStatus.DRAFT, scope="Laptops",
                     item="Lenovo ThinkPad T14 Gen 5", unit="unit",
                     unit_price=Decimal("8000"), currency="DKK")
        return record.id, draft.id


def test_confirming_a_corrected_draft_activates_the_agreement(client, engine, seed):
    agreement_id, term_id = _in_review(engine, seed)

    res = client.patch(f"/api/v1/agreement-terms/{term_id}", headers=auth("tokA"),
                       json={"unit_price": "7950", "status": "confirmed"})

    assert res.status_code == 200, res.text
    assert (res.json()["status"], res.json()["unit_price"]) == ("confirmed", "7950.0000")
    detail = client.get(f"/api/v1/agreements/{agreement_id}", headers=auth("tokA")).json()
    assert detail["status"] == "active"
    with Session(engine) as s:
        assert s.exec(select(PipelineRun).where(PipelineRun.kind == "analyse_agreements")).one()
        changes = s.exec(select(AuditLog).where(AuditLog.entity_id == term_id)).one().changes
        assert {change["field"] for change in changes} == {"status", "unit_price"}


def test_without_a_supplier_the_agreement_stays_in_review(client, engine, seed):
    agreement_id, term_id = _in_review(engine, seed, with_vendor=False)

    client.patch(f"/api/v1/agreement-terms/{term_id}", headers=auth("tokA"),
                 json={"status": "confirmed"})

    detail = client.get(f"/api/v1/agreements/{agreement_id}", headers=auth("tokA")).json()
    assert detail["status"] == "review"


def test_editing_what_is_judged_forgets_the_judgements(client, engine, seed):
    _, term_id = _in_review(engine, seed)
    with Session(engine) as s:
        s.add(AgreementScopeJudgement(term_id=term_id, term_key="k", question_key="q",
                                      in_scope=True, reason="A laptop."))
        s.commit()

    client.patch(f"/api/v1/agreement-terms/{term_id}", headers=auth("tokA"),
                 json={"item": "Lenovo ThinkPad T14s Gen 5"})

    with Session(engine) as s:
        assert s.exec(select(AgreementScopeJudgement)).all() == []


def test_rejecting_a_term_drops_its_findings(client, engine, seed):
    with Session(engine) as s:
        record = agreement(s, seed["comp_a"], vendor=supplier(s))
        rule = term(s, record.id)
        finding(s, agreement=record, term=rule, line_id=seed["line_a1"], invoice_id=seed["inv_a"])
        term_id = rule.id

    res = client.patch(f"/api/v1/agreement-terms/{term_id}", headers=auth("tokA"),
                       json={"status": "rejected"})

    assert res.json()["status"] == "rejected"
    with Session(engine) as s:
        assert s.exec(select(AgreementFinding)).all() == []


def test_a_manager_adds_a_missed_term(client, engine, seed):
    agreement_id, _ = _in_review(engine, seed)

    res = client.post(f"/api/v1/agreements/{agreement_id}/terms", headers=auth("tokA"),
                      json={"kind": "discount", "scope": "Accessories",
                            "discount_percent": "10"})

    assert res.status_code == 201, res.text
    body = res.json()
    assert (body["status"], body["source"], body["currency"]) == ("confirmed", "human", "DKK")


def test_a_viewer_cannot_review_terms(client, engine, seed):
    _, term_id = _in_review(engine, seed)

    res = client.patch(f"/api/v1/agreement-terms/{term_id}", headers=auth("tok_viewerA"),
                       json={"status": "confirmed"})

    assert res.status_code == 403


def test_a_finding_is_accepted_as_an_exception_and_reopened(client, engine, seed):
    with Session(engine) as s:
        record = agreement(s, seed["comp_a"], vendor=supplier(s))
        rule = term(s, record.id)
        finding_id = finding(s, agreement=record, term=rule, line_id=seed["line_a1"],
                             invoice_id=seed["inv_a"]).id

    accepted = client.patch(f"/api/v1/agreement-findings/{finding_id}", headers=auth("tokA"),
                            json={"review_status": "exception",
                                  "note": "Atea out of stock, urgent replacement"})
    reopened = client.patch(f"/api/v1/agreement-findings/{finding_id}", headers=auth("tokA"),
                            json={"review_status": "open"})

    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["review_note"] == "Atea out of stock, urgent replacement"
    assert accepted.json()["reviewed_by_name"] == "Alice"
    assert (reopened.json()["review_status"], reopened.json()["review_note"]) == ("open", None)


def test_the_report_leads_with_rule_breaks(client, engine, seed):
    with Session(engine) as s:
        vendor = supplier(s)
        record = agreement(s, seed["comp_a"], vendor=vendor)
        rule = term(s, record.id)
        price = term(s, record.id, kind=AgreementTermKind.AGREED_PRICE, scope="ThinkPad",
                     item="ThinkPad", unit_price=Decimal("8000"))
        finding(s, agreement=record, term=price, line_id=seed["line_a1"],
                invoice_id=seed["inv_a"], kind=FindingKind.COMPLIANT, amount="0",
                line_amount="4000.00", from_supplier=True, vendor_id=vendor.id)
        finding(s, agreement=record, term=rule, line_id=seed["line_a2"], invoice_id=seed["inv_a"],
                amount="1000.00")
        term_spend(s, rule, date(2026, 3, 1), "4000.00", from_supplier=True)
        term_spend(s, rule, date(2026, 3, 1), "1000.00", from_supplier=False)
        term_spend(s, price, date(2026, 3, 1), "4000.00", from_supplier=True)
        agreement_id = record.id

    report = client.get(f"/api/v1/agreements/{agreement_id}/report", headers=auth("tokA")).json()

    assert [item["kind"] for item in report["findings"]["items"]] == ["off_contract", "compliant"]
    assert (report["in_scope_spend"], report["supplier_spend"]) == ("5000.00", "4000.00")
    totals = {total["kind"]: (total["count"], total["amount"]) for total in report["totals"]}
    assert totals["off_contract"] == (1, "1000.00")


def _sortable_findings(engine, seed) -> str:
    with Session(engine) as s:
        atea = supplier(s)
        proshop = supplier(s, name="proshop A/S", vat="DK87654321")
        record = agreement(s, seed["comp_a"], vendor=atea)
        rule = term(s, record.id)
        price = term(s, record.id, kind=AgreementTermKind.AGREED_PRICE, scope="Servers",
                     item="Cloud server", unit_price=Decimal("80"))
        discount = term(s, record.id, kind=AgreementTermKind.DISCOUNT, scope="Support",
                        discount_percent=Decimal("10"))
        finding(s, agreement=record, term=rule, line_id=seed["line_a2"], invoice_id=seed["inv_a"],
                amount="1000.00", vendor_id=proshop.id, spent_on=date(2025, 7, 1))
        finding(s, agreement=record, term=price, line_id=seed["line_a1"], invoice_id=seed["inv_a"],
                kind=FindingKind.COMPLIANT, amount="0", line_amount="80.00", vendor_id=atea.id,
                spent_on=date(2025, 8, 1))
        finding(s, agreement=record, term=discount, line_id=seed["line_a1"],
                invoice_id=seed["inv_a"], kind=FindingKind.MISSED_DISCOUNT, amount="300.00",
                spent_on=date(2025, 6, 1))
        return record.id


def _sorted_kinds(client, agreement_id, **params) -> list[str]:
    res = client.get(f"/api/v1/agreements/{agreement_id}/report", headers=auth("tokA"),
                     params=params)
    assert res.status_code == 200, res.text
    return [item["kind"] for item in res.json()["findings"]["items"]]


def test_findings_are_sorted_by_severity_by_default(client, engine, seed):
    agreement_id = _sortable_findings(engine, seed)

    assert _sorted_kinds(client, agreement_id) == ["off_contract", "missed_discount", "compliant"]
    assert _sorted_kinds(client, agreement_id, sort="severity", order="asc") == [
        "compliant", "missed_discount", "off_contract"]


def test_findings_are_sorted_by_amount_and_date(client, engine, seed):
    agreement_id = _sortable_findings(engine, seed)

    assert _sorted_kinds(client, agreement_id, sort="amount") == [
        "off_contract", "missed_discount", "compliant"]
    assert _sorted_kinds(client, agreement_id, sort="amount", order="asc") == [
        "compliant", "missed_discount", "off_contract"]
    assert _sorted_kinds(client, agreement_id, sort="spent_on") == [
        "compliant", "off_contract", "missed_discount"]


def test_findings_are_sorted_by_item_and_supplier_with_unknown_suppliers_last(client, engine,
                                                                               seed):
    agreement_id = _sortable_findings(engine, seed)

    assert _sorted_kinds(client, agreement_id, sort="item") == [
        "missed_discount", "compliant", "off_contract"]
    assert _sorted_kinds(client, agreement_id, sort="supplier") == [
        "compliant", "off_contract", "missed_discount"]
    assert _sorted_kinds(client, agreement_id, sort="supplier", order="desc") == [
        "off_contract", "compliant", "missed_discount"]


def test_an_unknown_findings_sort_is_refused(client, engine, seed):
    agreement_id = _sortable_findings(engine, seed)

    for params in ({"sort": "reason"}, {"order": "sideways"}):
        res = client.get(f"/api/v1/agreements/{agreement_id}/report", headers=auth("tokA"),
                         params=params)
        assert res.status_code == 422


def test_commitment_progress_is_reported(client, engine, seed):
    with Session(engine) as s:
        vendor = supplier(s)
        record = agreement(s, seed["comp_a"], vendor=vendor, starts_on=date(2025, 1, 1),
                           ends_on=date(2025, 12, 31))
        commitment = term(s, record.id, kind=AgreementTermKind.VOLUME_COMMITMENT,
                          commitment_amount=Decimal("500000"), commitment_period="agreement",
                          currency="DKK",
                          tiers=[{"threshold": "100000", "rebate_percent": "1"},
                                 {"threshold": "400000", "rebate_percent": "2"}])
        term_spend(s, commitment, date(2025, 3, 1), "150000.00", from_supplier=True)
        term_spend(s, commitment, date(2025, 3, 1), "90000.00", from_supplier=False)
        agreement_id = record.id

    (progress,) = client.get(f"/api/v1/agreements/{agreement_id}/report",
                             headers=auth("tokA")).json()["commitments"]

    assert (progress["committed"], progress["spent"]) == ("500000.00", "150000.00")
    assert (progress["period_start"], progress["period_end"]) == ("2025-01-01", "2025-12-31")
    assert (progress["tier_reached"], progress["next_tier"]) == ("100000.00", "400000.00")
