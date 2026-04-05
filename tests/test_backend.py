"""Integration tests for backend server and WebSocket functionality."""

import pytest
import asyncio
from fastapi.testclient import TestClient
import json


# Import backend server
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.server import app, manager


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "service" in data
    assert "version" in data


def test_health_check(client):
    """Test detailed health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "active_sessions" in data
    assert "total_connections" in data
    assert "timestamp" in data


def test_create_session(client):
    """Test session creation."""
    session_data = {
        "session_id": "test_session_123",
        "participants": ["user1", "user2"],
        "created_at": 1708041600.0,
        "accessibility_mode": True
    }
    
    response = client.post("/sessions/create", json=session_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "created"
    assert data["session_id"] == "test_session_123"


def test_create_duplicate_session(client):
    """Test creating duplicate session fails."""
    session_data = {
        "session_id": "test_session_456",
        "participants": ["user1"],
        "created_at": 1708041600.0,
        "accessibility_mode": False
    }
    
    # First creation should succeed
    response1 = client.post("/sessions/create", json=session_data)
    assert response1.status_code == 200
    
    # Second creation should fail
    response2 = client.post("/sessions/create", json=session_data)
    assert response2.status_code == 400


def test_get_session(client):
    """Test retrieving session information."""
    # Create session first
    session_data = {
        "session_id": "test_session_789",
        "participants": ["user1"],
        "created_at": 1708041600.0,
        "accessibility_mode": True
    }
    client.post("/sessions/create", json=session_data)
    
    # Get session
    response = client.get("/sessions/test_session_789")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test_session_789"
    assert data["accessibility_mode"] is True


def test_get_nonexistent_session(client):
    """Test getting non-existent session returns 404."""
    response = client.get("/sessions/nonexistent_session")
    assert response.status_code == 404


def test_get_captions_empty(client):
    """Test getting captions for session with no captions."""
    response = client.get("/sessions/empty_session/captions")
    assert response.status_code == 200
    data = response.json()
    assert data["captions"] == []


def test_store_caption(client):
    """Test storing a caption."""
    caption_data = {
        "session_id": "test_session_caption",
        "user_id": "user1",
        "text": "Hello world",
        "timestamp": 1708041600.0,
        "is_confirmed": False
    }
    
    response = client.post("/captions/store", json=caption_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "stored"


def test_get_captions_with_data(client):
    """Test retrieving stored captions."""
    session_id = "test_session_with_captions"
    
    # Store multiple captions
    for i in range(5):
        caption_data = {
            "session_id": session_id,
            "user_id": "user1",
            "text": f"Caption {i}",
            "timestamp": 1708041600.0 + i,
            "is_confirmed": False
        }
        client.post("/captions/store", json=caption_data)
    
    # Retrieve captions
    response = client.get(f"/sessions/{session_id}/captions")
    assert response.status_code == 200
    data = response.json()
    assert len(data["captions"]) == 5


def test_get_captions_with_limit(client):
    """Test caption retrieval with limit."""
    session_id = "test_session_limit"
    
    # Store 10 captions
    for i in range(10):
        caption_data = {
            "session_id": session_id,
            "user_id": "user1",
            "text": f"Caption {i}",
            "timestamp": 1708041600.0 + i,
            "is_confirmed": False
        }
        client.post("/captions/store", json=caption_data)
    
    # Retrieve with limit
    response = client.get(f"/sessions/{session_id}/captions?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["captions"]) == 5


def test_websocket_connection():
    """Test WebSocket connection establishment."""
    # WebSocket testing requires pytest-asyncio which is not installed
    # This is a placeholder for full WebSocket integration tests
    # In production, install pytest-asyncio and use websockets library
    pytest.skip("WebSocket testing requires pytest-asyncio")


def test_connection_manager():
    """Test ConnectionManager functionality."""
    from backend.server import ConnectionManager
    
    mgr = ConnectionManager()
    
    # Test initial state
    assert len(mgr.active_connections) == 0
    assert len(mgr.user_mapping) == 0
    
    # Test get_session_participants
    participants = mgr.get_session_participants("nonexistent")
    assert participants == []


def test_caption_message_validation():
    """Test CaptionMessage model validation."""
    from backend.server import CaptionMessage
    
    # Valid caption
    caption = CaptionMessage(
        session_id="test",
        user_id="user1",
        text="Hello",
        timestamp=1708041600.0
    )
    assert caption.session_id == "test"
    assert caption.is_confirmed is False
    
    # Test with confirmed flag
    caption2 = CaptionMessage(
        session_id="test",
        user_id="user1",
        text="Hello",
        timestamp=1708041600.0,
        is_confirmed=True
    )
    assert caption2.is_confirmed is True


def test_correction_message_validation():
    """Test CorrectionMessage model validation."""
    from backend.server import CorrectionMessage
    
    correction = CorrectionMessage(
        user_id="user1",
        original_text="HELO",
        corrected_text="HELLO",
        timestamp=1708041600.0
    )
    assert correction.original_text == "HELO"
    assert correction.corrected_text == "HELLO"


def test_session_info_validation():
    """Test SessionInfo model validation."""
    from backend.server import SessionInfo
    
    session = SessionInfo(
        session_id="test",
        participants=["user1", "user2"],
        created_at=1708041600.0
    )
    assert len(session.participants) == 2
    assert session.accessibility_mode is False
    
    # Test with accessibility mode
    session2 = SessionInfo(
        session_id="test2",
        participants=["user1"],
        created_at=1708041600.0,
        accessibility_mode=True
    )
    assert session2.accessibility_mode is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
