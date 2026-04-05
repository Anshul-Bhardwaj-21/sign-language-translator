# Socket.IO Signaling Server

WebRTC signaling server for real-time video conferencing with Socket.IO.

## Features

- **WebRTC Signaling**: Handle offer, answer, and ICE candidate exchange
- **Participant Management**: Track participants joining and leaving meetings
- **Session State**: Store session data in Redis with TTL
- **Real-time Broadcasting**: Broadcast events to all meeting participants
- **Health Checks**: Monitor Redis connectivity and server health

## Requirements

- Python 3.8+
- Redis server running
- Dependencies: `python-socketio`, `fastapi`, `uvicorn`, `redis`

## Installation

```bash
pip install python-socketio fastapi uvicorn redis aiohttp
```

## Configuration

Set environment variables:

```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # Optional

# Server Configuration
SIGNALING_HOST=0.0.0.0
SIGNALING_PORT=8001
```

## Running the Server

### Development Mode

```bash
python backend/signaling_server.py
```

### Production Mode with Uvicorn

```bash
uvicorn signaling_server:socket_app --host 0.0.0.0 --port 8001
```

## Socket.IO Events

### Client → Server Events

#### join-meeting
Join a meeting and receive list of existing participants.

```javascript
socket.emit('join-meeting', {
  meetingId: 'meeting-123',
  userId: 'user-456',
  mediaCapabilities: {
    audio: true,
    video: true,
    screenShare: false
  }
});
```

**Response:**
```javascript
socket.on('join-meeting-success', (data) => {
  console.log('Joined successfully:', data.participants);
});
```

#### leave-meeting
Leave a meeting.

```javascript
socket.emit('leave-meeting', {
  meetingId: 'meeting-123',
  userId: 'user-456'
});
```

#### offer
Send WebRTC offer to another peer.

```javascript
socket.emit('offer', {
  to: 'user-789',
  from: 'user-456',
  sdp: rtcPeerConnection.localDescription
});
```

#### answer
Send WebRTC answer to another peer.

```javascript
socket.emit('answer', {
  to: 'user-456',
  from: 'user-789',
  sdp: rtcPeerConnection.localDescription
});
```

#### ice-candidate
Send ICE candidate to another peer.

```javascript
socket.emit('ice-candidate', {
  to: 'user-789',
  from: 'user-456',
  candidate: event.candidate
});
```

### Server → Client Events

#### participant-joined
Broadcast when a new participant joins.

```javascript
socket.on('participant-joined', (data) => {
  console.log('New participant:', data.participant);
});
```

#### participant-left
Broadcast when a participant leaves.

```javascript
socket.on('participant-left', (data) => {
  console.log('Participant left:', data.userId);
});
```

#### offer
Receive WebRTC offer from another peer.

```javascript
socket.on('offer', async (data) => {
  await rtcPeerConnection.setRemoteDescription(data.sdp);
  const answer = await rtcPeerConnection.createAnswer();
  await rtcPeerConnection.setLocalDescription(answer);
  socket.emit('answer', { to: data.from, from: myUserId, sdp: answer });
});
```

#### answer
Receive WebRTC answer from another peer.

```javascript
socket.on('answer', async (data) => {
  await rtcPeerConnection.setRemoteDescription(data.sdp);
});
```

#### ice-candidate
Receive ICE candidate from another peer.

```javascript
socket.on('ice-candidate', async (data) => {
  await rtcPeerConnection.addIceCandidate(data.candidate);
});
```

#### error
Receive error messages.

```javascript
socket.on('error', (data) => {
  console.error('Error:', data.message);
});
```

## API Endpoints

### GET /health
Health check endpoint.

```bash
curl http://localhost:8001/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "signaling-server",
  "redis": {
    "status": "healthy",
    "latency_ms": 1.5,
    "connected": true,
    "redis_version": "7.0.0"
  }
}
```

### GET /
Root endpoint with service information.

```bash
curl http://localhost:8001/
```

**Response:**
```json
{
  "service": "WebRTC Signaling Server",
  "version": "1.0.0",
  "socket_path": "/socket.io"
}
```

## Redis Data Structures

### Session State
```
Key: session:{user_id}
Value: {
  "meeting_id": str,
  "socket_id": str,
  "joined_at": ISO timestamp,
  "audio_enabled": bool,
  "video_enabled": bool,
  "screen_sharing": bool
}
TTL: 3600 seconds (1 hour)
```

### Meeting Participants
```
Key: meeting:{meeting_id}:participants
Type: Sorted Set
Members: user_id
Scores: join_timestamp
TTL: 86400 seconds (24 hours)
```

## Testing

Run unit tests:

```bash
pytest backend/test_signaling_server.py -v
```

## Architecture

```
Client (Browser)
    ↓ Socket.IO
Signaling Server (Python)
    ↓ Redis Protocol
Redis (Session State)
```

## Requirements Mapping

- **Requirement 21.6**: ICE connection establishment within 3 seconds
- **Requirement 23.6**: Maintain meeting state in distributed database (Redis)

## Security Considerations

1. **CORS Configuration**: Update `cors_allowed_origins` for production
2. **Authentication**: Add JWT token verification for Socket.IO connections
3. **Rate Limiting**: Implement rate limiting for signaling events
4. **TLS/SSL**: Use HTTPS and WSS in production
5. **Input Validation**: Validate all incoming event data

## Production Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY signaling_server.py redis_client.py ./

EXPOSE 8001

CMD ["uvicorn", "signaling_server:socket_app", "--host", "0.0.0.0", "--port", "8001"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  signaling-server:
    build: .
    ports:
      - "8001:8001"
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## Troubleshooting

### Connection Issues

1. Check Redis is running: `redis-cli ping`
2. Verify environment variables are set
3. Check firewall rules for port 8001
4. Review server logs for errors

### Performance Tuning

1. Increase Redis connection pool size: `REDIS_MAX_CONNECTIONS=100`
2. Use Redis Cluster for horizontal scaling
3. Enable Redis persistence for session recovery
4. Monitor with Prometheus metrics

## License

MIT License
