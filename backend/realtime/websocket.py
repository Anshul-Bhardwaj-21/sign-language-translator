from __future__ import annotations

import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from backend.schemas.events import RealtimeEnvelope

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/rooms/{room_id}")
async def room_socket(
    websocket: WebSocket,
    room_id: str,
    participant_id: str = Query(...),
    display_name: str = Query(...),
):
    room_service = websocket.app.state.room_service
    realtime_manager = websocket.app.state.realtime_manager

    room_service.connect_participant(room_id, participant_id, display_name)
    await realtime_manager.connect(websocket, room_id, participant_id, display_name)

    await websocket.send_json(
        {
            "type": "room.snapshot",
            "payload": room_service.snapshot(room_id).model_dump(mode="json"),
        }
    )
    await realtime_manager.broadcast(
        room_id,
        {
            "type": "room.participant-joined",
            "payload": {
                "participant_id": participant_id,
                "display_name": display_name,
            },
        },
        exclude=participant_id,
    )

    try:
        while True:
            envelope = RealtimeEnvelope.model_validate(await websocket.receive_json())
            await _handle_event(
                websocket=websocket,
                envelope=envelope,
                room_id=room_id,
                participant_id=participant_id,
            )
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for room=%s participant=%s", room_id, participant_id)
    finally:
        room_service.disconnect_participant(room_id, participant_id)
        await realtime_manager.disconnect(room_id, participant_id)
        await realtime_manager.broadcast(
            room_id,
            {
                "type": "room.participant-left",
                "payload": {"participant_id": participant_id},
            },
        )


async def _handle_event(
    websocket: WebSocket,
    envelope: RealtimeEnvelope,
    room_id: str,
    participant_id: str,
) -> None:
    room_service = websocket.app.state.room_service
    realtime_manager = websocket.app.state.realtime_manager
    payload = envelope.payload

    if envelope.type in {"signal.offer", "signal.answer", "signal.ice-candidate"}:
        target_id = str(payload.get("to_participant_id", ""))
        if target_id:
            await realtime_manager.send_to(
                room_id,
                target_id,
                {
                    "type": envelope.type,
                    "payload": {
                        **payload,
                        "from_participant_id": participant_id,
                    },
                },
            )
        return

    if envelope.type == "chat.message":
        message = str(payload.get("message", "")).strip()
        if not message:
            return
        event_payload = room_service.add_chat_message(room_id, participant_id, message)
        await realtime_manager.broadcast(
            room_id,
            {"type": "chat.message", "payload": event_payload},
        )
        return

    if envelope.type == "caption.publish":
        caption = str(payload.get("caption", "")).strip()
        confidence = float(payload.get("confidence", 0.0))
        if not caption:
            return
        event_payload = room_service.add_caption(room_id, participant_id, caption, confidence)
        await realtime_manager.broadcast(
            room_id,
            {"type": "caption.publish", "payload": event_payload},
        )
        return

    if envelope.type == "caption.clear":
        event_payload = room_service.clear_captions(room_id, participant_id)
        await realtime_manager.broadcast(
            room_id,
            {"type": "caption.clear", "payload": event_payload},
        )
        return

    if envelope.type == "status.update":
        room_service.update_media_state(
            room_id=room_id,
            participant_id=participant_id,
            mic_enabled=payload.get("mic_enabled"),
            camera_enabled=payload.get("camera_enabled"),
        )
        await realtime_manager.broadcast(
            room_id,
            {
                "type": "status.update",
                "payload": {
                    "participant_id": participant_id,
                    "mic_enabled": payload.get("mic_enabled"),
                    "camera_enabled": payload.get("camera_enabled"),
                },
            },
            exclude=participant_id,
        )
        return

    if envelope.type == "ping":
        await websocket.send_json({"type": "pong", "payload": {"room_id": room_id}})
        return

    await websocket.send_json(
        {
            "type": "system.error",
            "payload": {"message": f"Unsupported event type: {envelope.type}"},
        }
    )
