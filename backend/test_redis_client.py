"""
Unit Tests for Redis Client

Tests session state, frame buffers, participant tracking, and caching.
"""

import json
import time
from datetime import datetime

import pytest

from redis_client import RedisClient


@pytest.fixture
def redis_client():
    """Create Redis client for testing."""
    client = RedisClient(host="localhost", port=6379, db=1)  # Use db=1 for testing
    yield client
    # Cleanup: flush test database
    client.client.flushdb()
    client.close()


class TestHealthCheck:
    """Test Redis health check functionality."""
    
    def test_health_check_success(self, redis_client):
        """Test successful health check."""
        health = redis_client.health_check()
        
        assert health["status"] == "healthy"
        assert health["connected"] is True
        assert "latency_ms" in health
        assert health["latency_ms"] >= 0
        assert "redis_version" in health
        assert "connected_clients" in health
    
    def test_health_check_with_invalid_connection(self):
        """Test health check with invalid connection."""
        client = RedisClient(host="invalid-host", port=9999, db=0)
        health = client.health_check()
        
        assert health["status"] == "unhealthy"
        assert "error" in health


class TestSessionState:
    """Test session state management."""
    
    def test_set_and_get_session(self, redis_client):
        """Test setting and getting session data."""
        user_id = "user123"
        session_data = {
            "meeting_id": "meeting456",
            "socket_id": "socket789",
            "joined_at": datetime.now().timestamp(),
            "audio_enabled": True,
            "video_enabled": True,
        }
        
        # Set session
        result = redis_client.set_session(user_id, session_data, ttl_seconds=60)
        assert result is True
        
        # Get session
        retrieved = redis_client.get_session(user_id)
        assert retrieved is not None
        assert retrieved["meeting_id"] == session_data["meeting_id"]
        assert retrieved["socket_id"] == session_data["socket_id"]
        assert retrieved["audio_enabled"] == session_data["audio_enabled"]
    
    def test_get_nonexistent_session(self, redis_client):
        """Test getting non-existent session."""
        result = redis_client.get_session("nonexistent_user")
        assert result is None
    
    def test_delete_session(self, redis_client):
        """Test deleting session."""
        user_id = "user123"
        session_data = {"test": "data"}
        
        redis_client.set_session(user_id, session_data)
        assert redis_client.get_session(user_id) is not None
        
        # Delete session
        result = redis_client.delete_session(user_id)
        assert result is True
        
        # Verify deleted
        assert redis_client.get_session(user_id) is None
    
    def test_session_ttl_expiration(self, redis_client):
        """Test session TTL expiration."""
        user_id = "user123"
        session_data = {"test": "data"}
        
        # Set session with 1 second TTL
        redis_client.set_session(user_id, session_data, ttl_seconds=1)
        assert redis_client.get_session(user_id) is not None
        
        # Wait for expiration
        time.sleep(1.5)
        
        # Verify expired
        assert redis_client.get_session(user_id) is None
    
    def test_extend_session_ttl(self, redis_client):
        """Test extending session TTL."""
        user_id = "user123"
        session_data = {"test": "data"}
        
        # Set session with short TTL
        redis_client.set_session(user_id, session_data, ttl_seconds=2)
        
        # Extend TTL
        time.sleep(1)
        result = redis_client.extend_session_ttl(user_id, ttl_seconds=10)
        assert result is True
        
        # Wait past original TTL
        time.sleep(2)
        
        # Should still exist
        assert redis_client.get_session(user_id) is not None


class TestFrameBuffer:
    """Test frame buffer FIFO queue."""
    
    def test_push_and_get_frames(self, redis_client):
        """Test pushing and getting frames."""
        user_id = "user123"
        frames = [b"frame1", b"frame2", b"frame3"]
        
        # Push frames
        for frame in frames:
            result = redis_client.push_frame(user_id, frame)
            assert result is True
        
        # Get all frames
        retrieved = redis_client.get_frame_buffer(user_id)
        assert len(retrieved) == 3
        assert retrieved == frames
    
    def test_frame_buffer_max_size(self, redis_client):
        """Test frame buffer respects max size."""
        user_id = "user123"
        max_frames = 5
        
        # Push more frames than max
        for i in range(10):
            redis_client.push_frame(user_id, f"frame{i}".encode(), max_frames=max_frames)
        
        # Should only keep last 5
        retrieved = redis_client.get_frame_buffer(user_id)
        assert len(retrieved) == max_frames
        assert retrieved[0] == b"frame5"  # Oldest kept
        assert retrieved[-1] == b"frame9"  # Newest
    
    def test_get_frame_buffer_with_count(self, redis_client):
        """Test getting specific number of frames."""
        user_id = "user123"
        
        # Push 10 frames
        for i in range(10):
            redis_client.push_frame(user_id, f"frame{i}".encode())
        
        # Get last 3 frames
        retrieved = redis_client.get_frame_buffer(user_id, count=3)
        assert len(retrieved) == 3
        assert retrieved[0] == b"frame7"
        assert retrieved[-1] == b"frame9"
    
    def test_clear_frame_buffer(self, redis_client):
        """Test clearing frame buffer."""
        user_id = "user123"
        
        # Push frames
        redis_client.push_frame(user_id, b"frame1")
        redis_client.push_frame(user_id, b"frame2")
        
        assert redis_client.get_frame_buffer_size(user_id) == 2
        
        # Clear buffer
        result = redis_client.clear_frame_buffer(user_id)
        assert result is True
        
        # Verify cleared
        assert redis_client.get_frame_buffer_size(user_id) == 0
    
    def test_get_frame_buffer_size(self, redis_client):
        """Test getting frame buffer size."""
        user_id = "user123"
        
        assert redis_client.get_frame_buffer_size(user_id) == 0
        
        redis_client.push_frame(user_id, b"frame1")
        assert redis_client.get_frame_buffer_size(user_id) == 1
        
        redis_client.push_frame(user_id, b"frame2")
        assert redis_client.get_frame_buffer_size(user_id) == 2


