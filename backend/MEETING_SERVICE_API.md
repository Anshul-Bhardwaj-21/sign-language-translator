# Meeting Service REST API Documentation

## Overview

The Meeting Service provides REST API endpoints for managing video conference meetings. It handles meeting lifecycle operations including creation, joining, leaving, and host controls.

**Base URL**: `http://localhost:8002`

**Requirements Implemented**:
- 15.6: Host can lock meeting to prevent new participants
- 16.2: Waiting room for participant approval
- 25.1: Create meeting with configuration
- 25.2: Join/leave meeting functionality

## Authentication

Currently, the API uses simple user_id/host_id based authentication. JWT authentication will be added in task 2.4.

## Endpoints

### Health Check

#### GET /health

Check service health and database connectivity.

**Response**:
```json
{
  "status": "healthy",
  "service": "meeting_service",
  "database": "connected",
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

---

### Create Meeting

#### POST /api/meetings

Create a new meeting.

**Request Body**:
```json
{
  "title": "Team Standup",
  "host_id": "123e4567-e89b-12d3-a456-426614174001",
  "waiting_room_enabled": false,
  "recording_enabled": false,
  "max_participants": 100,
  "settings": {
    "video_quality": "720p",
    "enable_chat": true,
    "enable_screen_sharing": true,
    "enable_captions": false,
    "enable_sign_language": false,
    "sign_language": "ASL"
  }
}
```

**Response** (201 Created):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Team Standup",
  "host_id": "123e4567-e89b-12d3-a456-426614174001",
  "created_at": "2024-01-01T12:00:00.000000",
  "started_at": null,
  "ended_at": null,
  "is_locked": false,
  "waiting_room_enabled": false,
  "recording_enabled": false,
  "max_participants": 100,
  "settings": {
    "video_quality": "720p",
    "enable_chat": true,
    "enable_screen_sharing": true,
    "enable_captions": false,
    "enable_sign_language": false,
    "sign_language": "ASL"
  }
}
```

**Validation Rules**:
- `title`: Required, 1-255 characters
- `host_id`: Required
- `max_participants`: 2-1000
- `settings.video_quality`: "720p" or "1080p"
- `settings.sign_language`: "ASL" or "BSL"

---

### Get Meeting

#### GET /api/meetings/{meeting_id}

Retrieve meeting details by ID.

**Path Parameters**:
- `meeting_id` (UUID): Meeting identifier

**Response** (200 OK):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Team Standup",
  "host_id": "123e4567-e89b-12d3-a456-426614174001",
  "created_at": "2024-01-01T12:00:00.000000",
  "started_at": "2024-01-01T12:05:00.000000",
  "ended_at": null,
  "is_locked": false,
  "waiting_room_enabled": false,
  "recording_enabled": false,
  "max_participants": 100,
  "settings": {...}
}
```

**Error Responses**:
- 400: Invalid meeting ID format
- 404: Meeting not found

---

### End Meeting

#### DELETE /api/meetings/{meeting_id}

End a meeting by setting the ended_at timestamp. All active participants are automatically marked as left.

**Path Parameters**:
- `meeting_id` (UUID): Meeting identifier

**Response** (200 OK):
```json
{
  "success": true,
  "meeting_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Meeting ended successfully"
}
```

**Error Responses**:
- 400: Invalid meeting ID or meeting already ended
- 404: Meeting not found

---

### Join Meeting

#### POST /api/meetings/{meeting_id}/join

Join a meeting as a participant.

**Path Parameters**:
- `meeting_id` (UUID): Meeting identifier

**Request Body**:
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174003",
  "user_name": "John Doe"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "meeting_id": "123e4567-e89b-12d3-a456-426614174000",
  "participant_id": "123e4567-e89b-12d3-a456-426614174002",
  "message": "Successfully joined meeting"
}
```

**Business Rules**:
- Meeting must exist and not be ended
- Meeting must not be locked
- Meeting must not be full (participant count < max_participants)
- User cannot join the same meeting twice

**Error Responses**:
- 400: Invalid meeting ID, meeting ended, meeting full, or user already in meeting
- 403: Meeting is locked
- 404: Meeting not found

---

### Leave Meeting

#### POST /api/meetings/{meeting_id}/leave

