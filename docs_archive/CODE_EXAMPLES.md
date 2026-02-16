# Production Code Examples

## 1. React: Pre-Join Lobby Component

```typescript
// frontend/src/components/PreJoinLobby/PreJoinLobby.tsx

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { validateRoom } from '../../services/api/roomApi';

interface PreJoinLobbyProps {
  onJoin: (config: JoinConfig) => void;
}

interface JoinConfig {
  roomCode: string;
  cameraEnabled: boolean;
  micEnabled: boolean;
  accessibilityMode: boolean;
}

export const PreJoinLobby: React.FC<PreJoinLobbyProps> = ({ onJoin }) => {
  const { roomCode } = useParams<{ roomCode: string }>();
  const navigate = useNavigate();
  
  const [cameraEnabled, setCameraEnabled] = useState(false);
  const [micEnabled, setMicEnabled] = useState(true);
  const [accessibilityMode, setAccessibilityMode] = useState(false);
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string>('');
  const [isValidating, setIsValidating] = useState(true);
  
  const videoRef = useRef<HTMLVideoElement>(null);

  // Validate room on mount
  useEffect(() => {
    const validate = async () => {
      if (!roomCode) {
        setError('Invalid room code');
        setIsValidating(false);
        return;
      }

      try {
        const result = await validateRoom(roomCode);
        if (!result.valid) {
          setError('Room not found');
        } else if (result.is_full) {
          setError('Room is full');
        }
      } catch (err) {
        setError('Failed to validate room');
      } finally {
        setIsValidating(false);
      }
    };

    validate();
  }, [roomCode]);

  // Handle camera preview toggle
  const toggleCameraPreview = async () => {
    if (cameraEnabled) {
      // Stop camera
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        setCameraStream(null);
      }
      setCameraEnabled(false);
    } else {
      // Start camera
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480 },
          audio: false
        });
        
        setCameraStream(stream);
        setCameraEnabled(true);
        
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (err) {
        if (err instanceof Error) {
          if (err.name === 'NotAllowedError') {
            setError('Camera permission denied. Please allow camera access in your browser settings.');
          } else if (err.name === 'NotFoundError') {
            setError('No camera found. You can still join without camera.');
          } else {
            setError(`Camera error: ${err.message}`);
          }
        }
      }
    }
  };

  // Handle join meeting
  const handleJoin = () => {
    if (!roomCode) return;

    // Stop preview stream (will request again in call)
    if (cameraStream) {
      cameraStream.getTracks().forEach(track => track.stop());
    }

    onJoin({
      roomCode,
      cameraEnabled,
      micEnabled,
      accessibilityMode
    });

    navigate(`/call/${roomCode}`);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
      }
    };
  }, [cameraStream]);

  if (isValidating) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-white text-xl">Validating room...</div>
      </div>
    );
  }

  if (error && !error.includes('Camera')) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-gray-900">
        <div className="text-red-500 text-xl mb-4">{error}</div>
        <button
          onClick={() => navigate('/')}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Back to Home
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-900 p-8">
      <div className="max-w-2xl w-full bg-gray-800 rounded-lg shadow-xl p-8">
        {/* Room Code Display */}
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold text-white mb-2">Ready to join?</h1>
          <div className="flex items-center justify-center gap-2">
            <span className="text-gray-400">Room code:</span>
            <span className="text-blue-400 font-mono text-xl">{roomCode}</span>
            <button
              onClick={() => navigator.clipboard.writeText(roomCode || '')}
              className="px-3 py-1 bg-gray-700 text-white rounded hover:bg-gray-600"
              title="Copy room code"
            >
              📋 Copy
            </button>
          </div>
        </div>

        {/* Camera Preview */}
        <div className="mb-6">
          <div className="aspect-video bg-black rounded-lg overflow-hidden relative">
            {cameraEnabled ? (
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="text-6xl mb-4">📷</div>
                  <div className="text-gray-400">Camera preview off</div>
                </div>
              </div>
            )}
          </div>
          
          <button
            onClick={toggleCameraPreview}
            className="mt-3 w-full px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600"
          >
            {cameraEnabled ? '📹 Turn off camera preview' : '📷 Turn on camera preview'}
          </button>
        </div>

        {/* Error Message */}
        {error && error.includes('Camera') && (
          <div className="mb-4 p-3 bg-yellow-900 border border-yellow-700 rounded-lg">
            <div className="text-yellow-200 text-sm">{error}</div>
          </div>
        )}

        {/* Controls */}
        <div className="space-y-3 mb-6">
          <label className="flex items-center gap-3 p-3 bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-600">
            <input
              type="checkbox"
              checked={micEnabled}
              onChange={(e) => setMicEnabled(e.target.checked)}
              className="w-5 h-5"
            />
            <span className="text-white">🎤 Microphone</span>
          </label>

          <label className="flex items-center gap-3 p-3 bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-600">
            <input
              type="checkbox"
              checked={cameraEnabled}
              onChange={(e) => {
                if (!e.target.checked && cameraStream) {
                  cameraStream.getTracks().forEach(track => track.stop());
                  setCameraStream(null);
                }
                setCameraEnabled(e.target.checked);
              }}
              className="w-5 h-5"
            />
            <span className="text-white">📹 Camera</span>
          </label>

          <label className="flex items-center gap-3 p-3 bg-purple-900 rounded-lg cursor-pointer hover:bg-purple-800">
            <input
              type="checkbox"
              checked={accessibilityMode}
              onChange={(e) => setAccessibilityMode(e.target.checked)}
              className="w-5 h-5"
            />
            <span className="text-white">🧏 Accessibility Mode (Sign Language Recognition)</span>
          </label>
        </div>

        {/* Join Button */}
        <button
          onClick={handleJoin}
          className="w-full px-6 py-4 bg-blue-600 text-white text-lg font-semibold rounded-lg hover:bg-blue-700 transition-colors"
        >
          Join Meeting
        </button>

        {/* Info Text */}
        <div className="mt-4 text-center text-gray-400 text-sm">
          By joining, you agree to allow camera and microphone access if enabled.
        </div>
      </div>
    </div>
  );
};
```



