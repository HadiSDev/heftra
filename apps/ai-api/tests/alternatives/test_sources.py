"""Alternatives from the organization's purchases and from other organizations' prices."""
from __future__ import annotations

from decimal import Decimal

import pytest
from qdrant_client import QdrantClient
from sqlmodel import Session

from agreement_books import embed
from ai_api.alternatives.sources.benchmark import benchmark_candidates
from ai_api.alternatives.sources.history import history_candidates
from ai_api.specs.index import SpecEntry, SpecIndex
from alternatives_books import Shelves
from web_api.specs.specification import Specification


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture
def shelves(session) -> Shelves:
    return Shelves(session)


def test_the_same_keyboard_cheaper_at_another_supplier(session, shelves):
    acme = shelves.organization("Acme")
    keyboard = shelves.product("MXK73DK/A")
    mine = shelves.item(shelves.company(acme, "Acme DK"), "Magic Keyboard", unit_price="1136",
                        product=keyboard, vendor=shelves.vendor("CS-Online"))
    shelves.item(shelves.company(acme, "Acme SE"), "Magic Keyboard", unit_price="999",
                 product=keyboard, vendor=shelves.vendor("Proshop"))
    shelves.item(shelves.company(shelves.organization("Other")), "Magic Keyboard",
                 unit_price="900", product=keyboard)

    (found,) = history_candidates(session, shelves.context(mine), None)

    assert (found.unit_price, found.origin["supplier"], found.origin["company"]) == \
        (Decimal("999"), "Proshop", "Acme SE")


def test_a_similar_specification_is_found_through_the_index(session, shelves):
    acme = shelves.organization("Acme")
    company = shelves.company(acme)
    mine = shelves.item(company, "laptop dell", unit_price="9000")
    similar = shelves.item(company, "laptop dell thinkpad", unit_price="8000")
    index = SpecIndex(QdrantClient(location=":memory:"), embed)
    index.ensure([SpecEntry(item.id, company.id, acme.id, None,
                            Specification.model_validate(item.spec))
                  for item in (mine, similar)])

    (found,) = history_candidates(session, shelves.context(mine), index)

    assert found.ref_key == f"item:{similar.id}"
    assert found.match is None


def _six_others(shelves, prices, *, benchmark=True):
    keyboard = shelves.product("MXK73DK/A")
    for number, price in enumerate(prices):
        organization = shelves.organization(f"Org {number}", benchmark=benchmark)
        shelves.item(shelves.company(organization), "Magic Keyboard", unit_price=price,
                     product=keyboard)
    return keyboard


def test_other_customers_median_from_six_organizations(session, shelves):
    keyboard = _six_others(shelves, ["980", "999", "1010", "1050", "1136", "1190"])
    mine = shelves.item(shelves.company(shelves.organization("Acme")), "Magic Keyboard",
                        unit_price="1200", product=keyboard)

    (found,) = benchmark_candidates(session, shelves.context(mine))

    assert found.match.value == "exact"
    assert found.unit_price == Decimal("1030")
    assert found.origin == {"by": "product", "organizations": 6, "median": "1030.000000",
                            "lowest_quartile": "1001.750000"}


def test_too_few_organizations_give_no_benchmark(session, shelves):
    keyboard = _six_others(shelves, ["980", "999"])
    mine = shelves.item(shelves.company(shelves.organization("Acme")), "Magic Keyboard",
                        unit_price="1200", product=keyboard)

    assert benchmark_candidates(session, shelves.context(mine)) == []


def test_organizations_that_opted_out_are_left_out(session, shelves):
    keyboard = _six_others(shelves, ["980", "999", "1010"], benchmark=False)
    mine = shelves.item(shelves.company(shelves.organization("Acme")), "Magic Keyboard",
                        unit_price="1200", product=keyboard)

    assert benchmark_candidates(session, shelves.context(mine)) == []


def test_an_organization_that_opted_out_gets_no_benchmark(session, shelves):
    keyboard = _six_others(shelves, ["980", "999", "1010"])
    mine = shelves.item(shelves.company(shelves.organization("Acme", benchmark=False)),
                        "Magic Keyboard", unit_price="1200", product=keyboard)

    assert benchmark_candidates(session, shelves.context(mine)) == []


def test_the_same_specification_from_other_organizations(session, shelves):
    bar = {"item_class": "material", "product_type": "round bar", "pricing_unit": "kg"}
    for number, price in enumerate(["9.00", "9.10", "9.40", "9.80", "10.00"]):
        shelves.item(shelves.company(shelves.organization(f"Org {number}")), "S235 20mm",
                     unit_price=price, fields=bar)
    mine = shelves.item(shelves.company(shelves.organization("Acme")), "S235 20mm",
                        unit_price="10.40", fields=bar)

    (found,) = benchmark_candidates(session, shelves.context(mine))

    assert (found.match.value, found.unit_price) == ("equivalent", Decimal("9.4"))
    assert found.origin["organizations"] == 5
