# Sign Language Video Call Application

[![CI/CD Pipeline](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci-cd.yml)
[![Backend Tests](https://img.shields.io/badge/backend-tests-passing-brightgreen)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions)
[![Frontend Tests](https://img.shields.io/badge/frontend-tests-passing-brightgreen)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A real-time video calling application with ASL (American Sign Language) recognition and live captioning.

## 🚀 Quick Start (2-Minute Demo)

### Prerequisites
- **Python 3.10+** (check: `python --version`)
- **Node.js 18+** (check: `node --version`)
- **Webcam** (for video calling)

### Step 1: Start Backend (Terminal 1)

**Windows:**
```powershell
cd backend
.\run-dev.ps1
```

**Linux/Mac:**
```bash
cd backend
chmod +x run-dev.sh
./run-dev.sh
```

Wait for: `Application startup complete` message

### Step 2: Start Frontend (Terminal 2)

**Windows:**
```powershell
cd frontend
.\run-dev.ps1
```

**Linux/Mac:**
```bash
cd frontend
chmod +x run-dev.sh
./run-dev.sh
```

Wait for: `Local: http://localhost:5173` message

### Step 3: Demo the App

1. Open **TWO browser tabs** (Chrome/Edge recommended):
   - Tab A: http://localhost:5173
   - Tab B: http://localhost:5173

2. **Tab A** (Host):
   - Click "Create Room"
   - Copy the room code (e.g., "ABC123")
   - Enable camera when prompted
   - Turn ON "Accessibility Mode" (🧏 button)

3. **Tab B** (Guest):
   - Click "Join Room"
   - Paste the room code
   - Click "Join"
   - Enable camera when prompted

4. **Test Features**:
   - ✅ Both tabs should see each other's video
   - ✅ Wave your hand in Tab A → Tab B sees mock captions
   - ✅ Type in chat → messages appear in both tabs
   - ✅ Click speaker icon → browser TTS reads captions

## 📋 Features

### Core Features (Working)
- ✅ **WebRTC Video Calling** - Peer-to-peer video between 2+ users
- ✅ **WebSocket Signaling** - Real-time connection establishment
- ✅ **Mock ASL Recognition** - Deterministic gesture detection (offline)
- ✅ **Live Captions** - Real-time caption display with confidence scores
- ✅ **Text-to-Speech** - Browser-based TTS (no external API)
- ✅ **Chat** - Text messaging between participants
- ✅ **Accessibility Mode** - Toggle ASL recognition on/off
- ✅ **Camera Controls** - Turn camera on/off reliably
- ✅ **Keyboard Shortcuts** - Full keyboard navigation

### Mock Inference Mode
The app uses **mock ASL inference** by default (no external AI APIs required):
- Deterministic predictions based on hand geometry
- Works completely offline
- No API keys needed
- Suitable for demos and development

To use real ASL models, see `docs/ML_SETUP.md` (requires training data).

## 🏗️ Architecture

```
┌─────────────────┐         WebSocket          ┌─────────────────┐
│   Frontend      │◄──────────────────────────►│   Backend       │
│   (React +      │    Signaling + Captions    │   (FastAPI)     │
│    Vite)        │                            │                 │
└─────────────────┘                            └─────────────────┘
        │                                               │
        │ WebRTC (P2P)                                 │
        │                                               │
        ▼                                               ▼
┌─────────────────┐                            ┌─────────────────┐
│   Browser A     │◄──────────────────────────►│  Mock Inference │
│   (Peer 1)      │    Video/Audio Streams     │   Engine        │
└─────────────────┘                            └─────────────────┘
```

## 📁 Project Structure

```
sign-language-translator/
├── backend/
│   ├── simple_server.py      # Main FastAPI server
│   ├── mock_inference.py     # Mock ASL model (no external APIs)
│   ├── run-dev.ps1           # Windows start script
│   ├── run-dev.sh            # Linux/Mac start script
│   └── .env.example          # Environment variables template
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   └── VideoCallPage.tsx  # Main video call UI
│   │   ├── services/
│   │   │   ├── api.ts             # Backend API client
│   │   │   └── FrameCaptureManager.ts  # Frame capture logic
│   │   └── components/            # Reusable UI components
│   ├── run-dev.ps1           # Windows start script
│   ├── run-dev.sh            # Linux/Mac start script
│   └── .env                  # Environment variables
├── README.md                 # This file
├── backend/DEBUG_REPORT.md   # Backend debugging guide
└── frontend/DEBUG_REPORT.md  # Frontend debugging guide
```

## 🔧 Manual Setup (If Scripts Fail)

### Backend Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install fastapi uvicorn websockets python-multipart pydantic opencv-python numpy

# Run server
cd backend
python simple_server.py
```

Server runs on: http://localhost:8001

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm ci

# Run dev server
npm run dev
```

Frontend runs on: http://localhost:5173

## 🔄 CI/CD Pipeline

This project uses GitHub Actions for automated testing and deployment.

### Pipeline Stages

1. **Linting & Type Checking**
   - Backend: Black, isort, flake8
   - Frontend: ESLint, Prettier, TypeScript

2. **Testing**
   - Backend: pytest with PostgreSQL and Redis
   - Frontend: Vitest with React Testing Library

3. **Docker Build & Push**
   - Builds Docker images for backend and frontend
   - Pushes to GitHub Container Registry (ghcr.io)
   - Tags: `latest` (main), `develop`, `<branch>-<sha>`

4. **Deployment**
   - Staging: Auto-deploy on push to `develop` branch
   - Production: Auto-deploy on push to `main` branch

### Running CI Checks Locally

**Backend:**
```bash
cd backend

# Linting
black --check .
isort --check-only .
flake8 .

# Tests
pytest -v
```

**Frontend:**
```bash
cd frontend

# Linting
npm run lint
npm run format:check
npx tsc --noEmit

# Tests
npm run test
```

### Docker Images

Images are automatically built and pushed to GitHub Container Registry:

```bash
# Pull latest images
docker pull ghcr.io/YOUR_USERNAME/YOUR_REPO/backend:latest
docker pull ghcr.io/YOUR_USERNAME/YOUR_REPO/frontend:latest

# Run with Docker Compose
docker-compose up -d
```

### Environment Setup for CI/CD

Required secrets in GitHub repository settings:

- `GITHUB_TOKEN` - Automatically provided by GitHub Actions
- Additional secrets for deployment (if using external services):
  - `STAGING_DEPLOY_KEY` - SSH key for staging server
  - `PRODUCTION_DEPLOY_KEY` - SSH key for production server
  - `DOCKER_REGISTRY_TOKEN` - If using external registry

### Health Check Endpoints

The backend provides health check endpoints for monitoring:

- `GET /health` - Overall service health (includes Redis status)
- `GET /health/redis` - Dedicated Redis health check

Example response:
```json
{
  "status": "healthy",
  "service": "backend",
  "active_rooms": 5,
  "active_connections": 12,
  "timestamp": "2024-01-15T10:30:00",
  "redis": {
    "status": "healthy",
    "ping": true,
    "info": "Redis 7.0.0"
  }
}
```

## 🎮 Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `M` | Toggle microphone |
| `V` | Toggle camera |
| `A` | Toggle accessibility mode |
| `P` | Pause/resume gesture detection |
| `Ctrl+C` | Clear all captions |
| `Ctrl+S` | Speak captions aloud |
| `Enter` | Confirm current caption |

## 🐛 Troubleshooting

### Backend Issues

**Port 8001 already in use:**
```bash
# Windows
netstat -ano | findstr :8001
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8001 | xargs kill -9
```

**Python not found:**
- Install Python 3.10+ from https://www.python.org/downloads/
- Ensure "Add to PATH" is checked during installation

**Module not found errors:**
```bash
pip install --upgrade pip
pip install fastapi uvicorn websockets python-multipart pydantic opencv-python numpy
```

### Frontend Issues

**Port 5173 already in use:**
- Change port in `frontend/vite.config.ts`:
  ```typescript
  server: { port: 3000 }
  ```

**Node.js not found:**
- Install Node.js 18+ from https://nodejs.org/

**npm ci fails:**
```bash
rm -rf node_modules package-lock.json
npm install
```

### Camera Issues

**Camera not accessible:**
1. Close other apps using the camera (Zoom, Teams, etc.)
2. Check browser permissions (chrome://settings/content/camera)
3. Try a different browser (Chrome/Edge recommended)
4. Restart browser

**Camera shows black screen:**
1. Refresh the page
2. Click "Turn On Camera" button again
3. Check if camera works in other apps

### WebRTC Connection Issues

**Peers can't see each other:**
1. Ensure both tabs are on the same room code
2. Check browser console for errors (F12)
3. Disable browser extensions (ad blockers)
4. Try in incognito mode

**No video/audio:**
1. Check camera/mic permissions
2. Ensure STUN server is accessible (requires internet)
3. Check firewall settings

## 📊 Testing Checklist

- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] Can create a room
- [ ] Can join a room with code
- [ ] Camera turns on/off reliably
- [ ] Both peers see each other's video
- [ ] Captions appear when accessibility mode is on
- [ ] Chat messages are exchanged
- [ ] TTS speaks captions
- [ ] Keyboard shortcuts work
- [ ] Can leave call cleanly

## 🔐 Security Notes

**For Development Only:**
- CORS is wide open (all origins allowed)
- No authentication/authorization
- No HTTPS (required for production WebRTC)
- No rate limiting

**For Production:**
- Add proper authentication (JWT, OAuth)
- Restrict CORS to specific domains
- Use HTTPS with valid certificates
- Add rate limiting and input validation
- Use TURN server for NAT traversal
- Implement proper error handling

## 📚 Additional Documentation

- `backend/DEBUG_REPORT.md` - Backend debugging guide
- `frontend/DEBUG_REPORT.md` - Frontend debugging guide
- `docs/FIREBASE_SETUP.md` - Firebase integration (optional)
- `docs/ML_SETUP.md` - Real ASL model training (optional)

## 🤝 Contributing

This is a hackathon/demo project. For production use:
1. Replace mock inference with trained ASL models
2. Add proper authentication
3. Implement TURN server for NAT traversal
4. Add end-to-end encryption
5. Implement proper error handling and logging

## 📝 License

MIT License - See LICENSE file for details

## 🎯 Demo Script (2 Minutes)

**Presenter:**

1. "I'll show you a video call app with real-time sign language recognition."

2. **[Open two browser tabs]**
   - "Tab 1 creates a room, Tab 2 joins with the code."

3. **[Enable cameras]**
   - "Both participants can see each other."

4. **[Turn on Accessibility Mode in Tab 1]**
   - "Now I enable ASL recognition."

5. **[Wave hand in front of camera]**
   - "The system detects hand gestures and generates captions in real-time."
   - "Tab 2 sees the captions appear automatically."

6. **[Click speaker icon]**
   - "The browser reads the captions aloud using text-to-speech."

7. **[Type in chat]**
   - "We also have text chat for additional communication."

8. "This enables deaf/hard-of-hearing users to communicate naturally in video calls."

**Total time: ~2 minutes**

## 🚀 Next Steps

- [ ] Train real ASL model on dataset
- [ ] Add user authentication
- [ ] Implement TURN server
- [ ] Add recording functionality
- [ ] Mobile app (React Native)
- [ ] Multi-language support
- [ ] Gesture customization
- [ ] Analytics dashboard

---

**Built with ❤️ for accessibility**
