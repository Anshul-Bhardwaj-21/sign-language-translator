"""
Simple FastAPI Backend for Video Call Demo
- WebSocket signaling for WebRTC
- Mock ASL inference (no external APIs)
- Works completely offline
"""

import asyncio
import base64
import logging
import random
import string
from datetime import datetime
from typing import Dict, List, Optional, Set

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import mock inference
from mock_inference import create_mock_model, create_mock_text_generator

# Import Redis client
from redis_client import get_redis_client, close_redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class RoomCreateRequest(BaseModel):
    host_user_id: str
    accessibility_mode: bool = False
    max_participants: int = 10


class RoomJoinRequest(BaseModel):
    user_id: str
    user_name: str


# ============================================================================
# Room Manager
# ============================================================================

class Room:
    def __init__(self, room_code: str, host_user_id: str):
        self.room_code = room_code
        self.host_user_id = host_user_id
        self.participants: List[Dict[str, str]] = []
        self.created_at = datetime.now().timestamp()


class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
    
    def generate_room_code(self) -> str:
        """Generate unique 6-character room code"""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if code not in self.rooms:
                return code
    
    def create_room(self, room_code: str, host_user_id: str) -> str:
        """Create new room"""
        room = Room(room_code, host_user_id)
        self.rooms[room_code] = room
        return room_code
    
    def get_room(self, room_code: str) -> Optional[Room]:
        """Get room by code"""
        return self.rooms.get(room_code)
    
    def add_participant(self, room_code: str, user_id: str, user_name: str):
        """Add participant to room"""
        room = self.rooms.get(room_code)
        if room:
            room.participants.append({"user_id": user_id, "user_name": user_name})
    
    def remove_participant(self, room_code: str, user_id: str):
        """Remove participant from room"""
        room = self.rooms.get(room_code)
        if room:
            room.participants = [p for p in room.participants if p["user_id"] != user_id]


# ============================================================================
# Connection Manager
# ============================================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_mapping: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str, user_id: str):
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        
        self.active_connections[session_id].add(websocket)
        self.user_mapping[websocket] = user_id
        
        logger.info(f"User {user_id} connected to session {session_id}")
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        
        user_id = self.user_mapping.pop(websocket, "unknown")
        logger.info(f"User {user_id} disconnected from session {session_id}")
    
    async def broadcast_to_session(self, session_id: str, message: dict, exclude: Optional[WebSocket] = None):
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
        
        for conn in disconnected:
            self.disconnect(conn, session_id)


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Sign Language Video Call Backend",
    description="WebSocket signaling + Mock ASL inference",
    version="1.0.0"
)

# CORS - allow localhost for development
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

# Global instances
room_manager = RoomManager()
connection_manager = ConnectionManager()

# Mock models per user (lazy loaded)
mock_models: Dict[str, any] = {}
text_generators: Dict[str, any] = {}


# ============================================================================
# Lifecycle Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting up backend service...")
    # Initialize Redis client
    redis_client = get_redis_client()
    redis_health = redis_client.health_check()
    logger.info(f"Redis connection status: {redis_health['status']}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down backend service...")
    # Close Redis connections
    close_redis_client()
    logger.info("Redis connections closed")


# ============================================================================
# HTTP Endpoints
# ============================================================================

@app.get("/")
async def root():
    return {
        "status": "running",
        "service": "Sign Language Video Call Backend",
        "version": "1.0.0",
        "mode": "mock_inference"
    }


@app.get("/health")
async def health_check():
    """
    Comprehensive health check including Redis connectivity.
    
    Returns:
        Health status for backend service and Redis
    """
    # Get Redis client and check health
    redis_client = get_redis_client()
    redis_health = redis_client.health_check()
    
    # Overall health status
    overall_status = "healthy" if redis_health["status"] == "healthy" else "degraded"
    
    return {
        "status": overall_status,
        "service": "backend",
        "active_rooms": len(room_manager.rooms),
        "active_connections": sum(len(conns) for conns in connection_manager.active_connections.values()),
        "timestamp": datetime.now().isoformat(),
        "redis": redis_health,
    }


@app.get("/health/redis")
async def redis_health_check():
    """
    Dedicated Redis health check endpoint.
    
    Returns:
        Detailed Redis health information
    """
    redis_client = get_redis_client()
    return redis_client.health_check()


@app.post("/api/rooms/create")
async def create_room(request: RoomCreateRequest):
    """Create a new room"""
    room_code = room_manager.generate_room_code()
    room_manager.create_room(room_code, request.host_user_id)
    
    return {
        "room_code": room_code,
        "room_id": room_code,
        "created_at": datetime.now().timestamp(),
        "websocket_url": f"ws://localhost:8001/ws/{room_code}"
    }


