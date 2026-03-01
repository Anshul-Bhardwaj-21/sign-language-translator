# System Architecture Diagrams

## 1. High-Level System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         END USERS                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Desktop  │  │  Tablet  │  │  Mobile  │  │  Screen  │       │
│  │ Browser  │  │  Browser │  │  Browser │  │  Reader  │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
└───────┼─────────────┼─────────────┼─────────────┼──────────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                      │
                      │ HTTPS/WSS
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│                      CDN / LOAD BALANCER                        │
│                    (Nginx / CloudFlare)                         │
└─────────────────────┬───────────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ↓                           ↓
┌──────────────────┐      ┌──────────────────┐
│  REACT FRONTEND  │      │  PYTHON BACKEND  │
│  (Static Assets) │      │  (FastAPI)       │
│                  │      │                  │
│  - HTML/CSS/JS   │      │  - REST API      │
│  - WebRTC Logic  │      │  - WebSocket     │
│  - UI Components │      │  - ML Pipeline   │
└──────────────────┘      └────────┬─────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ↓              ↓              ↓
            ┌──────────┐   ┌──────────┐   ┌──────────┐
            │PostgreSQL│   │  Redis   │   │ML Models │
            │(Rooms/   │   │(Sessions)│   │(.pth/.pkl│
            │Captions) │   │          │   │ files)   │
            └──────────┘   └──────────┘   └──────────┘
```

## 2. Data Flow: Frame Processing Pipeline

```
USER CAMERA
    │
    │ 1. Capture video stream (25 FPS)
    ↓
┌─────────────────────────────────────┐
│  REACT: VideoStreamManager          │
│  - getUserMedia()                   │
│  - Display in <video> element       │
└─────────────┬───────────────────────┘
              │
              │ 2. Extract frame every 100ms (10 FPS)
              ↓
┌─────────────────────────────────────┐
│  REACT: FrameCaptureManager         │
│  - Draw to canvas (640x480)         │
│  - Convert to JPEG base64           │
│  - Compress to ~50KB                │
└─────────────┬───────────────────────┘
              │
              │ 3. HTTP POST
              ↓
┌─────────────────────────────────────┐
│  BACKEND: /api/ml/process-frame     │
│  - Decode base64                    │
│  - Validate image                   │
└─────────────┬───────────────────────┘
              │
              │ 4. Process with ML pipeline
              ↓
┌─────────────────────────────────────┐
│  MediaPipe Hands                    │
│  - Detect hand landmarks (21 points)│
│  - Return 3D coordinates            │
└─────────────┬───────────────────────┘
              │
              │ 5. If hand detected
              ↓
┌─────────────────────────────────────┐
│  Movement Tracker                   │
│  - Calculate velocity               │
│  - Determine state:                 │
│    • stable (ready for recognition) │
│    • moving (ignore)                │
│    • idle (no hand)                 │
└─────────────┬───────────────────────┘
              │
              │ 6. If stable
              ↓
┌─────────────────────────────────────┐
│  Gesture Classifier (PyTorch)       │
│  - Extract features from landmarks  │
│  - Compare to trained centroids     │
│  - Calculate confidence             │
└─────────────┬───────────────────────┘
              │
              │ 7. If confidence > threshold
              ↓
┌─────────────────────────────────────┐
│  Caption Generator                  │
│  - Map gesture to text              │
│  - Apply smoothing                  │
│  - Return caption                   │
└─────────────┬───────────────────────┘
              │
              │ 8. JSON response
              ↓
┌─────────────────────────────────────┐
│  REACT: CaptionManager              │
│  - Update UI state                  │
│  - Display caption overlay          │
│  - Trigger TTS (if enabled)         │
└─────────────────────────────────────┘