## 2. React: Frame Capture Manager

```typescript
// frontend/src/services/ml/FrameCaptureManager.ts

export interface MLResult {
  success: boolean;
  hand_detected: boolean;
  landmarks?: number[][];
  gesture: string;
  confidence: number;
  caption: string;
  movement_state: string;
  processing_time_ms: number;
  error?: string;
  fallback_mode?: string;
}

export class FrameCaptureManager {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private targetFPS: number = 10;
  private lastCaptureTime: number = 0;
  private isProcessing: boolean = false;
  private apiUrl: string;
  private userId: string;
  private sessionId: string;

  constructor(apiUrl: string, userId: string, sessionId: string) {
    this.canvas = document.createElement('canvas');
    this.ctx = this.canvas.getContext('2d')!;
    this.apiUrl = apiUrl;
    this.userId = userId;
    this.sessionId = sessionId;
  }

  setTargetFPS(fps: number): void {
    this.targetFPS = Math.max(1, Math.min(30, fps));
  }

  captureFrame(videoElement: HTMLVideoElement): string | null {
    const now = Date.now();
    const interval = 1000 / this.targetFPS;

    // Throttle frame capture
    if (now - this.lastCaptureTime < interval) {
      return null;
    }

    // Skip if still processing previous frame
    if (this.isProcessing) {
      return null;
    }

    this.lastCaptureTime = now;

    // Resize to 640x480 for ML processing
    this.canvas.width = 640;
    this.canvas.height = 480;
    this.ctx.drawImage(videoElement, 0, 0, 640, 480);

    // Convert to base64 JPEG (smaller than PNG)
    return this.canvas.toDataURL('image/jpeg', 0.8);
  }

  async processFrame(videoElement: HTMLVideoElement): Promise<MLResult | null> {
    const frame = this.captureFrame(videoElement);
    if (!frame) {
      return null;
    }

    this.isProcessing = true;

    try {
      const response = await fetch(`${this.apiUrl}/api/ml/process-frame`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          frame,
          user_id: this.userId,
          session_id: this.sessionId,
          timestamp: Date.now() / 1000
        }),
        signal: AbortSignal.timeout(5000) // 5 second timeout
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result: MLResult = await response.json();
      return result;

    } catch (error) {
      console.error('ML processing failed:', error);
      
      // Return fallback result (don't block UI)
      return {
        success: false,
        hand_detected: false,
        gesture: 'none',
        confidence: 0,
        caption: '',
        movement_state: 'error',
        processing_time_ms: 0,
        error: error instanceof Error ? error.message : 'Unknown error',
        fallback_mode: 'text_only'
      };

    } finally {
      this.isProcessing = false;
    }
  }

  // Process frames in a loop
  async startProcessing(
    videoElement: HTMLVideoElement,
    onResult: (result: MLResult) => void
  ): Promise<void> {
    const processLoop = async () => {
      const result = await this.processFrame(videoElement);
      if (result) {
        onResult(result);
      }

      // Continue loop
      requestAnimationFrame(processLoop);
    };

    processLoop();
  }
}
```

