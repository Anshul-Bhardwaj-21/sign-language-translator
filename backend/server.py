"""FastAPI backend server for video call signaling and caption sync."""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class CaptionMessage(BaseModel):
    session_id: str
    user_id: str
    text: str
    timestamp: float
    is_confirmed: bool = False


class CorrectionMessage(BaseModel):
    user_id: str
    original_text: str
    corrected_text: str
    timestamp: float


class SessionInfo(BaseModel):
    session_id: str
    participants: List[str]
    created_at: float
    accessibility_mode: bool = False


# ============================================================================
# Connection Manager
# ============================================================================

class ConnectionManager:
    """Manages WebSocket connections for real-time communication."""
    
    def __init__(self):
        # session_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # websocket -> user_id mapping
        self.user_mapping: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str, user_id: str):
        """Accept and register new WebSocket connection."""
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        
        self.active_connections[session_id].add(websocket)
        self.user_mapping[websocket] = user_id
        
        logger.info(f"User {user_id} connected to session {session_id}")
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove WebSocket connection."""
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        
        user_id = self.user_mapping.pop(websocket, "unknown")
        logger.info(f"User {user_id} disconnected from session {session_id}")
    
    async def broadcast_to_session(self, session_id: str, message: dict, exclude: Optional[WebSocket] = None):
        """Broadcast message to all connections in a session."""
        if session_id not in self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections[session_id]:
            if connection == exclude:
                continue
            
            try:
                await connection.send_json(message)
            except Exception as exc:
                logger.error(f"Failed to send message: {exc}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn, session_id)
    
    def get_session_participants(self, session_id: str) -> List[str]:
        """Get list of user IDs in a session."""
        if session_id not in self.active_connections:
            return []
        
        return [
            self.user_mapping.get(ws, "unknown")
            for ws in self.active_connections[session_id]
        ]


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Sign Language Accessibility Backend",
    description="WebSocket signaling and caption sync for video calls",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",  # Streamlit default
        "http://localhost:3000",  # React default
        "http://127.0.0.1:8501",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connection manager instance
manager = ConnectionManager()

# In-memory storage (replace with Firebase/database in production)
captions_store: Dict[str, List[CaptionMessage]] = {}
sessions_store: Dict[str, SessionInfo] = {}


# ============================================================================
# HTTP Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "service": "Sign Language Accessibility Backend",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "active_sessions": len(manager.active_connections),
        "total_connections": sum(len(conns) for conns in manager.active_connections.values()),
        "timestamp": datetime.now().isoformat()
    }


@app.post("/sessions/create")
async def create_session(session_info: SessionInfo):
    """Create a new video call session."""
    if session_info.session_id in sessions_store:
        raise HTTPException(status_code=400, detail="Session already exists")
    
    sessions_store[session_info.session_id] = session_info
    captions_store[session_info.session_id] = []
    
    logger.info(f"Created session: {session_info.session_id}")
    return {"status": "created", "session_id": session_info.session_id}


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session information."""
    if session_id not in sessions_store:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions_store[session_id]
    participants = manager.get_session_participants(session_id)
    
    return {
        "session_id": session.session_id,
        "participants": participants,
        "created_at": session.created_at,
        "accessibility_mode": session.accessibility_mode
    }


@app.get("/sessions/{session_id}/captions")
async def get_captions(session_id: str, limit: int = 50):
    """Get recent captions for a session."""
    if session_id not in captions_store:
        return {"captions": []}
    
    captions = captions_store[session_id][-limit:]
    return {"captions": [c.dict() for c in captions]}


@app.post("/captions/store")
async def store_caption(caption: CaptionMessage):
    """Store a caption (also broadcasts via WebSocket)."""
    if caption.session_id not in captions_store:
        captions_store[caption.session_id] = []
    
    captions_store[caption.session_id].append(caption)
    
    # Broadcast to session participants
    await manager.broadcast_to_session(
        caption.session_id,
        {
            "type": "caption",
            "data": caption.dict()
        }
    )
    
    return {"status": "stored"}


# ============================================================================
# WebSocket Endpoints
# ============================================================================

@app.websocket("/ws/{session_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, user_id: str):
    """
    WebSocket endpoint for real-time communication.
    
    Message types:
    - caption: Live caption update
    - correction: User correction for incremental learning
    - webrtc_signal: WebRTC signaling (offer/answer/ice)
    - status: User status update
    """
    await manager.connect(websocket, session_id, user_id)
    
    try:
        # Send session history to new joiner
        if session_id in captions_store:
            recent_captions = captions_store[session_id][-20:]
            await websocket.send_json({
                "type": "history",
                "data": [c.dict() for c in recent_captions]
            })
        
        # Notify others of new participant
        await manager.broadcast_to_session(
            session_id,
            {
                "type": "user_joined",
                "user_id": user_id,
                "timestamp": datetime.now().timestamp()
            },
            exclude=websocket
        )
        
        # Message handling loop
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "caption":
                # Store and broadcast caption
                caption = CaptionMessage(**data["data"])
                if session_id not in captions_store:
                    captions_store[session_id] = []
                captions_store[session_id].append(caption)
                
                await manager.broadcast_to_session(
                    session_id,
                    {"type": "caption", "data": caption.dict()},
                    exclude=websocket
                )
            
            elif message_type == "correction":
                # Broadcast correction for incremental learning
                await manager.broadcast_to_session(
                    session_id,
                    {"type": "correction", "data": data["data"]}
                )
            
            elif message_type == "webrtc_signal":
                # Forward WebRTC signaling to specific peer
                target_user = data.get("target_user")
                signal_data = data.get("data")
                
                # Find target user's websocket
                for ws in manager.active_connections.get(session_id, []):
                    if manager.user_mapping.get(ws) == target_user:
                        await ws.send_json({
                            "type": "webrtc_signal",
                            "from_user": user_id,
                            "data": signal_data
                        })
                        break
            
            elif message_type == "status":
                # Broadcast status update
                await manager.broadcast_to_session(
                    session_id,
                    {
                        "type": "status",
                        "user_id": user_id,
                        "data": data.get("data")
                    },
                    exclude=websocket
                )
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
        
        # Notify others of disconnect
        await manager.broadcast_to_session(
            session_id,
            {
                "type": "user_left",
                "user_id": user_id,
                "timestamp": datetime.now().timestamp()
            }
        )
    
    except Exception as exc:
        logger.error(f"WebSocket error: {exc}")
        manager.disconnect(websocket, session_id)


# ============================================================================
# Server Entry Point
# ============================================================================

def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the FastAPI server."""
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    start_server()
