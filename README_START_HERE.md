# 🎯 START HERE - Video Call App

## Problem: Camera Nahi Chal Raha?

**Reason:** Backend server nahi chal raha hai!

## Solution (2 Commands)

### Terminal 1 - Backend
```bash
cd backend
python server.py
```
**Keep running!** ✅

### Terminal 2 - Frontend
```bash
cd frontend
npm run dev
```
**Keep running!** ✅

### Browser
```
http://localhost:5173
```

## That's It! 🚀

Camera will work now. Test karo:
1. Create/Join room
2. Enter name
3. Click "Turn on camera preview"
4. Allow permission
5. Camera works! ✅

## All Features Working

✅ Camera preview
✅ Professional icons (no emojis)
✅ FPS (only when video ON)
✅ Display name validation
✅ Camera toggle
✅ Mic toggle
✅ Screen share
✅ Raise hand
✅ Chat
✅ Participants
✅ Admin controls
✅ Accessibility mode

## Need More Help?

Read these files:
1. `RUN_THIS_FIRST.md` - Detailed steps
2. `FIX_CAMERA_NOW.md` - Camera troubleshooting
3. `COMPLETE_SOLUTION.md` - Everything explained

## Quick Check

Backend running?
```bash
curl http://localhost:8000/health
```

Should return: `{"status":"healthy"}`

If not, backend nahi chal raha. Start karo!

---

**That's all you need to know. Start backend, start frontend, camera will work!** 💪
