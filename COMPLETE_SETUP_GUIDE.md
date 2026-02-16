# Complete Setup Guide - React + Python Sign Language Video Call App

## 🏗️ Architecture Overview

Your app uses a modern full-stack architecture:
- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: Python + FastAPI + WebSocket + ML Processing
- **Real-time**: WebSocket connections for live captions
- **ML**: MediaPipe + OpenCV for hand detection and gesture recognition

## 🚀 Quick Start (3 Steps)

### 1. Install Dependencies

#### Python Backend Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# OR minimal installation
pip install fastapi uvicorn opencv-python mediapipe numpy websockets
```

#### Node.js Frontend Dependencies
```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Go back to project root
cd ..
```

### 2. Start the Complete App
```bash
# Option 1: Use the startup script (recommended)
python start_full_app.py

# Option 2: Start services manually (see Manual Setup below)
```

### 3. Use the App
1. **Open browser**: Go to http://localhost:5173
2. **Landing page**: Click "Join Meeting" or "Create Room"
3. **Lobby screen**: Enter room code and your name
4. **Camera preview**: Test camera (optional)
5. **Join meeting**: Click "JOIN MEETING"
6. **Enable accessibility**: Toggle accessibility mode for sign language recognition
7. **Start signing**: Your gestures will be translated to live captions!

## 📋 Manual Setup (Alternative)

If you prefer to start services separately:

### Terminal 1 - Backend
```bash
# Start Python FastAPI backend
python backend/enhanced_server.py

# Should show: "Uvicorn running on http://0.0.0.0:8000"
```

### Terminal 2 - Frontend
```bash
# Navigate to frontend and start React dev server
cd frontend
npm run dev

# Should show: "Local: http://localhost:5173"
```

## 🔧 Prerequisites

### System Requirements
- **Python**: 3.8+ (tested with 3.14)
- **Node.js**: 16+ (for React frontend)
- **Camera**: Webcam or built-in camera
- **Browser**: Chrome, Firefox, or Edge (WebRTC support)

### Installation Check
```bash
# Check Python version
python --version

# Check Node.js version
node --version

# Check if camera is accessible
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.read()[0] else 'Camera Error'); cap.release()"
```

## 🎯 App Features & Usage

### Landing Page (http://localhost:5173)
- **Create Room**: Generate a new meeting room
- **Join Meeting**: Enter existing room code

### Pre-Join Lobby
- **Room Code**: Enter meeting room code
- **Display Name**: Your name for the meeting
- **Camera Preview**: Test camera before joining (optional)
- **Accessibility Mode**: Enable sign language recognition

### Video Call Interface
- **Camera Controls**: Turn camera on/off
- **Microphone**: Mute/unmute (placeholder)
- **Accessibility Mode**: Toggle sign language recognition
- **Live Captions**: Real-time gesture translation
- **Caption History**: Scrollable history of confirmed captions
- **Text-to-Speech**: Speak captions aloud
- **Keyboard Shortcuts**: M (mic), V (video), A (accessibility), P (pause)

### Sign Language Recognition
- **Supported Gestures**: Hello, Yes, and other trained signs
- **Real-time Processing**: Live gesture detection and translation
- **Confidence Indicators**: Visual feedback on recognition accuracy
- **Movement Tracking**: Only processes stable hand positions

## 🔍 Troubleshooting

### Backend Issues
```bash
# Check if backend is running
curl http://localhost:8000/health

# View backend logs
python backend/enhanced_server.py

# Common fixes
pip install --upgrade fastapi uvicorn opencv-python mediapipe
```

### Frontend Issues
```bash
# Check if frontend is running
curl http://localhost:5173

# Reinstall dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install

# Common fixes
npm install --legacy-peer-deps
```

### Camera Issues
```bash
# Test camera access
python -c "import cv2; cap = cv2.VideoCapture(0); ret, frame = cap.read(); print('Camera working' if ret else 'Camera failed'); cap.release()"

# Browser permissions
# - Allow camera access when prompted
# - Check browser settings for camera permissions
# - Close other apps using the camera
```

### WebSocket Connection Issues
```bash
# Check if WebSocket endpoint is accessible
# Backend should show WebSocket connections in logs

# Common fixes:
# - Restart both backend and frontend
# - Check firewall settings
# - Try different browser
```

## 🌐 URLs & Endpoints

### Frontend (React)
- **Main App**: http://localhost:5173
- **Landing**: http://localhost:5173/
- **Lobby**: http://localhost:5173/lobby/{roomCode}
- **Call**: http://localhost:5173/call/{roomCode}

### Backend (FastAPI)
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Create Room**: POST http://localhost:8000/api/rooms/create
- **Join Room**: POST http://localhost:8000/api/rooms/{roomCode}/join
- **ML Processing**: POST http://localhost:8000/api/ml/process-frame
- **WebSocket**: ws://localhost:8000/ws/{roomCode}/{userId}

## 📊 Performance Tips

### Optimal Settings
- **Camera Resolution**: 640x480 or 1280x720
- **Lighting**: Good, even lighting on hands
- **Background**: Contrasting background for better detection
- **Distance**: 2-3 feet from camera
- **Browser**: Chrome recommended for best WebRTC support

### System Resources
- **CPU**: Modern multi-core processor recommended
- **RAM**: 4GB+ available memory
- **Network**: Stable internet for WebSocket connections

## 🔒 Security Notes

### Development Mode
- CORS is configured for localhost only
- WebSocket connections are unencrypted (ws://)
- No authentication required

### Production Considerations
- Use HTTPS/WSS in production
- Implement proper authentication
- Configure CORS for your domain
- Add rate limiting for ML processing

## 🎉 Success Indicators

If everything is working correctly:

1. ✅ **Backend**: http://localhost:8000/health returns "healthy"
2. ✅ **Frontend**: http://localhost:5173 loads the landing page
3. ✅ **Camera**: Video preview works in lobby
4. ✅ **WebSocket**: Real-time connection established
5. ✅ **ML Processing**: Hand detection and gesture recognition active
6. ✅ **Captions**: Live sign language translation working

## 🚨 Common Error Solutions

### "Module not found" errors
```bash
pip install -r requirements.txt
cd frontend && npm install
```

### "Camera access denied"
- Allow camera permissions in browser
- Close other apps using camera
- Try different browser

### "WebSocket connection failed"
- Restart backend server
- Check if port 8000 is available
- Verify CORS settings

### "ML processing failed"
- Check if MediaPipe is properly installed
- Verify camera is working
- Check backend logs for detailed errors

The app is now ready for professional sign language video calls with real-time accessibility features! 🎉