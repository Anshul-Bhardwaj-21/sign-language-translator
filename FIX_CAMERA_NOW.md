# 🎥 Camera Fix - Step by Step

## Problem
Camera nahi chal raha because:
1. Backend server nahi chal raha (port 8000)
2. Video element play() interrupted error

## Solution - Do This NOW

### Step 1: Start Backend Server
```bash
# Option A: Use the batch file
START_BACKEND.bat

# Option B: Manual command
cd backend
python server.py
```

**You should see:**
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Keep Backend Running
Leave that terminal window open! Backend must keep running.

### Step 3: Start Frontend (in NEW terminal)
```bash
cd frontend
npm run dev
```

### Step 4: Test Camera
1. Go to `http://localhost:5173`
2. Create or join a room
3. In pre-join lobby, click "Turn on camera preview"
4. Allow camera permission when browser asks
5. Camera should work now!

## If Camera Still Not Working

### Check 1: Backend Running?
Open `http://localhost:8000/docs` in browser
- If it loads → Backend is running ✅
- If error → Backend not running ❌

### Check 2: Camera Permission?
1. Click the lock icon in browser address bar
2. Check if camera is "Allowed"
3. If "Blocked", change to "Allow" and refresh

### Check 3: Other Apps Using Camera?
Close these apps:
- Zoom
- Microsoft Teams
- Skype
- Any other video app

### Check 4: Browser Console
Press F12, check for errors:
- Red errors about camera → Permission issue
- "ERR_CONNECTION_REFUSED" → Backend not running

## Quick Test - Is Everything Working?

### Test Backend
```bash
curl http://localhost:8000/health
```
Should return: `{"status":"healthy"}`

### Test Frontend
Open: `http://localhost:5173`
Should show landing page

### Test Camera
1. Join a room
2. Click camera preview button
3. Browser asks for permission → Click "Allow"
4. Camera feed should appear

## Common Errors & Fixes

### Error: "ERR_CONNECTION_REFUSED"
**Fix:** Backend not running
```bash
cd backend
python server.py
```

### Error: "NotAllowedError: Permission denied"
**Fix:** Camera permission blocked
1. Click lock icon in address bar
2. Camera → Allow
3. Refresh page

### Error: "NotFoundError: Requested device not found"
**Fix:** No camera detected
1. Check if camera is connected
2. Try different browser
3. Check Device Manager (Windows)

### Error: "AbortError: The play() request was interrupted"
**Fix:** This is normal, ignore it. It happens when toggling camera quickly.

## Still Not Working?

### Nuclear Option - Reset Everything
```bash
# Stop all servers (Ctrl+C in both terminals)

# Clear browser cache
# Chrome: Ctrl+Shift+Delete → Clear cache

# Restart backend
cd backend
python server.py

# Restart frontend (new terminal)
cd frontend
npm run dev

# Try again
```

## What Should Work After Fix

✅ Backend running on port 8000
✅ Frontend running on port 5173
✅ Camera preview in pre-join lobby
✅ Camera toggle in video call
✅ Professional icons (no emojis)
✅ FPS counter (only when video ON)
✅ Display name input with validation

## Next Steps After Camera Works

Once camera is working, you'll have:
1. Working camera preview
2. Professional UI with icons
3. Display name validation
4. Complete video call interface
5. Admin controls
6. Chat panel
7. Participants list
8. Screen sharing
9. Raise hand
10. Accessibility mode

## Need More Help?

Share these details:
1. Backend terminal output
2. Frontend terminal output
3. Browser console errors (F12)
4. Which browser you're using
5. Operating system

I'll help you debug! 🚀
