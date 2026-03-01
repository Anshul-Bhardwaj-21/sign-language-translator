# Quick Start Guide: Production Architecture Implementation

## Overview

This guide helps you transition from your current Python/Streamlit prototype to a production-grade React + Python architecture for a Google Meet-style sign language accessible video meeting system.

## What You Have Now

✅ Working ML pipeline (MediaPipe + PyTorch)  
✅ Hand detection and gesture recognition  
✅ Caption generation  
✅ Streamlit UI prototype  

## What You Need to Build

🎯 React frontend with WebRTC  
🎯 FastAPI backend with your ML code  
🎯 Pre-join lobby (no auto-camera)  
🎯 Room system (create/join)  
🎯 Google Meet-style UI  

---

## Step 1: Understand the Architecture (30 minutes)

### Read These Documents in Order:

1. **PRODUCTION_SUMMARY.md** - High-level overview and why
2. **PRODUCTION_ARCHITECTURE.md** - Detailed technical specs
3. **ARCHITECTURE_DIAGRAMS.md** - Visual diagrams
4. **CODE_EXAMPLES.md** - Implementation examples

### Key Concepts to Understand:

- **Separation of Concerns:** React handles UI/WebRTC, Python handles ML
- **User Consent:** Camera never auto-starts, explicit join flow
- **Graceful Degradation:** Never crash, always provide fallback
- **Edge Cases:** Handle 60+ documented scenarios

---

## Step 2: Set Up Development Environment (1 hour)

### Prerequisites

```bash
# Check versions
node --version    # Should be 18+
python --version  # Should be 3.10+
docker --version  # Optional but recommended
```

### Project Structure

```bash
# Create project structure
mkdir sign-language-video-call
cd sign-language-video-call

# Create directories
mkdir -p frontend/src/{components,services,hooks,contexts,utils,styles}
mkdir -p backend/app/{api,ml,services,models,utils}
mkdir -p ml_models
mkdir -p docs
```

### Backend Setup

```bash
# Create Python virtual environment
cd backend
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Mac/Linux)
source .venv/bin/activate

# Install dependencies
pip install fastapi uvicorn websockets python-multipart
pip install mediapipe opencv-python numpy torch
pip install sqlalchemy psycopg2-binary redis
pip install pydantic python-dotenv

# Create requirements.txt
pip freeze > requirements.txt
```

### Frontend Setup

```bash
# Create React app with Vite + TypeScript
cd frontend
npm create vite@latest . -- --template react-ts

# Install dependencies
npm install
npm install react-router-dom
npm install socket.io-client
npm install tailwindcss postcss autoprefixer
npm install @types/node

# Initialize Tailwind
npx tailwindcss init -p
```

---

## Step 3: Migrate Your ML Code to FastAPI (2-3 hours)

### Copy Your Existing ML Code

```bash
# Copy your existing ML modules to backend
cp -r ../app/inference/* backend/app/ml/
cp -r ../app/camera/* backend/app/ml/
cp -r ../ml/models/* ml_models/
```

### Wrap in FastAPI Endpoints

Create `backend/app/main.py` (see CODE_EXAMPLES.md for full code):

```python
from fastapi import FastAPI
from app.ml.hand_detector import HandDetector  # Your existing code
from app.ml.gesture_classifier import GestureClassifier  # Your existing code

app = FastAPI()

# Initialize your existing ML components
hand_detector = HandDetector()
gesture_classifier = GestureClassifier()

@app.post("/api/ml/process-frame")
async def process_frame(request: FrameRequest):
    # Use your existing ML pipeline
    detection = hand_detector.detect(frame)
    gesture = gesture_classifier.predict(detection.landmarks)
    return {"caption": gesture, "confidence": 0.9}
```

### Test Backend

```bash
# Start server
cd backend
uvicorn app.main:app --reload

# Test in browser
# Open http://localhost:8000/docs
# Try the /health endpoint
```

---

## Step 4: Build React Frontend (4-6 hours)

### Phase 1: Landing Page (1 hour)

Create `frontend/src/pages/LandingPage.tsx`:

```typescript
export const LandingPage = () => {
  const navigate = useNavigate();
  
  const handleCreateRoom = async () => {
    const response = await fetch('http://localhost:8000/api/rooms/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ host_user_id: 'user_123' })
    });
    const { room_code } = await response.json();
    navigate(`/lobby/${room_code}`);
  };

  return (
    <div>
      <h1>Sign Language Video Call</h1>
      <button onClick={handleCreateRoom}>Create Room</button>
      <input placeholder="Enter room code" />
      <button>Join Room</button>
    </div>
  );
};
```

