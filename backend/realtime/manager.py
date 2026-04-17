from __future__ import annotations

import asyncio
from dataclasses import dataclass

from fastapi import WebSocket


@dataclass
class ConnectionContext:
    websocket: WebSocket
    room_id: str
    participant_id: str
    display_name: str


class RealtimeManager:
    def __init__(self) -> None:
        self._rooms: dict[str, dict[str, ConnectionContext]] = {}
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        room_id: str,
        participant_id: str,
        display_name: str,
    ) -> None:
        await websocket.accept()
        async with self._lock:
            room = self._rooms.setdefault(room_id, {})
            room[participant_id] = ConnectionContext(
                websocket=websocket,
                room_id=room_id,
                participant_id=participant_id,
                display_name=display_name,
            )

    async def disconnect(self, room_id: str, participant_id: str) -> None:
        async with self._lock:
            room = self._rooms.get(room_id)
            if room is None:
                return
            room.pop(participant_id, None)
            if not room:
                self._rooms.pop(room_id, None)

    async def send_to(self, room_id: str, participant_id: str, message: dict) -> None:
        room = self._rooms.get(room_id, {})
        connection = room.get(participant_id)
        if connection is None:
            return
        await connection.websocket.send_json(message)

    async def broadcast(self, room_id: str, message: dict, exclude: str | None = None) -> None:
        room = self._rooms.get(room_id, {})
        disconnected: list[str] = []

        for participant_id, context in room.items():
            if participant_id == exclude:
                continue
            try:
                await context.websocket.send_json(message)
            except Exception:
                disconnected.append(participant_id)

        for participant_id in disconnected:
            await self.disconnect(room_id, participant_id)

    def connected_participants(self, room_id: str) -> list[str]:
        return list(self._rooms.get(room_id, {}).keys())

