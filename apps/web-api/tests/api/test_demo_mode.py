"""The shared demo login sees what an organization admin sees, and can change nothing."""
from __future__ import annotations

import importlib
import pkgutil
import re

import pytest
from fastapi.routing import APIRoute

import web_api.routers
from web_api.auth.deps import DEMO_REFUSAL
from web_api.auth.principal import map_role, principal_from_claims
from web_api_testkit import auth

_DEMO = auth("tok_demoA")
_MODERATOR = auth("tok_moderatorA")

UNAUTHENTICATED_ROUTES = {
    ("POST", "/api/v1/public/demo-requests"),
    ("POST", "/api/v1/webhooks/clerk"),
}


def _write_routes() -> list[tuple[str, str]]:
    routes: set[tuple[str, str]] = set()
    for module in pkgutil.iter_modules(web_api.routers.__path__):
        router = getattr(importlib.import_module(f"web_api.routers.{module.name}"), "router", None)
        if router is None:
            continue
        for route in router.routes:
            if not isinstance(route, APIRoute):
                continue
            for method in route.methods - {"GET", "HEAD", "OPTIONS"}:
                routes.add((method, route.path))
    return sorted(routes - UNAUTHENTICATED_ROUTES)


WRITE_ROUTES = _write_routes()


def test_the_write_routes_are_found():
    assert ("PATCH", "/api/v1/invoice-lines/{line_id}") in WRITE_ROUTES
    assert ("DELETE", "/api/v1/organization") in WRITE_ROUTES


@pytest.mark.parametrize(("method", "path"), WRITE_ROUTES)
def test_the_demo_login_changes_nothing(client, seed, method, path):
    res = client.request(method, re.sub(r"\{[^}]+\}", "any", path), json={}, headers=_DEMO)

    assert res.status_code == 403
    assert res.json()["detail"] == DEMO_REFUSAL


def test_the_demo_login_cannot_change_a_real_line(client, seed):
    line = f"/api/v1/invoice-lines/{seed['line_a1']}"

    refused = client.patch(line, json={"emission_sector_id": None}, headers=_DEMO)

    assert refused.status_code == 403
    assert refused.json()["detail"] == DEMO_REFUSAL


@pytest.mark.parametrize("path", [
    "/api/v1/organization",
    "/api/v1/companies",
    "/api/v1/invoice-lines",
    "/api/v1/spend-trees",
    "/api/v1/admin/emission-factors",
])
def test_the_demo_login_reads_what_an_admin_reads(client, seed, path):
    assert client.get(path, headers=_DEMO).status_code == 200


def test_other_roles_still_save(client, seed):
    res = client.post("/api/v1/spend-trees", json={"name": "Saved"}, headers=_MODERATOR)

    assert res.status_code == 201, res.text


def test_the_demo_claim_makes_a_member_the_demo_login():
    principal = principal_from_claims({"sub": "user_demo", "org_role": "org:member", "demo": True})

    assert map_role(principal.role) == "demo"


def test_without_the_demo_claim_the_org_role_stands():
    principal = principal_from_claims({"sub": "user_1", "org_role": "org:member", "demo": None})

    assert map_role(principal.role) == "member"
