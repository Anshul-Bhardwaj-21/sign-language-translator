"""
Redis Client Wrapper for Session State and Frame Buffers

This module provides a Redis client with connection pooling for:
- Session state storage with TTL
- Frame buffer FIFO queue structure
- Meeting participants sorted set
- Distributed caching

Requirements: 23.6, 33.5, 47.5
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import redis
from redis.connection import ConnectionPool
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Redis client wrapper with connection pooling and utility methods.
    
    Features:
    - Connection pooling for efficient resource usage
    - Session state management with configurable TTL
    - FIFO frame buffer queues
    - Sorted sets for participant tracking
    - Health check support
    - Comprehensive error handling
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_connections: int = 50,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5,
        decode_responses: bool = False,
    ):
        """
        Initialize Redis client with connection pooling.
        
        Args:
            host: Redis server host
            port: Redis server port
            db: Redis database number
            password: Redis password (if required)
            max_connections: Maximum connections in pool
            socket_timeout: Socket timeout in seconds
            socket_connect_timeout: Socket connect timeout in seconds
            decode_responses: Whether to decode responses to strings
        """
        self.host = host
        self.port = port
        self.db = db
        
        # Create connection pool
        self.pool = ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            max_connections=max_connections,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            decode_responses=decode_responses,
        )
        
        # Create Redis client
        self.client = redis.Redis(connection_pool=self.pool)
        
        logger.info(
            f"Redis client initialized: {host}:{port} (db={db}, "
            f"max_connections={max_connections})"
        )
    
    def close(self):
        """Close all connections in the pool."""
        try:
            self.pool.disconnect()
            logger.info("Redis connection pool closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection pool: {e}")
    
    # ========================================================================
    # Health Check
    # ========================================================================
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Redis connection.
        
        Returns:
            Dict with health status, latency, and connection info
        """
        try:
            start_time = datetime.now()
            response = self.client.ping()
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            info = self.client.info()
            
            return {
                "status": "healthy" if response else "unhealthy",
                "latency_ms": round(latency_ms, 2),
                "connected": response,
                "redis_version": info.get("redis_version", "unknown"),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
            }
        except RedisConnectionError as e:
            logger.error(f"Redis connection error during health check: {e}")
            return {
                "status": "unhealthy",
                "error": "connection_failed",
                "message": str(e),
            }
        except RedisError as e:
            logger.error(f"Redis error during health check: {e}")
            return {
                "status": "unhealthy",
                "error": "redis_error",
                "message": str(e),
            }
        except Exception as e:
            logger.error(f"Unexpected error during health check: {e}")
            return {
                "status": "unhealthy",
                "error": "unexpected_error",
                "message": str(e),
            }
    
    # ========================================================================
    # Session State Management
    # ========================================================================
    
    def set_session(
        self,
        user_id: str,
        session_data: Dict[str, Any],
        ttl_seconds: int = 3600,
    ) -> bool:
        """
        Store session state with TTL.
        
        Args:
            user_id: User identifier
            session_data: Session data dictionary
            ttl_seconds: Time to live in seconds (default: 1 hour)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f"session:{user_id}"
            value = json.dumps(session_data)
            result = self.client.setex(key, ttl_seconds, value)
            
            logger.debug(f"Session set for user {user_id} with TTL {ttl_seconds}s")
            return bool(result)
        except Exception as e:
            logger.error(f"Error setting session for user {user_id}: {e}")
            return False
    
    def get_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session state.
        
        Args:
            user_id: User identifier
        
        Returns:
            Session data dictionary or None if not found
        """
        try:
            key = f"session:{user_id}"
            value = self.client.get(key)
            
            if value is None:
                return None
            
            return json.loads(value)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding session for user {user_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting session for user {user_id}: {e}")
            return None
    
    def delete_session(self, user_id: str) -> bool:
        """
        Delete session state.
        
        Args:
            user_id: User identifier
        
        Returns:
            True if deleted, False otherwise
        """
        try:
            key = f"session:{user_id}"
            result = self.client.delete(key)
            
            logger.debug(f"Session deleted for user {user_id}")
            return bool(result)
        except Exception as e:
            logger.error(f"Error deleting session for user {user_id}: {e}")
            return False
    
    def extend_session_ttl(self, user_id: str, ttl_seconds: int = 3600) -> bool:
        """
        Extend session TTL without modifying data.
        
        Args:
            user_id: User identifier
            ttl_seconds: New TTL in seconds
        
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f"session:{user_id}"
            result = self.client.expire(key, ttl_seconds)
            
            logger.debug(f"Session TTL extended for user {user_id} to {ttl_seconds}s")
            return bool(result)
        except Exception as e:
            logger.error(f"Error extending session TTL for user {user_id}: {e}")
            return False
    
    # ========================================================================
    # Frame Buffer FIFO Queue
    # ========================================================================
    
    def push_frame(
        self,
        user_id: str,
        frame_data: bytes,
        max_frames: int = 60,
    ) -> bool:
        """
        Push frame to FIFO buffer (right push, left trim).
        
        Args:
            user_id: User identifier
            frame_data: Frame data as bytes
            max_frames: Maximum frames to keep (default: 60 for 2 seconds at 30fps)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f"frame_buffer:{user_id}"
            
            # Push to right (newest)
            self.client.rpush(key, frame_data)
            
            # Trim to keep only max_frames (keep rightmost/newest)
            self.client.ltrim(key, -max_frames, -1)
            
            # Set expiration (10 minutes idle timeout)
            self.client.expire(key, 600)
            
            return True
        except Exception as e:
            logger.error(f"Error pushing frame for user {user_id}: {e}")
            return False
    
    def get_frame_buffer(
        self,
        user_id: str,
        count: Optional[int] = None,
    ) -> List[bytes]:
        """
        Get frames from buffer (oldest to newest).
        
        Args:
            user_id: User identifier
            count: Number of frames to retrieve (None = all)
        
        Returns:
            List of frame data as bytes
        """
        try:
            key = f"frame_buffer:{user_id}"
            
            if count is None:
                # Get all frames
                frames = self.client.lrange(key, 0, -1)
            else:
                # Get last N frames
                frames = self.client.lrange(key, -count, -1)
            
            return frames
        except Exception as e:
            logger.error(f"Error getting frame buffer for user {user_id}: {e}")
            return []
    
    def clear_frame_buffer(self, user_id: str) -> bool:
        """
        Clear frame buffer for user.
        
        Args:
            user_id: User identifier
        
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f"frame_buffer:{user_id}"
            result = self.client.delete(key)
            
            logger.debug(f"Frame buffer cleared for user {user_id}")
            return bool(result)
        except Exception as e:
            logger.error(f"Error clearing frame buffer for user {user_id}: {e}")
            return False
    
    def get_frame_buffer_size(self, user_id: str) -> int:
        """
        Get current frame buffer size.
        
        Args:
            user_id: User identifier
        
        Returns:
            Number of frames in buffer
        """
        try:
            key = f"frame_buffer:{user_id}"
            return self.client.llen(key)
        except Exception as e:
            logger.error(f"Error getting frame buffer size for user {user_id}: {e}")
            return 0
    
    # ========================================================================
    # Meeting Participants Sorted Set
    # ========================================================================
    
    def add_participant(
        self,
        meeting_id: str,
        user_id: str,
        join_timestamp: Optional[float] = None,
    ) -> bool:
        """
        Add participant to meeting sorted set.
        
        Args:
            meeting_id: Meeting identifier
            user_id: User identifier
            join_timestamp: Join timestamp (default: current time)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f"meeting:{meeting_id}:participants"
            score = join_timestamp or datetime.now().timestamp()
            
            result = self.client.zadd(key, {user_id: score})
            
            # Set expiration (24 hours)
            self.client.expire(key, 86400)
            
            logger.debug(f"Participant {user_id} added to meeting {meeting_id}")
            return bool(result)
        except Exception as e:
            logger.error(
                f"Error adding participant {user_id} to meeting {meeting_id}: {e}"
            )
            return False
    
    def remove_participant(self, meeting_id: str, user_id: str) -> bool:
        """
        Remove participant from meeting sorted set.
        
        Args:
            meeting_id: Meeting identifier
            user_id: User identifier
        
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f"meeting:{meeting_id}:participants"
            result = self.client.zrem(key, user_id)
            
            logger.debug(f"Participant {user_id} removed from meeting {meeting_id}")
            return bool(result)
        except Exception as e:
            logger.error(
                f"Error removing participant {user_id} from meeting {meeting_id}: {e}"
            )
            return False
    
    def get_participants(
        self,
        meeting_id: str,
        with_scores: bool = False,
    ) -> List[Tuple[str, float]] | List[str]:
        """
        Get all participants in meeting (ordered by join time).
        
        Args:
            meeting_id: Meeting identifier
            with_scores: Whether to include join timestamps
        
        Returns:
            List of user IDs or list of (user_id, timestamp) tuples
        """
        try:
            key = f"meeting:{meeting_id}:participants"
            
            if with_scores:
                # Returns list of (member, score) tuples
                return self.client.zrange(key, 0, -1, withscores=True)
            else:
                # Returns list of members
                return self.client.zrange(key, 0, -1)
        except Exception as e:
            logger.error(f"Error getting participants for meeting {meeting_id}: {e}")
            return []
    
    def get_participant_count(self, meeting_id: str) -> int:
        """
        Get participant count for meeting.
        
        Args:
            meeting_id: Meeting identifier
        
        Returns:
            Number of participants
        """
        try:
            key = f"meeting:{meeting_id}:participants"
            return self.client.zcard(key)
        except Exception as e:
            logger.error(
                f"Error getting participant count for meeting {meeting_id}: {e}"
            )
            return 0
    
    def get_participant_join_time(
        self,
        meeting_id: str,
        user_id: str,
    ) -> Optional[float]:
        """
        Get join timestamp for specific participant.
        
        Args:
            meeting_id: Meeting identifier
            user_id: User identifier
        
        Returns:
            Join timestamp or None if not found
        """
        try:
            key = f"meeting:{meeting_id}:participants"
            score = self.client.zscore(key, user_id)
            return score
        except Exception as e:
            logger.error(
                f"Error getting join time for participant {user_id} "
                f"in meeting {meeting_id}: {e}"
            )
            return None
    
    # ========================================================================
    # Distributed Caching
    # ========================================================================
    
    def cache_set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """
        Set cache value with optional TTL.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl_seconds: Time to live in seconds (None = no expiration)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = f"cache:{key}"
            serialized_value = json.dumps(value)
            
            if ttl_seconds:
                result = self.client.setex(cache_key, ttl_seconds, serialized_value)
            else:
                result = self.client.set(cache_key, serialized_value)
            
            return bool(result)
        except Exception as e:
            logger.error(f"Error setting cache for key {key}: {e}")
            return False
    
    def cache_get(self, key: str) -> Optional[Any]:
        """
        Get cache value.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found
        """
        try:
            cache_key = f"cache:{key}"
            value = self.client.get(cache_key)
            
            if value is None:
                return None
            
            return json.loads(value)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding cache for key {key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting cache for key {key}: {e}")
            return None
    
    def cache_delete(self, key: str) -> bool:
        """
        Delete cache value.
        
        Args:
            key: Cache key
        
        Returns:
            True if deleted, False otherwise
        """
        try:
            cache_key = f"cache:{key}"
            result = self.client.delete(cache_key)
            return bool(result)
        except Exception as e:
            logger.error(f"Error deleting cache for key {key}: {e}")
            return False
    
    def cache_exists(self, key: str) -> bool:
        """
        Check if cache key exists.
        
        Args:
            key: Cache key
        
        Returns:
            True if exists, False otherwise
        """
        try:
            cache_key = f"cache:{key}"
            return bool(self.client.exists(cache_key))
        except Exception as e:
            logger.error(f"Error checking cache existence for key {key}: {e}")
            return False


# ============================================================================
# Factory Function
# ============================================================================

def create_redis_client_from_env() -> RedisClient:
    """
    Create Redis client from environment variables.
    
    Environment variables:
        REDIS_HOST: Redis host (default: localhost)
        REDIS_PORT: Redis port (default: 6379)
        REDIS_DB: Redis database number (default: 0)
        REDIS_PASSWORD: Redis password (optional)
        REDIS_MAX_CONNECTIONS: Max connections in pool (default: 50)
    
    Returns:
        Configured RedisClient instance
    """
    return RedisClient(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
        password=os.getenv("REDIS_PASSWORD"),
        max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "50")),
    )


# ============================================================================
# Global Instance (Singleton Pattern)
# ============================================================================

_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """
    Get global Redis client instance (singleton).
    
    Returns:
        Global RedisClient instance
    """
    global _redis_client
    
    if _redis_client is None:
        _redis_client = create_redis_client_from_env()
    
    return _redis_client


def close_redis_client():
    """Close global Redis client instance."""
    global _redis_client
    
    if _redis_client is not None:
        _redis_client.close()
        _redis_client = None
