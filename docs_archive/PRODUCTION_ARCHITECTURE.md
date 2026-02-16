# Production-Grade Sign Language Accessible Video Meeting System
## Architecture Design Document

**Version:** 2.0  
**Date:** February 15, 2026  
**Status:** Production Architecture Specification

---

## Executive Summary

This document specifies a production-grade, accessibility-first video meeting system similar to Google Meet, with ML-powered sign language recognition. The architecture prioritizes user consent, graceful degradation, and real-world edge cases.

### Why Python-Only UI is Insufficient

**Current State:** Python (Streamlit) handles both UI and ML
**Problem:** 
- Streamlit is server-rendered, not suitable for real-time WebRTC
- No native WebRTC support (requires complex workarounds)
- Poor mobile experience
- Limited UI customization
- Not scalable for production video calls

**Solution:** React frontend + Python backend separation

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT (React)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Pre-Join    │  │  Video Call  │  │ Accessibility│     │
│  │  Lobby       │→ │  UI          │  │ Overlay      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│                            │                                │
└────────────────────────────┼────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │   WebSocket     │
                    │   + REST API    │
                    └────────┬────────┘
                             │
┌────────────────────────────┼────────────────────────────────┐
│                  BACKEND (Python/FastAPI)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Signaling   │  │  ML Pipeline │  │  Caption     │     │
│  │  Server      │  │  (MediaPipe) │  │  Sync        │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```



### Component Responsibilities

#### React Frontend (Client)
- **WebRTC Management:** Peer connections, media streams, ICE candidates
- **UI Rendering:** Real-time video grid, controls, captions overlay
- **User Input:** Camera/mic permissions, room joining, settings
- **Frame Capture:** Extract frames from video stream for ML processing
- **Caption Display:** Smooth animations, high-contrast overlays
- **Offline Handling:** Graceful degradation when backend unavailable

#### Python Backend (Server)
- **ML Inference:** MediaPipe hand detection, gesture classification
- **Signaling:** WebRTC offer/answer/ICE exchange
- **Caption Sync:** Broadcast captions to all participants
- **Room Management:** Create/join/leave room logic
- **Data Storage:** Caption history, user corrections
- **Model Updates:** Incremental learning from corrections

---

## Core Requirements Implementation

### 1. Pre-Join Lobby (MANDATORY)

**React Component:** `PreJoinLobby.tsx`

```typescript
interface PreJoinState {
  roomCode: string;
  cameraEnabled: boolean;
  micEnabled: boolean;
  accessibilityMode: boolean;
  cameraPreview: MediaStream | null;
}

// User flow:
// 1. Enter room code OR click "Create Room"
// 2. Optional: Toggle camera preview
// 3. Toggle mic/accessibility mode
// 4. Explicit "Join Meeting" button
```

**Key Features:**
- Camera NEVER auto-starts
- Preview is optional toggle
- Clear "Join Meeting" CTA
- Validate room code before joining
- Show error states (invalid room, room full)



### 2. Room System

**Backend API Endpoints:**

```python
# Room Management
POST   /api/rooms/create          # Create new room
GET    /api/rooms/{code}/validate # Check if room exists
POST   /api/rooms/{code}/join     # Join room (returns WebSocket URL)
DELETE /api/rooms/{code}/leave    # Leave room
GET    /api/rooms/{code}/info     # Get room info (participants, status)

# Room States
- WAITING: Room created, no participants
- ACTIVE: At least one participant
- FULL: Max participants reached
- ENDED: Host ended meeting
```

**Room Code Generation:**
- 6-8 alphanumeric characters
- Collision-resistant (check existing codes)
- Human-readable (avoid ambiguous chars: 0/O, 1/I)

**Edge Cases Handled:**
- Invalid room code → Show error, stay in lobby
- Room full → Show "Room is full" message
- Host ended meeting → Graceful disconnect, show message
- Network disconnect → Auto-reconnect with exponential backoff

### 3. Video Call UI (Google Meet Style)

**React Component Structure:**

```
VideoCallUI/
├── VideoGrid.tsx          # Central 16:9 video grid
├── ControlBar.tsx         # Bottom controls
├── StatusBar.tsx          # Top status (FPS, detection state)
├── CaptionOverlay.tsx     # Live captions over video
└── SettingsPanel.tsx      # Side panel for settings
```

**Layout Specifications:**

```css
/* Central Video Grid */
.video-grid {
  aspect-ratio: 16/9;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 8px;
  background: #202124;
}

/* Bottom Control Bar */
.control-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 80px;
  background: rgba(32, 33, 36, 0.95);
  backdrop-filter: blur(10px);
}

/* Caption Overlay */
.caption-overlay {
  position: absolute;
  bottom: 100px; /* Above control bar */
  left: 50%;
  transform: translateX(-50%);
  max-width: 80%;
  background: rgba(0, 0, 0, 0.9);
  padding: 16px 24px;
  border-radius: 8px;
  font-size: 24px; /* Large for accessibility */
  color: #ffffff;
  text-align: center;
}
```

**Control Bar Buttons:**
1. **Mic** - Toggle microphone (red when muted)
2. **Camera** - Toggle camera (red when off)
3. **Accessibility Mode** - Toggle sign language recognition
4. **Pause Gestures** - Pause gesture detection
5. **Clear Captions** - Clear caption history
6. **Settings** - Open settings panel
7. **Leave** - End call (red, confirmation dialog)



### 4. Accessibility Features (CORE VALUE)

**Caption Display Requirements:**

```typescript
interface CaptionStyle {
  fontSize: '24px' | '32px' | '40px';  // User configurable
  fontFamily: 'Arial, sans-serif';      // High readability
  backgroundColor: 'rgba(0, 0, 0, 0.9)'; // High contrast
  color: '#ffffff';                      // WCAG AAA compliant
  textShadow: '0 2px 4px rgba(0, 0, 0, 0.8)'; // Readability
  lineHeight: 1.4;                       // Comfortable reading
  maxWidth: '80%';                       // Don't cover video
}

