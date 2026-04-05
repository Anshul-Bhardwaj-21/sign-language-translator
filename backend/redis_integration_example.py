"""
Redis Integration Example

This file demonstrates how to integrate Redis client with the meeting application.
Shows practical usage patterns for session state, frame buffers, and participant tracking.

Requirements: 23.6, 33.5, 47.5
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List

from redis_client import get_redis_client, close_redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Session Management Integration
# ============================================================================

class SessionManager:
    """
    Manages user sessions with Redis backend.
    
    Integrates with WebSocket connections to track active users.
    """
    
    def __init__(self):
        self.redis = get_redis_client()
    
    async def create_session(
        self,
        user_id: str,
        meeting_id: str,
        socket_id: str,
        audio_enabled: bool = True,
        video_enabled: bool = True,
    ) -> bool:
        """
        Create new user session.
        
        Args:
            user_id: User identifier
            meeting_id: Meeting identifier
            socket_id: WebSocket connection ID
            audio_enabled: Audio status
            video_enabled: Video status
        
        Returns:
            True if successful
        """
        session_data = {
            "meeting_id": meeting_id,
            "socket_id": socket_id,
            "joined_at": datetime.now().timestamp(),
            "audio_enabled": audio_enabled,
            "video_enabled": video_enabled,
            "last_activity": datetime.now().timestamp(),
        }
        
        # Store session with 1 hour TTL
        success = self.redis.set_session(user_id, session_data, ttl_seconds=3600)
        
        if success:
            logger.info(f"Session created for user {user_id} in meeting {meeting_id}")
        
        return success
    
    async def update_session_activity(self, user_id: str) -> bool:
        """
        Update last activity timestamp and extend TTL.
        
        Args:
            user_id: User identifier
        
        Returns:
            True if successful
        """
        session = self.redis.get_session(user_id)
        
        if session is None:
            logger.warning(f"Session not found for user {user_id}")
            return False
        
        # Update last activity
        session["last_activity"] = datetime.now().timestamp()
        
        # Update session and extend TTL
        success = self.redis.set_session(user_id, session, ttl_seconds=3600)
        
        return success
    
    async def toggle_audio(self, user_id: str, enabled: bool) -> bool:
        """
        Toggle audio status in session.
        
        Args:
            user_id: User identifier
            enabled: Audio enabled status
        
        Returns:
            True if successful
        """
        session = self.redis.get_session(user_id)
        
        if session is None:
            return False
        
        session["audio_enabled"] = enabled
        return self.redis.set_session(user_id, session, ttl_seconds=3600)
    
    async def toggle_video(self, user_id: str, enabled: bool) -> bool:
        """
        Toggle video status in session.
        
        Args:
            user_id: User identifier
            enabled: Video enabled status
        
        Returns:
            True if successful
        """
        session = self.redis.get_session(user_id)
        
        if session is None:
            return False
        
        session["video_enabled"] = enabled
        return self.redis.set_session(user_id, session, ttl_seconds=3600)
    
    async def end_session(self, user_id: str) -> bool:
        """
        End user session.
        
        Args:
            user_id: User identifier
        
        Returns:
            True if successful
        """
        success = self.redis.delete_session(user_id)
        
        if success:
            logger.info(f"Session ended for user {user_id}")
        
        return success


# ============================================================================
# Frame Buffer Integration
# ============================================================================

class FrameBufferManager:
    """
    Manages video frame buffers for inference service.
    
    Implements FIFO queue with automatic size management.
    """
    
    def __init__(self):
        self.redis = get_redis_client()
        self.max_frames = 60  # 2 seconds at 30fps
    
    async def add_frame(self, user_id: str, frame_data: bytes) -> bool:
        """
        Add frame to user's buffer.
        
        Args:
            user_id: User identifier
            frame_data: Frame data as bytes
        
        Returns:
            True if successful
        """
        return self.redis.push_frame(user_id, frame_data, max_frames=self.max_frames)
    
    async def get_frames_for_inference(
        self,
        user_id: str,
        count: int = 60,
    ) -> List[bytes]:
        """
        Get frames for inference processing.
        
        Args:
            user_id: User identifier
            count: Number of frames to retrieve
        
        Returns:
            List of frame data
        """
        frames = self.redis.get_frame_buffer(user_id, count=count)
        
        logger.debug(f"Retrieved {len(frames)} frames for user {user_id}")
        
        return frames
    
    async def clear_buffer(self, user_id: str) -> bool:
        """
        Clear frame buffer for user.
        
        Args:
            user_id: User identifier
        
        Returns:
            True if successful
        """
        return self.redis.clear_frame_buffer(user_id)
    
    async def get_buffer_status(self, user_id: str) -> Dict[str, int]:
        """
        Get buffer status information.
        
        Args:
            user_id: User identifier
        
        Returns:
            Dict with buffer size and max size
        """
        size = self.redis.get_frame_buffer_size(user_id)
        
        return {
            "current_size": size,
            "max_size": self.max_frames,
            "utilization_percent": (size / self.max_frames) * 100,
        }


# ============================================================================
# Meeting Participants Integration
# ============================================================================

class MeetingParticipantManager:
    """
    Manages meeting participants with Redis sorted sets.
    
    Tracks join times and provides ordered participant lists.
    """
    
    def __init__(self):
        self.redis = get_redis_client()
    
    async def add_participant(
        self,
        meeting_id: str,
        user_id: str,
        user_name: str,
    ) -> bool:
        """
        Add participant to meeting.
        
        Args:
            meeting_id: Meeting identifier
            user_id: User identifier
            user_name: User display name
        
        Returns:
            True if successful
        """
        join_time = datetime.now().timestamp()
        
        # Add to sorted set
        success = self.redis.add_participant(meeting_id, user_id, join_time)
        
        if success:
            # Cache user name
            self.redis.cache_set(
                f"user_name:{user_id}",
                user_name,
                ttl_seconds=86400,  # 24 hours
            )
            
            logger.info(
                f"Participant {user_name} ({user_id}) joined meeting {meeting_id}"
            )
        
        return success
    
    async def remove_participant(self, meeting_id: str, user_id: str) -> bool:
        """
        Remove participant from meeting.
        
        Args:
            meeting_id: Meeting identifier
            user_id: User identifier
        
        Returns:
            True if successful
        """
        success = self.redis.remove_participant(meeting_id, user_id)
        
        if success:
            logger.info(f"Participant {user_id} left meeting {meeting_id}")
        
        return success
    
    async def get_participants(self, meeting_id: str) -> List[Dict[str, any]]:
        """
        Get all participants with details.
        
        Args:
            meeting_id: Meeting identifier
        
        Returns:
            List of participant dictionaries
        """
        # Get participants with join times
        participants_raw = self.redis.get_participants(meeting_id, with_scores=True)
        
        participants = []
        for user_id_bytes, join_time in participants_raw:
            user_id = user_id_bytes.decode() if isinstance(user_id_bytes, bytes) else user_id_bytes
            
            # Get cached user name
            user_name = self.redis.cache_get(f"user_name:{user_id}") or user_id
            
            participants.append({
                "user_id": user_id,
                "user_name": user_name,
                "join_time": join_time,
                "join_time_iso": datetime.fromtimestamp(join_time).isoformat(),
            })
        
        return participants
    
    async def get_participant_count(self, meeting_id: str) -> int:
        """
        Get participant count.
        
        Args:
            meeting_id: Meeting identifier
        
        Returns:
            Number of participants
        """
        return self.redis.get_participant_count(meeting_id)
    
    async def is_participant_in_meeting(
        self,
        meeting_id: str,
        user_id: str,
    ) -> bool:
        """
        Check if user is in meeting.
        
        Args:
            meeting_id: Meeting identifier
            user_id: User identifier
        
        Returns:
            True if participant is in meeting
        """
        join_time = self.redis.get_participant_join_time(meeting_id, user_id)
        return join_time is not None


# ============================================================================
# Example Usage
# ============================================================================

async def example_meeting_flow():
    """
    Example: Complete meeting flow with Redis integration.
    """
    logger.info("=== Starting Example Meeting Flow ===")
    
    # Initialize managers
    session_mgr = SessionManager()
    frame_mgr = FrameBufferManager()
    participant_mgr = MeetingParticipantManager()
    
    # Meeting and user IDs
    meeting_id = "meeting_123"
    user1_id = "user_alice"
    user2_id = "user_bob"
    
    try:
        # 1. Users join meeting
        logger.info("\n1. Users joining meeting...")
        
        await session_mgr.create_session(
            user1_id, meeting_id, "socket_1", audio_enabled=True, video_enabled=True
        )
        await participant_mgr.add_participant(meeting_id, user1_id, "Alice")
        
        await asyncio.sleep(1)  # Simulate time delay
        
        await session_mgr.create_session(
            user2_id, meeting_id, "socket_2", audio_enabled=True, video_enabled=False
        )
        await participant_mgr.add_participant(meeting_id, user2_id, "Bob")
        
        # 2. Check participants
        logger.info("\n2. Checking participants...")
        participants = await participant_mgr.get_participants(meeting_id)
        count = await participant_mgr.get_participant_count(meeting_id)
        
        logger.info(f"Participant count: {count}")
        for p in participants:
            logger.info(f"  - {p['user_name']} joined at {p['join_time_iso']}")
        
        # 3. Process video frames
        logger.info("\n3. Processing video frames...")
        
        # Simulate adding frames
        for i in range(10):
            frame_data = f"frame_{i}".encode()
            await frame_mgr.add_frame(user1_id, frame_data)
        
        buffer_status = await frame_mgr.get_buffer_status(user1_id)
        logger.info(f"Buffer status: {buffer_status}")
        
        # Get frames for inference
        frames = await frame_mgr.get_frames_for_inference(user1_id, count=5)
        logger.info(f"Retrieved {len(frames)} frames for inference")
        
        # 4. Update session activity
        logger.info("\n4. Updating session activity...")
        await session_mgr.update_session_activity(user1_id)
        await session_mgr.toggle_video(user2_id, True)
        
        # 5. User leaves meeting
        logger.info("\n5. User leaving meeting...")
        await participant_mgr.remove_participant(meeting_id, user1_id)
        await session_mgr.end_session(user1_id)
        await frame_mgr.clear_buffer(user1_id)
        
        remaining_count = await participant_mgr.get_participant_count(meeting_id)
        logger.info(f"Remaining participants: {remaining_count}")
        
        # 6. Cleanup
        logger.info("\n6. Cleaning up...")
        await participant_mgr.remove_participant(meeting_id, user2_id)
        await session_mgr.end_session(user2_id)
        
        logger.info("\n=== Example Completed Successfully ===")
    
    except Exception as e:
        logger.error(f"Error in example flow: {e}")
    
    finally:
        # Close Redis connection
        close_redis_client()


async def example_health_check():
    """
    Example: Health check integration.
    """
    logger.info("=== Health Check Example ===")
    
    redis = get_redis_client()
    health = redis.health_check()
    
    logger.info(f"Status: {health['status']}")
    logger.info(f"Latency: {health.get('latency_ms', 'N/A')} ms")
    logger.info(f"Redis Version: {health.get('redis_version', 'N/A')}")
    logger.info(f"Connected Clients: {health.get('connected_clients', 'N/A')}")
    
    close_redis_client()


if __name__ == "__main__":
    # Run examples
    print("\n" + "="*60)
    print("Redis Integration Examples")
    print("="*60 + "\n")
    
    # Note: These examples require Redis to be running
    # Start Redis with: docker compose up -d redis
    
    try:
        asyncio.run(example_health_check())
        print("\n")
        asyncio.run(example_meeting_flow())
    except Exception as e:
        logger.error(f"Failed to run examples: {e}")
        logger.info("Make sure Redis is running: docker compose up -d redis")
