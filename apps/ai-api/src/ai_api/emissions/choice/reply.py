"""The model's single-shot answer."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ChoiceReply(BaseModel):
    choice: int = Field(description="Number of the chosen sector from the list, or 0 if none fits.")
    confidence: float = Field(description="Confidence from 0.0 to 1.0.")
    rationale: str = Field(description="One sentence saying why this sector.")