interface Caption {
  text: string;
  confidence: number;
  timestamp: number;
  userId: string;
  isConfirmed: boolean;
}
```

**Gesture-Based Controls:**

```typescript
enum GestureControl {
  CONFIRM = 'fist',           // Confirm current caption
  UNDO = 'two_fingers',       // Undo last word
  PAUSE = 'open_palm',        // Pause recognition
}

// Gesture detection requirements:
// - Minimum hold: 8 frames (~0.3s at 25 FPS)
// - Cooldown: 15 frames (~0.6s) between triggers
// - Visual feedback: Show gesture icon when detected
```

**Text-to-Speech Integration:**

```typescript
// Use Web Speech API (browser native)
const speak = (text: string) => {
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = userSettings.ttsSpeed; // 0.5 - 2.0
  utterance.pitch = 1.0;
  utterance.volume = 1.0;
  speechSynthesis.speak(utterance);
};

// Auto-speak on confirm (user configurable)
if (userSettings.autoSpeak && caption.isConfirmed) {
  speak(caption.text);
}
```

**Keyboard Navigation:**

```typescript
// All controls accessible via keyboard
const keyboardShortcuts = {
  'Alt+M': 'Toggle Mic',
  'Alt+C': 'Toggle Camera',
  'Alt+A': 'Toggle Accessibility Mode',
  'Alt+P': 'Pause Gestures',
  'Alt+S': 'Speak Captions',
  'Alt+L': 'Leave Call',
  'Escape': 'Close Settings',
};

// Focus indicators: 2px solid outline
// Tab order: Logical flow through controls
```



### 5. ML / Backend (Python)

**API Contract:**

```python
# Frame Processing Endpoint
POST /api/ml/process-frame
Request:
{
  "frame": "base64_encoded_image",
  "user_id": "user_123",
  "session_id": "room_abc",
  "timestamp": 1708012800.123
}

Response:
{
  "success": true,
  "hand_detected": true,
  "landmarks": [[x1, y1, z1], ...],  # 21 landmarks
  "gesture": "HELLO",
  "confidence": 0.91,
  "caption": "Hello everyone",
  "movement_state": "stable",
  "processing_time_ms": 45.2
}

# Error Response
{
  "success": false,
  "error": "MediaPipe initialization failed",
  "fallback_mode": "text_only",
  "processing_time_ms": 2.1
}
```

**ML Pipeline Architecture:**

```python
class MLPipeline:
    def __init__(self):
        self.hand_detector = MediaPipeHands()
        self.gesture_classifier = GestureClassifier()
        self.movement_tracker = MovementTracker()
        self.smoothing_buffer = SmoothingBuffer(window=5)
    
    async def process_frame(self, frame: np.ndarray) -> MLResult:
        try:
            # 1. Hand Detection (MediaPipe)
            detection = await self.hand_detector.detect(frame)
            if not detection.success:
                return MLResult(success=False, error=detection.error)
            
            # 2. Movement Tracking
            movement = self.movement_tracker.update(detection.landmarks)
            if movement.state not in ['stable', 'idle']:
                return MLResult(success=True, hand_detected=True, 
                               gesture='none', caption='')
            
            # 3. Gesture Classification
            gesture = await self.gesture_classifier.predict(
                detection.landmarks,
                confidence_threshold=0.58
            )
            
            # 4. Smoothing
            smoothed = self.smoothing_buffer.add(gesture)
            
            return MLResult(
                success=True,
                hand_detected=True,
                landmarks=detection.landmarks,
                gesture=smoothed.label,
                confidence=smoothed.confidence,
                caption=smoothed.text,
                movement_state=movement.state
            )
        
        except Exception as e:
            logger.error(f"ML pipeline error: {e}")
            return MLResult(success=False, error=str(e))
```

**Graceful Degradation:**

```python
# If ML model fails to load
if not model_loaded:
    return {
        "success": True,
        "fallback_mode": "heuristic",
        "caption": "Model unavailable - using basic detection",
        "confidence": 0.0
    }

# If MediaPipe fails
if mediapipe_error:
    return {
        "success": True,
        "fallback_mode": "text_only",
        "caption": "Hand detection unavailable",
        "confidence": 0.0
    }

# Never crash - always return structured response
```



### 6. Frontend (React) - WebRTC Implementation

**Frame Capture Strategy:**

```typescript
class FrameCaptureManager {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private targetFPS: number = 10; // Reduced FPS for ML processing
  private lastCaptureTime: number = 0;
  
  captureFrame(videoElement: HTMLVideoElement): string | null {
    const now = Date.now();
    const interval = 1000 / this.targetFPS;
    
    // Throttle frame capture
    if (now - this.lastCaptureTime < interval) {
      return null;
    }
    
    this.lastCaptureTime = now;
    
    // Resize to 640x480 for ML processing (reduce bandwidth)
    this.canvas.width = 640;
    this.canvas.height = 480;
    this.ctx.drawImage(videoElement, 0, 0, 640, 480);
    
    // Convert to base64 JPEG (smaller than PNG)
    return this.canvas.toDataURL('image/jpeg', 0.8);
  }
  
  async sendToBackend(frame: string): Promise<MLResult> {
    try {
      const response = await fetch('/api/ml/process-frame', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          frame,
          user_id: this.userId,
          session_id: this.sessionId,
          timestamp: Date.now() / 1000
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('ML processing failed:', error);
      // Don't block UI - return fallback
      return {
        success: false,
        error: error.message,
        fallback_mode: 'text_only'
      };
    }
  }
}
```

**WebRTC Video Stream Management:**

```typescript
class VideoStreamManager {
  private peerConnection: RTCPeerConnection;
  private localStream: MediaStream | null = null;
  
