from __future__ import annotations

import random
import string
from dataclasses import dataclass, field
from datetime import datetime

from backend.core.errors import AppError
from backend.schemas.room import ParticipantSnapshot, RoomSnapshot


@dataclass
class ParticipantState:
    participant_id: str
    display_name: str
    role: str
    joined_at: datetime = field(default_factory=datetime.utcnow)
    connected: bool = False
    mic_enabled: bool = True
    camera_enabled: bool = True


@dataclass
class RoomState:
    room_id: str
    room_name: str
    accessibility_mode: bool
    max_participants: int
    created_at: datetime = field(default_factory=datetime.utcnow)
    participants: dict[str, ParticipantState] = field(default_factory=dict)
    recent_chat: list[dict[str, str]] = field(default_factory=list)
    recent_captions: list[dict[str, str]] = field(default_factory=list)


class RoomService:
    def __init__(self, default_capacity: int, max_capacity: int) -> None:
        self._default_capacity = default_capacity
        self._max_capacity = max_capacity
        self._rooms: dict[str, RoomState] = {}

    def create_room(
        self,
        display_name: str,
        participant_id: str | None,
        room_name: str,
        accessibility_mode: bool,
        max_participants: int,
    ) -> RoomState:
        room_id = self._generate_room_id()
        capacity = max(2, min(max_participants or self._default_capacity, self._max_capacity))
        room = RoomState(
            room_id=room_id,
            room_name=room_name,
            accessibility_mode=accessibility_mode,
            max_participants=capacity,
        )

        host_id = participant_id or f"host-{room_id.lower()}"
        room.participants[host_id] = ParticipantState(
            participant_id=host_id,
            display_name=display_name,
            role="host",
        )
        self._rooms[room_id] = room
        return room

    def join_room(self, room_id: str, display_name: str, participant_id: str | None) -> RoomState:
        room = self.get_room(room_id)
        member_id = participant_id or f"guest-{room_id.lower()}-{len(room.participants) + 1}"

        if member_id not in room.participants and len(room.participants) >= room.max_participants:
            raise AppError("Room is full.", code="room_full", status_code=409)

        role = "host" if not room.participants else "guest"
        room.participants.setdefault(
            member_id,
            ParticipantState(
                participant_id=member_id,
                display_name=display_name,
                role=role,
            ),
        )
        return room

    def get_room(self, room_id: str) -> RoomState:
        room = self._rooms.get(room_id.upper())
        if room is None:
            raise AppError("Room not found.", code="room_not_found", status_code=404)
        return room

    def connect_participant(self, room_id: str, participant_id: str, display_name: str) -> RoomState:
        room = self.get_room(room_id)
        room.participants.setdefault(
            participant_id,
            ParticipantState(
                participant_id=participant_id,
                display_name=display_name,
                role="guest" if room.participants else "host",
            ),
        )
        room.participants[participant_id].display_name = display_name
        room.participants[participant_id].connected = True
        return room

    def disconnect_participant(self, room_id: str, participant_id: str) -> RoomState | None:
        room = self._rooms.get(room_id.upper())
        if room is None:
            return None
        participant = room.participants.get(participant_id)
        if participant is not None:
            participant.connected = False
        return room

    def update_media_state(
        self,
        room_id: str,
        participant_id: str,
        mic_enabled: bool | None,
        camera_enabled: bool | None,
    ) -> RoomState:
        room = self.get_room(room_id)
        participant = room.participants.get(participant_id)
        if participant is None:
            raise AppError("Participant not found.", code="participant_not_found", status_code=404)
        if mic_enabled is not None:
            participant.mic_enabled = mic_enabled
        if camera_enabled is not None:
            participant.camera_enabled = camera_enabled
        return room

    def add_chat_message(self, room_id: str, participant_id: str, message: str) -> dict[str, str]:
        room = self.get_room(room_id)
        participant = room.participants.get(participant_id)
        payload = {
            "participant_id": participant_id,
            "display_name": participant.display_name if participant else participant_id,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        room.recent_chat.append(payload)
        room.recent_chat = room.recent_chat[-20:]
        return payload

    def add_caption(self, room_id: str, participant_id: str, caption: str, confidence: float) -> dict[str, str]:
        room = self.get_room(room_id)
        participant = room.participants.get(participant_id)
        payload = {
            "participant_id": participant_id,
            "display_name": participant.display_name if participant else participant_id,
            "caption": caption,
            "confidence": f"{confidence:.2f}",
            "timestamp": datetime.utcnow().isoformat(),
        }
        room.recent_captions.append(payload)
        room.recent_captions = room.recent_captions[-20:]
        return payload

    def clear_captions(self, room_id: str, participant_id: str) -> dict[str, str]:
        room = self.get_room(room_id)
        room.recent_captions = []
        return {
            "participant_id": participant_id,
            "room_id": room.room_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def snapshot(self, room_id: str) -> RoomSnapshot:
        room = self.get_room(room_id)
        participants = [
            ParticipantSnapshot(
                participant_id=participant.participant_id,
                display_name=participant.display_name,
                role=participant.role,
                joined_at=participant.joined_at,
                connected=participant.connected,
                mic_enabled=participant.mic_enabled,
                camera_enabled=participant.camera_enabled,
            )
            for participant in room.participants.values()
        ]
        return RoomSnapshot(
            room_id=room.room_id,
            room_name=room.room_name,
            accessibility_mode=room.accessibility_mode,
            max_participants=room.max_participants,
            created_at=room.created_at,
            participants=participants,
            recent_chat=room.recent_chat,
            recent_captions=room.recent_captions,
        )

    def active_room_count(self) -> int:
        return len(self._rooms)

    def connected_participant_count(self) -> int:
        return sum(1 for room in self._rooms.values() for participant in room.participants.values() if participant.connected)

    @staticmethod
    def _generate_room_id() -> str:
        alphabet = string.ascii_uppercase + string.digits
        return "".join(random.choice(alphabet) for _ in range(6))
