# Setup Instructions - Get Running in 5 Minutes

## Prerequisites Check

Before starting, ensure you have:

- ✅ **Python 3.10+** installed
  ```bash
  python --version
  ```

- ✅ **Node.js 18+** installed
  ```bash
  node --version
  ```

- ✅ **npm** installed
  ```bash
  npm --version
  ```

If missing, install from:
- Python: https://www.python.org/downloads/
- Node.js: https://nodejs.org/ (includes npm)

## Step-by-Step Setup

### 1. Install Frontend Dependencies (2 minutes)

```bash
cd frontend
npm install
```

This installs React, TypeScript, Tailwind CSS, and other dependencies.

**Expected output:**
```
added 200 packages in 45s
```

### 2. Verify Backend Dependencies (1 minute)

Your existing Python dependencies should already be installed. Verify:

```bash
python -c "import fastapi, mediapipe, cv2, numpy; print('✅ All dependencies installed')"
```

If you see errors, install missing packages:

```bash
pip install fastapi uvicorn mediapipe opencv-python numpy pydantic
```

### 3. Start Backend Server (30 seconds)

```bash
# From project root
python backend/enhanced_server.py
```

**Expected output:**
```
INFO:     Started server process
INFO:     HandDetector initialized successfully
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**✅ Backend is ready when you see "Uvicorn running"**

### 4. Start Frontend Server (30 seconds)

Open a **new terminal** (keep backend running):

```bash
cd frontend
npm run dev
```

**Expected output:**
```
  VITE v5.0.8  ready in 500 ms

  ➜  Local:   http://localhost:3000/
```

**✅ Frontend is ready when you see the Local URL**

### 5. Open in Browser (10 seconds)

Navigate to: **http://localhost:3000**

You should see the landing page with:
- "Sign Language Video Call" title
- "Create New Room" button
- Room code input field

## Quick Test

### Test 1: Create a Room

1. Click **"➕ Create New Room"**
2. You should be redirected to pre-join lobby
3. See a 6-character room code (e.g., "ABC123")

**✅ Room system works!**

### Test 2: Camera Preview

1. In pre-join lobby, click **"Turn on camera preview"**
2. Browser asks for camera permission → Click "Allow"
3. You should see your video feed

**✅ Camera access works!**

### Test 3: Join Meeting

1. Click **"Join Meeting"**
2. You should enter the video call page
3. See your video (if camera enabled)

**✅ Video call page works!**

### Test 4: Accessibility Mode

1. In video call, click the **🧏** button (accessibility mode)
2. Show your hand to the camera
3. Status bar should show "✋ Hand Detected"
4. If hand is stable, you'll see captions

**✅ ML integration works!**

## Troubleshooting

### Problem: "npm: command not found"

**Solution:** Install Node.js from https://nodejs.org/

### Problem: "Module not found: mediapipe"

**Solution:**
```bash
pip install mediapipe opencv-python numpy
```

### Problem: "Port 3000 already in use"

**Solution:**
```bash
# Kill process on port 3000
npx kill-port 3000

# Or change port in vite.config.ts:
server: { port: 3001 }
```

### Problem: "Port 8000 already in use"

**Solution:**
```bash
# Kill process on port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or change port in enhanced_server.py:
uvicorn.run(app, host="0.0.0.0", port=8001)
```

### Problem: Camera permission denied

**Solution:**
- Chrome: Go to chrome://settings/content/camera
- Allow localhost to access camera
- Refresh page

### Problem: Backend crashes on startup

**Solution:**
```bash
# Check Python version (need 3.10+)
python --version

# Reinstall dependencies
pip install -r requirements.txt

# Try running with verbose logging
python backend/enhanced_server.py --log-level debug
```

### Problem: Frontend shows blank page

**Solution:**
1. Check browser console (F12) for errors
2. Verify backend is running (http://localhost:8000/health)
3. Clear browser cache (Ctrl+Shift+Delete)
4. Try incognito mode

## Verification Checklist

After setup, verify everything works:

- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] Landing page loads in browser
- [ ] Can create a room
- [ ] Can see room code in pre-join lobby
- [ ] Camera preview works (optional)
- [ ] Can join meeting
- [ ] Video call page loads
- [ ] Control buttons respond
- [ ] Accessibility mode detects hand
- [ ] Captions appear when hand is stable

## What's Running

When everything is set up, you should have:

1. **Backend Server** (Terminal 1)
   - Running on http://localhost:8000
   - Processing ML requests
   - Managing rooms

2. **Frontend Server** (Terminal 2)
   - Running on http://localhost:3000
   - Serving React app
   - Hot-reloading on changes

3. **Browser** (http://localhost:3000)
   - React application
   - Video call interface
   - ML integration

## Quick Commands Reference

```bash
# Start backend
python backend/enhanced_server.py

# Start frontend
cd frontend && npm run dev

# Install frontend dependencies
cd frontend && npm install

# Install backend dependencies
pip install -r requirements.txt

# Build frontend for production
cd frontend && npm run build

# Check backend health
curl http://localhost:8000/health

# Stop all (Ctrl+C in each terminal)
```

## Next Steps

Once everything is running:

1. **Test the full flow** - Create room → Join → Enable accessibility → Show hand
2. **Read REACT_IMPLEMENTATION_README.md** - Detailed documentation
3. **Customize** - Change colors, fonts, add features
4. **Deploy** - Follow deployment guide for production

## Need Help?

If you're stuck:

1. Check the error message in terminal
2. Look at browser console (F12)
3. Verify all prerequisites are installed
4. Try restarting both servers
5. Check REACT_IMPLEMENTATION_README.md for detailed docs

## Success!

If you can:
- ✅ Create a room
- ✅ See camera preview
- ✅ Join meeting
- ✅ See hand detection working

**You're all set! The system is working correctly.** 🎉

Now you have a production-grade React + Python video meeting system with ML-powered sign language recognition!

