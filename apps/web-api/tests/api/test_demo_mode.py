"""The demo role is refused what the hosted demo has no worker, AI, file store or real ERP for."""
from __future__ import annotations

import importlib
import pkgutil

import pytest
from fastapi.routing import APIRoute

import web_api.routers
from web_api.auth.deps import refuse_in_demo
from web_api.auth.principal import map_role, principal_from_claims
from web_api_testkit import auth

_DEMO = auth("tok_demoA")
_MODERATOR = auth("tok_moderatorA")
_REFUSED = "Not available in the demo"

REFUSED_ROUTES = [
    ("post", "/api/v1/invoices/{inv_a}/reprocess"),
    ("patch", "/api/v1/items/any/specification"),
    ("post", "/api/v1/items/any/find-alternatives"),
    ("post", "/api/v1/invoice-lines/{line_a1}/find-alternatives"),
    ("post", "/api/v1/companies/{comp_a}/agreements"),
    ("delete", "/api/v1/agreements/any"),
    ("get", "/api/v1/agreements/any/document"),
    ("post", "/api/v1/agreements/any/read"),
    ("post", "/api/v1/companies/{comp_a}/agreements/analyse"),
    ("post", "/api/v1/companies"),
    ("patch", "/api/v1/companies/{comp_a}"),
    ("post", "/api/v1/companies/{comp_a}/recompute-fx"),
    ("post", "/api/v1/companies/{comp_a}/recategorize"),
    ("post", "/api/v1/companies/{comp_a}/deactivate"),
    ("post", "/api/v1/companies/{comp_a}/activate"),
    ("delete", "/api/v1/companies/{comp_a}"),
    ("post", "/api/v1/erp-integrations"),
    ("patch", "/api/v1/erp-integrations/any"),
    ("post", "/api/v1/erp-integrations/any/disconnect"),
    ("post", "/api/v1/erp-integrations/any/reconnect"),
    ("post", "/api/v1/erp-integrations/any/replace"),
    ("post", "/api/v1/erp-integrations/any/test-connection"),
    ("post", "/api/v1/erp-integrations/any/refresh-accounts"),
    ("post", "/api/v1/companies/{comp_a}/runs"),
]

DEMO_ALLOWED_ROUTES = {
    ("PATCH", "/api/v1/agreement-findings/{finding_id}"),
    ("POST", "/api/v1/agreements/{agreement_id}/terms"),
    ("PATCH", "/api/v1/agreement-terms/{term_id}"),
    ("PATCH", "/api/v1/agreements/{agreement_id}"),
    ("PATCH", "/api/v1/alternatives/{alternative_id}"),
    ("PATCH", "/api/v1/erp-accounts/{account_id}"),
    ("POST", "/api/v1/invoice-lines/{line_id}/verify"),
    ("PATCH", "/api/v1/invoice-lines/{line_id}"),
    ("POST", "/api/v1/invoices/{invoice_id}/lines"),
    ("DELETE", "/api/v1/invoice-lines/{line_id}"),
    ("PATCH", "/api/v1/invoices/{invoice_id}"),
    ("POST", "/api/v1/invoices/{invoice_id}/verify"),
    ("POST", "/api/v1/spend-trees/default"),
    ("POST", "/api/v1/spend-trees"),
    ("PATCH", "/api/v1/spend-trees/{tree_id}"),
    ("POST", "/api/v1/spend-trees/{tree_id}/archive"),
    ("DELETE", "/api/v1/spend-trees/{tree_id}"),
    ("POST", "/api/v1/spend-trees/{tree_id}/import"),
    ("POST", "/api/v1/spend-trees/{tree_id}/nodes"),
    ("PATCH", "/api/v1/spend-tree-nodes/{node_id}"),
    ("DELETE", "/api/v1/spend-tree-nodes/{node_id}"),
    ("POST", "/api/v1/spend-tree-suggestions/{suggestion_id}/accept"),
    ("POST", "/api/v1/spend-tree-suggestions/{suggestion_id}/reopen"),
    ("POST", "/api/v1/spend-tree-suggestions/{suggestion_id}/dismiss"),
}

BEYOND_A_MODERATOR_ROUTES = {
    ("POST", "/api/v1/admin/emission-factors/sets/{factor_set_id}/activate"),
    ("POST", "/api/v1/admin/emission-factors/price-index/refresh"),
    ("POST", "/api/v1/admin/emission-factors/workbooks"),
    ("PATCH", "/api/v1/organization"),
    ("DELETE", "/api/v1/organization"),
    ("POST", "/api/v1/public/demo-requests"),
    ("POST", "/api/v1/webhooks/clerk"),
}


def _request(client, method: str, path: str, seed: dict, headers: dict):
    return client.request(method.upper(), path.format(**seed), json={}, headers=headers)


def _detail(response) -> object:
    if response.headers.get("content-type", "").startswith("application/json"):
        return response.json().get("detail")
    return None


@pytest.mark.parametrize(("method", "path"), REFUSED_ROUTES)
def test_the_demo_role_is_refused(client, seed, method, path):
    res = _request(client, method, path, seed, _DEMO)

    assert res.status_code == 403
    assert res.json()["detail"] == _REFUSED


@pytest.mark.parametrize(("method", "path"), REFUSED_ROUTES)
def test_a_moderator_is_not_refused_for_the_demo(client, seed, method, path):
    res = _request(client, method, path, seed, _MODERATOR)

    assert _detail(res) != _REFUSED


def test_the_demo_claim_makes_a_member_the_demo_role():
    principal = principal_from_claims({"sub": "user_demo", "org_role": "org:member", "demo": True})

    assert map_role(principal.role) == "demo"


def test_without_the_demo_claim_the_org_role_stands():
    principal = principal_from_claims({"sub": "user_1", "org_role": "org:member", "demo": None})

    assert map_role(principal.role) == "member"


def test_the_demo_role_chooses_an_emission_sector(client, seed):
    res = client.patch(f"/api/v1/invoice-lines/{seed['line_a1']}",
                       json={"emission_sector_id": None}, headers=_DEMO)

    assert res.status_code == 200, res.text


def test_the_demo_role_builds_a_spend_tree(client, seed):
    created = client.post("/api/v1/spend-trees", json={"name": "Demo tree"}, headers=_DEMO)
    assert created.status_code == 201, created.text

    node = client.post(f"/api/v1/spend-trees/{created.json()['id']}/nodes",
                       json={"name": "Facilities"}, headers=_DEMO)

    assert node.status_code == 201, node.text


def _mutating_routes() -> set[tuple[str, str, bool]]:
    routes: set[tuple[str, str, bool]] = set()
    for module in pkgutil.iter_modules(web_api.routers.__path__):
        router = getattr(importlib.import_module(f"web_api.routers.{module.name}"), "router", None)
        if router is None:
            continue
        for route in router.routes:
            if not isinstance(route, APIRoute):
                continue
            refused = any(dep.dependency is refuse_in_demo for dep in route.dependencies)
            for method in route.methods - {"GET", "HEAD", "OPTIONS"}:
                routes.add((method, route.path, refused))
    return routes


def test_the_demo_role_cannot_manage_the_organization(client, seed):
    res = client.patch("/api/v1/organization", json={"name": "Taken over"}, headers=_DEMO)

    assert res.status_code == 403


def test_every_write_route_is_refused_or_allowed_in_the_demo_on_purpose():
    unclassified = {
        (method, path) for method, path, refused in _mutating_routes()
        if not refused and (method, path) not in DEMO_ALLOWED_ROUTES | BEYOND_A_MODERATOR_ROUTES
    }

    assert unclassified == set()
