"""Request and response bodies for the public demo request form."""
from __future__ import annotations

import re
from typing import Annotated, Literal, Optional

from pydantic import AfterValidator, BaseModel, StringConstraints

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s.]+$")

MESSAGE_MAX_LENGTH = 2_000


def _email_address(value: str) -> str:
    if not _EMAIL_PATTERN.match(value):
        raise ValueError("must be a valid email address")
    return value


def _blank_to_none(value: str) -> Optional[str]:
    if value == "":
        return None
    return value


RequiredText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
EmailAddress = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=254),
    AfterValidator(_email_address),
]
Message = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=MESSAGE_MAX_LENGTH),
    AfterValidator(_blank_to_none),
]
CompanySize = Literal["1-49", "50-249", "250-999", "1000+"]


class DemoRequestCreate(BaseModel):
    """What a visitor submits from the landing site's demo form."""

    name: RequiredText
    email: EmailAddress
    company: RequiredText
    company_size: CompanySize
    message: Optional[Message] = None
    consent: Literal[True]
    website: Optional[str] = None
    rendered_at: int


class DemoRequestAccepted(BaseModel):
    """The booking link for an accepted request, or null when there is none to give."""

    booking_url: Optional[str]
