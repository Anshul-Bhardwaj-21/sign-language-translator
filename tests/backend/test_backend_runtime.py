from __future__ import annotations

import base64

import cv2
import numpy as np
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def _encode_frame() -> str:
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    ok, buffer = cv2.imencode(".jpg", frame)
    assert ok
    return base64.b64encode(buffer.tobytes()).decode("utf-8")


def test_health_endpoint_returns_runtime_snapshot() -> None:
    response = client.get("/health")
    payload = response.json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["data"]["service"] == "SignBridge Backend"
    assert payload["data"]["engine"] == "heuristic"


def test_room_create_and_join_flow() -> None:
    create_response = client.post(
        "/rooms",
        json={
            "display_name": "Host User",
            "participant_id": "host-1",
            "room_name": "Accessibility Design Review",
            "max_participants": 2,
        },
    )
    create_payload = create_response.json()
    room_id = create_payload["data"]["room_id"]

    join_response = client.post(
        f"/rooms/{room_id}/join",
        json={"display_name": "Guest User", "participant_id": "guest-1"},
    )
    join_payload = join_response.json()

    assert create_response.status_code == 200
    assert join_response.status_code == 200
    assert join_payload["data"]["room_id"] == room_id
    assert len(join_payload["data"]["participants"]) == 2


def test_predict_endpoint_returns_structured_response() -> None:
    response = client.post(
        "/predict",
        json={
            "image_base64": _encode_frame(),
            "room_id": "ROOM42",
            "participant_id": "user-42",
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert "label" in payload["data"]
    assert "quality" in payload["data"]
    assert "overlay" in payload["data"]
    assert payload["data"]["engine"] == "heuristic"
