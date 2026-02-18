"""FastAPI backend server for video call signaling and caption sync."""

from __future__ import annotations

import asyncio
import base64
import io
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import numpy as np
import cv2

# Import CV modules
from app.inference.hand_detector import HandDetector, create_hand_detector
from app.inference.asl_classifier import ASLClassifier, create_asl_classifier
from app.inference.text_generator import TextGenerator, create_text_generator
from app.inference.gesture_controls import GestureController
from app.inference.movement_tracker import MovementTracker

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
    allow_methods=["GET", "POST", "OPTIONS"],  # Explicit methods only
    allow_headers=["Content-Type", "Authorization"],  # Explicit headers only
    max_age=3600,  # Cache preflight requests for 1 hour
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
# CV Pipeline State Management
# ============================================================================

class CVPipelineState:
    """Manages CV pipeline instances per user session."""
    
    def __init__(self):
        self.hand_detector: Optional[HandDetector] = None
        self.asl_classifier: Optional[ASLClassifier] = None
        self.text_generator: Optional[TextGenerator] = None
        self.gesture_controller: Optional[GestureController] = None
        self.movement_tracker: Optional[MovementTracker] = None
    
    def initialize(self):
        """Initialize all CV components."""
        try:
            self.hand_detector = create_hand_detector(max_num_hands=1)
            self.asl_classifier = create_asl_classifier()
            self.text_generator = create_text_generator()
            self.gesture_controller = GestureController()
            self.movement_tracker = MovementTracker()
            logger.info("CV pipeline initialized")
        except Exception as exc:
            logger.error(f"Failed to initialize CV pipeline: {exc}")
    
    def cleanup(self):
        """Clean up CV resources."""
        if self.hand_detector:
            self.hand_detector.close()
        if self.text_generator:
            self.text_generator.reset()


# CV pipeline instances per session
cv_pipelines: Dict[str, CVPipelineState] = {}


async def process_cv_frame(
    frame_data: dict,
    pipeline: CVPipelineState,
    websocket: WebSocket
) -> None:
    """
    Process single video frame through CV pipeline.
    
    Pipeline:
    1. Decode frame
    2. Detect hand
    3. Classify ASL gesture
    4. Generate text
    5. Detect control gestures (fist)
    6. Send captions
    7. Trigger TTS on sentence confirmation
    """
    try:
        # Decode base64 JPEG
        image_data = base64.b64decode(frame_data["image"])
        nparr = np.frombuffer(image_data, np.uint8)
        frame_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame_bgr is None:
            await websocket.send_json({
                "type": "error",
                "code": "INVALID_FRAME",
                "message": "Failed to decode frame",
                "severity": "warning",
                "timestamp": int(datetime.now().timestamp() * 1000)
            })
            return
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        
        # 1. Hand detection
        hand_result = pipeline.hand_detector.detect(frame_rgb, draw_landmarks=False)
        
        if not hand_result.hand_detected:
            # No hand detected - send nothing caption
            await websocket.send_json({
                "type": "caption",
                "level": "live",
                "text": "",
                "confidence": 0.0,
                "timestamp": int(datetime.now().timestamp() * 1000)
            })
            return
        
        # 2. Movement tracking
        movement_snapshot = pipeline.movement_tracker.update(hand_result.primary_landmarks)
        
        # 3. ASL classification (only on stable hand)
        if movement_snapshot.state in {"stable", "idle"}:
            asl_prediction = pipeline.asl_classifier.predict(frame_rgb)
            
            if asl_prediction.is_stable and asl_prediction.letter != "nothing":
                # 4. Text generation
                text_state = pipeline.text_generator.add_letter(asl_prediction.letter)
                
                # Send live caption (current word)
                if text_state.current_word:
                    await websocket.send_json({
                        "type": "caption",
                        "level": "live",
                        "text": text_state.current_word,
                        "confidence": asl_prediction.confidence,
                        "timestamp": int(datetime.now().timestamp() * 1000)
                    })
                
                # Send confirmed words
                if text_state.confirmed_words:
                    await websocket.send_json({
                        "type": "caption",
                        "level": "word",
                        "text": " ".join(text_state.confirmed_words),
                        "confidence": 1.0,
                        "timestamp": int(datetime.now().timestamp() * 1000)
                    })
        
        # 5. Gesture control detection (fist for sentence confirmation)
        gesture_event = pipeline.gesture_controller.update(
            hand_result.primary_landmarks,
            movement_snapshot.state,
            hand_result.handedness
        )
        
        if gesture_event.confirmed and gesture_event.action == "confirm_sentence":
            sentence = pipeline.text_generator.confirm_sentence_by_fist()
            if sentence:
                # Send confirmed sentence
                await websocket.send_json({
                    "type": "caption",
                    "level": "sentence",
                    "text": sentence,
                    "confidence": 1.0,
                    "timestamp": int(datetime.now().timestamp() * 1000)
                })
                
                # 6. Generate TTS audio
                await generate_and_send_tts(sentence, websocket)
        
        # Check for idle timeout sentence confirmation
        idle_sentence = pipeline.text_generator.confirm_sentence_by_idle()
        if idle_sentence:
            await websocket.send_json({
                "type": "caption",
                "level": "sentence",
                "text": idle_sentence,
                "confidence": 1.0,
                "timestamp": int(datetime.now().timestamp() * 1000)
            })
            await generate_and_send_tts(idle_sentence, websocket)
    
    except Exception as exc:
        logger.error(f"CV frame processing error: {exc}")
        await websocket.send_json({
            "type": "error",
            "code": "PROCESSING_FAILED",
            "message": str(exc),
            "severity": "recoverable",
            "timestamp": int(datetime.now().timestamp() * 1000)
        })


