# Redis Setup Guide

This document describes the Redis configuration for session state management, frame buffering, and distributed caching.

## Overview

Redis is used for:
- **Session State Storage**: User session data with TTL
- **Frame Buffer FIFO Queues**: Video frame buffering for inference
- **Meeting Participants Tracking**: Sorted sets ordered by join time
- **Distributed Caching**: General-purpose caching with TTL

**Requirements**: 23.6, 33.5, 47.5

## Architecture

### Data Structures

#### 1. Session State (String with TTL)
```
Key: session:{user_id}
Value: JSON-encoded session data
TTL: 3600 seconds (1 hour, configurable)

Example:
{
  "meeting_id": "meeting123",
  "socket_id": "socket456",
  "joined_at": 1234567890.0,
  "audio_enabled": true,
  "video_enabled": true
}
```

#### 2. Frame Buffer (List - FIFO Queue)
```
Key: frame_buffer:{user_id}
Value: List of frame data (bytes)
Max Size: 60 frames (2 seconds at 30fps)
TTL: 600 seconds (10 minutes idle timeout)

Operations:
- RPUSH: Add new frame to right (newest)
- LTRIM: Keep only last N frames
- LRANGE: Get frames (oldest to newest)
```

#### 3. Meeting Participants (Sorted Set)
```
Key: meeting:{meeting_id}:participants
Members: user_id
Scores: join_timestamp
TTL: 86400 seconds (24 hours)

Operations:
- ZADD: Add participant with join time
- ZREM: Remove participant
- ZRANGE: Get participants ordered by join time
- ZCARD: Get participant count
- ZSCORE: Get specific participant's join time
```

#### 4. Distributed Cache (String with TTL)
```
Key: cache:{key}
Value: JSON-encoded data
TTL: Configurable per key

Example:
cache:model_metadata -> {"version": "1.0", "accuracy": 0.95}
```

## Configuration

### Environment Variables

```bash
# Redis connection
REDIS_HOST=localhost          # Redis server host
REDIS_PORT=6379              # Redis server port
REDIS_DB=0                   # Redis database number
REDIS_PASSWORD=              # Redis password (optional)
REDIS_MAX_CONNECTIONS=50     # Max connections in pool
```

### Docker Compose

Redis is configured in `docker-compose.yml`:

```yaml
redis:
  image: redis:7-alpine
  container_name: meeting-redis
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 5s
    retries: 5
```

## Usage

### Python API

```python
from redis_client import get_redis_client

# Get singleton instance
redis_client = get_redis_client()

# Session management
redis_client.set_session("user123", {"meeting_id": "meeting456"}, ttl_seconds=3600)
session = redis_client.get_session("user123")
redis_client.delete_session("user123")

# Frame buffer
redis_client.push_frame("user123", frame_bytes, max_frames=60)
frames = redis_client.get_frame_buffer("user123")
redis_client.clear_frame_buffer("user123")

# Meeting participants
redis_client.add_participant("meeting123", "user456")
participants = redis_client.get_participants("meeting123")
count = redis_client.get_participant_count("meeting123")
redis_client.remove_participant("meeting123", "user456")

# Caching
redis_client.cache_set("key", {"data": "value"}, ttl_seconds=300)
value = redis_client.cache_get("key")
redis_client.cache_delete("key")
```

## Health Checks

### Endpoints

1. **Combined Health Check**: `GET /health`
   - Returns overall service health including Redis status
   
2. **Redis-Specific Health Check**: `GET /health/redis`
   - Returns detailed Redis health information

### Response Format

```json
{
  "status": "healthy",
  "latency_ms": 1.23,
  "connected": true,
  "redis_version": "7.2.0",
  "used_memory_human": "1.5M",
  "connected_clients": 5,
  "uptime_seconds": 86400
}
```

### Health Status Values

- `healthy`: Redis is operational
- `unhealthy`: Redis connection failed or error occurred
- `degraded`: Partial functionality (used in combined health check)

## Connection Pooling

The Redis client uses connection pooling for efficient resource management:

- **Max Connections**: 50 (configurable via `REDIS_MAX_CONNECTIONS`)
- **Socket Timeout**: 5 seconds
- **Connect Timeout**: 5 seconds
- **Automatic Reconnection**: Handled by redis-py library

### Benefits

1. **Resource Efficiency**: Reuses connections instead of creating new ones
2. **Performance**: Reduces connection overhead
3. **Scalability**: Handles concurrent requests efficiently
4. **Reliability**: Automatic connection recovery