Leave a meeting as a participant.

**Path Parameters**:
- `meeting_id` (UUID): Meeting identifier

**Request Body**:
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174003"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "meeting_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Successfully left meeting"
}
```

**Error Responses**:
- 400: Invalid meeting ID
- 404: Participant not found in meeting

---

### Lock/Unlock Meeting

#### PUT /api/meetings/{meeting_id}/lock

Lock or unlock a meeting to control participant access. Only the host can perform this action.

**Path Parameters**:
- `meeting_id` (UUID): Meeting identifier

**Request Body**:
```json
{
  "is_locked": true,
  "host_id": "123e4567-e89b-12d3-a456-426614174001"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "meeting_id": "123e4567-e89b-12d3-a456-426614174000",
  "is_locked": true,
  "message": "Meeting locked successfully"
}
```

**Business Rules**:
- Only the meeting host can lock/unlock
- Cannot lock an ended meeting

**Error Responses**:
- 400: Invalid meeting ID or meeting has ended
- 403: User is not the host
- 404: Meeting not found

---

## Error Response Format

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- 400: Bad Request (validation error, business rule violation)
- 403: Forbidden (authorization error)
- 404: Not Found (resource doesn't exist)
- 422: Unprocessable Entity (Pydantic validation error)
- 500: Internal Server Error (database or server error)
- 503: Service Unavailable (database connection failed)

---

## Running the Service

### Development Mode

```bash
# Start the service
python backend/meeting_service.py

# Service will run on http://localhost:8002
```

### With Docker

```bash
# Build and run with docker-compose
docker-compose up meeting_service
```

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string (default: `postgresql://meeting_user:meeting_pass@localhost:5432/meeting_db`)

---

## Testing

Run the test suite:

```bash
# Run all tests
pytest backend/test_meeting_service.py -v

# Run specific test
pytest backend/test_meeting_service.py::test_create_meeting_success -v

# Run with coverage
pytest backend/test_meeting_service.py --cov=meeting_service --cov-report=html
```

---

## Database Schema

The service uses the following tables:

### meetings
- `id` (UUID): Primary key
- `title` (VARCHAR): Meeting title
- `host_id` (UUID): Foreign key to users
- `created_at` (TIMESTAMP): Creation time
- `started_at` (TIMESTAMP): First participant join time
- `ended_at` (TIMESTAMP): Meeting end time
- `is_locked` (BOOLEAN): Lock status
- `waiting_room_enabled` (BOOLEAN): Waiting room feature
- `recording_enabled` (BOOLEAN): Recording feature
- `max_participants` (INTEGER): Maximum participant count
- `settings` (JSONB): Meeting configuration

### participants
- `id` (UUID): Primary key
- `meeting_id` (UUID): Foreign key to meetings
- `user_id` (UUID): Foreign key to users
- `joined_at` (TIMESTAMP): Join time
- `left_at` (TIMESTAMP): Leave time
- `is_host` (BOOLEAN): Host status
- `is_co_host` (BOOLEAN): Co-host status
- `audio_enabled` (BOOLEAN): Audio status
- `video_enabled` (BOOLEAN): Video status

---

## Next Steps

Future enhancements (from tasks.md):
- Task 2.2: Unit tests for Meeting Service
- Task 2.3: Participant management endpoints (mute, remove, video control)
- Task 2.4: JWT authentication service
- Task 2.5: Property tests for authentication

---

## API Design Decisions

1. **UUID Format**: All IDs use UUID v4 for uniqueness and security
2. **Timezone-Aware Timestamps**: All timestamps use UTC timezone
3. **JSONB Settings**: Meeting settings stored as JSONB for flexibility
4. **Soft Delete**: Meetings are ended (ended_at set) rather than deleted
5. **Automatic Timestamps**: started_at set on first participant join
6. **Host Verification**: Lock endpoint verifies host_id matches meeting host
7. **Participant Limits**: Enforced at join time to prevent overcrowding
8. **Idempotency**: Join endpoint prevents duplicate participant entries

---

## CORS Configuration

The service allows requests from:
- http://localhost:3000
- http://localhost:5173
- http://127.0.0.1:3000
- http://127.0.0.1:5173

Update `allow_origins` in `meeting_service.py` for production deployment.
