"""The agent's final answer, as it must write it."""
from __future__ import annotations

from pydantic import BaseModel, Field


class AgentReply(BaseModel):
    code: str | None = Field(
        description="The chosen sector's code exactly as a tool showed it, or null if none fits."
    )
    confidence: float = Field(description="Confidence from 0.0 to 1.0.")
    rationale: str = Field(description="One sentence saying why this sector.")