@app.get("/api/rooms/{room_code}/validate")
async def validate_room(room_code: str):
    """Validate if room exists"""
    room = room_manager.get_room(room_code)
    
    if not room:
        return {"valid": False, "error": "Room not found"}
    
    return {
        "valid": True,
        "room_id": room.room_code,
        "participants_count": len(room.participants),
        "is_full": False,
        "accessibility_mode": True
    }


@app.post("/api/rooms/{room_code}/join")
async def join_room(room_code: str, request: RoomJoinRequest):
    """Join an existing room"""
    room = room_manager.get_room(room_code)
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    room_manager.add_participant(room_code, request.user_id, request.user_name)
    
    return {
        "success": True,
        "room_id": room.room_code,
        "websocket_url": f"ws://localhost:8001/ws/{room_code}/{request.user_id}",
        "existing_participants": [
            {"user_id": p["user_id"], "user_name": p["user_name"]}
            for p in room.participants
            if p["user_id"] != request.user_id
        ]
    }


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@app.websocket("/ws/{room_code}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, room_code: str, user_id: str):
    """
    WebSocket endpoint for:
    1. WebRTC signaling (offer/answer/ICE candidates)
    2. Caption broadcasting
    3. Video frame processing (mock ASL inference)
    """
    await connection_manager.connect(websocket, room_code, user_id)
    
    # Initialize mock model for this user
    if user_id not in mock_models:
        mock_models[user_id] = create_mock_model(mode="deterministic")
        text_generators[user_id] = create_mock_text_generator()
        logger.info(f"Initialized mock model for user {user_id}")
    
    try:
        # Notify others of new participant
        await connection_manager.broadcast_to_session(
            room_code,
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
            
            if message_type == "webrtc_signal":
                # Forward WebRTC signaling to target peer
                target_user = data.get("target_user")
                signal_data = data.get("data")
                
                # Broadcast to all in room (simple mesh topology)
                await connection_manager.broadcast_to_session(
                    room_code,
                    {
                        "type": "webrtc_signal",
                        "from_user": user_id,
                        "target_user": target_user,
                        "data": signal_data
                    },
                    exclude=websocket
                )
            
            elif message_type == "video_frame":
                # Process frame with mock inference
                try:
                    # Decode base64 image
                    image_data = data.get("image", "").split(',')[-1]
                    image_bytes = base64.b64decode(image_data)
                    nparr = np.frombuffer(image_bytes, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        # Simple hand detection (mock - just check if frame is not empty)
                        hand_detected = frame.size > 0
                        
                        if hand_detected:
                            # Mock landmarks (dummy data)
                            landmarks = [(i * 0.05, i * 0.05, 0.0) for i in range(21)]
                            
                            # Get prediction from mock model
                            model = mock_models[user_id]
                            prediction = model.predict(landmarks)
                            
                            # Generate text
                            text_gen = text_generators[user_id]
                            if prediction.is_stable:
                                result = text_gen.add_letter(prediction.letter)
                                
                                # Send caption to client
                                await websocket.send_json({
                                    "type": "caption",
                                    "level": "live",
                                    "text": result["current_word"],
                                    "confidence": prediction.confidence,
                                    "timestamp": int(datetime.now().timestamp() * 1000)
                                })
                                
                                # Broadcast to others in room
                                if result["current_word"]:
                                    await connection_manager.broadcast_to_session(
                                        room_code,
                                        {
                                            "type": "caption",
                                            "user_id": user_id,
                                            "data": {
                                                "text": result["current_word"],
                                                "confidence": prediction.confidence
                                            }
                                        },
                                        exclude=websocket
                                    )
                        else:
                            # No hand detected
                            await websocket.send_json({
                                "type": "caption",
                                "level": "live",
                                "text": "",
                                "confidence": 0.0,
                                "timestamp": int(datetime.now().timestamp() * 1000)
                            })
                
                except Exception as e:
                    logger.error(f"Frame processing error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Frame processing failed: {str(e)}"
                    })
            
            elif message_type == "caption":
                # Broadcast caption to others
                await connection_manager.broadcast_to_session(
                    room_code,
                    {
                        "type": "caption",
                        "user_id": user_id,
                        "data": data.get("data")
                    },
                    exclude=websocket
                )
            
            elif message_type == "chat":
                # Broadcast chat message
                await connection_manager.broadcast_to_session(
                    room_code,
                    {
                        "type": "chat",
                        "user_id": user_id,
                        "data": data.get("data")
                    },
                    exclude=websocket
                )
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
    
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, room_code)
        
        # Cleanup user models
        if user_id in mock_models:
            del mock_models[user_id]
        if user_id in text_generators:
            del text_generators[user_id]
        
        # Notify others
        await connection_manager.broadcast_to_session(
            room_code,
            {
                "type": "user_left",
                "user_id": user_id,
                "timestamp": datetime.now().timestamp()
            }
        )
    
    except Exception as exc:
        logger.error(f"WebSocket error: {exc}")
        connection_manager.disconnect(websocket, room_code)


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
