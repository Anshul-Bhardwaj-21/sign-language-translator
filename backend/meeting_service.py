"""
Meeting Service REST API

Provides REST endpoints for meeting management including:
- Create, get, delete meetings
- Join, leave meetings
- Lock meetings
- Participant management

Requirements: 15.6, 16.2, 25.1, 25.2
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

import psycopg2
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models for Request/Response Validation
# ============================================================================

class MeetingSettings(BaseModel):
    """Meeting configuration settings."""
    video_quality: str = Field(default="720p", pattern="^(720p|1080p)$")
    enable_chat: bool = True
    enable_screen_sharing: bool = True
    enable_captions: bool = False
    enable_sign_language: bool = False
    sign_language: str = Field(default="ASL", pattern="^(ASL|BSL)$")


class CreateMeetingRequest(BaseModel):
    """Request model for creating a meeting."""
    title: str = Field(..., min_length=1, max_length=255)
    host_id: str
    waiting_room_enabled: bool = False
    recording_enabled: bool = False
    max_participants: int = Field(default=100, ge=2, le=1000)
    settings: Optional[MeetingSettings] = None


class MeetingResponse(BaseModel):
    """Response model for meeting data."""
    id: str
    title: str
    host_id: str
    created_at: str
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    is_locked: bool
    waiting_room_enabled: bool
    recording_enabled: bool
    max_participants: int
    settings: dict


class JoinMeetingRequest(BaseModel):
    """Request model for joining a meeting."""
    user_id: str
    user_name: str = Field(..., min_length=1, max_length=255)


class JoinMeetingResponse(BaseModel):
    """Response model for join meeting."""
    success: bool
    meeting_id: str
    participant_id: str
    message: str


class LeaveMeetingRequest(BaseModel):
    """Request model for leaving a meeting."""
    user_id: str


class LockMeetingRequest(BaseModel):
    """Request model for locking/unlocking a meeting."""
    is_locked: bool
    host_id: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None


# ============================================================================
# Database Connection
# ============================================================================

def get_database_url():
    """Get database URL from environment or use default."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://meeting_user:meeting_pass@localhost:5432/meeting_db"
    )


def parse_database_url(url: str) -> dict:
    """Parse PostgreSQL URL into connection parameters."""
    url = url.replace("postgresql://", "")
    
    if "@" in url:
        auth, rest = url.split("@", 1)
        user, password = auth.split(":", 1)
    else:
        raise ValueError("Invalid database URL format")
    
    if "/" in rest:
        host_port, dbname = rest.split("/", 1)
    else:
        raise ValueError("Invalid database URL format")
    
    if ":" in host_port:
        host, port = host_port.split(":", 1)
    else:
        host = host_port
        port = "5432"
    
    return {
        "host": host,
        "port": port,
        "dbname": dbname,
        "user": user,
        "password": password
    }


