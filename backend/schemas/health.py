from __future__ import annotations

from pydantic import BaseModel, Field


class HealthData(BaseModel):
    service: str = Field(..., examples=["SignBridge Backend"])
    version: str = Field(..., examples=["2.0.0"])
    environment: str = Field(..., examples=["development"])
    engine: str = Field(..., examples=["heuristic"])
    engine_ready: bool
    rooms_active: int
    connected_participants: int
    uptime_seconds: float


class HealthResponse(BaseModel):
    success: bool = True
    message: str = "Backend healthy."
    data: HealthData

