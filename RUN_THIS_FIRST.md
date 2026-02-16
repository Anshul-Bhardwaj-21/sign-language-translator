# 🚀 RUN THIS FIRST - Simple 3-Step Guide

## Your Problem
Camera nahi chal raha because **backend server nahi chal raha hai**.

## Solution (3 Steps)

### Step 1: Start Backend
Open **Command Prompt** or **PowerShell** and run:
```bash
cd backend
python server.py
```

**Keep this window open!** You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Start Frontend
Open **NEW** Command Prompt/PowerShell and run:
```bash
cd frontend
npm run dev
```

**Keep this window open too!** You should see:
```
VITE ready in XXX ms
Local: http://localhost:5173/
```

### Step 3: Open Browser
Go to: `http://localhost:5173`

## Test Camera

1. Click "Create Room" or "Join Room"
2. Enter room code (if joining)
3. **Enter your name** (required!)
4. Click "Turn on camera preview"
5. Browser will ask for camera permission → Click **"Allow"**
6. Camera should work! ✅

## Quick Check - Is Backend Running?

Open this in browser: `http://localhost:8000/docs`
- If it loads → Backend is running ✅
- If error → Backend not running, go back to Step 1 ❌

## If Camera Still Not Working

### 1. Close Other Apps
Close these if open:
- Zoom
- Microsoft Teams
- Skype
- Any video calling app

### 2. Check Browser Permission
1. Click the **lock icon** in address bar
2. Find "Camera" → Should be "Allow"
3. If "Block", change to "Allow"
4. Refresh page

### 3. Try Different Browser
- Chrome (best)
- Edge (good)
- Firefox (good)
- Safari (may have issues)

## What You'll See When It Works

### Pre-Join Lobby
- Display name input (required)
- Camera preview button
- Microphone toggle
- Accessibility mode toggle
- Professional icons (no emojis!)

### Video Call Page
- Your video feed
- Camera toggle button (Video icon)
- Mic toggle button (Mic icon)
- Screen share button
- Raise hand button
- Chat button
- Participants button
- Accessibility button
- Leave button
- FPS counter (only when video is ON)

## All Features Available

✅ Camera preview before joining
✅ Display name validation
✅ Professional icon buttons
✅ Multi-participant grid layout
✅ Admin controls (you're the host):
   - Mute all participants
   - Mute individual participant
   - Remove participant
   - Ask to speak
✅ Chat panel
✅ Participants list
✅ Screen sharing
✅ Raise hand
✅ Accessibility mode (sign language)
✅ FPS counter (only when video ON)

## Still Having Issues?

Run this command to check everything:
```bash
# Check if backend is running
curl http://localhost:8000/health

# Should return: {"status":"healthy"}
```

If you see errors, share:
1. Backend terminal output
2. Frontend terminal output  
3. Browser console errors (press F12)

I'll help you fix it! 🎯