class TestMeetingParticipants:
    """Test meeting participants sorted set."""
    
    def test_add_and_get_participants(self, redis_client):
        """Test adding and getting participants."""
        meeting_id = "meeting123"
        user1 = "user1"
        user2 = "user2"
        user3 = "user3"
        
        # Add participants with timestamps
        redis_client.add_participant(meeting_id, user1, 1000.0)
        redis_client.add_participant(meeting_id, user2, 2000.0)
        redis_client.add_participant(meeting_id, user3, 3000.0)
        
        # Get participants (should be ordered by join time)
        participants = redis_client.get_participants(meeting_id)
        assert len(participants) == 3
        assert participants[0] == user1.encode()  # First to join
        assert participants[1] == user2.encode()
        assert participants[2] == user3.encode()  # Last to join
    
    def test_get_participants_with_scores(self, redis_client):
        """Test getting participants with join timestamps."""
        meeting_id = "meeting123"
        user1 = "user1"
        timestamp1 = 1000.0
        
        redis_client.add_participant(meeting_id, user1, timestamp1)
        
        # Get with scores
        participants = redis_client.get_participants(meeting_id, with_scores=True)
        assert len(participants) == 1
        assert participants[0][0] == user1.encode()
        assert participants[0][1] == timestamp1
    
    def test_remove_participant(self, redis_client):
        """Test removing participant."""
        meeting_id = "meeting123"
        user1 = "user1"
        user2 = "user2"
        
        redis_client.add_participant(meeting_id, user1)
        redis_client.add_participant(meeting_id, user2)
        
        assert redis_client.get_participant_count(meeting_id) == 2
        
        # Remove participant
        result = redis_client.remove_participant(meeting_id, user1)
        assert result is True
        
        # Verify removed
        assert redis_client.get_participant_count(meeting_id) == 1
        participants = redis_client.get_participants(meeting_id)
        assert user1.encode() not in participants
    
    def test_get_participant_count(self, redis_client):
        """Test getting participant count."""
        meeting_id = "meeting123"
        
        assert redis_client.get_participant_count(meeting_id) == 0
        
        redis_client.add_participant(meeting_id, "user1")
        assert redis_client.get_participant_count(meeting_id) == 1
        
        redis_client.add_participant(meeting_id, "user2")
        assert redis_client.get_participant_count(meeting_id) == 2
    
    def test_get_participant_join_time(self, redis_client):
        """Test getting participant join time."""
        meeting_id = "meeting123"
        user_id = "user1"
        join_time = 1234567890.0
        
        redis_client.add_participant(meeting_id, user_id, join_time)
        
        retrieved_time = redis_client.get_participant_join_time(meeting_id, user_id)
        assert retrieved_time == join_time
    
    def test_get_nonexistent_participant_join_time(self, redis_client):
        """Test getting join time for non-existent participant."""
        result = redis_client.get_participant_join_time("meeting123", "nonexistent")
        assert result is None


class TestDistributedCaching:
    """Test distributed caching functionality."""
    
    def test_cache_set_and_get(self, redis_client):
        """Test setting and getting cache values."""
        key = "test_key"
        value = {"data": "test", "number": 42, "list": [1, 2, 3]}
        
        # Set cache
        result = redis_client.cache_set(key, value)
        assert result is True
        
        # Get cache
        retrieved = redis_client.cache_get(key)
        assert retrieved == value
    
    def test_cache_with_ttl(self, redis_client):
        """Test cache with TTL expiration."""
        key = "test_key"
        value = {"data": "test"}
        
        # Set cache with 1 second TTL
        redis_client.cache_set(key, value, ttl_seconds=1)
        assert redis_client.cache_get(key) is not None
        
        # Wait for expiration
        time.sleep(1.5)
        
        # Verify expired
        assert redis_client.cache_get(key) is None
    
    def test_cache_delete(self, redis_client):
        """Test deleting cache."""
        key = "test_key"
        value = {"data": "test"}
        
        redis_client.cache_set(key, value)
        assert redis_client.cache_get(key) is not None
        
        # Delete cache
        result = redis_client.cache_delete(key)
        assert result is True
        
        # Verify deleted
        assert redis_client.cache_get(key) is None
    
    def test_cache_exists(self, redis_client):
        """Test checking cache existence."""
        key = "test_key"
        
        assert redis_client.cache_exists(key) is False
        
        redis_client.cache_set(key, {"data": "test"})
        assert redis_client.cache_exists(key) is True
        
        redis_client.cache_delete(key)
        assert redis_client.cache_exists(key) is False
    
    def test_cache_get_nonexistent(self, redis_client):
        """Test getting non-existent cache."""
        result = redis_client.cache_get("nonexistent_key")
        assert result is None


class TestErrorHandling:
    """Test error handling in Redis operations."""
    
    def test_invalid_json_in_session(self, redis_client):
        """Test handling of invalid JSON in session data."""
        user_id = "user123"
        
        # Manually set invalid JSON
        redis_client.client.set(f"session:{user_id}", "invalid json")
        
        # Should return None instead of raising exception
        result = redis_client.get_session(user_id)
        assert result is None
    
    def test_invalid_json_in_cache(self, redis_client):
        """Test handling of invalid JSON in cache."""
        key = "test_key"
        
        # Manually set invalid JSON
        redis_client.client.set(f"cache:{key}", "invalid json")
        
        # Should return None instead of raising exception
        result = redis_client.cache_get(key)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