def get_db_connection():
    """Create and return a database connection."""
    db_url = get_database_url()
    conn_params = parse_database_url(db_url)
    
    try:
        conn = psycopg2.connect(**conn_params, cursor_factory=RealDictCursor)
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        )


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Meeting Service API",
    description="REST API for meeting management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Meeting Service API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        
        return {
            "status": "healthy",
            "service": "meeting_service",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "meeting_service",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@app.post("/api/meetings", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
async def create_meeting(request: CreateMeetingRequest):
    """
    Create a new meeting.
    
    Requirements: 25.1
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Generate meeting ID
        meeting_id = str(uuid4())
        
        # Prepare settings
        settings = request.settings.model_dump() if request.settings else MeetingSettings().model_dump()
        
        # Insert meeting
        cursor.execute("""
            INSERT INTO meetings (
                id, title, host_id, created_at, is_locked,
                waiting_room_enabled, recording_enabled, max_participants, settings
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, title, host_id, created_at, started_at, ended_at,
                      is_locked, waiting_room_enabled, recording_enabled,
                      max_participants, settings
        """, (
            meeting_id,
            request.title,
            request.host_id,
            datetime.now(timezone.utc),
            False,
            request.waiting_room_enabled,
            request.recording_enabled,
            request.max_participants,
            psycopg2.extras.Json(settings)
        ))
        
        meeting = cursor.fetchone()
        conn.commit()
        
        logger.info(f"Created meeting {meeting_id} by host {request.host_id}")
        
        return MeetingResponse(
            id=str(meeting['id']),
            title=meeting['title'],
            host_id=str(meeting['host_id']),
            created_at=meeting['created_at'].isoformat(),
            started_at=meeting['started_at'].isoformat() if meeting['started_at'] else None,
            ended_at=meeting['ended_at'].isoformat() if meeting['ended_at'] else None,
            is_locked=meeting['is_locked'],
            waiting_room_enabled=meeting['waiting_room_enabled'],
            recording_enabled=meeting['recording_enabled'],
            max_participants=meeting['max_participants'],
            settings=meeting['settings']
        )
        
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error creating meeting: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create meeting"
        )
    finally:
        if conn:
            cursor.close()
            conn.close()


@app.get("/api/meetings/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(meeting_id: str):
    """
    Get meeting details by ID.
    
    Requirements: 25.1
    """
    conn = None
    try:
        # Validate UUID format
        try:
            UUID(meeting_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid meeting ID format"
            )
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, host_id, created_at, started_at, ended_at,
                   is_locked, waiting_room_enabled, recording_enabled,
                   max_participants, settings
            FROM meetings
            WHERE id = %s
        """, (meeting_id,))
        
        meeting = cursor.fetchone()
        
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found"
            )
        
        return MeetingResponse(
            id=str(meeting['id']),
            title=meeting['title'],
            host_id=str(meeting['host_id']),
            created_at=meeting['created_at'].isoformat(),
            started_at=meeting['started_at'].isoformat() if meeting['started_at'] else None,
            ended_at=meeting['ended_at'].isoformat() if meeting['ended_at'] else None,
            is_locked=meeting['is_locked'],
            waiting_room_enabled=meeting['waiting_room_enabled'],
            recording_enabled=meeting['recording_enabled'],
            max_participants=meeting['max_participants'],
            settings=meeting['settings']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting meeting {meeting_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve meeting"
        )
    finally:
        if conn:
            cursor.close()
            conn.close()


@app.delete("/api/meetings/{meeting_id}", status_code=status.HTTP_200_OK)
async def end_meeting(meeting_id: str):
    """
    End a meeting by setting ended_at timestamp.
    
    Requirements: 25.1
    """
    conn = None
    try:
        # Validate UUID format
        try:
            UUID(meeting_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid meeting ID format"
            )
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if meeting exists
        cursor.execute("SELECT id, ended_at FROM meetings WHERE id = %s", (meeting_id,))
        meeting = cursor.fetchone()
        
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found"
            )
        
        if meeting['ended_at']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Meeting already ended"
            )
        
        # Update meeting end time
        cursor.execute("""
            UPDATE meetings
            SET ended_at = %s
            WHERE id = %s
        """, (datetime.now(timezone.utc), meeting_id))
        
        # Update all participants' left_at time
        cursor.execute("""
            UPDATE participants
            SET left_at = %s
            WHERE meeting_id = %s AND left_at IS NULL
        """, (datetime.now(timezone.utc), meeting_id))
        
        conn.commit()
        
        logger.info(f"Ended meeting {meeting_id}")
        
        return {
            "success": True,
            "meeting_id": meeting_id,
            "message": "Meeting ended successfully"
        }
        
    except HTTPException:
        raise
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error ending meeting {meeting_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to end meeting"
        )
    finally:
        if conn:
            cursor.close()
            conn.close()


