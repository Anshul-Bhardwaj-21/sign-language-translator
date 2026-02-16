"""Enhanced FastAPI backend with ML integration for sign language video calls."""

from __future__ import annotations

import asyncio
import base64
import logging
import random
import string
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
import uvicorn

# Add parent directory to path to import app modules
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Import existing ML components
try:
    from app.inference.hand_detector import HandDetector, create_hand_detector
    from app.inference.movement_tracker import MovementTracker
    ML_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ML components not available: {e}")
    ML_AVAILABLE = False

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


class FrameRequest(BaseModel):
    frame: str
    user_id: str
    session_id: str
    timestamp: float
    
    @field_validator('frame')
    @classmethod
    def validate_frame(cls, v: str) -> str:
        if not v.startswith('data:image/jpeg;base64,'):
            raise ValueError('Invalid frame format')
        if len(v) > 2_000_000:  # 2MB limit
            raise ValueError('Frame too large')
        return v


class MLResult(BaseModel):
    success: bool
    hand_detected: bool
    landmarks: Optional[List[List[float]]] = None
    gesture: str = "none"
    confidence: float = 0.0
    caption: str = ""
    movement_state: str = "idle"
    processing_time_ms: float = 0.0
    error: Optional[str] = None
    fallback_mode: Optional[str] = None


# ============================================================================
# Room Manager
# ============================================================================

class Room:
    def __init__(self, room_code: str, room_id: str, host_user_id: str, 
                 accessibility_mode: bool, max_participants: int):
        self.room_code = room_code
        self.room_id = room_id
        self.host_user_id = host_user_id
        self.accessibility_mode = accessibility_mode
        self.max_participants = max_participants
        self.participants: List[Dict[str, str]] = []
        self.created_at = datetime.now().timestamp()


class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
    
    def generate_room_code(self) -> str:
        """Generate a unique 6-character room code."""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if code not in self.rooms:
                return code
    
    def create_room(self, room_code: str, host_user_id: str, 
                   accessibility_mode: bool, max_participants: int) -> str:
        """Create a new room."""
        room_id = f"room_{datetime.now().timestamp()}"
        room = Room(room_code, room_id, host_user_id, accessibility_mode, max_participants)
        self.rooms[room_code] = room
        return room_id
    
    def get_room(self, room_code: str) -> Optional[Room]:
        """Get room by code."""
        return self.rooms.get(room_code)
    
    def add_participant(self, room_code: str, user_id: str, user_name: str):
        """Add participant to room."""
        room = self.rooms.get(room_code)
        if room:
            room.participants.append({"user_id": user_id, "user_name": user_name})
    
    def remove_participant(self, room_code: str, user_id: str):
        """Remove participant from room."""
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
    title="Sign Language Accessibility Backend",
    description="Enhanced backend with ML integration",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Explicit methods only
    allow_headers=["Content-Type", "Authorization"],  # Explicit headers only
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Global instances
room_manager = RoomManager()
connection_manager = ConnectionManager()
hand_detector: Optional[HandDetector] = None
movement_trackers: Dict[str, MovementTracker] = {}


# Initialize ML components (lazy loading - only when needed)
@app.on_event("startup")
async def startup_event():
    global hand_detector
    
    # Don't initialize MediaPipe on startup to avoid camera lock
    # It will be initialized on first frame processing request
    logger.info("Backend started - ML components will be loaded on demand")
    hand_detector = None


# ============================================================================
# Room Management Endpoints
# ============================================================================

@app.post("/api/rooms/create")
async def create_room(request: RoomCreateRequest):
    """Create a new room."""
    room_code = room_manager.generate_room_code()
    room_id = room_manager.create_room(
        room_code=room_code,
        host_user_id=request.host_user_id,
        accessibility_mode=request.accessibility_mode,
        max_participants=request.max_participants
    )
    
    return {
        "room_code": room_code,
        "room_id": room_id,
        "created_at": datetime.now().timestamp(),
        "websocket_url": f"ws://localhost:8000/ws/{room_code}"
    }


@app.get("/api/rooms/{room_code}/validate")
async def validate_room(room_code: str):
    """Validate if room exists and is joinable."""
    room = room_manager.get_room(room_code)
    
    if not room:
        return {
            "valid": False,
            "error": "Room not found"
        }
    
    return {
        "valid": True,
        "room_id": room.room_id,
        "participants_count": len(room.participants),
        "is_full": len(room.participants) >= room.max_participants,
        "accessibility_mode": room.accessibility_mode
    }