## 3. React: WebRTC Peer Connection Manager

```typescript
// frontend/src/services/webrtc/PeerConnectionManager.ts

import { SignalingClient } from './SignalingClient';

export interface PeerConfig {
  userId: string;
  roomCode: string;
  signalingUrl: string;
}

export class PeerConnectionManager {
  private peerConnection: RTCPeerConnection | null = null;
  private localStream: MediaStream | null = null;
  private remoteStreams: Map<string, MediaStream> = new Map();
  private signalingClient: SignalingClient;
  private config: PeerConfig;

  constructor(config: PeerConfig) {
    this.config = config;
    this.signalingClient = new SignalingClient(config.signalingUrl);
  }

  async initialize(
    cameraEnabled: boolean,
    micEnabled: boolean
  ): Promise<void> {
    // Create peer connection
    this.peerConnection = new RTCPeerConnection({
      iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' }
      ]
    });

    // Get local media
    if (cameraEnabled || micEnabled) {
      try {
        this.localStream = await navigator.mediaDevices.getUserMedia({
          video: cameraEnabled ? {
            width: { ideal: 1280 },
            height: { ideal: 720 },
            frameRate: { ideal: 25, max: 30 }
          } : false,
          audio: micEnabled ? {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true
          } : false
        });

        // Add tracks to peer connection
        this.localStream.getTracks().forEach(track => {
          this.peerConnection!.addTrack(track, this.localStream!);
        });

      } catch (error) {
        console.error('Failed to get user media:', error);
        throw error;
      }
    }

    // Handle ICE candidates
    this.peerConnection.onicecandidate = (event) => {
      if (event.candidate) {
        this.signalingClient.sendSignal({
          type: 'ice-candidate',
          candidate: event.candidate
        });
      }
    };

    // Handle remote tracks
    this.peerConnection.ontrack = (event) => {
      const [remoteStream] = event.streams;
      const remoteUserId = event.track.id; // Simplified - use proper user ID
      this.remoteStreams.set(remoteUserId, remoteStream);
      
      // Notify listeners
      this.onRemoteStreamAdded?.(remoteUserId, remoteStream);
    };

    // Handle connection state changes
    this.peerConnection.onconnectionstatechange = () => {
      console.log('Connection state:', this.peerConnection?.connectionState);
      
      if (this.peerConnection?.connectionState === 'failed') {
        this.onConnectionFailed?.();
      }
    };

    // Connect to signaling server
    await this.signalingClient.connect(
      this.config.roomCode,
      this.config.userId
    );

    // Handle signaling messages
    this.signalingClient.onSignal = async (signal) => {
      await this.handleSignal(signal);
    };
  }

  private async handleSignal(signal: any): Promise<void> {
    if (!this.peerConnection) return;

    switch (signal.type) {
      case 'offer':
        await this.peerConnection.setRemoteDescription(
          new RTCSessionDescription(signal.sdp)
        );
        const answer = await this.peerConnection.createAnswer();
        await this.peerConnection.setLocalDescription(answer);
        this.signalingClient.sendSignal({
          type: 'answer',
          sdp: answer
        });
        break;

      case 'answer':
        await this.peerConnection.setRemoteDescription(
          new RTCSessionDescription(signal.sdp)
        );
        break;

      case 'ice-candidate':
        await this.peerConnection.addIceCandidate(
          new RTCIceCandidate(signal.candidate)
        );
        break;
    }
  }

  async createOffer(): Promise<void> {
    if (!this.peerConnection) return;

    const offer = await this.peerConnection.createOffer();
    await this.peerConnection.setLocalDescription(offer);
    
    this.signalingClient.sendSignal({
      type: 'offer',
      sdp: offer
    });
  }

  getLocalStream(): MediaStream | null {
    return this.localStream;
  }

  getRemoteStreams(): Map<string, MediaStream> {
    return this.remoteStreams;
  }

  toggleCamera(enabled: boolean): void {
    if (!this.localStream) return;

    this.localStream.getVideoTracks().forEach(track => {
      track.enabled = enabled;
    });
  }

  toggleMic(enabled: boolean): void {
    if (!this.localStream) return;

    this.localStream.getAudioTracks().forEach(track => {
      track.enabled = enabled;
    });
  }

  disconnect(): void {
    // Stop local stream
    if (this.localStream) {
      this.localStream.getTracks().forEach(track => track.stop());
      this.localStream = null;
    }

    // Close peer connection
    if (this.peerConnection) {
      this.peerConnection.close();
      this.peerConnection = null;
    }

    // Disconnect signaling
    this.signalingClient.disconnect();

    // Clear remote streams
    this.remoteStreams.clear();
  }

  // Event handlers (set by consumer)
  onRemoteStreamAdded?: (userId: string, stream: MediaStream) => void;
  onRemoteStreamRemoved?: (userId: string) => void;
  onConnectionFailed?: () => void;
}
```



