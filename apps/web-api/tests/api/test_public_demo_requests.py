"""The landing site's demo request form: stored when genuine, absorbed when not."""
from __future__ import annotations

import time

import pytest
from sqlmodel import Session, select

from web_api import config
from web_api.db.models import DemoRequest

_URL = "/api/v1/public/demo-requests"
_BOOKING_URL = "https://cal.example/heftra-demo"


def _now_ms() -> int:
    return time.time_ns() // 1_000_000


def _body(**overrides) -> dict:
    body = {
        "name": "  Ada Lovelace ",
        "email": "ada@example.com",
        "company": "Analytical Engines ApS",
        "company_size": "50-249",
        "message": "We spend a lot on steel.",
        "consent": True,
        "website": "",
        "rendered_at": _now_ms() - 10_000,
    }
    body.update(overrides)
    return body


def _stored(engine) -> list[DemoRequest]:
    with Session(engine) as session:
        return list(session.exec(select(DemoRequest)).all())


def _error_fields(response) -> set[str]:
    return {error["loc"][-1] for error in response.json()["detail"]}


@pytest.fixture(autouse=True)
def booking_url(monkeypatch):
    monkeypatch.setattr(config, "DEMO_BOOKING_URL", _BOOKING_URL)
    monkeypatch.setattr(config, "DEMO_REQUEST_RATE_LIMIT", 5)


def test_valid_request_is_stored_and_answered_with_the_booking_url(client, engine):
    response = client.post(_URL, json=_body(), headers={"User-Agent": "pytest-browser"})

    assert response.status_code == 201
    assert response.json() == {"booking_url": _BOOKING_URL}
    (row,) = _stored(engine)
    assert row.name == "Ada Lovelace"
    assert row.email == "ada@example.com"
    assert row.company == "Analytical Engines ApS"
    assert row.company_size == "50-249"
    assert row.message == "We spend a lot on steel."
    assert row.consented_at is not None
    assert row.source_ip == "testclient"
    assert row.user_agent == "pytest-browser"


def test_blank_message_is_stored_as_none(client, engine):
    response = client.post(_URL, json=_body(message="   "))

    assert response.status_code == 201
    (row,) = _stored(engine)
    assert row.message is None


def test_booking_url_is_null_when_not_configured(client, engine, monkeypatch):
    monkeypatch.setattr(config, "DEMO_BOOKING_URL", "")

    response = client.post(_URL, json=_body())

    assert response.status_code == 201
    assert response.json() == {"booking_url": None}
    assert len(_stored(engine)) == 1


@pytest.mark.parametrize(
    ("overrides", "field"),
    [
        ({"consent": False}, "consent"),
        ({"email": "not-an-email"}, "email"),
        ({"company_size": "5000+"}, "company_size"),
        ({"name": "   "}, "name"),
        ({"company": ""}, "company"),
        ({"message": "x" * 2_001}, "message"),
    ],
)
def test_invalid_request_is_rejected_with_the_field_named(client, engine, overrides, field):
    response = client.post(_URL, json=_body(**overrides))

    assert response.status_code == 422
    assert field in _error_fields(response)
    assert _stored(engine) == []


def test_missing_consent_is_rejected(client, engine):
    body = _body()
    del body["consent"]

    response = client.post(_URL, json=body)

    assert response.status_code == 422
    assert "consent" in _error_fields(response)
    assert _stored(engine) == []


def test_filled_honeypot_is_absorbed_without_storing(client, engine):
    response = client.post(_URL, json=_body(website="https://spam.example"))

    assert response.status_code == 201
    assert response.json() == {"booking_url": None}
    assert _stored(engine) == []


def test_too_fast_submission_is_absorbed_without_storing(client, engine):
    response = client.post(_URL, json=_body(rendered_at=_now_ms() - 500))

    assert response.status_code == 201
    assert response.json() == {"booking_url": None}
    assert _stored(engine) == []


def test_requests_over_the_limit_are_refused_with_retry_after(client, engine):
    for _ in range(5):
        assert client.post(_URL, json=_body()).status_code == 201

    response = client.post(_URL, json=_body())

    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) > 0
    assert len(_stored(engine)) == 5


def test_rate_limit_follows_the_configured_value(client, engine, monkeypatch):
    monkeypatch.setattr(config, "DEMO_REQUEST_RATE_LIMIT", 2)

    statuses = [client.post(_URL, json=_body()).status_code for _ in range(3)]

    assert statuses == [201, 201, 429]
    assert len(_stored(engine)) == 2
