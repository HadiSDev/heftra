"""The voucher list sorts by the column asked for, across pages, with unknown values last."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session

from web_api.db.models import Company, ErpAccount, ErpEntry, ErpIntegration, Invoice, Vendor
from web_api_testkit import auth


@pytest.fixture
def sortable_vouchers(engine, seed):
    """Four Org A vouchers whose number, supplier, date and spend each order them differently."""
    with Session(engine) as s:
        integration = ErpIntegration(company_id=seed["comp_a"], erp_type="mock")
        s.add(integration)
        s.commit()
        expense = ErpAccount(erp_integration_id=integration.id, erp_account_code="6020",
                             erp_account_name="Software", erp_account_type="expense")
        s.add(expense)
        s.commit()

        def invoice_from(name: str) -> str:
            vendor = Vendor(name=name)
            s.add(vendor)
            s.commit()
            invoice = Invoice(company_id=seed["comp_a"], vendor_id=vendor.id, currency="DKK",
                              total=Decimal("1"), status="uncategorized")
            s.add(invoice)
            s.commit()
            return invoice.id

        def posting(voucher_id: str, **fields) -> None:
            converted = fields.pop("converted", True)
            if converted:
                fields["base_currency"] = "DKK"
                fields["base_debit_amount"] = fields.get("debit_amount")
                fields["base_credit_amount"] = fields.get("credit_amount")
            s.add(ErpEntry(company_id=seed["comp_a"], erp_account_id=expense.id,
                           voucher_id=voucher_id, entry_type="purchase_invoice",
                           currency="DKK", status="pending", **fields))

        posting("A", voucher_number="9", source_invoice_id=invoice_from("Zeta"),
                accounting_date=date(2025, 7, 1), debit_amount=Decimal("500.00"))
        posting("B", voucher_number="10", source_invoice_id=invoice_from("Alpha"),
                accounting_date=date(2025, 7, 3), debit_amount=Decimal("50.00"))
        posting("C", voucher_number="11", accounting_date=date(2025, 7, 2),
                credit_amount=Decimal("30.00"))
        posting("D", debit_amount=Decimal("70.00"), converted=False)
        s.commit()


def _order(client, **params) -> list[str]:
    response = client.get("/api/v1/erp-entries/vouchers", headers=auth("tokA"), params=params)
    assert response.status_code == 200, response.text
    return [group["voucher_id"] for group in response.json()["items"]]


def test_the_list_is_newest_first_by_default(client, sortable_vouchers):
    assert _order(client) == ["B", "C", "A", "D"]


def test_oldest_first_still_leaves_the_undated_voucher_last(client, sortable_vouchers):
    assert _order(client, sort="accounting_date", order="asc") == ["A", "C", "B", "D"]


def test_voucher_numbers_sort_as_numbers_largest_first(client, sortable_vouchers):
    assert _order(client, sort="voucher_number") == ["C", "B", "A", "D"]
    assert _order(client, sort="voucher_number", order="asc") == ["A", "B", "C", "D"]


def test_suppliers_sort_a_to_z_with_the_unlinked_last(client, sortable_vouchers):
    assert _order(client, sort="vendor_name") == ["B", "A", "C", "D"]
    assert _order(client, sort="vendor_name", order="desc") == ["A", "B", "C", "D"]


def test_amounts_sort_by_net_base_spend_with_the_unconverted_last(client, sortable_vouchers):
    assert _order(client, sort="amount") == ["A", "B", "C", "D"]
    assert _order(client, sort="amount", order="asc") == ["C", "B", "A", "D"]


def test_the_sort_holds_across_pages(client, sortable_vouchers):
    pages = [_order(client, sort="amount", page_size=2, page=page) for page in (1, 2)]
    assert pages == [["A", "B"], ["C", "D"]]


def test_ties_fall_back_to_newest_first(client, sortable_vouchers):
    assert _order(client, sort="vendor_name")[2:] == ["C", "D"]


def test_an_unknown_sort_or_order_is_rejected(client, sortable_vouchers):
    for params in ({"sort": "emissions"}, {"order": "sideways"}):
        response = client.get("/api/v1/erp-entries/vouchers", headers=auth("tokA"), params=params)
        assert response.status_code == 422


def test_amounts_across_base_currencies_cannot_be_sorted(client, engine, seed, sortable_vouchers):
    with Session(engine) as s:
        s.add(Company(organization_id=seed["org_a"], name="Acme Euro", base_currency="EUR"))
        s.commit()

    response = client.get("/api/v1/erp-entries/vouchers", headers=auth("tokA"),
                          params={"sort": "amount"})

    assert response.status_code == 422
    assert _order(client, sort="vendor_name") == ["B", "A", "C", "D"]