  async initializeLocalStream(constraints: MediaStreamConstraints): Promise<void> {
    try {
      this.localStream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          frameRate: { ideal: 25, max: 30 }
        },
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      
      // Add tracks to peer connection
      this.localStream.getTracks().forEach(track => {
        this.peerConnection.addTrack(track, this.localStream!);
      });
      
    } catch (error) {
      if (error.name === 'NotAllowedError') {
        throw new Error('Camera permission denied');
      } else if (error.name === 'NotFoundError') {
        throw new Error('No camera found');
      } else {
        throw new Error(`Camera error: ${error.message}`);
      }
    }
  }
  
  stopLocalStream(): void {
    if (this.localStream) {
      this.localStream.getTracks().forEach(track => track.stop());
      this.localStream = null;
    }
  }
}
```

**Caption Overlay Component:**

```typescript
const CaptionOverlay: React.FC<CaptionProps> = ({ caption, confidence }) => {
  const [visible, setVisible] = useState(false);
  
  useEffect(() => {
    if (caption) {
      setVisible(true);
    }
  }, [caption]);
  
  return (
    <div 
      className={`caption-overlay ${visible ? 'fade-in' : ''}`}
      role="status"
      aria-live="polite"
      aria-atomic="true"
    >
      <span className="caption-text">{caption}</span>
      {confidence > 0 && (
        <span className="caption-confidence">
          {Math.round(confidence * 100)}% confident
        </span>
      )}
    </div>
  );
};
```



---

## Edge Cases Handling

### Camera / Media

**Permission Denied:**
```typescript
try {
  await navigator.mediaDevices.getUserMedia({ video: true });
} catch (error) {
  if (error.name === 'NotAllowedError') {
    showError({
      title: 'Camera Permission Required',
      message: 'Please allow camera access in your browser settings.',
      action: 'Open Settings',
      actionUrl: 'chrome://settings/content/camera'
    });
  }
}
```

**Camera In Use:**
```typescript
// Detect if camera is already in use
if (error.name === 'NotReadableError') {
  showError({
    title: 'Camera Already In Use',
    message: 'Close other apps using your camera and try again.',
    action: 'Retry'
  });
}
```

**Camera Disconnected Mid-Call:**
```typescript
videoTrack.addEventListener('ended', () => {
  showNotification({
    type: 'warning',
    message: 'Camera disconnected. Reconnecting...',
    duration: 3000
  });
  
  // Attempt reconnection
  setTimeout(() => reconnectCamera(), 1000);
});
```

**Slow Device:**
```typescript
// Monitor FPS and adapt
if (averageFPS < 10) {
  // Reduce ML processing rate
  frameCaptureManager.setTargetFPS(5);
  
  // Reduce video quality
  videoTrack.applyConstraints({
    width: 640,
    height: 480,
    frameRate: 15
  });
  
  showNotification({
    type: 'info',
    message: 'Performance mode enabled for your device',
    duration: 5000
  });
}
```

### Backend

**ML Model Fails to Load:**
```python
try:
    model = load_model('gesture_classifier.pth')
except Exception as e:
    logger.error(f"Model load failed: {e}")
    model = None  # Use heuristic fallback
    
# Always return valid response
if model is None:
    return {
        "success": True,
        "fallback_mode": "heuristic",
        "caption": gesture_heuristic(landmarks),
        "confidence": 0.5
    }
```

**MediaPipe Missing:**
```python
try:
    import mediapipe as mp
except ImportError:
    logger.error("MediaPipe not installed")
    # Fallback to text-only mode
    return {
        "success": True,
        "fallback_mode": "text_only",
        "error": "Hand detection unavailable"
    }
