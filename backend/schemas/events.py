from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RealtimeEnvelope(BaseModel):
    type: str = Field(..., examples=["chat.message"])
    payload: dict[str, Any] = Field(default_factory=dict)

