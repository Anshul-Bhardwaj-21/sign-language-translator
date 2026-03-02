"""
Unit tests for Meeting Service REST API

Tests all endpoints with valid and invalid data to ensure proper
request validation, error handling, and HTTP status codes.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import psycopg2

from meeting_service import app, get_db_connection


# Test client
client = TestClient(app)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_db_connection():
    """Mock database connection."""
    with patch('meeting_service.get_db_connection') as mock_conn:
        # Create mock connection and cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        
        mock_connection.cursor.return_value = mock_cursor
        mock_conn.return_value = mock_connection
        
        yield mock_connection, mock_cursor


@pytest.fixture
def sample_meeting_data():
    """Sample meeting data for tests."""
    return {
        'id': '123e4567-e89b-12d3-a456-426614174000',
        'title': 'Test Meeting',
        'host_id': '123e4567-e89b-12d3-a456-426614174001',
        'created_at': datetime(2024, 1, 1, 12, 0, 0),
        'started_at': None,
        'ended_at': None,
        'is_locked': False,
        'waiting_room_enabled': False,
        'recording_enabled': False,
        'max_participants': 100,
        'settings': {
            'video_quality': '720p',
            'enable_chat': True,
            'enable_screen_sharing': True,
            'enable_captions': False,
            'enable_sign_language': False,
            'sign_language': 'ASL'
        }
    }


# ============================================================================
# Test Root and Health Endpoints
# ============================================================================

def test_root_endpoint():
    """Test root endpoint returns service info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data['service'] == "Meeting Service API"
    assert data['version'] == "1.0.0"
    assert data['status'] == "running"


def test_health_check_healthy(mock_db_connection):
    """Test health check when database is connected."""
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = (1,)
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == "healthy"
    assert data['database'] == "connected"


def test_health_check_unhealthy():
    """Test health check when database is disconnected."""
    with patch('meeting_service.get_db_connection', side_effect=Exception("Connection failed")):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == "unhealthy"
        assert data['database'] == "disconnected"


# ============================================================================
# Test Create Meeting Endpoint
# ============================================================================

def test_create_meeting_success(mock_db_connection, sample_meeting_data):
    """Test successful meeting creation."""
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = sample_meeting_data
    
    request_data = {
        "title": "Test Meeting",
        "host_id": "123e4567-e89b-12d3-a456-426614174001",
        "waiting_room_enabled": False,
        "recording_enabled": False,
        "max_participants": 100
    }
    
    response = client.post("/api/meetings", json=request_data)
    assert response.status_code == 201
    data = response.json()
    assert data['title'] == "Test Meeting"
    assert data['host_id'] == request_data['host_id']
    assert data['is_locked'] is False


def test_create_meeting_with_settings(mock_db_connection, sample_meeting_data):
    """Test meeting creation with custom settings."""
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = sample_meeting_data
    
    request_data = {
        "title": "Test Meeting",
        "host_id": "123e4567-e89b-12d3-a456-426614174001",
        "settings": {
            "video_quality": "1080p",
            "enable_chat": True,
            "enable_sign_language": True,
            "sign_language": "BSL"
        }
    }
    
    response = client.post("/api/meetings", json=request_data)
    assert response.status_code == 201


def test_create_meeting_invalid_title():
    """Test meeting creation with empty title."""
    request_data = {
        "title": "",
        "host_id": "123e4567-e89b-12d3-a456-426614174001"
    }
    
    response = client.post("/api/meetings", json=request_data)
    assert response.status_code == 422  # Validation error


def test_create_meeting_invalid_max_participants():
    """Test meeting creation with invalid max_participants."""
    request_data = {
        "title": "Test Meeting",
        "host_id": "123e4567-e89b-12d3-a456-426614174001",
        "max_participants": 1  # Less than minimum of 2
    }
    
    response = client.post("/api/meetings", json=request_data)
    assert response.status_code == 422


def test_create_meeting_database_error(mock_db_connection):
    """Test meeting creation with database error."""
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = psycopg2.Error("Database error")
    
    request_data = {
        "title": "Test Meeting",
        "host_id": "123e4567-e89b-12d3-a456-426614174001"
    }
    
    response = client.post("/api/meetings", json=request_data)
    assert response.status_code == 500


# ============================================================================
# Test Get Meeting Endpoint
# ============================================================================

