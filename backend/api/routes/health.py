from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Request

from backend.core.config import settings
from backend.schemas.health import HealthData, HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def get_health(request: Request) -> HealthResponse:
    room_service = request.app.state.room_service
    model_service = request.app.state.model_service
    started_at = request.app.state.started_at
    uptime = (datetime.now(timezone.utc) - started_at).total_seconds()

    return HealthResponse(
        data=HealthData(
            service=settings.app_name,
            version=settings.app_version,
            environment=settings.environment,
            engine=model_service.primary_engine_name(),
            engine_ready=model_service.engine_ready(),
            rooms_active=room_service.active_room_count(),
            connected_participants=room_service.connected_participant_count(),
            uptime_seconds=round(uptime, 2),
        )
    )


@router.get("/ice-servers")
async def get_ice_servers() -> dict:
    """Return ICE server config for WebRTC peer connections."""
    servers = [{"urls": settings.stun_server}]
    if settings.turn_url:
        turn_entry: dict = {"urls": settings.turn_url}
        if settings.turn_username:
            turn_entry["username"] = settings.turn_username
        if settings.turn_password:
            turn_entry["credential"] = settings.turn_password
        servers.append(turn_entry)
    return {"iceServers": servers}

