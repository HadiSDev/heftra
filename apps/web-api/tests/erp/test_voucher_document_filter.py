"""Vouchers by the state of their document: the ones that failed, and the ones whose total disagrees."""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlmodel import Session

from web_api.db.models import Invoice

from web_api_testkit import auth

_LIST = "/api/v1/erp-entries/vouchers"
_SUMMARY = "/api/v1/erp-entries/vouchers/summary"


def _set_invoice(engine, invoice_id: str, **fields) -> None:
    with Session(engine) as s:
        invoice = s.get(Invoice, invoice_id)
        for name, value in fields.items():
            setattr(invoice, name, value)
        s.add(invoice)
        s.commit()


def _vouchers(client, **params) -> list[dict]:
    res = client.get(_LIST, params=params, headers=auth("tokA"))
    assert res.status_code == 200, res.text
    return res.json()["items"]


def test_only_vouchers_whose_document_failed_are_listed(client, engine, voucher_seed):
    assert _vouchers(client, document="failed") == []

    _set_invoice(engine, voucher_seed["inv_a"], doc_status="failed")

    assert [v["voucher_id"] for v in _vouchers(client, document="failed")] == ["4821"]


def test_only_vouchers_whose_total_disagrees_are_listed(client, engine, voucher_seed):
    _set_invoice(engine, voucher_seed["inv_a"], document_total=Decimal("100.00"))
    assert _vouchers(client, document="mismatch") == []

    _set_invoice(engine, voucher_seed["inv_a"], document_total=Decimal("999.00"))

    assert [v["voucher_id"] for v in _vouchers(client, document="mismatch")] == ["4821"]


def test_the_summary_takes_the_same_filter(client, engine, voucher_seed):
    _set_invoice(engine, voucher_seed["inv_a"], doc_status="failed")

    res = client.get(_SUMMARY, params={"document": "failed"}, headers=auth("tokA"))

    assert res.status_code == 200
    assert [row["voucher_count"] for row in res.json()["rows"]] == [1]


@pytest.mark.parametrize("url", [_LIST, _SUMMARY])
def test_an_unknown_document_state_is_refused(client, voucher_seed, url):
    assert client.get(url, params={"document": "lost"}, headers=auth("tokA")).status_code == 422