@app.post("/api/rooms/{room_code}/join")
async def join_room(room_code: str, request: RoomJoinRequest):
    """Join an existing room."""
    room = room_manager.get_room(room_code)
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if len(room.participants) >= room.max_participants:
        raise HTTPException(status_code=403, detail="Room is full")
    
    room_manager.add_participant(room_code, request.user_id, request.user_name)
    
    return {
        "success": True,
        "room_id": room.room_id,
        "websocket_url": f"ws://localhost:8000/ws/{room_code}/{request.user_id}",
        "existing_participants": [
            {"user_id": p["user_id"], "user_name": p["user_name"]}
            for p in room.participants
            if p["user_id"] != request.user_id
        ]
    }


# ============================================================================
# ML Processing Endpoint
# ============================================================================

@app.post("/api/ml/process-frame", response_model=MLResult)
async def process_frame(request: FrameRequest):
    """Process a video frame for hand detection and gesture recognition."""
    start_time = asyncio.get_event_loop().time()
    
    global hand_detector
    
    # Lazy load hand detector on first use
    if hand_detector is None and ML_AVAILABLE:
        try:
            logger.info("Initializing HandDetector on first use...")
            hand_detector = create_hand_detector()
            logger.info("HandDetector initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize HandDetector: {e}")
    
    # Check if ML components are available
    if hand_detector is None:
        return MLResult(
            success=True,
            hand_detected=False,
            gesture="none",
            caption="",
            movement_state="error",
            processing_time_ms=0.0,
            error="Hand detector not initialized",
            fallback_mode="text_only"
        )
    
    try:
        # Decode base64 image
        image_data = request.frame.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise ValueError("Failed to decode image")
        
        # Convert BGR to RGB (MediaPipe expects RGB)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect hand
        detection = hand_detector.detect(frame_rgb, draw_landmarks=False)
        
        if not detection.hand_detected or not detection.primary_landmarks:
            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
            return MLResult(
                success=True,
                hand_detected=False,
                gesture="none",
                caption="",
                movement_state="no_hand",
                processing_time_ms=processing_time
            )
        
        # Get or create movement tracker for this user
        if request.user_id not in movement_trackers:
            movement_trackers[request.user_id] = MovementTracker()
        
        tracker = movement_trackers[request.user_id]
        snapshot = tracker.update(detection.primary_landmarks)
        
        # Only classify if hand is stable
        if snapshot.state not in ['stable', 'idle']:
            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
            return MLResult(
                success=True,
                hand_detected=True,
                landmarks=detection.primary_landmarks,
                gesture="none",
                caption="",
                movement_state=snapshot.state,
                processing_time_ms=processing_time
            )
        
        # Simple heuristic gesture recognition (replace with your trained model)
        gesture, confidence = _predict_gesture_heuristic(detection.primary_landmarks)
        caption = gesture if confidence > 0.5 else ""
        
        processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        return MLResult(
            success=True,
            hand_detected=True,
            landmarks=detection.primary_landmarks,
            gesture=gesture,
            confidence=confidence,
            caption=caption,
            movement_state=snapshot.state,
            processing_time_ms=processing_time
        )
    
    except Exception as e:
        logger.error(f"ML processing error: {e}")
        processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        return MLResult(
            success=False,
            hand_detected=False,
            gesture="none",
            caption="",
            movement_state="error",
            processing_time_ms=processing_time,
            error=str(e),
            fallback_mode="heuristic"
        )


def _predict_gesture_heuristic(landmarks: List[tuple]) -> tuple[str, float]:
    """Simple heuristic gesture recognition (replace with trained model)."""
    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    middle_tip = landmarks[12]
    wrist = landmarks[0]
    
    # Calculate openness
    openness = (wrist[1] - index_tip[1] + wrist[1] - middle_tip[1]) / 2.0
    
    # Simple heuristics
    if openness > 0.20:
        return "HELLO", 0.65
    elif openness < 0.10:
        return "YES", 0.60
    else:
        return "SIGN", 0.55


@app.get("/api/ml/model-info")
async def get_model_info():
    """Get information about loaded ML models."""
    return {
        "hand_detector_loaded": hand_detector is not None,
        "ml_available": ML_AVAILABLE,
        "model_version": "2.0.0"
    }


# ============================================================================
# Health Check
# ============================================================================

@app.get("/")
async def root():
    return {
        "status": "running",
        "service": "Sign Language Accessibility Backend (Enhanced)",
        "version": "2.0.0",
        "ml_available": ML_AVAILABLE
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "hand_detector": "loaded" if hand_detector else "not loaded",
        "active_rooms": len(room_manager.rooms),
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@app.websocket("/ws/{room_code}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, room_code: str, user_id: str):
    """WebSocket endpoint for real-time communication."""
    await connection_manager.connect(websocket, room_code, user_id)
    
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
            
            if message_type == "caption":
                await connection_manager.broadcast_to_session(
                    room_code,
                    {
                        "type": "caption",
                        "user_id": user_id,
                        "data": data.get("data")
                    },
                    exclude=websocket
                )
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
    
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, room_code)
        
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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
