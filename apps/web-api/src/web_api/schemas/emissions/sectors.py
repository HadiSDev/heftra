"""An emission sector as a line or the sector picker shows it."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class EmissionSectorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
