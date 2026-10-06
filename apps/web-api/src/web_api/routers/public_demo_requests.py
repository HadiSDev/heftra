"""Demo requests from the public landing site, accepted without an account."""
from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session

from web_api import config
from web_api.db.models import DemoRequest
from web_api.demo_requests.guard import is_automated_submission
from web_api.demo_requests.rate_limiter import SlidingWindowRateLimiter
from web_api.schemas.demo_requests import DemoRequestAccepted, DemoRequestCreate

from ..auth.deps import get_session

router = APIRouter(prefix="/api/v1", tags=["public"])

RATE_LIMIT_WINDOW_SECONDS = 60 * 60

_UNKNOWN_CLIENT = "unknown"


def new_demo_request_limiter() -> SlidingWindowRateLimiter:
    return SlidingWindowRateLimiter(window_seconds=RATE_LIMIT_WINDOW_SECONDS)


def get_demo_request_limiter(request: Request) -> SlidingWindowRateLimiter:
    """The application's limiter, so each app instance counts requests on its own."""
    return request.app.state.demo_request_limiter


def _client_ip(request: Request) -> str | None:
    if request.client is None:
        return None
    return request.client.host


@router.post(
    "/public/demo-requests",
    status_code=status.HTTP_201_CREATED,
    response_model=DemoRequestAccepted,
)
def create_demo_request(
    body: DemoRequestCreate,
    request: Request,
    limiter: SlidingWindowRateLimiter = Depends(get_demo_request_limiter),
    session: Session = Depends(get_session),
) -> DemoRequestAccepted:
    source_ip = _client_ip(request)
    decision = limiter.admit(
        source_ip or _UNKNOWN_CLIENT, config.DEMO_REQUEST_RATE_LIMIT, time.monotonic()
    )
    if not decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many demo requests; please try again later.",
            headers={"Retry-After": str(decision.retry_after_seconds)},
        )

    if is_automated_submission(body.website, body.rendered_at, time.time_ns() // 1_000_000):
        return DemoRequestAccepted(booking_url=None)

    session.add(
        DemoRequest(
            name=body.name,
            email=body.email,
            company=body.company,
            company_size=body.company_size,
            message=body.message,
            consented_at=datetime.now(timezone.utc),
            source_ip=source_ip,
            user_agent=request.headers.get("user-agent"),
        )
    )
    session.commit()
    return DemoRequestAccepted(booking_url=config.DEMO_BOOKING_URL or None)