```

**Latency Spikes:**
```python
# Timeout for ML processing
async def process_with_timeout(frame, timeout=0.1):
    try:
        return await asyncio.wait_for(
            ml_pipeline.process(frame),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.warning("ML processing timeout")
        return {
            "success": True,
            "skipped": True,
            "reason": "timeout"
        }
```

**Partial Response:**
```python
# Always validate response structure
def validate_ml_response(response: dict) -> MLResult:
    required_fields = ['success', 'hand_detected']
    
    for field in required_fields:
        if field not in response:
            logger.error(f"Missing field: {field}")
            return MLResult(
                success=False,
                error=f"Invalid response: missing {field}"
            )
    
    return MLResult(**response)
```



### UX

**Joining Without Camera:**
```typescript
// Allow joining with camera off
const joinMeeting = async (cameraEnabled: boolean) => {
  if (!cameraEnabled) {
    showNotification({
      type: 'info',
      message: 'You joined without camera. Enable it anytime from controls.',
      duration: 5000
    });
  }
  
  await connectToRoom(roomCode, { video: cameraEnabled, audio: true });
};
```

**Accessibility Mode ON with No Gestures:**
```typescript
// Show helpful message
if (accessibilityMode && !handDetected && timeSinceEnable > 10000) {
  showHelpTooltip({
    message: 'No hand detected. Position your hand in frame for sign language recognition.',
    position: 'center',
    dismissible: true
  });
}
```

**Switching Accessibility Mid-Call:**
```typescript
const toggleAccessibilityMode = async (enabled: boolean) => {
  setAccessibilityMode(enabled);
  
  if (enabled) {
    // Start ML processing
    frameCaptureManager.start();
    showNotification({
      type: 'success',
      message: 'Accessibility mode enabled. Your signs will be translated to text.',
      duration: 3000
    });
  } else {
    // Stop ML processing
    frameCaptureManager.stop();
    showNotification({
      type: 'info',
      message: 'Accessibility mode disabled.',
      duration: 2000
    });
  }
};
```

**Leaving and Rejoining Same Room:**
```typescript
// Preserve room state
const leaveRoom = async (saveState: boolean = true) => {
  if (saveState) {
    localStorage.setItem('lastRoomCode', roomCode);
    localStorage.setItem('lastSettings', JSON.stringify(userSettings));
  }
  
  await peerConnection.close();
  stopLocalStream();
};

const rejoinLastRoom = async () => {
  const lastRoomCode = localStorage.getItem('lastRoomCode');
  const lastSettings = JSON.parse(localStorage.getItem('lastSettings') || '{}');
  
  if (lastRoomCode) {
    await joinRoom(lastRoomCode, lastSettings);
  }
};
```

### Performance

**Cap FPS:**
```typescript
// Adaptive FPS based on device performance
class AdaptiveFPSManager {
  private targetFPS: number = 25;
  private minFPS: number = 10;
  private maxFPS: number = 30;
  
  adjustFPS(currentFPS: number, cpuUsage: number): void {
    if (cpuUsage > 80 || currentFPS < this.minFPS) {
      this.targetFPS = Math.max(this.minFPS, this.targetFPS - 5);
    } else if (cpuUsage < 50 && currentFPS >= this.targetFPS) {
      this.targetFPS = Math.min(this.maxFPS, this.targetFPS + 5);
    }
  }
}
```

**Drop Frames Gracefully:**
```typescript
// Skip ML processing if queue is backed up
class FrameQueue {
  private queue: Frame[] = [];
  private maxQueueSize: number = 3;
  
  enqueue(frame: Frame): boolean {
    if (this.queue.length >= this.maxQueueSize) {
      // Drop oldest frame
      this.queue.shift();
      console.warn('Frame dropped due to processing backlog');
    }
    
    this.queue.push(frame);
    return true;
  }
}
```

**Mobile Fallback (Text-Only):**
```typescript
// Detect mobile device
const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

if (isMobile) {
  showNotification({
    type: 'info',
    message: 'Mobile detected. Gesture recognition may be limited. Consider using desktop for best experience.',
    duration: 8000
  });
  
  // Reduce ML processing rate
  frameCaptureManager.setTargetFPS(5);
  
  // Offer text-only mode
  if (confirm('Enable text-only mode for better performance?')) {
    setAccessibilityMode(false);
  }
}
```



---

## Folder Structure

### React Frontend

```
frontend/
├── public/
│   ├── index.html
│   └── manifest.json
├── src/
│   ├── components/
│   │   ├── PreJoinLobby/
│   │   │   ├── PreJoinLobby.tsx
│   │   │   ├── RoomCodeInput.tsx
│   │   │   ├── CameraPreview.tsx
│   │   │   └── PreJoinControls.tsx
│   │   ├── VideoCall/
│   │   │   ├── VideoCallUI.tsx
│   │   │   ├── VideoGrid.tsx
│   │   │   ├── VideoTile.tsx
│   │   │   ├── ControlBar.tsx
│   │   │   ├── StatusBar.tsx
│   │   │   └── SettingsPanel.tsx
│   │   ├── Accessibility/
│   │   │   ├── CaptionOverlay.tsx
│   │   │   ├── GestureIndicator.tsx
│   │   │   └── AccessibilityControls.tsx
│   │   └── Common/
│   │       ├── Button.tsx
│   │       ├── Modal.tsx
│   │       └── Notification.tsx
│   ├── services/
│   │   ├── webrtc/
│   │   │   ├── PeerConnectionManager.ts
│   │   │   ├── SignalingClient.ts
│   │   │   └── MediaStreamManager.ts
│   │   ├── ml/
│   │   │   ├── FrameCaptureManager.ts
│   │   │   ├── MLClient.ts
│   │   │   └── CaptionManager.ts
│   │   └── api/
│   │       ├── roomApi.ts
│   │       ├── captionApi.ts
│   │       └── wsClient.ts
│   ├── hooks/
│   │   ├── useWebRTC.ts
│   │   ├── useAccessibility.ts
│   │   ├── useMediaDevices.ts
│   │   └── useKeyboardShortcuts.ts
│   ├── contexts/
│   │   ├── RoomContext.tsx
│   │   ├── UserContext.tsx
│   │   └── AccessibilityContext.tsx
│   ├── utils/
│   │   ├── errorHandling.ts
│   │   ├── validation.ts
│   │   └── constants.ts
│   ├── styles/
│   │   ├── global.css
│   │   ├── meet-theme.css
│   │   └── accessibility.css
│   ├── App.tsx
│   └── index.tsx
├── package.json
├── tsconfig.json
└── README.md
```

### Python Backend

```
backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── rooms.py          # Room management endpoints
│   │   ├── ml.py             # ML processing endpoints
│   │   ├── captions.py       # Caption sync endpoints
│   │   └── websocket.py      # WebSocket handlers
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── hand_detector.py  # MediaPipe wrapper
│   │   ├── gesture_classifier.py
│   │   ├── movement_tracker.py
│   │   ├── smoothing.py
│   │   └── model_loader.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── room_manager.py
│   │   ├── caption_sync.py
│   │   └── connection_manager.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── room.py
│   │   ├── caption.py
│   │   └── user.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── error_handling.py
│   │   ├── validation.py
│   │   └── logging_config.py
│   ├── config.py
│   └── main.py
├── ml_models/
│   ├── gesture_classifier.pth
│   ├── landmark_classifier.pkl
│   └── model_metadata.json
├── tests/
│   ├── test_api.py
│   ├── test_ml_pipeline.py
│   ├── test_room_manager.py
│   └── test_websocket.py
├── requirements.txt
├── Dockerfile
└── README.md
```



---

## Room Join Flow (Step-by-Step)

### User Journey

```
1. LANDING PAGE
   ↓
   User sees two options:
   - [Create Room] button
   - [Join Room] input + button
   
2. CREATE ROOM PATH
   ↓
   Click "Create Room"
   ↓
   Backend generates unique room code (e.g., "ABC-123")
   ↓
   Navigate to Pre-Join Lobby with room code
   
3. JOIN ROOM PATH
   ↓
   Enter room code in input
   ↓
   Click "Join Room"
   ↓
   Validate room code with backend
   ↓
   If valid: Navigate to Pre-Join Lobby
   If invalid: Show error "Room not found"
   
4. PRE-JOIN LOBBY
   ↓
   Display:
   - Room code (with copy button)
   - Camera preview (OFF by default)
   - [Toggle Camera Preview] button
   - [Toggle Mic] button (ON by default)
   - [Toggle Accessibility Mode] checkbox
   - [Join Meeting] button (primary CTA)
   
   User actions:
   - Optional: Enable camera preview
   - Optional: Toggle mic
   - Optional: Enable accessibility mode
   - Required: Click "Join Meeting"
   
5. JOINING MEETING
   ↓
   Show loading state: "Connecting..."
   ↓
   Request camera/mic permissions (if enabled)
   ↓
   If permission denied:
     - Show error message
     - Offer to join without camera/mic
     - Stay in Pre-Join Lobby
   ↓
   If permission granted:
     - Initialize WebRTC connection
     - Connect to signaling server
     - Exchange ICE candidates
   ↓
   If connection fails:
     - Show error message
     - Offer retry
     - Stay in Pre-Join Lobby
   
6. IN MEETING
   ↓
   Display Video Call UI:
   - Central video grid (16:9)
   - Bottom control bar
   - Top status bar
   - Caption overlay (if accessibility mode)
   
   User can:
   - Toggle camera/mic anytime
   - Enable/disable accessibility mode
   - View live captions
   - Use gesture controls
   - Leave meeting
```

### Technical Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    1. LANDING PAGE                          │
│  ┌──────────────┐              ┌──────────────┐            │
│  │ Create Room  │              │  Join Room   │            │
│  └──────┬───────┘              └──────┬───────┘            │
└─────────┼──────────────────────────────┼───────────────────┘
          │                              │
          │ POST /api/rooms/create       │ GET /api/rooms/{code}/validate
          ↓                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    2. BACKEND                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Room Manager                                        │  │
│  │  - Generate unique code                              │  │
│  │  - Create room record                                │  │
│  │  - Return room code                                  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────┬───────────────────────────────────┬───────────────┘
          │                                   │
          │ Return: { room_code: "ABC-123" }  │ Return: { valid: true }
          ↓                                   ↓
┌─────────────────────────────────────────────────────────────┐
│                 3. PRE-JOIN LOBBY                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Room Code: ABC-123 [Copy]                           │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────┐    │  │
│  │  │  Camera Preview (OFF)                       │    │  │
│  │  │  [Click to enable preview]                  │    │  │
│  │  └─────────────────────────────────────────────┘    │  │
│  │                                                       │  │
│  │  [🎤 Mic: ON]  [📹 Camera: OFF]                     │  │
│  │  [☑ Accessibility Mode]                              │  │
│  │                                                       │  │
│  │  [Join Meeting] ← PRIMARY CTA                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────┬───────────────────────────────────────────────────┘
          │
          │ Click "Join Meeting"
          ↓
┌─────────────────────────────────────────────────────────────┐
│              4. PERMISSION REQUEST                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Browser: "Allow camera and microphone?"            │  │
│  │  [Block] [Allow]                                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────┬───────────────────────────────────────────────────┘
          │
          │ If ALLOW
          ↓
┌─────────────────────────────────────────────────────────────┐
│              5. WEBRTC CONNECTION                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. Connect to signaling server (WebSocket)         │  │
│  │  2. Create RTCPeerConnection                        │  │
│  │  3. Add local media tracks                          │  │
│  │  4. Exchange SDP offer/answer                       │  │
│  │  5. Exchange ICE candidates                         │  │
│  │  6. Establish peer connection                       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────┬───────────────────────────────────────────────────┘
          │
          │ Connection established
          ↓
┌─────────────────────────────────────────────────────────────┐
│                 6. VIDEO CALL UI                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Status: 🟢 Connected | 25 FPS | ✋ Hand Detected   │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────┐    │  │
│  │  │                                             │    │  │
│  │  │         VIDEO GRID (16:9)                   │    │  │
│  │  │                                             │    │  │
│  │  └─────────────────────────────────────────────┘    │  │
│  │                                                       │  │
│  │  Caption: "Hello everyone" (91% confident)           │  │
│  │                                                       │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │  [🎤] [📹] [🧏] [⏸] [🗑] [⚙] [📞]                  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```



---

## Why Python-Only UI is Insufficient

### Current Limitations (Streamlit)

1. **No Native WebRTC Support**
   - Streamlit is server-rendered, not client-side
   - WebRTC requires client-side peer connections
   - Workarounds are complex and unreliable

2. **Poor Real-Time Performance**
   - Streamlit reruns entire script on state change
   - High latency for real-time video updates
   - Not suitable for <100ms latency requirements

3. **Limited UI Customization**
   - Cannot achieve Google Meet-style UI
   - Limited control over layout and styling
   - No smooth animations or transitions

4. **No Mobile Support**
   - Streamlit UI not optimized for mobile
   - Touch interactions limited
   - Responsive design difficult

5. **Scalability Issues**
   - Each user requires server-side session
   - High server resource usage
   - Not suitable for 100+ concurrent users

6. **No Offline Capability**
   - Requires constant server connection
   - Cannot cache UI for offline use
   - Poor network resilience

### React Advantages

1. **Native WebRTC Support**
   - Direct access to browser WebRTC APIs
   - Client-side peer connections
   - Low latency, high performance

2. **Real-Time UI Updates**
   - React state management for instant updates
   - Virtual DOM for efficient rendering
   - Smooth 60 FPS animations

3. **Full UI Control**
   - CSS-in-JS for custom styling
   - Component libraries (Material-UI, Ant Design)
   - Pixel-perfect Google Meet clone

4. **Mobile-First Design**
   - Responsive by default
   - Touch gesture support
   - Progressive Web App (PWA) capability

5. **Scalability**
   - Client-side rendering reduces server load
   - CDN distribution for static assets
   - Supports thousands of concurrent users

6. **Offline-First**
   - Service workers for offline caching
   - Local state management
   - Graceful degradation

### Hybrid Architecture Benefits

**React Frontend:**
- Handles all UI rendering
- Manages WebRTC connections
- Captures and displays video
- Provides smooth user experience

**Python Backend:**
- Focuses on ML processing
- Handles complex computations
- Manages data persistence
- Provides REST/WebSocket APIs

**Result:**
- Best of both worlds
- Clear separation of concerns
- Scalable and maintainable
- Production-ready architecture



---

## Minimal Viable Demo Plan

### Phase 1: Core Infrastructure (Week 1-2)

**Backend Setup:**
- [ ] FastAPI server with WebSocket support
- [ ] Room management API (create, join, validate)
- [ ] ML processing endpoint (frame → caption)
- [ ] Basic error handling and logging

**Frontend Setup:**
- [ ] React app with TypeScript
- [ ] Routing (landing, lobby, call)
- [ ] Basic component structure
- [ ] WebSocket client

**Deliverable:** Backend and frontend can communicate

### Phase 2: Pre-Join Lobby (Week 2-3)

**Features:**
- [ ] Landing page with create/join options
- [ ] Room code generation and validation
- [ ] Pre-join lobby UI
- [ ] Camera preview toggle
- [ ] Mic/accessibility toggles
- [ ] Permission handling

**Deliverable:** Users can create/join rooms and configure settings

### Phase 3: WebRTC Video Call (Week 3-4)

**Features:**
- [ ] WebRTC peer connection setup
- [ ] Local/remote video streams
- [ ] Video grid layout (16:9)
- [ ] Basic control bar (mic, camera, leave)
- [ ] Connection state management

**Deliverable:** Basic video call works between 2 users

### Phase 4: ML Integration (Week 4-5)

**Features:**
- [ ] Frame capture from video stream
- [ ] Send frames to backend for processing
- [ ] MediaPipe hand detection
- [ ] Gesture classification
- [ ] Caption generation

**Deliverable:** Hand gestures detected and classified

### Phase 5: Accessibility Features (Week 5-6)

**Features:**
- [ ] Caption overlay on video
- [ ] High-contrast, large text
- [ ] Text-to-speech integration
- [ ] Gesture controls (confirm, undo, pause)
- [ ] Keyboard shortcuts
- [ ] Screen reader support

**Deliverable:** Full accessibility mode functional

### Phase 6: Polish & Edge Cases (Week 6-7)

**Features:**
- [ ] Error handling for all edge cases
- [ ] Loading states and animations
- [ ] Performance optimization
- [ ] Mobile responsive design
- [ ] Comprehensive testing

**Deliverable:** Production-ready demo

### Phase 7: Documentation (Week 7-8)

**Deliverables:**
- [ ] User guide
- [ ] API documentation
- [ ] Deployment guide
- [ ] Demo video
- [ ] Presentation slides



---

## API Contract Between React and Python

### REST API Endpoints

#### Room Management

```typescript
// Create Room
POST /api/rooms/create
Request: {
  host_user_id: string;
  accessibility_mode: boolean;
  max_participants?: number;
}
Response: {
  room_code: string;
  room_id: string;
  created_at: number;
  websocket_url: string;
}

// Validate Room
GET /api/rooms/{room_code}/validate
Response: {
  valid: boolean;
  room_id: string;
  participants_count: number;
  is_full: boolean;
  accessibility_mode: boolean;
}

// Join Room
POST /api/rooms/{room_code}/join
Request: {
  user_id: string;
  user_name: string;
}
Response: {
  success: boolean;
  room_id: string;
  websocket_url: string;
  existing_participants: Array<{
    user_id: string;
    user_name: string;
  }>;
}

// Leave Room
DELETE /api/rooms/{room_code}/leave
Request: {
  user_id: string;
}
Response: {
  success: boolean;
}
```

#### ML Processing

```typescript
// Process Frame
POST /api/ml/process-frame
Request: {
  frame: string;              // base64 encoded JPEG
  user_id: string;
  session_id: string;
  timestamp: number;
  sequence_id?: number;       // For tracking frame order
}
Response: {
  success: boolean;
  hand_detected: boolean;
  landmarks?: Array<[number, number, number]>;  // 21 landmarks
  gesture: string;            // "HELLO", "YES", "none", etc.
  confidence: number;         // 0.0 - 1.0
  caption: string;            // Translated text
  movement_state: string;     // "stable", "moving", "idle"
  processing_time_ms: number;
  error?: string;
  fallback_mode?: string;     // "heuristic", "text_only"
}

// Get Model Info
GET /api/ml/model-info
Response: {
  model_loaded: boolean;
  model_version: string;
  supported_gestures: string[];
  sequence_length: number;
  min_confidence: number;
}
```

#### Caption Management

```typescript
// Store Caption
POST /api/captions/store
Request: {
  session_id: string;
  user_id: string;
  text: string;
  confidence: number;
  timestamp: number;
  is_confirmed: boolean;
}
Response: {
  success: boolean;
  caption_id: string;
}

// Get Caption History
GET /api/captions/{session_id}?limit=50
Response: {
  captions: Array<{
    caption_id: string;
    user_id: string;
    text: string;
    confidence: number;
    timestamp: number;
    is_confirmed: boolean;
  }>;
}

// Submit Correction
POST /api/captions/correct
Request: {
  caption_id: string;
  original_text: string;
  corrected_text: string;
  user_id: string;
}
Response: {
  success: boolean;
  queued_for_training: boolean;
}
```

### WebSocket Protocol

```typescript
// Connection
ws://backend-url/ws/{session_id}/{user_id}

// Message Types (Client → Server)
{
  type: "caption",
  data: {
    text: string;
    confidence: number;
    timestamp: number;
    is_confirmed: boolean;
  }
}

{
  type: "webrtc_signal",
  target_user: string,
  data: {
    type: "offer" | "answer" | "ice-candidate";
    sdp?: string;
    candidate?: RTCIceCandidate;
  }
}

{
  type: "status",
  data: {
    camera_enabled: boolean;
    mic_enabled: boolean;
    accessibility_mode: boolean;
  }
}

// Message Types (Server → Client)
{
  type: "caption",
  data: {
    user_id: string;
    text: string;
    confidence: number;
    timestamp: number;
  }
}

{
  type: "user_joined",
  user_id: string;
  user_name: string;
  timestamp: number;
}

{
  type: "user_left",
  user_id: string;
  timestamp: number;
}

{
  type: "webrtc_signal",
  from_user: string;
  data: {
    type: "offer" | "answer" | "ice-candidate";
    sdp?: string;
    candidate?: RTCIceCandidate;
  }
}

{
  type: "error",
  error: string;
  code: string;
}
```

### Error Codes

```typescript
enum ErrorCode {
  // Room Errors
  ROOM_NOT_FOUND = "ROOM_001",
  ROOM_FULL = "ROOM_002",
  INVALID_ROOM_CODE = "ROOM_003",
  
  // ML Errors
  ML_MODEL_NOT_LOADED = "ML_001",
  ML_PROCESSING_FAILED = "ML_002",
  ML_TIMEOUT = "ML_003",
  MEDIAPIPE_ERROR = "ML_004",
  
  // Media Errors
  CAMERA_PERMISSION_DENIED = "MEDIA_001",
  CAMERA_NOT_FOUND = "MEDIA_002",
  CAMERA_IN_USE = "MEDIA_003",
  
  // Network Errors
  WEBSOCKET_DISCONNECTED = "NET_001",
  WEBRTC_CONNECTION_FAILED = "NET_002",
  API_TIMEOUT = "NET_003",
}
```



---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER BROWSER (React)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                        PRE-JOIN LOBBY                                 │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │ │
│  │  │ Room Code   │  │  Camera     │  │ Accessibility│                  │ │
│  │  │ Input       │  │  Preview    │  │ Toggle      │                  │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │ │
│  │                    [Join Meeting Button]                              │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                    │                                        │
│                                    ↓ User clicks "Join"                    │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                        VIDEO CALL UI                                  │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │ │
│  │  │  Status Bar: FPS | Hand Detection | Accessibility Badge        │ │ │
│  │  └─────────────────────────────────────────────────────────────────┘ │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │ │
│  │  │                                                                 │ │ │
│  │  │                    VIDEO GRID (16:9)                            │ │ │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │ │ │
│  │  │  │ User 1   │  │ User 2   │  │ User 3   │                     │ │ │
│  │  │  │ Video    │  │ Video    │  │ Video    │                     │ │ │
│  │  │  └──────────┘  └──────────┘  └──────────┘                     │ │ │
│  │  │                                                                 │ │ │
│  │  │  Caption Overlay: "Hello everyone" (91% confident)             │ │ │
│  │  └─────────────────────────────────────────────────────────────────┘ │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │ │
│  │  │  Control Bar: [🎤] [📹] [🧏] [⏸] [🗑] [⚙] [📞]              │ │ │
│  │  └─────────────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                      CLIENT-SIDE SERVICES                             │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │ │
│  │  │   WebRTC     │  │    Frame     │  │   Caption    │               │ │
│  │  │   Manager    │  │   Capture    │  │   Manager    │               │ │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │ │
│  └─────────┼──────────────────┼──────────────────┼─────────────────────┘ │
└────────────┼──────────────────┼──────────────────┼───────────────────────┘
             │                  │                  │
             │ Peer-to-Peer     │ HTTP POST        │ WebSocket
             │ (Video/Audio)    │ (Frames)         │ (Captions)
             │                  │                  │
┌────────────┼──────────────────┼──────────────────┼───────────────────────┐
│            │                  ↓                  ↓                       │
│  ┌─────────┼──────────────────────────────────────────────────────────┐ │
│  │         │              BACKEND SERVER (Python/FastAPI)             │ │
│  │         │                                                           │ │
│  │  ┌──────┴──────┐  ┌──────────────┐  ┌──────────────┐             │ │
│  │  │  Signaling  │  │  ML Pipeline │  │   Caption    │             │ │
│  │  │  Server     │  │              │  │   Sync       │             │ │
│  │  │             │  │  ┌────────┐  │  │              │             │ │
│  │  │ WebSocket   │  │  │MediaPipe│ │  │  WebSocket   │             │ │
│  │  │ Handler     │  │  │ Hands  │  │  │  Broadcast   │             │ │
│  │  │             │  │  └────┬───┘  │  │              │             │ │
│  │  │ - Offer/    │  │       │      │  │ - Sync to    │             │ │
│  │  │   Answer    │  │  ┌────▼───┐  │  │   all users  │             │ │
│  │  │ - ICE       │  │  │Gesture │  │  │ - History    │             │ │
│  │  │   Candidates│  │  │Classify│  │  │ - Corrections│             │ │
│  │  └─────────────┘  │  └────┬───┘  │  └──────────────┘             │ │
│  │                   │       │      │                                │ │
│  │                   │  ┌────▼───┐  │                                │ │
│  │                   │  │Caption │  │                                │ │
│  │                   │  │Generate│  │                                │ │
│  │                   │  └────────┘  │                                │ │
│  │                   └──────────────┘                                │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                      DATA LAYER                                   │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │ │
│  │  │   Rooms DB   │  │  Captions DB │  │  ML Models   │           │ │
│  │  │              │  │              │  │              │           │ │
│  │  │ - Room codes │  │ - History    │  │ - Gesture    │           │ │
│  │  │ - Participants│ │ - Corrections│  │   Classifier │           │ │
│  │  │ - Status     │  │ - Timestamps │  │ - Centroids  │           │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │ │
│  └───────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘

LEGEND:
─────  HTTP/REST API
═════  WebSocket
─ ─ ─  WebRTC Peer-to-Peer
```



---

## Technology Stack

### Frontend (React)

**Core:**
- React 18+ (with Hooks)
- TypeScript 5+
- Vite (build tool)

**WebRTC:**
- Native WebRTC APIs
- simple-peer (WebRTC wrapper)
- socket.io-client (signaling)

**UI/Styling:**
- Tailwind CSS (utility-first)
- Framer Motion (animations)
- Radix UI (accessible components)

**State Management:**
- React Context API
- Zustand (lightweight state)

**Testing:**
- Jest (unit tests)
- React Testing Library
- Playwright (E2E tests)

### Backend (Python)

**Core:**
- Python 3.10+
- FastAPI (async web framework)
- Uvicorn (ASGI server)

**ML/Computer Vision:**
- MediaPipe (hand detection)
- PyTorch (gesture classification)
- NumPy (numerical operations)
- OpenCV (image processing)

**WebSocket:**
- FastAPI WebSocket support
- python-socketio (alternative)

**Data Storage:**
- SQLite (development)
- PostgreSQL (production)
- Redis (caching, sessions)

**Testing:**
- pytest (unit tests)
- pytest-asyncio (async tests)
- httpx (API testing)

### Infrastructure

**Development:**
- Docker (containerization)
- Docker Compose (multi-container)

**Production:**
- Kubernetes (orchestration)
- Nginx (reverse proxy)
- Let's Encrypt (SSL/TLS)

**Monitoring:**
- Prometheus (metrics)
- Grafana (dashboards)
- Sentry (error tracking)

**CI/CD:**
- GitHub Actions
- Automated testing
- Deployment pipelines

---

## Security Considerations

### Authentication & Authorization

```typescript
// JWT-based authentication
interface AuthToken {
  user_id: string;
  room_id: string;
  permissions: string[];
  exp: number;  // Expiration timestamp
}

// Validate token on WebSocket connection
const validateToken = async (token: string): Promise<boolean> => {
  try {
    const decoded = jwt.verify(token, SECRET_KEY);
    return decoded.exp > Date.now() / 1000;
  } catch {
    return false;
  }
};
```

### Data Privacy

- **No PII in logs:** Sanitize all log messages
- **Encrypted connections:** HTTPS/WSS only
- **Local-first ML:** Process frames locally when possible
- **Minimal data retention:** Delete captions after 24 hours
- **User consent:** Explicit opt-in for data collection

### Rate Limiting

```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@app.post("/api/ml/process-frame")
@limiter.limit("30/minute")  # Max 30 frames per minute per user
async def process_frame(request: FrameRequest):
    # Process frame
    pass
```

### Input Validation

```python
from pydantic import BaseModel, validator

class FrameRequest(BaseModel):
    frame: str
    user_id: str
    session_id: str
    
    @validator('frame')
    def validate_frame(cls, v):
        # Check base64 format
        if not v.startswith('data:image/jpeg;base64,'):
            raise ValueError('Invalid frame format')
        
        # Check size (max 1MB)
        if len(v) > 1_000_000:
            raise ValueError('Frame too large')
        
        return v
```

---

## Performance Optimization

### Frontend

**Code Splitting:**
```typescript
// Lazy load components
const VideoCallUI = lazy(() => import('./components/VideoCall/VideoCallUI'));
const SettingsPanel = lazy(() => import('./components/SettingsPanel'));
```

**Memoization:**
```typescript
// Prevent unnecessary re-renders
const VideoTile = memo(({ stream, userId }: VideoTileProps) => {
  return <video srcObject={stream} autoPlay />;
});
```

**Debouncing:**
```typescript
// Debounce frame capture
const debouncedCapture = debounce(captureFrame, 100);
```

### Backend

**Async Processing:**
```python
# Process frames asynchronously
@app.post("/api/ml/process-frame")
async def process_frame(request: FrameRequest):
    result = await asyncio.create_task(
        ml_pipeline.process(request.frame)
    )
    return result
```

**Caching:**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_model():
    return load_model('gesture_classifier.pth')
```

**Connection Pooling:**
```python
# Database connection pool
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10
)
```

---

## Deployment Strategy

### Development Environment

```bash
# Frontend
cd frontend
npm install
npm run dev  # http://localhost:3000

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload  # http://localhost:8000
```

### Production Deployment

**Docker Compose:**
```yaml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    environment:
      - REACT_APP_API_URL=https://api.example.com
  
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://...
    volumes:
      - ./ml_models:/app/ml_models
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=accessibility_db
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

**Kubernetes (Production):**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: accessibility-backend:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

---

## Conclusion

This architecture provides a production-grade foundation for a sign language accessible video meeting system. Key principles:

1. **User Consent First:** No auto-start camera, explicit join flow
2. **Accessibility Core:** High contrast, large text, keyboard navigation
3. **Graceful Degradation:** Never crash, always provide fallback
4. **Separation of Concerns:** React for UI, Python for ML
5. **Real-World Ready:** Handles 60+ edge cases
6. **Scalable Design:** Supports 100+ concurrent users
7. **Privacy Focused:** Local-first, minimal data retention

This is not a demo—it's a foundation for real assistive technology.