def test_get_meeting_success(mock_db_connection, sample_meeting_data):
    """Test successful meeting retrieval."""
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = sample_meeting_data
    
    meeting_id = "123e4567-e89b-12d3-a456-426614174000"
    response = client.get(f"/api/meetings/{meeting_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == meeting_id
    assert data['title'] == "Test Meeting"


def test_get_meeting_not_found(mock_db_connection):
    """Test getting non-existent meeting."""
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = None
    
    meeting_id = "123e4567-e89b-12d3-a456-426614174000"
    response = client.get(f"/api/meetings/{meeting_id}")
    
    assert response.status_code == 404
    assert "not found" in response.json()['detail'].lower()


def test_get_meeting_invalid_id():
    """Test getting meeting with invalid UUID."""
    response = client.get("/api/meetings/invalid-uuid")
    assert response.status_code == 400
    assert "invalid" in response.json()['detail'].lower()


# ============================================================================
# Test Delete Meeting Endpoint
# ============================================================================

def test_end_meeting_success(mock_db_connection):
    """Test successful meeting end."""
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = {
        'id': '123e4567-e89b-12d3-a456-426614174000',
        'ended_at': None
    }
    
    meeting_id = "123e4567-e89b-12d3-a456-426614174000"
    response = client.delete(f"/api/meetings/{meeting_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert data['meeting_id'] == meeting_id


def test_end_meeting_not_found(mock_db_connection):
    """Test ending non-existent meeting."""
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = None
    
    meeting_id = "123e4567-e89b-12d3-a456-426614174000"
    response = client.delete(f"/api/meetings/{meeting_id}")
    
    assert response.status_code == 404


def test_end_meeting_already_ended(mock_db_connection):
    """Test ending already ended meeting."""
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = {
        'id': '123e4567-e89b-12d3-a456-426614174000',
        'ended_at': datetime(2024, 1, 1, 13, 0, 0)
    }
    
    meeting_id = "123e4567-e89b-12d3-a456-426614174000"
    response = client.delete(f"/api/meetings/{meeting_id}")
    
    assert response.status_code == 400
    assert "already ended" in response.json()['detail'].lower()


# ============================================================================
# Test Join Meeting Endpoint
# ============================================================================

def test_join_meeting_success(mock_db_connection):
    """Test successful meeting join."""
    mock_connection, mock_cursor = mock_db_connection
    
    # Mock meeting exists and is not locked
    mock_cursor.fetchone.side_effect = [
        {
            'id': '123e4567-e89b-12d3-a456-426614174000',
            'host_id': '123e4567-e89b-12d3-a456-426614174001',
            'is_locked': False,
            'ended_at': None,
            'max_participants': 100
        },
        {'count': 5},  # Current participant count
        None,  # User not already in meeting
        {'id': '123e4567-e89b-12d3-a456-426614174002'}  # Inserted participant
    ]
    
    meeting_id = "123e4567-e89b-12d3-a456-426614174000"
    request_data = {
        "user_id": "123e4567-e89b-12d3-a456-426614174003",
        "user_name": "Test User"
    }
    
    response = client.post(f"/api/meetings/{meeting_id}/join", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert data['meeting_id'] == meeting_id


def test_join_meeting_not_found(mock_db_connection):
    """Test joining non-existent meeting."""
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = None
    
    meeting_id = "123e4567-e89b-12d3-a456-426614174000"
    request_data = {
        "user_id": "123e4567-e89b-12d3-a456-426614174003",
        "user_name": "Test User"
    }
    
    response = client.post(f"/api/meetings/{meeting_id}/join", json=request_data)
    assert response.status_code == 404


def test_join_meeting_locked(mock_db_connection):
    """Test joining locked meeting."""
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = {
        'id': '123e4567-e89b-12d3-a456-426614174000',
        'host_id': '123e4567-e89b-12d3-a456-426614174001',
        'is_locked': True,
        'ended_at': None,
        'max_participants': 100
    }
    
    meeting_id = "123e4567-e89b-12d3-a456-426614174000"
    request_data = {
        "user_id": "123e4567-e89b-12d3-a456-426614174003",
        "user_name": "Test User"
    }
    
    response = client.post(f"/api/meetings/{meeting_id}/join", json=request_data)
    assert response.status_code == 403
    assert "locked" in response.json()['detail'].lower()


def test_join_meeting_ended(mock_db_connection):
    """Test joining ended meeting."""
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = {
        'id': '123e4567-e89b-12d3-a456-426614174000',
        'host_id': '123e4567-e89b-12d3-a456-426614174001',
        'is_locked': False,
        'ended_at': datetime(2024, 1, 1, 13, 0, 0),
        'max_participants': 100
    }
    
    meeting_id = "123e4567-e89b-12d3-a456-426614174000"
    request_data = {
        "user_id": "123e4567-e89b-12d3-a456-426614174003",
        "user_name": "Test User"
    }
    
    response = client.post(f"/api/meetings/{meeting_id}/join", json=request_data)
    assert response.status_code == 400
    assert "ended" in response.json()['detail'].lower()


def test_join_meeting_full(mock_db_connection):
    """Test joining full meeting."""
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.side_effect = [
        {
            'id': '123e4567-e89b-12d3-a456-426614174000',
            'host_id': '123e4567-e89b-12d3-a456-426614174001',
            'is_locked': False,
            'ended_at': None,
            'max_participants': 10
        },
        {'count': 10}  # Meeting is full
    ]
    
    meeting_id = "123e4567-e89b-12d3-a456-426614174000"
    request_data = {
        "user_id": "123e4567-e89b-12d3-a456-426614174003",
        "user_name": "Test User"
    }
    
    response = client.post(f"/api/meetings/{meeting_id}/join", json=request_data)
    assert response.status_code == 400
    assert "full" in response.json()['detail'].lower()


# ============================================================================
# Test Leave Meeting Endpoint
# ============================================================================

def test_leave_meeting_success(mock_db_connection):
    """Test successful meeting leave."""
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = {
        'id': '123e4567-e89b-12d3-a456-426614174002'
    }
    
    meeting_id = "123e4567-e89b-12d3-a456-426614174000"
    request_data = {
        "user_id": "123e4567-e89b-12d3-a456-426614174003"
    }
    
    response = client.post(f"/api/meetings/{meeting_id}/leave", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True


def test_leave_meeting_not_participant(mock_db_connection):
    """Test leaving meeting when not a participant."""
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = None
    
    meeting_id = "123e4567-e89b-12d3-a456-426614174000"
    request_data = {
        "user_id": "123e4567-e89b-12d3-a456-426614174003"
    }
    
    response = client.post(f"/api/meetings/{meeting_id}/leave", json=request_data)
    assert response.status_code == 404


# ============================================================================
# Test Lock Meeting Endpoint
# ============================================================================

def test_lock_meeting_success(mock_db_connection):
    """Test successful meeting lock."""
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = {
        'id': '123e4567-e89b-12d3-a456-426614174000',
        'host_id': '123e4567-e89b-12d3-a456-426614174001',
        'ended_at': None
    }
    
    meeting_id = "123e4567-e89b-12d3-a456-426614174000"
    request_data = {
        "is_locked": True,
        "host_id": "123e4567-e89b-12d3-a456-426614174001"
    }
    
    response = client.put(f"/api/meetings/{meeting_id}/lock", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert data['is_locked'] is True


def test_unlock_meeting_success(mock_db_connection):
    """Test successful meeting unlock."""
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = {
        'id': '123e4567-e89b-12d3-a456-426614174000',
        'host_id': '123e4567-e89b-12d3-a456-426614174001',
        'ended_at': None
    }
    
    meeting_id = "123e4567-e89b-12d3-a456-426614174000"
    request_data = {
        "is_locked": False,
        "host_id": "123e4567-e89b-12d3-a456-426614174001"
    }
    
    response = client.put(f"/api/meetings/{meeting_id}/lock", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert data['is_locked'] is False


def test_lock_meeting_not_host(mock_db_connection):
    """Test locking meeting by non-host."""
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = {
        'id': '123e4567-e89b-12d3-a456-426614174000',
        'host_id': '123e4567-e89b-12d3-a456-426614174001',
        'ended_at': None
    }
    
    meeting_id = "123e4567-e89b-12d3-a456-426614174000"
    request_data = {
        "is_locked": True,
        "host_id": "123e4567-e89b-12d3-a456-426614174999"  # Different host
    }
    
    response = client.put(f"/api/meetings/{meeting_id}/lock", json=request_data)
    assert response.status_code == 403
    assert "host" in response.json()['detail'].lower()


def test_lock_meeting_ended(mock_db_connection):
    """Test locking ended meeting."""
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = {
        'id': '123e4567-e89b-12d3-a456-426614174000',
        'host_id': '123e4567-e89b-12d3-a456-426614174001',
        'ended_at': datetime(2024, 1, 1, 13, 0, 0)
    }
    
    meeting_id = "123e4567-e89b-12d3-a456-426614174000"
    request_data = {
        "is_locked": True,
        "host_id": "123e4567-e89b-12d3-a456-426614174001"
    }
    
    response = client.put(f"/api/meetings/{meeting_id}/lock", json=request_data)
    assert response.status_code == 400
    assert "ended" in response.json()['detail'].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