### Phase 2: Pre-Join Lobby (2 hours)

See `CODE_EXAMPLES.md` for full `PreJoinLobby.tsx` component.

Key features:
- Room code display with copy button
- Camera preview (OFF by default, toggle to enable)
- Mic/camera/accessibility toggles
- Explicit "Join Meeting" button
- Permission error handling

### Phase 3: Video Call UI (2-3 hours)

See `CODE_EXAMPLES.md` for full `VideoCallUI.tsx` component.

Key features:
- WebRTC peer connections
- Video grid (16:9 aspect ratio)
- Control bar (Meet-style)
- Caption overlay
- Status bar (FPS, hand detection)

### Phase 4: Routing

Create `frontend/src/App.tsx`:

```typescript
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { LandingPage } from './pages/LandingPage';
import { PreJoinLobby } from './components/PreJoinLobby/PreJoinLobby';
import { VideoCallUI } from './components/VideoCall/VideoCallUI';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/lobby/:roomCode" element={<PreJoinLobby />} />
        <Route path="/call/:roomCode" element={<VideoCallUI />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```

---

## Step 5: Integrate Frontend and Backend (2-3 hours)

### WebSocket Connection

Create `frontend/src/services/api/wsClient.ts`:

```typescript
export class WebSocketClient {
  private ws: WebSocket | null = null;

  connect(roomCode: string, userId: string) {
    this.ws = new WebSocket(`ws://localhost:8000/ws/${roomCode}/${userId}`);
    
    this.ws.onopen = () => console.log('Connected');
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };
  }

  sendCaption(caption: string) {
    this.ws?.send(JSON.stringify({
      type: 'caption',
      data: { text: caption }
    }));
  }
}
```

### Frame Capture and ML Processing

See `CODE_EXAMPLES.md` for full `FrameCaptureManager.ts`.

Key features:
- Capture frames at 10 FPS (reduced from 25 FPS video)
- Resize to 640x480 (reduce bandwidth)
- Convert to JPEG base64
- POST to backend `/api/ml/process-frame`
- Handle errors gracefully (don't block UI)

---

## Step 6: Test End-to-End (1-2 hours)

### Test Checklist

- [ ] Landing page loads
- [ ] Create room generates code
- [ ] Pre-join lobby shows room code
- [ ] Camera preview toggle works
- [ ] Permission denied shows error
- [ ] Join meeting enters video call
- [ ] Local video displays
- [ ] Control buttons work (mic, camera)
- [ ] Accessibility mode enables ML processing
- [ ] Hand gestures detected
- [ ] Captions appear on screen
- [ ] Leave call returns to landing page

### Common Issues

**Camera not working:**
- Check browser permissions (chrome://settings/content/camera)
- Ensure HTTPS or localhost (WebRTC requirement)
- Check console for errors

**Backend not responding:**
- Check backend is running (`uvicorn app.main:app --reload`)
- Check CORS settings in FastAPI
- Check network tab in browser DevTools

**ML processing slow:**
- Reduce frame capture rate (5 FPS instead of 10)
- Check backend logs for errors
- Ensure MediaPipe is installed correctly

---

## Step 7: Add Edge Case Handling (2-3 hours)

### Priority Edge Cases

1. **Camera Permission Denied**
   ```typescript
   try {
     stream = await navigator.mediaDevices.getUserMedia({ video: true });
   } catch (error) {
     if (error.name === 'NotAllowedError') {
       showError('Camera permission denied. Please allow in browser settings.');
       // Offer to join without camera
     }
   }
   ```

2. **Backend Unavailable**
   ```typescript
   try {
     const result = await fetch('/api/ml/process-frame', { ... });
   } catch (error) {
     console.error('Backend unavailable, using fallback');
     // Continue without ML processing
   }
   ```

3. **Room Full**
   ```typescript
   const { is_full } = await validateRoom(roomCode);
   if (is_full) {
     showError('Room is full. Please try another room.');
   }
   ```

4. **Network Disconnect**
   ```typescript
   peerConnection.onconnectionstatechange = () => {
     if (peerConnection.connectionState === 'failed') {
       showNotification('Connection lost. Reconnecting...');
       attemptReconnect();
     }
   };
   ```

---

## Step 8: Polish and Deploy (2-3 hours)

### Styling

Use Tailwind CSS for Google Meet-style UI:

```css
/* Dark theme */
.bg-meet-dark { background: #202124; }
.bg-meet-gray { background: #3c4043; }

/* Control bar */
.control-button {
  @apply w-14 h-14 rounded-full bg-gray-700 hover:bg-gray-600;
  @apply flex items-center justify-center text-white text-2xl;
  @apply transition-all duration-200;
}

/* Caption overlay */
.caption-overlay {
  @apply absolute bottom-24 left-1/2 transform -translate-x-1/2;
  @apply bg-black bg-opacity-90 rounded-lg p-6;
  @apply text-white text-3xl font-semibold text-center;
}
```

### Deployment

**Option 1: Docker Compose (Recommended)**

```bash
# Build and run
docker-compose up --build

# Access at http://localhost:3000
```

**Option 2: Manual Deployment**

```bash
# Backend
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm run build
npm run preview
```

**Option 3: Cloud Deployment**

- Frontend: Vercel, Netlify, or AWS S3 + CloudFront
- Backend: AWS EC2, Google Cloud Run, or Heroku
- Database: AWS RDS or Heroku Postgres

---

## Timeline Estimate

### Minimal Viable Demo (40-50 hours)

- **Day 1-2:** Environment setup + backend migration (8-10 hours)
- **Day 3-4:** React frontend basics (landing + lobby) (8-10 hours)
- **Day 5-6:** Video call UI + WebRTC (10-12 hours)
- **Day 7:** ML integration (6-8 hours)
- **Day 8:** Edge cases + polish (6-8 hours)

### Production Ready (80-100 hours)

- Add above 40-50 hours
- **Week 2:** Security, authentication, rate limiting (15-20 hours)
- **Week 3:** Performance optimization, mobile support (15-20 hours)
- **Week 4:** Testing, documentation, deployment (10-15 hours)

---

## Success Criteria

### For Demo/Hackathon

✅ Pre-join lobby with explicit join flow  
✅ 2-user video call works  
✅ Hand gestures detected and translated  
✅ Captions overlaid on video  
✅ Google Meet-style UI  
✅ Handles camera permission denied  
✅ Never crashes  

### For Production

✅ All above +  
✅ 10+ concurrent users per room  
✅ Mobile responsive  
✅ <100ms ML latency  
✅ 99.9% uptime  
✅ WCAG AA accessibility  
✅ Comprehensive logging  
✅ 80%+ test coverage  

---

## Next Steps

1. **Start with Backend** - Wrap your existing ML code in FastAPI
2. **Build Pre-Join Lobby** - Get the user consent flow right
3. **Add WebRTC** - Use example code from CODE_EXAMPLES.md
4. **Integrate ML** - Connect frame capture to your backend
5. **Polish UI** - Make it look like Google Meet
6. **Handle Edge Cases** - Test all failure scenarios
7. **Deploy** - Use Docker Compose for easy deployment

---

## Resources

- **WebRTC Tutorial:** https://webrtc.org/getting-started/overview
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **React + TypeScript:** https://react-typescript-cheatsheet.netlify.app/
- **Tailwind CSS:** https://tailwindcss.com/docs
- **MediaPipe:** https://google.github.io/mediapipe/solutions/hands.html

---

## Getting Help

If you get stuck:

1. Check the error message in browser console
2. Check backend logs (`uvicorn` output)
3. Review CODE_EXAMPLES.md for reference implementations
4. Test each component independently
5. Use browser DevTools Network tab to debug API calls

---

## Final Checklist

Before considering it "done":

- [ ] User can create room without camera starting
- [ ] User can join room with code
- [ ] Camera preview is optional in lobby
- [ ] Video call works between 2 users
- [ ] Hand gestures are detected
- [ ] Captions appear on screen
- [ ] UI looks professional (Meet-style)
- [ ] Camera permission denied is handled
- [ ] Backend errors don't crash frontend
- [ ] Room full scenario is handled
- [ ] User can leave and rejoin
- [ ] Mobile layout is usable

---

**Remember:** This is a production architecture, not a toy demo. Take time to understand the concepts, handle edge cases properly, and build something that real users can depend on.

Good luck! 🚀