## Error Handling

All Redis operations include comprehensive error handling:

```python
try:
    result = redis_client.set_session(user_id, data)
except RedisConnectionError:
    # Handle connection failure
    logger.error("Redis connection failed")
except RedisError:
    # Handle Redis-specific errors
    logger.error("Redis operation failed")
except Exception:
    # Handle unexpected errors
    logger.error("Unexpected error")
```

### Graceful Degradation

When Redis is unavailable:
- Operations return `False` or `None` instead of raising exceptions
- Errors are logged for monitoring
- Application continues to function (with reduced features)

## Testing

### Unit Tests

Run Redis client tests:

```bash
# Start Redis (if not running)
docker-compose up -d redis

# Run tests
cd backend
pytest test_redis_client.py -v
```

### Test Coverage

- Health checks
- Session state management (CRUD, TTL)
- Frame buffer operations (push, get, clear)
- Meeting participants (add, remove, count)
- Distributed caching (set, get, delete, exists)
- Error handling (invalid JSON, connection failures)

## Performance Considerations

### Frame Buffer Optimization

- **Max Size**: 60 frames (2 seconds at 30fps)
- **Automatic Trimming**: Keeps only newest frames
- **Idle Timeout**: 10 minutes (prevents memory leaks)
- **Bandwidth**: ~2KB per frame (landmarks) vs ~50-200KB (raw frames)

### Session State

- **TTL**: 1 hour default (prevents stale sessions)
- **Extension**: Can extend TTL without modifying data
- **Cleanup**: Automatic expiration (no manual cleanup needed)

### Participant Tracking

- **Sorted Set**: O(log N) insertion and removal
- **Ordered Retrieval**: O(N) for all participants
- **Count**: O(1) operation
- **TTL**: 24 hours (meeting cleanup)

## Monitoring

### Key Metrics

1. **Connection Health**
   - Latency (ms)
   - Connected clients
   - Failed connections

2. **Memory Usage**
   - Used memory
   - Peak memory
   - Memory fragmentation

3. **Operation Metrics**
   - Commands per second
   - Hit rate (cache)
   - Evicted keys

### Logging

All operations are logged with appropriate levels:

```python
logger.debug("Session set for user {user_id}")  # Verbose operations
logger.info("Redis connection status: healthy")  # Important events
logger.error("Error setting session: {error}")   # Failures
```

## Production Considerations

### Security

1. **Password Protection**: Set `REDIS_PASSWORD` in production
2. **Network Isolation**: Use private network or VPN
3. **TLS/SSL**: Enable for encrypted connections
4. **Firewall**: Restrict access to Redis port

### Persistence

Redis is configured with RDB snapshots:

```yaml
volumes:
  - redis_data:/data
```

For production, consider:
- **AOF (Append-Only File)**: Better durability
- **Backup Strategy**: Regular snapshots
- **Replication**: Master-slave setup

### Scaling

For high-traffic scenarios:

1. **Redis Cluster**: Horizontal scaling with sharding
2. **Redis Sentinel**: High availability with automatic failover
3. **Read Replicas**: Distribute read load
4. **Connection Pooling**: Increase `REDIS_MAX_CONNECTIONS`

## Troubleshooting

### Common Issues

1. **Connection Refused**
   ```bash
   # Check if Redis is running
   docker-compose ps redis
   
   # Check Redis logs
   docker-compose logs redis
   ```

2. **High Memory Usage**
   ```bash
   # Check memory stats
   redis-cli INFO memory
   
   # Check key count
   redis-cli DBSIZE
   ```

3. **Slow Operations**
   ```bash
   # Monitor slow queries
   redis-cli SLOWLOG GET 10
   
   # Check latency
   redis-cli --latency
   ```

### Debug Commands

```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli

# Check all keys
KEYS *

# Get key type
TYPE session:user123

# Get TTL
TTL session:user123

# Get list length
LLEN frame_buffer:user123

# Get sorted set size
ZCARD meeting:meeting123:participants
```

## References

- [Redis Documentation](https://redis.io/documentation)
- [redis-py Documentation](https://redis-py.readthedocs.io/)
- [Redis Best Practices](https://redis.io/topics/best-practices)
- [Requirements 23.6, 33.5, 47.5](../.kiro/specs/advanced-meeting-features/requirements.md)
