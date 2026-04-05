#!/usr/bin/env python3
"""
Redis Setup Verification Script

This script verifies that Redis is properly configured and all functionality works.
Run this after starting Redis to ensure everything is set up correctly.

Usage:
    python verify_redis_setup.py
"""

import sys
import time
from datetime import datetime

from redis_client import create_redis_client_from_env


def print_section(title: str):
    """Print section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def verify_connection():
    """Verify Redis connection."""
    print_section("1. Connection Test")
    
    try:
        redis_client = create_redis_client_from_env()
        print(f"✓ Redis client created")
        print(f"  Host: {redis_client.host}")
        print(f"  Port: {redis_client.port}")
        print(f"  DB: {redis_client.db}")
        return redis_client
    except Exception as e:
        print(f"✗ Failed to create Redis client: {e}")
        return None


def verify_health_check(redis_client):
    """Verify health check."""
    print_section("2. Health Check")
    
    try:
        health = redis_client.health_check()
        
        if health["status"] == "healthy":
            print(f"✓ Redis is healthy")
            print(f"  Latency: {health['latency_ms']} ms")
            print(f"  Version: {health['redis_version']}")
            print(f"  Memory: {health['used_memory_human']}")
            print(f"  Clients: {health['connected_clients']}")
            print(f"  Uptime: {health['uptime_seconds']} seconds")
            return True
        else:
            print(f"✗ Redis is unhealthy: {health.get('error', 'unknown')}")
            return False
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False


def verify_session_state(redis_client):
    """Verify session state operations."""
    print_section("3. Session State Test")
    
    try:
        user_id = "test_user_123"
        session_data = {
            "meeting_id": "test_meeting",
            "socket_id": "test_socket",
            "joined_at": datetime.now().timestamp(),
            "audio_enabled": True,
            "video_enabled": True,
        }
        
        # Set session
        result = redis_client.set_session(user_id, session_data, ttl_seconds=60)
        if not result:
            print(f"✗ Failed to set session")
            return False
        print(f"✓ Session set for user {user_id}")
        
        # Get session
        retrieved = redis_client.get_session(user_id)
        if retrieved is None:
            print(f"✗ Failed to get session")
            return False
        print(f"✓ Session retrieved")
        
        # Verify data
        if retrieved["meeting_id"] != session_data["meeting_id"]:
            print(f"✗ Session data mismatch")
            return False
        print(f"✓ Session data verified")
        
        # Extend TTL
        result = redis_client.extend_session_ttl(user_id, ttl_seconds=120)
        if not result:
            print(f"✗ Failed to extend TTL")
            return False
        print(f"✓ Session TTL extended")
        
        # Delete session
        result = redis_client.delete_session(user_id)
        if not result:
            print(f"✗ Failed to delete session")
            return False
        print(f"✓ Session deleted")
        
        return True
    except Exception as e:
        print(f"✗ Session state test failed: {e}")
        return False


def verify_frame_buffer(redis_client):
    """Verify frame buffer operations."""
    print_section("4. Frame Buffer Test")
    
    try:
        user_id = "test_user_456"
        
        # Push frames
        for i in range(10):
            frame_data = f"frame_{i}".encode()
            result = redis_client.push_frame(user_id, frame_data, max_frames=60)
            if not result:
                print(f"✗ Failed to push frame {i}")
                return False
        print(f"✓ Pushed 10 frames")
        
        # Get buffer size
        size = redis_client.get_frame_buffer_size(user_id)
        if size != 10:
            print(f"✗ Buffer size mismatch: expected 10, got {size}")
            return False
        print(f"✓ Buffer size verified: {size} frames")
        
        # Get frames
        frames = redis_client.get_frame_buffer(user_id)
        if len(frames) != 10:
            print(f"✗ Frame count mismatch: expected 10, got {len(frames)}")
            return False
        print(f"✓ Retrieved {len(frames)} frames")
        
        # Get last 5 frames
        frames = redis_client.get_frame_buffer(user_id, count=5)
        if len(frames) != 5:
            print(f"✗ Frame count mismatch: expected 5, got {len(frames)}")
            return False
        print(f"✓ Retrieved last 5 frames")
        
        # Clear buffer
        result = redis_client.clear_frame_buffer(user_id)
        if not result:
            print(f"✗ Failed to clear buffer")
            return False
        print(f"✓ Buffer cleared")
        
        # Verify cleared
        size = redis_client.get_frame_buffer_size(user_id)
        if size != 0:
            print(f"✗ Buffer not empty after clear: {size} frames")
            return False
        print(f"✓ Buffer empty verified")
        
        return True
    except Exception as e:
        print(f"✗ Frame buffer test failed: {e}")
        return False


def verify_participants(redis_client):
    """Verify meeting participants operations."""
    print_section("5. Meeting Participants Test")
    
    try:
        meeting_id = "test_meeting_789"
        
        # Add participants
        users = [
            ("user1", 1000.0),
            ("user2", 2000.0),
            ("user3", 3000.0),
        ]
        
        for user_id, timestamp in users:
            result = redis_client.add_participant(meeting_id, user_id, timestamp)
            if not result:
                print(f"✗ Failed to add participant {user_id}")
                return False
        print(f"✓ Added {len(users)} participants")
        
        # Get count
        count = redis_client.get_participant_count(meeting_id)
        if count != len(users):
            print(f"✗ Participant count mismatch: expected {len(users)}, got {count}")
            return False
        print(f"✓ Participant count verified: {count}")
        
        # Get participants
        participants = redis_client.get_participants(meeting_id)
        if len(participants) != len(users):
            print(f"✗ Participant list mismatch")
            return False
        print(f"✓ Retrieved {len(participants)} participants")
        
        # Get participants with scores
        participants_with_scores = redis_client.get_participants(
            meeting_id, with_scores=True
        )
        if len(participants_with_scores) != len(users):
            print(f"✗ Participant list with scores mismatch")
            return False
        print(f"✓ Retrieved participants with join times")
        
        # Get specific participant join time
        join_time = redis_client.get_participant_join_time(meeting_id, "user2")
        if join_time != 2000.0:
            print(f"✗ Join time mismatch: expected 2000.0, got {join_time}")
            return False
        print(f"✓ Participant join time verified")
        
        # Remove participant
        result = redis_client.remove_participant(meeting_id, "user2")
        if not result:
            print(f"✗ Failed to remove participant")
            return False
        print(f"✓ Participant removed")
        
        # Verify count after removal
        count = redis_client.get_participant_count(meeting_id)
        if count != 2:
            print(f"✗ Count after removal mismatch: expected 2, got {count}")
            return False
        print(f"✓ Count after removal verified: {count}")
        
        return True
    except Exception as e:
        print(f"✗ Participants test failed: {e}")
        return False


def verify_caching(redis_client):
    """Verify distributed caching operations."""
    print_section("6. Distributed Caching Test")
    
    try:
        key = "test_cache_key"
        value = {
            "data": "test_value",
            "number": 42,
            "list": [1, 2, 3],
            "nested": {"key": "value"},
        }
        
        # Set cache
        result = redis_client.cache_set(key, value, ttl_seconds=60)
        if not result:
            print(f"✗ Failed to set cache")
            return False
        print(f"✓ Cache set")
        
        # Check exists
        exists = redis_client.cache_exists(key)
        if not exists:
            print(f"✗ Cache key doesn't exist")
            return False
        print(f"✓ Cache key exists")
        
        # Get cache
        retrieved = redis_client.cache_get(key)
        if retrieved != value:
            print(f"✗ Cache value mismatch")
            return False
        print(f"✓ Cache value verified")
        
        # Delete cache
        result = redis_client.cache_delete(key)
        if not result:
            print(f"✗ Failed to delete cache")
            return False
        print(f"✓ Cache deleted")
        
        # Verify deleted
        exists = redis_client.cache_exists(key)
        if exists:
            print(f"✗ Cache key still exists after delete")
            return False
        print(f"✓ Cache deletion verified")
        
        return True
    except Exception as e:
        print(f"✗ Caching test failed: {e}")
        return False


def main():
    """Run all verification tests."""
    print("\n" + "="*60)
    print("  Redis Setup Verification")
    print("="*60)
    
    # Connect to Redis
    redis_client = verify_connection()
    if redis_client is None:
        print("\n✗ FAILED: Could not connect to Redis")
        print("\nMake sure Redis is running:")
        print("  docker compose up -d redis")
        sys.exit(1)
    
    # Run tests
    tests = [
        ("Health Check", lambda: verify_health_check(redis_client)),
        ("Session State", lambda: verify_session_state(redis_client)),
        ("Frame Buffer", lambda: verify_frame_buffer(redis_client)),
        ("Meeting Participants", lambda: verify_participants(redis_client)),
        ("Distributed Caching", lambda: verify_caching(redis_client)),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print_section("Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    # Cleanup
    redis_client.close()
    
    # Exit code
    if passed == total:
        print("\n✓ All tests passed! Redis setup is working correctly.")
        sys.exit(0)
    else:
        print(f"\n✗ {total - passed} test(s) failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