## 4. Python: FastAPI Backend with ML Integration

```python
# backend/app/main.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
import asyncio
import base64
import numpy as np
import cv2
from typing import Optional, List
import logging

# Import your existing ML components
from app.ml.hand_detector import HandDetector
from app.ml.gesture_classifier import GestureClassifier
from app.ml.movement_tracker import MovementTracker
from app.services.room_manager import RoomManager
from app.services.connection_manager import ConnectionManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Sign Language Accessibility Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
room_manager = RoomManager()
connection_manager = ConnectionManager()
hand_detector: Optional[HandDetector] = None
gesture_classifier: Optional[GestureClassifier] = None
movement_tracker = MovementTracker()

# Initialize ML components
@app.on_event("startup")
async def startup_event():
    global hand_detector, gesture_classifier
    
    try:
        hand_detector = HandDetector()
        logger.info("HandDetector initialized")
    except Exception as e:
        logger.error(f"Failed to initialize HandDetector: {e}")
        hand_detector = None
    
    try:
        gesture_classifier = GestureClassifier()
        logger.info("GestureClassifier initialized")
    except Exception as e:
        logger.error(f"Failed to initialize GestureClassifier: {e}")
        gesture_classifier = None


# ============================================================================
# Data Models
# ============================================================================

class FrameRequest(BaseModel):
    frame: str
    user_id: str
    session_id: str
    timestamp: float
    
    @validator('frame')
    def validate_frame(cls, v):
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


class RoomCreateRequest(BaseModel):
    host_user_id: str
    accessibility_mode: bool = False
    max_participants: int = 10


class RoomJoinRequest(BaseModel):
    user_id: str
    user_name: str


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
        "created_at": asyncio.get_event_loop().time(),
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
            {"user_id": p.user_id, "user_name": p.user_name}
            for p in room.participants
            if p.user_id != request.user_id
        ]
    }


# ============================================================================
# ML Processing Endpoint
# ============================================================================

@app.post("/api/ml/process-frame", response_model=MLResult)
async def process_frame(request: FrameRequest):
    """Process a video frame for hand detection and gesture recognition."""
    start_time = asyncio.get_event_loop().time()
    
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
        
        # Track movement
        snapshot = movement_tracker.update(detection.primary_landmarks)
        
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
        
        # Classify gesture
        if gesture_classifier:
            gesture, confidence = gesture_classifier.predict(
                detection.primary_landmarks,
                confidence_threshold=0.58
            )
            caption = gesture if confidence > 0.58 else ""
        else:
            # Fallback to heuristic
            gesture, confidence = "SIGN", 0.5
            caption = ""
        
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


@app.get("/api/ml/model-info")
async def get_model_info():
    """Get information about loaded ML models."""
    return {
        "hand_detector_loaded": hand_detector is not None,
        "gesture_classifier_loaded": gesture_classifier is not None,
        "supported_gestures": gesture_classifier.get_labels() if gesture_classifier else [],
        "model_version": "1.0.0"
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
                "timestamp": asyncio.get_event_loop().time()
            },
            exclude=websocket
        )
        
        # Message handling loop
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "caption":
                # Broadcast caption to all participants
                await connection_manager.broadcast_to_session(
                    room_code,
                    {
                        "type": "caption",
                        "user_id": user_id,
                        "data": data.get("data")
                    },
                    exclude=websocket
                )
            
            elif message_type == "webrtc_signal":
                # Forward WebRTC signaling to specific peer
                target_user = data.get("target_user")
                await connection_manager.send_to_user(
                    room_code,
                    target_user,
                    {
                        "type": "webrtc_signal",
                        "from_user": user_id,
                        "data": data.get("data")
                    }
                )
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
    
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, room_code)
        
        # Notify others of disconnect
        await connection_manager.broadcast_to_session(
            room_code,
            {
                "type": "user_left",
                "user_id": user_id,
                "timestamp": asyncio.get_event_loop().time()
            }
        )
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket, room_code)


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "hand_detector": "loaded" if hand_detector else "not loaded",
        "gesture_classifier": "loaded" if gesture_classifier else "not loaded",
        "active_rooms": room_manager.get_active_room_count(),
        "timestamp": asyncio.get_event_loop().time()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
```



