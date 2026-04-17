from __future__ import annotations

from fastapi import APIRouter, Request

from backend.schemas.room import RoomCreateRequest, RoomJoinRequest, RoomResponse

router = APIRouter()


@router.post("", response_model=RoomResponse)
async def create_room(request_body: RoomCreateRequest, request: Request) -> RoomResponse:
    room_service = request.app.state.room_service
    room = room_service.create_room(
        display_name=request_body.display_name,
        participant_id=request_body.participant_id,
        room_name=request_body.room_name,
        accessibility_mode=request_body.accessibility_mode,
        max_participants=request_body.max_participants,
    )
    return RoomResponse(
        message="Room created.",
        data=room_service.snapshot(room.room_id),
    )


@router.post("/{room_id}/join", response_model=RoomResponse)
async def join_room(room_id: str, request_body: RoomJoinRequest, request: Request) -> RoomResponse:
    room_service = request.app.state.room_service
    room = room_service.join_room(
        room_id=room_id,
        display_name=request_body.display_name,
        participant_id=request_body.participant_id,
    )
    return RoomResponse(
        message="Room joined.",
        data=room_service.snapshot(room.room_id),
    )


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(room_id: str, request: Request) -> RoomResponse:
    room_service = request.app.state.room_service
    snapshot = room_service.snapshot(room_id)
    return RoomResponse(message="Room loaded.", data=snapshot)