@app.post("/api/meetings/{meeting_id}/join", response_model=JoinMeetingResponse)
async def join_meeting(meeting_id: str, request: JoinMeetingRequest):
    """
    Join a meeting as a participant.
    
    Requirements: 25.2
    """
    conn = None
    try:
        # Validate UUID format
        try:
            UUID(meeting_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid meeting ID format"
            )
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if meeting exists and is not ended
        cursor.execute("""
            SELECT id, host_id, is_locked, ended_at, max_participants
            FROM meetings
            WHERE id = %s
        """, (meeting_id,))
        
        meeting = cursor.fetchone()
        
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found"
            )
        
        if meeting['ended_at']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Meeting has ended"
            )
        
        if meeting['is_locked']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Meeting is locked"
            )
        
        # Check participant count
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM participants
            WHERE meeting_id = %s AND left_at IS NULL
        """, (meeting_id,))
        
        participant_count = cursor.fetchone()['count']
        
        if participant_count >= meeting['max_participants']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Meeting is full"
            )
        
        # Check if user already in meeting
        cursor.execute("""
            SELECT id FROM participants
            WHERE meeting_id = %s AND user_id = %s AND left_at IS NULL
        """, (meeting_id, request.user_id))
        
        existing_participant = cursor.fetchone()
        
        if existing_participant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already in meeting"
            )
        
        # Add participant
        participant_id = str(uuid4())
        is_host = str(meeting['host_id']) == request.user_id
        
        cursor.execute("""
            INSERT INTO participants (
                id, meeting_id, user_id, joined_at, is_host
            ) VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (
            participant_id,
            meeting_id,
            request.user_id,
            datetime.now(timezone.utc),
            is_host
        ))
        
        # Update meeting started_at if this is the first participant
        cursor.execute("""
            UPDATE meetings
            SET started_at = %s
            WHERE id = %s AND started_at IS NULL
        """, (datetime.now(timezone.utc), meeting_id))
        
        conn.commit()
        
        logger.info(f"User {request.user_id} joined meeting {meeting_id}")
        
        return JoinMeetingResponse(
            success=True,
            meeting_id=meeting_id,
            participant_id=participant_id,
            message="Successfully joined meeting"
        )
        
    except HTTPException:
        raise
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error joining meeting {meeting_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to join meeting"
        )
    finally:
        if conn:
            cursor.close()
            conn.close()


@app.post("/api/meetings/{meeting_id}/leave")
async def leave_meeting(meeting_id: str, request: LeaveMeetingRequest):
    """
    Leave a meeting as a participant.
    
    Requirements: 25.2
    """
    conn = None
    try:
        # Validate UUID format
        try:
            UUID(meeting_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid meeting ID format"
            )
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if participant is in meeting
        cursor.execute("""
            SELECT id FROM participants
            WHERE meeting_id = %s AND user_id = %s AND left_at IS NULL
        """, (meeting_id, request.user_id))
        
        participant = cursor.fetchone()
        
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Participant not found in meeting"
            )
        
        # Update participant left_at time
        cursor.execute("""
            UPDATE participants
            SET left_at = %s
            WHERE meeting_id = %s AND user_id = %s AND left_at IS NULL
        """, (datetime.now(timezone.utc), meeting_id, request.user_id))
        
        conn.commit()
        
        logger.info(f"User {request.user_id} left meeting {meeting_id}")
        
        return {
            "success": True,
            "meeting_id": meeting_id,
            "message": "Successfully left meeting"
        }
        
    except HTTPException:
        raise
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error leaving meeting {meeting_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to leave meeting"
        )
    finally:
        if conn:
            cursor.close()
            conn.close()


@app.put("/api/meetings/{meeting_id}/lock")
async def lock_meeting(meeting_id: str, request: LockMeetingRequest):
    """
    Lock or unlock a meeting to prevent new participants from joining.
    
    Requirements: 15.6
    """
    conn = None
    try:
        # Validate UUID format
        try:
            UUID(meeting_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid meeting ID format"
            )
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if meeting exists and verify host
        cursor.execute("""
            SELECT id, host_id, ended_at
            FROM meetings
            WHERE id = %s
        """, (meeting_id,))
        
        meeting = cursor.fetchone()
        
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found"
            )
        
        if meeting['ended_at']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Meeting has ended"
            )
        
        # Verify host authorization
        if str(meeting['host_id']) != request.host_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the host can lock/unlock the meeting"
            )
        
        # Update meeting lock status
        cursor.execute("""
            UPDATE meetings
            SET is_locked = %s
            WHERE id = %s
        """, (request.is_locked, meeting_id))
        
        conn.commit()
        
        action = "locked" if request.is_locked else "unlocked"
        logger.info(f"Meeting {meeting_id} {action} by host {request.host_id}")
        
        return {
            "success": True,
            "meeting_id": meeting_id,
            "is_locked": request.is_locked,
            "message": f"Meeting {action} successfully"
        }
        
    except HTTPException:
        raise
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error locking meeting {meeting_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update meeting lock status"
        )
    finally:
        if conn:
            cursor.close()
            conn.close()


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )
