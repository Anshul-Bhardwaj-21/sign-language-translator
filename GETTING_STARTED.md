# Getting Started - 5 Minutes to Running

## What You're About to Run

A complete React + Python video meeting system with real-time sign language recognition.

## Prerequisites

Check you have these installed:

```bash
# Check Node.js (need 18+)
node --version

# Check Python (need 3.10+)
python --version
```

Don't have them? Install:
- **Node.js**: https://nodejs.org/ (download LTS version)
- **Python**: https://www.python.org/downloads/

## Installation (First Time Only)

### Step 1: Install Frontend Dependencies

```bash
cd frontend
npm install
```

Wait for: `added 200 packages in 45s`

### Step 2: Verify Backend Dependencies

Your Python dependencies should already be installed. If not:

```bash
pip install fastapi uvicorn mediapipe opencv-python numpy pydantic
```

## Running the Application

### Terminal 1: Start Backend

```bash
# From project root
python backend/enhanced_server.py
```

Wait for: `Uvicorn running on http://0.0.0.0:8000`

### Terminal 2: Start Frontend

```bash
# From project root
cd frontend
npm run dev
```

Wait for: `Local: http://localhost:3000/`

### Browser: Open Application

Go to: **http://localhost:3000**

## Try It Out

1. Click **"Create New Room"**
2. You'll see a room code (e.g., "ABC123")
3. Camera preview is OFF (as required)
4. Click **"Turn on camera preview"** to test
5. Click **"Join Meeting"**
6. You're in the video call!
7. Click **🧏** button to enable accessibility mode
8. Show your hand to camera
9. See "Hand Detected" status
10. See captions appear!

## Troubleshooting

### "npm: command not found"
Install Node.js from https://nodejs.org/

### "Module not found: mediapipe"
```bash
pip install mediapipe opencv-python numpy
```

### Camera permission denied
- Chrome: chrome://settings/content/camera
- Allow localhost to access camera
- Refresh page

### Port already in use
```bash
# Kill port 3000
npx kill-port 3000

# Kill port 8000 (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

## What's Next?

- Read **README.md** for full documentation
- Check **START_HERE.md** for detailed guide
- See **REACT_IMPLEMENTATION_README.md** for architecture

## Quick Commands

```bash
# Start backend
python backend/enhanced_server.py

# Start frontend (new terminal)
cd frontend && npm run dev

# Install dependencies (first time)
cd frontend && npm install

# Build for production
cd frontend && npm run build
```

## Success!

If you can:
- ✅ Create a room
- ✅ See camera preview
- ✅ Join meeting
- ✅ See hand detection working

**You're all set!** The system is working correctly. 🎉

