from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ParticipantSnapshot(BaseModel):
    participant_id: str
    display_name: str
    role: str
    joined_at: datetime
    connected: bool
    mic_enabled: bool
    camera_enabled: bool


class RoomSnapshot(BaseModel):
    room_id: str
    room_name: str
    accessibility_mode: bool
    max_participants: int
    created_at: datetime
    participants: list[ParticipantSnapshot] = Field(default_factory=list)
    recent_chat: list[dict[str, str]] = Field(default_factory=list)
    recent_captions: list[dict[str, str]] = Field(default_factory=list)


class RoomCreateRequest(BaseModel):
    display_name: str
    participant_id: str | None = None
    room_name: str = "Live translation room"
    accessibility_mode: bool = True
    max_participants: int = 2


class RoomJoinRequest(BaseModel):
    display_name: str
    participant_id: str | None = None


class RoomResponse(BaseModel):
    success: bool = True
    message: str
    data: RoomSnapshot