TOTAL LATENCY: ~80-120ms
- Frame capture: 10ms
- Network: 20-30ms
- ML processing: 40-60ms
- UI update: 10ms
```

## 3. WebRTC Signaling Flow

```
USER A (React)                BACKEND (Python)              USER B (React)
     │                              │                              │
     │ 1. Create Room               │                              │
     ├─────POST /api/rooms/create──→│                              │
     │←────{room_code: "ABC123"}────┤                              │
     │                              │                              │
     │ 2. Connect WebSocket         │                              │
     ├─────WS /ws/ABC123/userA─────→│                              │
     │←────Connected────────────────┤                              │
     │                              │                              │
     │                              │  3. User B joins             │
     │                              │←─POST /api/rooms/ABC123/join─┤
     │                              ├──{success: true}────────────→│
     │                              │                              │
     │                              │  4. Connect WebSocket        │
     │                              │←─WS /ws/ABC123/userB─────────┤
     │                              ├──Connected──────────────────→│
     │                              │                              │
     │ 5. Notify User A             │  6. Notify User B            │
     │←────{type: "user_joined"}────┤──{type: "user_joined"}──────→│
     │                              │                              │
     │ 7. Create Offer              │                              │
     ├─────{type: "webrtc_signal",─→│                              │
     │      data: {type: "offer",   │                              │
     │             sdp: "..."}}     │                              │
     │                              │  8. Forward to User B        │
     │                              ├──{type: "webrtc_signal"}────→│
     │                              │                              │
     │                              │  9. Create Answer            │
     │                              │←─{type: "webrtc_signal",─────┤
     │                              │   data: {type: "answer",     │
     │                              │          sdp: "..."}}        │
     │ 10. Forward to User A        │                              │
     │←────{type: "webrtc_signal"}──┤                              │
     │                              │                              │
     │ 11. Exchange ICE Candidates  │  12. Exchange ICE Candidates │
     ├─────{type: "webrtc_signal",─→├──{type: "webrtc_signal"}────→│
     │      data: {type: "ice",     │                              │
     │             candidate: ...}} │                              │
     │                              │                              │
     │ 13. PEER CONNECTION ESTABLISHED (Direct P2P)                │
     │←─────────────────────────────────────────────────────────→│
     │                    Video/Audio Stream                       │
     │                                                             │
     │ 14. Caption Generated        │                              │
     ├─────{type: "caption",────────→│                              │
     │      data: {text: "Hello"}}  │                              │
     │                              │  15. Broadcast Caption       │
     │                              ├──{type: "caption"}──────────→│
     │                              │                              │
```

## 4. Component Architecture: React Frontend

```
App.tsx
  │
  ├─ Router
  │   │
  │   ├─ / (Landing Page)
  │   │   └─ LandingPage.tsx
  │   │       ├─ CreateRoomButton
  │   │       └─ JoinRoomInput
  │   │
  │   ├─ /lobby/:roomCode (Pre-Join Lobby)
  │   │   └─ PreJoinLobby.tsx
  │   │       ├─ RoomCodeDisplay
  │   │       ├─ CameraPreview
  │   │       ├─ MediaControls
  │   │       │   ├─ MicToggle
  │   │       │   ├─ CameraToggle
  │   │       │   └─ AccessibilityToggle
  │   │       └─ JoinButton
  │   │
  │   └─ /call/:roomCode (Video Call)
  │       └─ VideoCallUI.tsx
  │           ├─ StatusBar.tsx
  │           │   ├─ FPSIndicator
  │           │   ├─ HandDetectionBadge
  │           │   └─ AccessibilityBadge
  │           │
  │           ├─ VideoGrid.tsx
  │           │   ├─ LocalVideoTile
  │           │   └─ RemoteVideoTile[]
  │           │       └─ VideoTile.tsx
  │           │           ├─ <video>
  │           │           ├─ UserNameLabel
  │           │           └─ AudioIndicator
  │           │
  │           ├─ CaptionOverlay.tsx
  │           │   ├─ LiveCaption
  │           │   ├─ ConfidenceIndicator
  │           │   └─ ConfirmedTranscript
  │           │
  │           ├─ ControlBar.tsx
  │           │   ├─ MicButton
  │           │   ├─ CameraButton
  │           │   ├─ AccessibilityButton
  │           │   ├─ PauseButton
  │           │   ├─ ClearButton
  │           │   ├─ SpeakButton
  │           │   ├─ SettingsButton
  │           │   └─ LeaveButton
  │           │
  │           └─ SettingsPanel.tsx
  │               ├─ GestureSettings
  │               ├─ DisplaySettings
  │               └─ AudioSettings
  │
  ├─ Contexts
  │   ├─ RoomContext
  │   │   └─ Provides: roomCode, participants, roomState
  │   │
  │   ├─ UserContext
  │   │   └─ Provides: userId, userName, userSettings
  │   │
  │   └─ AccessibilityContext
  │       └─ Provides: accessibilityMode, captions, gestures
  │
  └─ Services
      ├─ WebRTC
      │   ├─ PeerConnectionManager
      │   ├─ SignalingClient
      │   └─ MediaStreamManager
      │
      ├─ ML
      │   ├─ FrameCaptureManager
      │   ├─ MLClient
      │   └─ CaptionManager
      │
      └─ API
          ├─ roomApi
          ├─ captionApi
          └─ wsClient
