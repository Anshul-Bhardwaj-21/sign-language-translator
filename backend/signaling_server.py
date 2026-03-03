"""
Socket.IO Signaling Server for WebRTC and Real-Time Communication

This module provides a Socket.IO server for:
- WebRTC signaling (offer, answer, ICE candidates)
- Real-time participant management
- Session state management in Redis
- Broadcasting events to meeting participants

Requirements: 21.6, 23.6
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

import psycopg2
from psycopg2.extras import RealDictCursor
import socketio
from fastapi import FastAPI
from redis_client import get_redis_client

logger = logging.getLogger(__name__)

# Initialize Socket.IO server with async mode
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',  # Configure appropriately for production
    logger=True,
    engineio_logger=True,
)

# Create FastAPI app
app = FastAPI(
    title="WebRTC Signaling Server",
    description="Socket.IO server for WebRTC signaling and real-time events",
    version="1.0.0",
)

# Wrap with Socket.IO ASGI app
socket_app = socketio.ASGIApp(
    sio,
    other_asgi_app=app,
    socketio_path='/socket.io',
)

# Get Redis client for session state
redis_client = get_redis_client()

# In-memory mapping of socket_id to user_id for quick lookups
socket_to_user: Dict[str, str] = {}
user_to_socket: Dict[str, str] = {}


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
        raise


# ============================================================================
# Helper Functions
# ============================================================================

async def get_user_id_from_socket(sid: str) -> Optional[str]:
    """Get user_id from socket_id."""
    return socket_to_user.get(sid)


async def get_socket_id_from_user(user_id: str) -> Optional[str]:
    """Get socket_id from user_id."""
    return user_to_socket.get(user_id)


async def get_meeting_participants_sockets(meeting_id: str) -> List[str]:
    """Get all socket IDs for participants in a meeting."""
    participant_ids = redis_client.get_participants(meeting_id)
    socket_ids = []
    
    for user_id in participant_ids:
        socket_id = await get_socket_id_from_user(user_id)
        if socket_id:
            socket_ids.append(socket_id)
    
    return socket_ids


async def broadcast_to_meeting(
    meeting_id: str,
    event: str,
    data: Dict[str, Any],
    exclude_sid: Optional[str] = None,
):
    """Broadcast event to all participants in a meeting."""
    socket_ids = await get_meeting_participants_sockets(meeting_id)
    
    for socket_id in socket_ids:
        if exclude_sid and socket_id == exclude_sid:
            continue
        
        try:
            await sio.emit(event, data, room=socket_id)
        except Exception as e:
            logger.error(f"Error broadcasting to socket {socket_id}: {e}")


# ============================================================================
# Socket.IO Event Handlers
# ============================================================================

@sio.event
async def connect(sid: str, environ: Dict[str, Any]):
    """
    Handle client connection.
    
    Args:
        sid: Socket ID
        environ: ASGI environment dict
    """
    logger.info(f"Client connected: {sid}")
    return True


@sio.event
async def disconnect(sid: str):
    """
    Handle client disconnection.
    
    Args:
        sid: Socket ID
    """
    logger.info(f"Client disconnected: {sid}")
    
    # Get user_id from socket mapping
    user_id = await get_user_id_from_socket(sid)
    
    if user_id:
        # Get session to find meeting_id
        session = redis_client.get_session(user_id)
        
        if session and 'meeting_id' in session:
            meeting_id = session['meeting_id']
            
            # Remove participant from meeting
            redis_client.remove_participant(meeting_id, user_id)
            
            # Broadcast participant left event
            await broadcast_to_meeting(
                meeting_id,
                'participant-left',
                {'userId': user_id},
                exclude_sid=sid,
            )
            
            logger.info(f"User {user_id} left meeting {meeting_id}")
        
        # Clean up session
        redis_client.delete_session(user_id)
        
        # Clean up socket mappings
        socket_to_user.pop(sid, None)
        user_to_socket.pop(user_id, None)


@sio.event
async def join_meeting(sid: str, data: Dict[str, Any]):
    """
    Handle join-meeting event.
    
    Client sends:
        {
            "meetingId": str,
            "userId": str,
            "mediaCapabilities": {
                "audio": bool,
                "video": bool,
                "screenShare": bool
            }
        }
    
    Server responds with:
        {
            "success": bool,
            "participants": List[Dict],
            "error": Optional[str]
        }
    
    Broadcasts to other participants:
        'participant-joined': { participant }
    
    Requirements: 21.6, 23.6
    """
    try:
        meeting_id = data.get('meetingId')
        user_id = data.get('userId')
        media_capabilities = data.get('mediaCapabilities', {})
        
        if not meeting_id or not user_id:
            await sio.emit('error', {
                'message': 'Missing meetingId or userId'
            }, room=sid)
            return
        
        # Store socket mapping
        socket_to_user[sid] = user_id
        user_to_socket[user_id] = sid
        
        # Get existing participants before adding new one
        existing_participants = redis_client.get_participants(meeting_id)
        
        # Create session state in Redis
        session_data = {
            'meeting_id': meeting_id,
            'socket_id': sid,
            'joined_at': datetime.now().isoformat(),
            'audio_enabled': media_capabilities.get('audio', True),
            'video_enabled': media_capabilities.get('video', True),
            'screen_sharing': False,
        }
        
        redis_client.set_session(user_id, session_data, ttl_seconds=3600)
        
        # Add participant to meeting sorted set
        redis_client.add_participant(meeting_id, user_id)
        
        # Prepare participant info
        participant_info = {
            'userId': user_id,
            'joinedAt': session_data['joined_at'],
            'audioEnabled': session_data['audio_enabled'],
            'videoEnabled': session_data['video_enabled'],
            'screenSharing': False,
        }
        
        # Send success response with existing participants
        existing_participants_info = []
        for participant_id in existing_participants:
            participant_session = redis_client.get_session(participant_id)
            if participant_session:
                existing_participants_info.append({
                    'userId': participant_id,
                    'joinedAt': participant_session.get('joined_at'),
                    'audioEnabled': participant_session.get('audio_enabled', True),
                    'videoEnabled': participant_session.get('video_enabled', True),
                    'screenSharing': participant_session.get('screen_sharing', False),
                })
        
        await sio.emit('join-meeting-success', {
            'success': True,
            'participants': existing_participants_info,
        }, room=sid)
        
        # Broadcast to other participants that new participant joined
        await broadcast_to_meeting(
            meeting_id,
            'participant-joined',
            {'participant': participant_info},
            exclude_sid=sid,
        )
        
        logger.info(
            f"User {user_id} joined meeting {meeting_id} "
            f"(total participants: {redis_client.get_participant_count(meeting_id)})"
        )
        
    except Exception as e:
        logger.error(f"Error in join_meeting: {e}", exc_info=True)
        await sio.emit('error', {
            'message': f'Failed to join meeting: {str(e)}'
        }, room=sid)


@sio.event
async def leave_meeting(sid: str, data: Dict[str, Any]):
    """
    Handle leave-meeting event.
    
    Client sends:
        {
            "meetingId": str,
            "userId": str
        }
    
    Broadcasts to other participants:
        'participant-left': { userId }
    
    Requirements: 21.6, 23.6
    """
    try:
        meeting_id = data.get('meetingId')
        user_id = data.get('userId')
        
        if not meeting_id or not user_id:
            await sio.emit('error', {
                'message': 'Missing meetingId or userId'
            }, room=sid)
            return
        
        # Remove participant from meeting
        redis_client.remove_participant(meeting_id, user_id)
        
        # Clean up session
        redis_client.delete_session(user_id)
        
        # Clean up socket mappings
        socket_to_user.pop(sid, None)
        user_to_socket.pop(user_id, None)
        
        # Broadcast to other participants
        await broadcast_to_meeting(
            meeting_id,
            'participant-left',
            {'userId': user_id},
            exclude_sid=sid,
        )
        
        # Send confirmation to leaving user
        await sio.emit('leave-meeting-success', {
            'success': True
        }, room=sid)
        
        logger.info(
            f"User {user_id} left meeting {meeting_id} "
            f"(remaining participants: {redis_client.get_participant_count(meeting_id)})"
        )
        
    except Exception as e:
        logger.error(f"Error in leave_meeting: {e}", exc_info=True)
        await sio.emit('error', {
            'message': f'Failed to leave meeting: {str(e)}'
        }, room=sid)


@sio.event
async def offer(sid: str, data: Dict[str, Any]):
    """
    Handle WebRTC offer signaling.
    
    Client sends:
        {
            "to": str,  # target user_id
            "from": str,  # sender user_id
            "sdp": str  # SDP offer
        }
    
    Forwards to target peer.
    
    Requirements: 21.6
    """
    try:
        to_user_id = data.get('to')
        from_user_id = data.get('from')
        sdp = data.get('sdp')
        
        if not to_user_id or not from_user_id or not sdp:
            logger.warning(f"Invalid offer data from {sid}")
            return
        
        # Get target socket ID
        target_sid = await get_socket_id_from_user(to_user_id)
        
        if not target_sid:
            logger.warning(f"Target user {to_user_id} not found for offer")
            return
        
        # Forward offer to target
        await sio.emit('offer', {
            'from': from_user_id,
            'sdp': sdp,
        }, room=target_sid)
        
        logger.debug(f"Forwarded offer from {from_user_id} to {to_user_id}")
        
    except Exception as e:
        logger.error(f"Error in offer: {e}", exc_info=True)


@sio.event
async def answer(sid: str, data: Dict[str, Any]):
    """
    Handle WebRTC answer signaling.
    
    Client sends:
        {
            "to": str,  # target user_id
            "from": str,  # sender user_id
            "sdp": str  # SDP answer
        }
    
    Forwards to target peer.
    
    Requirements: 21.6
    """
    try:
        to_user_id = data.get('to')
        from_user_id = data.get('from')
        sdp = data.get('sdp')
        
        if not to_user_id or not from_user_id or not sdp:
            logger.warning(f"Invalid answer data from {sid}")
            return
        
        # Get target socket ID
        target_sid = await get_socket_id_from_user(to_user_id)
        
        if not target_sid:
            logger.warning(f"Target user {to_user_id} not found for answer")
            return
        
        # Forward answer to target
        await sio.emit('answer', {
            'from': from_user_id,
            'sdp': sdp,
        }, room=target_sid)
        
        logger.debug(f"Forwarded answer from {from_user_id} to {to_user_id}")
        
    except Exception as e:
        logger.error(f"Error in answer: {e}", exc_info=True)


@sio.event
async def ice_candidate(sid: str, data: Dict[str, Any]):
    """
    Handle ICE candidate signaling.
    
    Client sends:
        {
            "to": str,  # target user_id
            "from": str,  # sender user_id
            "candidate": Dict  # ICE candidate
        }
    
    Forwards to target peer.
    
    Requirements: 21.6
    """
    try:
        to_user_id = data.get('to')
        from_user_id = data.get('from')
        candidate = data.get('candidate')
        
        if not to_user_id or not from_user_id or not candidate:
            logger.warning(f"Invalid ICE candidate data from {sid}")
            return
        
        # Get target socket ID
        target_sid = await get_socket_id_from_user(to_user_id)
        
        if not target_sid:
            logger.warning(f"Target user {to_user_id} not found for ICE candidate")
            return
        
        # Forward ICE candidate to target
        await sio.emit('ice-candidate', {
            'from': from_user_id,
            'candidate': candidate,
        }, room=target_sid)
        
        logger.debug(f"Forwarded ICE candidate from {from_user_id} to {to_user_id}")
        
    except Exception as e:
        logger.error(f"Error in ice_candidate: {e}", exc_info=True)


@sio.event
async def toggle_audio(sid: str, data: Dict[str, Any]):
    """
    Handle toggle-audio event.
    
    Client sends:
        {
            "userId": str,
            "meetingId": str,
            "enabled": bool
        }
    
    Updates session state and broadcasts to all participants.
    
    Requirements: 15.1
    """
    try:
        user_id = data.get('userId')
        meeting_id = data.get('meetingId')
        enabled = data.get('enabled', False)
        
        if not user_id or not meeting_id:
            await sio.emit('error', {
                'message': 'Missing userId or meetingId'
            }, room=sid)
            return
        
        # Get session from Redis
        session = redis_client.get_session(user_id)
        
        if not session:
            logger.warning(f"Session not found for user {user_id}")
            await sio.emit('error', {
                'message': 'Session not found'
            }, room=sid)
            return
        
        # Update audio state in session
        session['audio_enabled'] = enabled
        redis_client.set_session(user_id, session, ttl_seconds=3600)
        
        # Broadcast media state change to all participants
        await broadcast_to_meeting(
            meeting_id,
            'participant-updated',
            {
                'userId': user_id,
                'updates': {
                    'audioEnabled': enabled
                }
            },
        )
        
        logger.info(f"User {user_id} audio {'enabled' if enabled else 'disabled'} in meeting {meeting_id}")
        
    except Exception as e:
        logger.error(f"Error in toggle_audio: {e}", exc_info=True)
        await sio.emit('error', {
            'message': f'Failed to toggle audio: {str(e)}'
        }, room=sid)


@sio.event
async def toggle_video(sid: str, data: Dict[str, Any]):
    """
    Handle toggle-video event.
    
    Client sends:
        {
            "userId": str,
            "meetingId": str,
            "enabled": bool
        }
    
    Updates session state and broadcasts to all participants.
    
    Requirements: 15.3
    """
    try:
        user_id = data.get('userId')
        meeting_id = data.get('meetingId')
        enabled = data.get('enabled', False)
        
        if not user_id or not meeting_id:
            await sio.emit('error', {
                'message': 'Missing userId or meetingId'
            }, room=sid)
            return
        
        # Get session from Redis
        session = redis_client.get_session(user_id)
        
        if not session:
            logger.warning(f"Session not found for user {user_id}")
            await sio.emit('error', {
                'message': 'Session not found'
            }, room=sid)
            return
        
        # Update video state in session
        session['video_enabled'] = enabled
        redis_client.set_session(user_id, session, ttl_seconds=3600)
        
        # Broadcast media state change to all participants
        await broadcast_to_meeting(
            meeting_id,
            'participant-updated',
            {
                'userId': user_id,
                'updates': {
                    'videoEnabled': enabled
                }
            },
        )
        
        logger.info(f"User {user_id} video {'enabled' if enabled else 'disabled'} in meeting {meeting_id}")
        
    except Exception as e:
        logger.error(f"Error in toggle_video: {e}", exc_info=True)
        await sio.emit('error', {
            'message': f'Failed to toggle video: {str(e)}'
        }, room=sid)


@sio.event
async def start_screen_share(sid: str, data: Dict[str, Any]):
    """
    Handle start-screen-share event.
    
    Client sends:
        {
            "userId": str,
            "meetingId": str
        }
    
    Ensures only one participant can share at a time, updates session state,
    and broadcasts to all participants.
    
    Requirements: 2.4, 2.5
    """
    try:
        user_id = data.get('userId')
        meeting_id = data.get('meetingId')
        
        if not user_id or not meeting_id:
            await sio.emit('error', {
                'message': 'Missing userId or meetingId'
            }, room=sid)
            return
        
        # Check if anyone else is already screen sharing (Requirement 2.5)
        participants = redis_client.get_participants(meeting_id)
        for participant_id in participants:
            participant_session = redis_client.get_session(participant_id)
            if participant_session and participant_session.get('screen_sharing', False):
                if participant_id != user_id:
                    await sio.emit('error', {
                        'message': 'Another participant is already screen sharing',
                        'code': 'SCREEN_SHARE_IN_PROGRESS'
                    }, room=sid)
                    logger.warning(
                        f"User {user_id} attempted to screen share while {participant_id} "
                        f"is already sharing in meeting {meeting_id}"
                    )
                    return
        
        # Get session from Redis
        session = redis_client.get_session(user_id)
        
        if not session:
            logger.warning(f"Session not found for user {user_id}")
            await sio.emit('error', {
                'message': 'Session not found'
            }, room=sid)
            return
        
        # Update screen sharing state in session
        session['screen_sharing'] = True
        redis_client.set_session(user_id, session, ttl_seconds=3600)
        
        # Broadcast media state change to all participants (Requirement 2.4)
        await broadcast_to_meeting(
            meeting_id,
            'participant-updated',
            {
                'userId': user_id,
                'updates': {
                    'screenSharing': True
                }
            },
        )
        
        logger.info(f"User {user_id} started screen sharing in meeting {meeting_id}")
        
    except Exception as e:
        logger.error(f"Error in start_screen_share: {e}", exc_info=True)
        await sio.emit('error', {
            'message': f'Failed to start screen share: {str(e)}'
        }, room=sid)


@sio.event
async def stop_screen_share(sid: str, data: Dict[str, Any]):
    """
    Handle stop-screen-share event.
    
    Client sends:
        {
            "userId": str,
            "meetingId": str
        }
    
    Updates session state and broadcasts to all participants.
    
    Requirements: 2.4, 2.5
    """
    try:
        user_id = data.get('userId')
        meeting_id = data.get('meetingId')
        
        if not user_id or not meeting_id:
            await sio.emit('error', {
                'message': 'Missing userId or meetingId'
            }, room=sid)
            return
        
        # Get session from Redis
        session = redis_client.get_session(user_id)
        
        if not session:
            logger.warning(f"Session not found for user {user_id}")
            await sio.emit('error', {
                'message': 'Session not found'
            }, room=sid)
            return
        
        # Update screen sharing state in session
        session['screen_sharing'] = False
        redis_client.set_session(user_id, session, ttl_seconds=3600)
        
        # Broadcast media state change to all participants
        await broadcast_to_meeting(
            meeting_id,
            'participant-updated',
            {
                'userId': user_id,
                'updates': {
                    'screenSharing': False
                }
            },
        )
        
        logger.info(f"User {user_id} stopped screen sharing in meeting {meeting_id}")
        
    except Exception as e:
        logger.error(f"Error in stop_screen_share: {e}", exc_info=True)
        await sio.emit('error', {
            'message': f'Failed to stop screen share: {str(e)}'
        }, room=sid)


# ============================================================================
# Chat and Reactions Event Handlers
# ============================================================================

@sio.event
async def send_chat_message(sid: str, data: Dict[str, Any]):
    """
    Handle send-chat-message event.
    
    Client sends:
        {
            "meetingId": str,
            "senderId": str,
            "senderName": str,
            "messageText": str,
            "recipientId": str (optional, for private messages)
        }
    
    Stores message in PostgreSQL and broadcasts to participants.
    
    Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
    """
    try:
        meeting_id = data.get('meetingId')
        sender_id = data.get('senderId')
        sender_name = data.get('senderName')
        message_text = data.get('messageText')
        recipient_id = data.get('recipientId')  # None for public messages
        
        if not all([meeting_id, sender_id, sender_name, message_text]):
            await sio.emit('error', {
                'message': 'Missing required fields'
            }, room=sid)
            return
        
        # Store message in PostgreSQL
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            message_id = str(uuid4())
            timestamp = datetime.utcnow()
            is_private = recipient_id is not None
            
            cursor.execute(
                """
                INSERT INTO chat_messages 
                (id, meeting_id, sender_id, recipient_id, message_text, timestamp, is_private)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (message_id, meeting_id, sender_id, recipient_id, message_text, timestamp, is_private)
            )
            conn.commit()
            
            # Prepare message payload
            message_payload = {
                'id': message_id,
                'meetingId': meeting_id,
                'senderId': sender_id,
                'senderName': sender_name,
                'messageText': message_text,
                'timestamp': timestamp.isoformat(),
                'isPrivate': is_private
            }
            
            if is_private:
                # Send to recipient only
                message_payload['recipientId'] = recipient_id
                recipient_socket = await get_socket_id_from_user(recipient_id)
                if recipient_socket:
                    await sio.emit('chat-message', message_payload, room=recipient_socket)
                # Also send back to sender
                await sio.emit('chat-message', message_payload, room=sid)
            else:
                # Broadcast to all participants in the meeting
                await broadcast_to_meeting(
                    meeting_id,
                    'chat-message',
                    message_payload
                )
            
            logger.info(f"Chat message from {sender_id} in meeting {meeting_id} (private: {is_private})")
            
        finally:
            if conn:
                cursor.close()
                conn.close()
        
    except Exception as e:
        logger.error(f"Error in send_chat_message: {e}", exc_info=True)
        await sio.emit('error', {
            'message': f'Failed to send chat message: {str(e)}'
        }, room=sid)