## 5. React: Video Call UI Component

```typescript
// frontend/src/components/VideoCall/VideoCallUI.tsx

import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { PeerConnectionManager } from '../../services/webrtc/PeerConnectionManager';
import { FrameCaptureManager, MLResult } from '../../services/ml/FrameCaptureManager';
import { VideoGrid } from './VideoGrid';
import { ControlBar } from './ControlBar';
import { StatusBar } from './StatusBar';
import { CaptionOverlay } from './CaptionOverlay';

export const VideoCallUI: React.FC = () => {
  const { roomCode } = useParams<{ roomCode: string }>();
  const navigate = useNavigate();
  
  const [peerManager, setPeerManager] = useState<PeerConnectionManager | null>(null);
  const [frameCaptureManager, setFrameCaptureManager] = useState<FrameCaptureManager | null>(null);
  
  const [cameraEnabled, setCameraEnabled] = useState(true);
  const [micEnabled, setMicEnabled] = useState(true);
  const [accessibilityMode, setAccessibilityMode] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  
  const [localStream, setLocalStream] = useState<MediaStream | null>(null);
  const [remoteStreams, setRemoteStreams] = useState<Map<string, MediaStream>>(new Map());
  
  const [currentCaption, setCurrentCaption] = useState<string>('');
  const [captionConfidence, setCaptionConfidence] = useState<number>(0);
  const [confirmedCaptions, setConfirmedCaptions] = useState<string[]>([]);
  
  const [fps, setFps] = useState<number>(0);
  const [handDetected, setHandDetected] = useState<boolean>(false);
  const [gestureStable, setGestureStable] = useState<boolean>(false);
  
  const localVideoRef = useRef<HTMLVideoElement>(null);

  // Initialize peer connection and frame capture
  useEffect(() => {
    const initialize = async () => {
      if (!roomCode) return;

      try {
        // Initialize peer connection
        const peer = new PeerConnectionManager({
          userId: 'user_' + Math.random().toString(36).substr(2, 9),
          roomCode,
          signalingUrl: 'ws://localhost:8000'
        });

        await peer.initialize(cameraEnabled, micEnabled);
        setPeerManager(peer);

        // Get local stream
        const stream = peer.getLocalStream();
        setLocalStream(stream);

        // Set up remote stream handler
        peer.onRemoteStreamAdded = (userId, stream) => {
          setRemoteStreams(prev => new Map(prev).set(userId, stream));
        };

        peer.onRemoteStreamRemoved = (userId) => {
          setRemoteStreams(prev => {
            const newMap = new Map(prev);
            newMap.delete(userId);
            return newMap;
          });
        };

        // Initialize frame capture for ML
        if (accessibilityMode) {
          const frameCapture = new FrameCaptureManager(
            'http://localhost:8000',
            peer.config.userId,
            roomCode
          );
          setFrameCaptureManager(frameCapture);
        }

      } catch (error) {
        console.error('Failed to initialize:', error);
        alert('Failed to initialize video call. Please check camera/mic permissions.');
        navigate('/');
      }
    };

    initialize();

    return () => {
      peerManager?.disconnect();
    };
  }, [roomCode]);

  // Start ML processing when accessibility mode is enabled
  useEffect(() => {
    if (!accessibilityMode || !frameCaptureManager || !localVideoRef.current) {
      return;
    }

    const handleMLResult = (result: MLResult) => {
      if (!result.success) {
        console.error('ML processing failed:', result.error);
        return;
      }

      setHandDetected(result.hand_detected);
      setGestureStable(result.movement_state === 'stable');

      if (result.caption && result.confidence > 0.58) {
        setCurrentCaption(result.caption);
        setCaptionConfidence(result.confidence);
      }
    };

    frameCaptureManager.startProcessing(localVideoRef.current, handleMLResult);
  }, [accessibilityMode, frameCaptureManager]);

  // Update local video element
  useEffect(() => {
    if (localVideoRef.current && localStream) {
      localVideoRef.current.srcObject = localStream;
    }
  }, [localStream]);

  // Calculate FPS
  useEffect(() => {
    let frameCount = 0;
    let lastTime = Date.now();

    const interval = setInterval(() => {
      const now = Date.now();
      const elapsed = (now - lastTime) / 1000;
      setFps(frameCount / elapsed);
      frameCount = 0;
      lastTime = now;
    }, 1000);

    const countFrame = () => {
      frameCount++;
      requestAnimationFrame(countFrame);
    };
    countFrame();

    return () => clearInterval(interval);
  }, []);

  // Control handlers
  const handleToggleCamera = () => {
    const newState = !cameraEnabled;
    setCameraEnabled(newState);
    peerManager?.toggleCamera(newState);
  };

  const handleToggleMic = () => {
    const newState = !micEnabled;
    setMicEnabled(newState);
    peerManager?.toggleMic(newState);
  };

  const handleToggleAccessibility = () => {
    setAccessibilityMode(!accessibilityMode);
  };

  const handlePause = () => {
    setIsPaused(!isPaused);
  };

  const handleClear = () => {
    setCurrentCaption('');
    setConfirmedCaptions([]);
  };

  const handleSpeak = () => {
    const text = [...confirmedCaptions, currentCaption].join(' ');
    if (text && 'speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      speechSynthesis.speak(utterance);
    }
  };

  const handleLeave = () => {
    if (confirm('Are you sure you want to leave the call?')) {
      peerManager?.disconnect();
      navigate('/');
    }
  };

  const handleConfirmCaption = () => {
    if (currentCaption) {
      setConfirmedCaptions(prev => [...prev, currentCaption]);
      setCurrentCaption('');
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-900">
      {/* Status Bar */}
      <StatusBar
        fps={fps}
        handDetected={handDetected}
        gestureStable={gestureStable}
        accessibilityMode={accessibilityMode}
      />

      {/* Video Grid */}
      <div className="flex-1 relative">
        <VideoGrid
          localStream={localStream}
          remoteStreams={remoteStreams}
          localVideoRef={localVideoRef}
        />

        {/* Caption Overlay */}
        {accessibilityMode && (
          <CaptionOverlay
            currentCaption={currentCaption}
            confidence={captionConfidence}
            confirmedCaptions={confirmedCaptions}
            onConfirm={handleConfirmCaption}
          />
        )}
      </div>

      {/* Control Bar */}
      <ControlBar
        cameraEnabled={cameraEnabled}
        micEnabled={micEnabled}
        accessibilityMode={accessibilityMode}
        isPaused={isPaused}
        onToggleCamera={handleToggleCamera}
        onToggleMic={handleToggleMic}
        onToggleAccessibility={handleToggleAccessibility}
        onPause={handlePause}
        onClear={handleClear}
        onSpeak={handleSpeak}
        onLeave={handleLeave}
      />
    </div>
  );
};
```