```

## 5. Backend Service Architecture

```
FastAPI Application
  │
  ├─ API Routes
  │   │
  │   ├─ /api/rooms/*
  │   │   └─ rooms.py
  │   │       ├─ create_room()
  │   │       ├─ validate_room()
  │   │       ├─ join_room()
  │   │       └─ leave_room()
  │   │
  │   ├─ /api/ml/*
  │   │   └─ ml.py
  │   │       ├─ process_frame()
  │   │       └─ get_model_info()
  │   │
  │   ├─ /api/captions/*
  │   │   └─ captions.py
  │   │       ├─ store_caption()
  │   │       ├─ get_history()
  │   │       └─ submit_correction()
  │   │
  │   └─ /ws/{session_id}/{user_id}
  │       └─ websocket.py
  │           └─ websocket_endpoint()
  │
  ├─ Services
  │   │
  │   ├─ RoomManager
  │   │   ├─ create_room()
  │   │   ├─ get_room()
  │   │   ├─ add_participant()
  │   │   └─ remove_participant()
  │   │
  │   ├─ ConnectionManager
  │   │   ├─ connect()
  │   │   ├─ disconnect()
  │   │   └─ broadcast_to_session()
  │   │
  │   └─ CaptionSync
  │       ├─ store_caption()
  │       ├─ get_history()
  │       └─ sync_to_participants()
  │
  ├─ ML Pipeline
  │   │
  │   ├─ HandDetector (MediaPipe)
  │   │   ├─ detect()
  │   │   └─ get_landmarks()
  │   │
  │   ├─ MovementTracker
  │   │   ├─ update()
  │   │   └─ get_state()
  │   │
  │   ├─ GestureClassifier (PyTorch)
  │   │   ├─ predict()
  │   │   └─ get_confidence()
  │   │
  │   └─ SmoothingBuffer
  │       ├─ add()
  │       └─ get_smoothed()
  │
  └─ Data Layer
      │
      ├─ PostgreSQL
      │   ├─ rooms table
      │   ├─ participants table
      │   └─ captions table
      │
      ├─ Redis
      │   ├─ session cache
      │   └─ rate limiting
      │
      └─ File System
          └─ ML models (.pth, .pkl)
```

## 6. Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         PRODUCTION                              │
└─────────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │   Internet   │
                    └──────┬───────┘
                           │
                           ↓
                    ┌──────────────┐
                    │ Load Balancer│
                    │  (Nginx)     │
                    └──────┬───────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ↓              ↓              ↓
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ Frontend │   │ Frontend │   │ Frontend │
    │ Server 1 │   │ Server 2 │   │ Server 3 │
    │ (Nginx)  │   │ (Nginx)  │   │ (Nginx)  │
    └──────────┘   └──────────┘   └──────────┘
         │              │              │
         └──────────────┼──────────────┘
                        │
                        ↓
                 ┌──────────────┐
                 │ API Gateway  │
                 └──────┬───────┘
                        │
            ┌───────────┼───────────┐
            │           │           │
            ↓           ↓           ↓
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │ Backend  │ │ Backend  │ │ Backend  │
    │ Pod 1    │ │ Pod 2    │ │ Pod 3    │
    │(FastAPI) │ │(FastAPI) │ │(FastAPI) │
    └────┬─────┘ └────┬─────┘ └────┬─────┘
         │            │            │
         └────────────┼────────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
         ↓            ↓            ↓
  ┌──────────┐ ┌──────────┐ ┌──────────┐
  │PostgreSQL│ │  Redis   │ │   S3     │
  │ Primary  │ │ Cluster  │ │(ML Models│
  └────┬─────┘ └──────────┘ └──────────┘
       │
       ↓
  ┌──────────┐
  │PostgreSQL│
  │ Replica  │
  └──────────┘

MONITORING:
┌──────────┐ ┌──────────┐ ┌──────────┐
│Prometheus│→│ Grafana  │ │  Sentry  │
└──────────┘ └──────────┘ └──────────┘
```

