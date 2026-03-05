# SignBridge Application Flow Documentation

## Table of Contents
1. [Application Overview](#application-overview)
2. [Complete File Structure](#complete-file-structure)
3. [Application Routes](#application-routes)
4. [Navigation Flow](#navigation-flow)
5. [Button Click Flows](#button-click-flows)
6. [Backend API Endpoints](#backend-api-endpoints)
7. [WebSocket Events](#websocket-events)
8. [Known Bugs and Issues](#known-bugs-and-issues)
9. [Features Status](#features-status)

---

## Application Overview

**SignBridge** is a real-time sign language video communication platform with AI-powered ASL (American Sign Language) interpretation.

### Tech Stack
- **Frontend**: React 18 + TypeScript + Vite + TailwindCSS
- **Backend**: Python FastAPI + WebSocket (Socket.IO)
- **ML**: Mock inference (placeholder for real ASL model)
- **State Management**: React Context API
- **Routing**: React Router v6
- **Real-time**: WebRTC + WebSocket

### Key Features
- Real-time video calling with WebRTC
- Sign language gesture recognition (mock mode)
- Live captions with confidence scores
- Accessibility-first design (WCAG AA compliant)
- Multi-layout support (Grid, Spotlight, Sidebar)
- Chat functionality
- Screen sharing
- Recording capabilities

---

## Complete File Structure

```
signbridge/
├── frontend/
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   │   ├── ui/              # Base UI components (buttons, cards, etc.)
│   │   │   ├── ChatPanel.tsx    # Chat interface
│   │   │   ├── ControlBar.tsx   # Meeting controls
│   │   │   ├── VideoGrid.tsx    # Video layout manager
│   │   │   └── VideoTile.tsx    # Individual video tile
│   │   ├── contexts/            # React Context providers
│   │   │   ├── AppContext.tsx   # Global app state
│   │   │   ├── AuthContext.tsx  # Authentication state
│   │   │   ├── MeetingContext.tsx # Meeting state
│   │   │   ├── ThemeContext.tsx # Theme management
│   │   │   └── WebSocketContext.tsx # WebSocket connection
│   │   ├── hooks/               # Custom React hooks
│   │   │   └── useWebRTC.ts     # WebRTC connection management
│   │   ├── pages/               # Page components (routes)
│   │   │   ├── LandingPageNew.tsx    # Landing page (/)
│   │   │   ├── LoginPage.tsx         # Login/signup (/login)
│   │   │   ├── DashboardNew.tsx      # User dashboard (/dashboard)
│   │   │   ├── PreJoinLobby.tsx      # Pre-join lobby (/lobby)
│   │   │   ├── VideoCallPage.tsx     # Video call (/call/:roomCode)
│   │   │   ├── MeetingRoom.tsx       # Meeting room (/meeting/:roomCode)
│   │   │   └── AdminDashboard.tsx    # Admin panel (/admin)
│   │   ├── services/            # API and service layer
│   │   │   ├── api.ts           # REST API client
│   │   │   └── FrameCaptureManager.ts # Video frame processing
│   │   ├── styles/              # Global styles
│   │   ├── types/               # TypeScript type definitions
│   │   ├── utils/               # Utility functions
│   │   ├── App.tsx              # Main app component with routing
│   │   └── main.tsx             # Application entry point
│   ├── public/                  # Static assets
│   ├── package.json             # Dependencies
│   └── vite.config.ts           # Vite configuration
│
├── backend/
│   ├── simple_server.py         # Main FastAPI server
│   ├── mock_inference.py        # Mock ASL inference engine
│   ├── signaling_server.py      # WebRTC signaling server
│   ├── meeting_service.py       # Meeting management
│   ├── auth_service.py          # Authentication service
│   ├── redis_client.py          # Redis connection
│   ├── cloud_storage.py         # Cloud storage integration
│   ├── database/                # Database schema and setup
│   │   ├── schema.sql           # PostgreSQL schema
│   │   └── init_db.py           # Database initialization
│   ├── models/                  # Data models
│   └── storage/                 # File storage
│       └── datasets/            # ASL training datasets
│
├── docs/                        # Documentation
├── scripts/                     # Deployment scripts
└── docker-compose.yml           # Docker configuration
```

---

## Application Routes

### Public Routes (No Authentication Required)
| Route | Component | Description |
|-------|-----------|-------------|
| `/` | LandingPageNew | Landing page with features showcase |
| `/login` | LoginPage | Login/signup page |

### Protected Routes (Authentication Required)
| Route | Component | Description |
|-------|-----------|-------------|
| `/dashboard` | DashboardNew | User dashboard with stats and quick actions |
| `/lobby` | PreJoinLobby | Pre-join lobby (create new room) |
| `/lobby/:roomCode` | PreJoinLobby | Pre-join lobby (join existing room) |
| `/call/:roomCode` | VideoCallPage | Video call page (legacy) |
| `/meeting/:roomCode` | MeetingRoom | Meeting room (new implementation) |

### Admin Routes (Admin Authentication Required)
| Route | Component | Description |
|-------|-----------|-------------|
| `/admin` | AdminDashboard | Admin dashboard with system stats |

### Route Protection
- **ProtectedRoute**: Redirects to `/login` if not authenticated
- **AdminRoute**: Redirects to `/login` if not authenticated, redirects to `/dashboard` if not admin

---

## Navigation Flow

### 1. Landing Page Flow
```
LandingPageNew (/)
├── "Get Started" button → /login
├── "Learn More" button → Scroll to features section
└── "Launch SignBridge Now" button → /home ❌ BUG (should be /dashboard)
```

### 2. Login Flow
```
LoginPage (/login)
├── Login with credentials → /dashboard
├── Sign up with credentials → /dashboard
├── Continue as Guest → /dashboard
└── Admin login → /admin (if admin credentials)
```

### 3. Dashboard Flow
```
DashboardNew (/dashboard)
├── "Create Meeting" button → /lobby?create=true
├── "Join Meeting" button → Modal → /lobby/:roomCode
└── Recent conversations → (future: navigate to past meetings)
```

### 4. Pre-Join Lobby Flow
```
PreJoinLobby (/lobby or /lobby/:roomCode)
├── Generate room code (if create=true)
├── Enter room code manually
├── Enter display name
├── Toggle camera preview
├── Toggle accessibility mode
└── "JOIN MEETING" button → /call/:roomCode or /meeting/:roomCode
```

### 5. Video Call Flow
```
VideoCallPage (/call/:roomCode)
├── Camera controls (on/off)
├── Microphone controls (on/off)
├── Accessibility mode toggle
├── Caption display and history
├── Pause/Resume gesture detection
└── "Leave Call" button → / (landing page)
```

### 6. Meeting Room Flow
```
MeetingRoom (/meeting/:roomCode)
├── Video grid with participants
├── Layout switching (Grid/Spotlight/Sidebar)
├── Control bar (audio/video/screen share)
├── Chat panel
├── Participant list
└── "Leave Meeting" button → / (landing page)
```

---

## Button Click Flows

### Landing Page Buttons
1. **"Get Started"** → `navigate('/login')`
2. **"Learn More"** → Smooth scroll to features section
3. **"Launch SignBridge Now"** → `navigate('/home')` ❌ **BUG: Should be `/dashboard`**

### Dashboard Buttons
1. **"Create Meeting"** → `navigate('/lobby?create=true')`
   - Auto-generates room code via API
   - Opens lobby with pre-filled room code
2. **"Join Meeting"** → Opens modal
   - User enters room code
   - Validates room code
   - `navigate('/lobby/:roomCode')`

### Pre-Join Lobby Buttons
1. **"Generate Room Code" (Plus icon)** → Calls `api.createRoom()`
   - Creates new room on backend
   - Fills room code input
2. **"Turn on camera preview"** → Requests camera permission
   - Initializes MediaStream
   - Displays video preview
3. **"Turn off camera preview"** → Stops camera
   - Stops all video tracks
   - Clears video element
4. **"JOIN MEETING"** → Validates and navigates
   - Validates room exists
   - Stops camera preview
   - `navigate('/call/:roomCode')` with state

### Video Call Page Buttons
1. **Microphone Toggle** → `handleToggleMic()`
   - Enables/disables audio tracks
2. **Camera Toggle** → `handleToggleCamera()`
   - Starts/stops video stream
   - Handles camera initialization
3. **Accessibility Toggle** → `handleToggleAccessibility()`
   - Enables/disables ASL recognition
   - Shows/hides captions
4. **Pause/Resume** → `handlePause()`
   - Pauses/resumes gesture detection
5. **Clear Captions** → `handleClear()`
   - Clears caption history
6. **Speak Captions** → `handleSpeak()`
   - Uses Web Speech API for TTS
7. **Leave Call** → `handleLeave()`
   - Confirms with user
   - Cleans up streams
   - `navigate('/')`

### Meeting Room Buttons
1. **Layout Buttons** → `handleLayoutChange(layout)`
   - Switches between Grid/Spotlight/Sidebar
2. **Audio Toggle** → `handleToggleAudio()`
   - Toggles local audio
   - Notifies other participants
3. **Video Toggle** → `handleToggleVideo()`
   - Toggles local video
   - Notifies other participants
4. **Screen Share** → `handleToggleScreenShare()`
   - Starts/stops screen sharing
   - Notifies other participants
5. **Hand Raise** → `handleToggleHandRaise()`
   - Raises/lowers hand
   - Notifies other participants
6. **Chat Toggle** → `handleToggleChat()`
   - Opens/closes chat panel
7. **Pin Participant** → `handlePinParticipant()`
   - Pins/unpins participant video
8. **Leave Meeting** → `handleLeaveMeeting()`
   - Sends leave event
   - `navigate('/')`

---

## Backend API Endpoints

### Base URL
- Development: `http://localhost:8001`
- Environment variable: `VITE_API_URL`

### REST API Endpoints

#### 1. Health Check
```
GET /
Response: { status, service, version, mode }

GET /health
Response: { status, service, active_rooms, active_connections, timestamp, redis }

GET /health/redis
Response: { status, connected, latency_ms, error }
```

#### 2. Room Management
```
POST /api/rooms/create
Body: { host_user_id, accessibility_mode, max_participants }
Response: { room_code, room_id, created_at, websocket_url }

GET /api/rooms/:roomCode/validate
Response: { valid, room_id, participants_count, is_full, accessibility_mode, error }

POST /api/rooms/:roomCode/join
Body: { user_id, user_name }
Response: { success, room_id, websocket_url, existing_participants }
```

#### 3. ML Processing (Future)
```
POST /api/ml/process-frame
Body: { frame, user_id, session_id, timestamp }
Response: { success, hand_detected, landmarks, gesture, confidence, caption, movement_state, processing_time_ms }
```

### WebSocket Endpoint
```
WS /ws/:roomCode/:userId
```

---

## WebSocket Events

### Client → Server Events

#### 1. WebRTC Signaling
```javascript
{
  type: "webrtc_signal",
  target_user: "user_id",
  data: { offer | answer | ice_candidate }
}
```

#### 2. Video Frame Processing
```javascript
{
  type: "video_frame",
  image: "base64_encoded_image"
}
```

#### 3. Caption Broadcasting
```javascript
{
  type: "caption",
  data: { text, confidence }
}
```

#### 4. Chat Messages
```javascript
{
  type: "chat",
  data: { message, timestamp }
}
```

#### 5. Meeting Events (Socket.IO)
```javascript
// Join meeting
emit("join-meeting", {
  meetingId, userId, userName, mediaCapabilities
})

// Leave meeting
emit("leave-meeting", {
  meetingId, userId
})

// Send chat message
emit("send-chat-message", {
  meetingId, senderId, senderName, messageText
})

// Start/stop screen share
emit("start-screen-share", { meetingId, userId })
emit("stop-screen-share", { meetingId, userId })
```

### Server → Client Events

#### 1. WebRTC Signaling
```javascript
{
  type: "webrtc_signal",
  from_user: "user_id",
  target_user: "user_id",
  data: { offer | answer | ice_candidate }
}
```

#### 2. Caption Updates
```javascript
{
  type: "caption",
  level: "live",
  text: "recognized_text",
  confidence: 0.95,
  timestamp: 1234567890
}
```

#### 3. User Events
```javascript
{
  type: "user_joined",
  user_id: "user_id",
  timestamp: 1234567890
}

{
  type: "user_left",
  user_id: "user_id",
  timestamp: 1234567890
}
```

#### 4. Meeting Events (Socket.IO)
```javascript
// Join success
on("join-meeting-success", {
  participants: [...]
})

// Participant events
on("participant-joined", { participant })
on("participant-left", { userId })
on("participant-updated", { userId, updates })

// Active speaker detection
on("active-speaker-changed", { userId })
on("active-signer-detected", { userId })

// Chat messages
on("chat-message", {
  id, senderId, senderName, messageText, timestamp, isPrivate
})

// Errors
on("error", { message })
```

---

## Known Bugs and Issues

### 🔴 Critical Bugs

#### 1. Landing Page Navigation Bug
**Location**: `frontend/src/pages/LandingPageNew.tsx:241`
```typescript
// BUG: Redirects to /home which doesn't exist
onClick={() => navigate('/home')}

// FIX: Should redirect to /dashboard
onClick={() => navigate('/dashboard')}
```
**Impact**: Users clicking "Launch SignBridge Now" get a 404 error
**Status**: ❌ Not Fixed

#### 2. Missing Backend Connectivity Check
**Location**: Application startup
**Issue**: No health check on app load to verify backend is running
**Impact**: Users don't know if backend is down until they try to create/join a room
**Status**: ❌ Not Fixed

#### 3. Camera Preview Issues
**Location**: `frontend/src/pages/PreJoinLobby.tsx`
**Issues**:
- Race condition in camera initialization (concurrent calls)
- Video element not properly waiting for metadata
- Play() promise rejection not handled
- No retry mechanism
**Impact**: Camera preview fails intermittently
**Status**: ⚠️ Partially Fixed (has safeguards but needs improvement)

### 🟡 Medium Priority Bugs

#### 4. Missing Error Boundaries
**Location**: Throughout application
**Issue**: No React Error Boundaries to catch component errors
**Impact**: Entire app crashes on component errors
**Status**: ❌ Not Fixed

#### 5. Insufficient Try-Catch Blocks
**Location**: Multiple async operations
**Issue**: Many async operations lack error handling
**Impact**: Unhandled promise rejections
**Status**: ❌ Not Fixed

#### 6. Missing Console Logging
**Location**: Throughout application
**Issue**: Insufficient logging for debugging
**Impact**: Hard to debug issues in production
**Status**: ⚠️ Partially implemented

#### 7. No Backend Unavailable Modal
**Location**: Application-wide
**Issue**: No user-friendly modal when backend is down
**Impact**: Poor user experience when backend fails
**Status**: ❌ Not Fixed

### 🟢 Low Priority Issues

#### 8. Inconsistent Route Naming
**Issue**: Two video call pages (`/call` and `/meeting`)
**Impact**: Confusion about which to use
**Status**: ⚠️ Both exist, need consolidation

#### 9. Mock Data in Production
**Location**: `frontend/src/pages/AdminDashboard.tsx`
**Issue**: Uses demo.json for admin stats
**Impact**: Not showing real data
**Status**: ⚠️ Expected (demo mode)

#### 10. No Loading States
**Location**: Multiple components
**Issue**: Missing loading indicators for async operations
**Impact**: Poor UX during loading
**Status**: ⚠️ Partially implemented

---

## Features Status

### ✅ Working Features

1. **Authentication System**
   - Login with email/password
   - Sign up with email/password
   - Guest login
   - Admin login (admin@videocall.com / Admin@2024)
   - Protected routes
   - Session persistence (localStorage)

2. **Room Management**
   - Create new room with auto-generated code
   - Join existing room with code
   - Room validation
   - Room code generation (6-character alphanumeric)

3. **Pre-Join Lobby**
   - Display name input
   - Room code input/generation
   - Camera preview toggle
   - Accessibility mode toggle
   - Camera permission handling

4. **Video Call (VideoCallPage)**
   - Local video stream
   - Camera on/off toggle
   - Microphone on/off toggle
   - Accessibility mode toggle
   - Live captions (mock mode)
   - Caption history
   - Caption confirmation
   - Text-to-speech
   - Pause/resume gesture detection
   - Keyboard shortcuts
   - FPS counter
   - Hand detection indicator
   - Gesture stability indicator

5. **Meeting Room (MeetingRoom)**
   - WebRTC peer connections
   - Multiple participants
   - Video grid layout
   - Spotlight layout
   - Sidebar layout
   - Active speaker detection
   - Participant list
   - Audio/video controls
   - Screen sharing
   - Hand raise
   - Chat panel
   - Pin participant

6. **UI/UX**
   - Dark/light theme toggle
   - Responsive design
   - Accessibility features (WCAG AA)
   - Keyboard navigation
   - Screen reader support
   - Loading states (partial)
   - Error messages (partial)

7. **Dashboard**
   - User statistics
   - Usage analytics chart
   - Recent conversations
   - Quick actions (create/join)
   - AI status indicator

8. **Admin Dashboard**
   - System statistics
   - User management view
   - Meeting overview
   - Recent activity log
   - Top users list

### ⚠️ Partially Working Features

1. **ASL Recognition**
   - Status: Mock mode only
   - Mock inference engine works
   - Real ML model not integrated
   - Caption generation works (mock data)

2. **WebSocket Communication**
   - Status: Implemented but needs testing
   - Socket.IO connection works
   - Event handlers implemented
   - Signaling works (basic)

3. **Error Handling**
   - Status: Inconsistent
   - Some try-catch blocks exist
   - Missing error boundaries
   - Incomplete error messages

4. **Backend Health Monitoring**
   - Status: Backend has endpoints
   - Frontend doesn't check on startup
   - No automatic reconnection
   - No user notification

### ❌ Not Working / Not Implemented

1. **Real ASL Model Integration**
   - ML model training incomplete
   - No real gesture recognition
   - Using mock predictions only

2. **Recording Feature**
   - UI exists but not functional
   - No backend recording service
   - No storage integration

3. **Firebase Authentication**
   - Placeholder only
   - Using local authentication
   - No real user database

4. **Redis Integration**
   - Backend has Redis client
   - Not used in production
   - Session storage not implemented

5. **PostgreSQL Database**
   - Schema exists
   - Not connected to application
   - Using in-memory storage

6. **Cloud Storage**
   - Backend has integration code
   - Not configured
   - No file uploads

7. **Email Notifications**
   - Not implemented
   - No email service

8. **Meeting Recording Playback**
   - Not implemented
   - No recording storage

9. **Breakout Rooms**
   - Not implemented
   - No UI or backend support

10. **Waiting Room**
    - Not implemented
    - All users join directly

11. **Meeting Scheduling**
    - Not implemented
    - Only instant meetings

12. **User Profiles**
    - Basic info only
    - No profile editing
    - No avatar upload

---

## Context Providers

### 1. AppContext
**File**: `frontend/src/contexts/AppContext.tsx`
**State**:
- `theme`: 'dark' | 'light'
- `user`: User object or null
- `aiStatus`: 'connected' | 'mock' | 'disconnected' | 'error'
- `totalWordsRecognized`: number
- `isInCall`: boolean
- `connectionStrength`: number (0-100)

### 2. AuthContext
**File**: `frontend/src/contexts/AuthContext.tsx`
**State**:
- `user`: User object or null
- `isAuthenticated`: boolean
**Methods**:
- `login(email, password)`
- `signup(name, email, password)`
- `loginAsGuest(name)`
- `logout()`

### 3. MeetingContext
**File**: `frontend/src/contexts/MeetingContext.tsx`
**State**:
- `meetingId`: string
- `participants`: Participant[]
- `activeLayout`: 'grid' | 'spotlight' | 'sidebar' | 'accessibility'
- `activeSpeaker`: string | null
- `activeSigner`: string | null
- `pinnedParticipant`: string | null
- `isRecording`: boolean
- `screenSharingParticipant`: string | null

### 4. WebSocketContext
**File**: `frontend/src/contexts/WebSocketContext.tsx`
**State**:
- `isConnected`: boolean
- `socket`: Socket | null
**Methods**:
- `connect(roomCode, userId)`
- `disconnect()`
- `sendMessage(event, data)`
- `subscribe(event, handler)`

### 5. ThemeContext
**File**: `frontend/src/contexts/ThemeContext.tsx`
**State**:
- `theme`: 'dark' | 'light'
**Methods**:
- `toggleTheme()`

---

## Environment Variables

### Frontend (.env)
```bash
VITE_API_URL=http://localhost:8001
VITE_SOCKET_URL=http://localhost:8001
```

### Backend (.env)
```bash
# Server
HOST=0.0.0.0
PORT=8001

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/signbridge

# Cloud Storage
CLOUD_STORAGE_BUCKET=signbridge-recordings
CLOUD_STORAGE_CREDENTIALS=path/to/credentials.json

# Firebase
FIREBASE_API_KEY=
FIREBASE_AUTH_DOMAIN=
FIREBASE_PROJECT_ID=
```

---

## Development Commands

### Frontend
```bash
cd frontend
npm install          # Install dependencies
npm run dev          # Start dev server (http://localhost:3000)
npm run build        # Build for production
npm run preview      # Preview production build
npm run test         # Run tests
npm run lint         # Lint code
npm run format       # Format code
```

### Backend
```bash
cd backend
pip install -r requirements.txt  # Install dependencies
python simple_server.py          # Start server (http://localhost:8001)
python -m pytest                 # Run tests
```

### Full Stack
```bash
# Start both frontend and backend
npm run dev          # From root (if configured)

# Or use Docker
docker-compose up    # Start all services
```

---

## Summary

This document provides a complete overview of the SignBridge application architecture, navigation flows, and current status. Use this as a reference for:
- Understanding the application structure
- Debugging navigation issues
- Identifying which features work and which don't
- Planning bug fixes and new features
- Onboarding new developers

**Last Updated**: 2024
**Version**: 1.0.0