## 6. React: Caption Overlay Component

```typescript
// frontend/src/components/VideoCall/CaptionOverlay.tsx

import React, { useEffect, useState } from 'react';

interface CaptionOverlayProps {
  currentCaption: string;
  confidence: number;
  confirmedCaptions: string[];
  onConfirm: () => void;
}

export const CaptionOverlay: React.FC<CaptionOverlayProps> = ({
  currentCaption,
  confidence,
  confirmedCaptions,
  onConfirm
}) => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (currentCaption) {
      setVisible(true);
    }
  }, [currentCaption]);

  // Auto-confirm after 3 seconds of stable caption
  useEffect(() => {
    if (!currentCaption) return;

    const timer = setTimeout(() => {
      onConfirm();
    }, 3000);

    return () => clearTimeout(timer);
  }, [currentCaption, onConfirm]);

  const confirmedText = confirmedCaptions.join(' ');

  return (
    <div className="absolute bottom-24 left-1/2 transform -translate-x-1/2 max-w-4xl w-full px-8">
      {/* Current Caption */}
      {currentCaption && (
        <div
          className={`
            bg-black bg-opacity-90 rounded-lg p-6 mb-4
            transition-all duration-300
            ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
          `}
          role="status"
          aria-live="polite"
          aria-atomic="true"
        >
          <div className="text-white text-3xl font-semibold text-center leading-relaxed">
            {currentCaption}
          </div>
          
          {confidence > 0 && (
            <div className="text-blue-400 text-sm text-center mt-2">
              {Math.round(confidence * 100)}% confident
            </div>
          )}

          <div className="flex justify-center gap-4 mt-4">
            <button
              onClick={onConfirm}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              title="Confirm caption (or wait 3 seconds)"
            >
              ✓ Confirm
            </button>
          </div>
        </div>
      )}

      {/* Confirmed Captions */}
      {confirmedText && (
        <div
          className="bg-gray-800 bg-opacity-80 rounded-lg p-4"
          role="log"
          aria-live="polite"
        >
          <div className="text-gray-300 text-lg text-center">
            {confirmedText}
          </div>
        </div>
      )}
    </div>
  );
};
```

## 7. Docker Compose for Development

```yaml
# docker-compose.yml

version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - REACT_APP_API_URL=http://localhost:8000
      - REACT_APP_WS_URL=ws://localhost:8000
    depends_on:
      - backend

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - ./ml_models:/app/ml_models
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/accessibility_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=accessibility_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

## 8. Environment Setup Scripts

```bash
# setup.sh - Development environment setup

#!/bin/bash

echo "Setting up Sign Language Accessibility Video Call System..."

# Backend setup
echo "Setting up backend..."
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ..

# Frontend setup
echo "Setting up frontend..."
cd frontend
npm install
cd ..

# Create .env files
echo "Creating environment files..."

cat > backend/.env << EOF
DATABASE_URL=postgresql://postgres:password@localhost:5432/accessibility_db
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
EOF

cat > frontend/.env << EOF
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
EOF

echo "Setup complete!"
echo ""
echo "To start development:"
echo "1. Backend: cd backend && uvicorn app.main:app --reload"
echo "2. Frontend: cd frontend && npm run dev"
echo ""
echo "Or use Docker Compose: docker-compose up"
```