@sio.event
async def raise_hand(sid: str, data: Dict[str, Any]):
    """
    Handle raise-hand event.
    
    Client sends:
        {
            "userId": str,
            "userName": str,
            "meetingId": str,
            "raised": bool
        }
    
    Broadcasts hand raise status to all participants (ephemeral, not stored).
    
    Requirements: 7.1, 7.2, 7.3, 7.5
    """
    try:
        user_id = data.get('userId')
        user_name = data.get('userName')
        meeting_id = data.get('meetingId')
        raised = data.get('raised', True)
        
        if not all([user_id, user_name, meeting_id]):
            await sio.emit('error', {
                'message': 'Missing required fields'
            }, room=sid)
            return
        
        # Broadcast hand raise status to all participants
        await broadcast_to_meeting(
            meeting_id,
            'hand-raised',
            {
                'userId': user_id,
                'userName': user_name,
                'raised': raised,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"User {user_id} {'raised' if raised else 'lowered'} hand in meeting {meeting_id}")
        
    except Exception as e:
        logger.error(f"Error in raise_hand: {e}", exc_info=True)
        await sio.emit('error', {
            'message': f'Failed to raise hand: {str(e)}'
        }, room=sid)


@sio.event
async def send_reaction(sid: str, data: Dict[str, Any]):
    """
    Handle send-reaction event.
    
    Client sends:
        {
            "userId": str,
            "userName": str,
            "meetingId": str,
            "reaction": str  # emoji: 'thumbs-up', 'clapping', 'heart', 'thinking', 'laughing'
        }
    
    Broadcasts reaction to all participants (ephemeral, not stored).
    
    Requirements: 7.6, 7.7
    """
    try:
        user_id = data.get('userId')
        user_name = data.get('userName')
        meeting_id = data.get('meetingId')
        reaction = data.get('reaction')
        
        if not all([user_id, user_name, meeting_id, reaction]):
            await sio.emit('error', {
                'message': 'Missing required fields'
            }, room=sid)
            return
        
        # Validate reaction type
        valid_reactions = ['thumbs-up', 'clapping', 'heart', 'thinking', 'laughing']
        if reaction not in valid_reactions:
            await sio.emit('error', {
                'message': f'Invalid reaction. Must be one of: {", ".join(valid_reactions)}'
            }, room=sid)
            return
        
        # Broadcast reaction to all participants
        await broadcast_to_meeting(
            meeting_id,
            'reaction',
            {
                'userId': user_id,
                'userName': user_name,
                'reaction': reaction,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"User {user_id} sent reaction '{reaction}' in meeting {meeting_id}")
        
    except Exception as e:
        logger.error(f"Error in send_reaction: {e}", exc_info=True)
        await sio.emit('error', {
            'message': f'Failed to send reaction: {str(e)}'
        }, room=sid)


# ============================================================================
# FastAPI Health Check Endpoint
# ============================================================================

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status including Redis connectivity
    """
    redis_health = redis_client.health_check()
    
    return {
        "status": "healthy" if redis_health["status"] == "healthy" else "unhealthy",
        "service": "signaling-server",
        "redis": redis_health,
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "WebRTC Signaling Server",
        "version": "1.0.0",
        "socket_path": "/socket.io",
    }


# ============================================================================
# Application Lifecycle
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    logger.info("Signaling server starting up...")
    
    # Test Redis connection
    redis_health = redis_client.health_check()
    if redis_health["status"] != "healthy":
        logger.error(f"Redis health check failed: {redis_health}")
    else:
        logger.info(f"Redis connected: {redis_health}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Signaling server shutting down...")
    
    # Clear socket mappings
    socket_to_user.clear()
    user_to_socket.clear()


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    
    # Get configuration from environment
    host = os.getenv("SIGNALING_HOST", "0.0.0.0")
    port = int(os.getenv("SIGNALING_PORT", "8001"))
    
    logger.info(f"Starting signaling server on {host}:{port}")
    
    # Run server
    uvicorn.run(
        socket_app,
        host=host,
        port=port,
        log_level="info",
    )