async def generate_and_send_tts(text: str, websocket: WebSocket) -> None:
    """Generate TTS audio and send to client."""
    try:
        # Use gTTS for MP3 generation
        from gtts import gTTS
        
        # Generate speech
        tts = gTTS(text=text, lang='en', slow=False)
        
        # Save to bytes buffer
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        # Encode to base64
        audio_base64 = base64.b64encode(audio_buffer.read()).decode('utf-8')
        
        # Send to client
        await websocket.send_json({
            "type": "audio",
            "format": "mp3",
            "data": audio_base64,
            "timestamp": int(datetime.now().timestamp() * 1000)
        })
        
        logger.info(f"TTS audio sent for text: {text}")
    
    except ImportError:
        logger.warning("gTTS not installed. Install with: pip install gtts")
        # Send caption only without audio
    except Exception as exc:
        logger.error(f"TTS generation failed: {exc}")
        # Continue without audio


# ============================================================================
# WebSocket Endpoints
# ============================================================================

@app.websocket("/ws/cv/{session_id}/{user_id}")
async def cv_websocket_endpoint(websocket: WebSocket, session_id: str, user_id: str):
    """
    Computer Vision WebSocket endpoint for ASL recognition.
    
    Receives video frames, processes through CV pipeline, sends captions and audio.
    
    Message types (Client → Server):
    - video_frame: Frame data for processing
    
    Message types (Server → Client):
    - caption: Live/word/sentence caption
    - audio: TTS audio (base64 MP3)
    - error: Processing error
    """
    await websocket.accept()
    
    # Initialize CV pipeline for this session
    pipeline_key = f"{session_id}_{user_id}"
    if pipeline_key not in cv_pipelines:
        cv_pipelines[pipeline_key] = CVPipelineState()
        cv_pipelines[pipeline_key].initialize()
    
    pipeline = cv_pipelines[pipeline_key]
    
    # Check if ASL model is loaded
    if not pipeline.asl_classifier or not pipeline.asl_classifier.is_ready():
        await websocket.send_json({
            "type": "error",
            "code": "MODEL_NOT_FOUND",
            "message": "ASL model not found. Run backend/train_asl_model.py to train the model.",
            "severity": "fatal",
            "timestamp": int(datetime.now().timestamp() * 1000)
        })
        await websocket.close()
        return
    
    logger.info(f"CV WebSocket connected: {user_id} in session {session_id}")
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "video_frame":
                # Process frame immediately (frontend already throttles to 10 FPS)
                await process_cv_frame(data, pipeline, websocket)
    
    except WebSocketDisconnect:
        logger.info(f"CV WebSocket disconnected: {user_id}")
    except Exception as exc:
        logger.error(f"CV WebSocket error: {exc}")
    finally:
        # Cleanup
        if pipeline_key in cv_pipelines:
            cv_pipelines[pipeline_key].cleanup()
            del cv_pipelines[pipeline_key]


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
