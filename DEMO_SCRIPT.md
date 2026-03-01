# 2-Minute Demo Script

## Setup (Before Demo)

1. Start backend: `cd backend && python simple_server.py`
2. Start frontend: `cd frontend && npm run dev`
3. Open two browser tabs: http://localhost:5173

## Demo Flow (2 Minutes)

### Minute 1: Setup & Connection

**[0:00-0:15] Introduction**
> "I'm going to show you a video calling app with real-time sign language recognition that helps deaf and hard-of-hearing users communicate."

**[0:15-0:30] Create Room (Tab A)**
1. Click "Create Room"
2. Show room code (e.g., "ABC123")
3. Enable camera when prompted

**[0:30-0:45] Join Room (Tab B)**
1. Click "Join Room"
2. Enter room code "ABC123"
3. Enable camera when prompted

**[0:45-1:00] Verify Connection**
> "Both participants can now see each other in real-time."

### Minute 2: Features Demo

**[1:00-1:15] Enable Accessibility Mode (Tab A)**
1. Click 🧏 button (Accessibility Mode)
2. Show purple indicator appears

**[1:15-1:30] Demonstrate ASL Recognition**
1. Wave hand in front of camera (Tab A)
2. Point to captions appearing in Tab B
> "The system detects hand gestures and generates live captions."

**[1:30-1:45] Text-to-Speech**
1. Click 🔊 speaker icon
2. Browser reads captions aloud
> "Captions can be spoken aloud using text-to-speech."

**[1:45-2:00] Chat Feature**
1. Type message in chat: "Hello!"
2. Show message appears in both tabs
> "Users can also communicate via text chat."

**[2:00] Closing**
> "This enables natural communication for deaf/hard-of-hearing users in video calls. Thank you!"

## Backup Talking Points

If extra time or questions:

- **Technology**: "Built with React, FastAPI, and WebRTC for peer-to-peer video."
- **Accessibility**: "Follows WCAG AA guidelines with keyboard navigation and screen reader support."
- **Privacy**: "Video streams are peer-to-peer, not stored on servers."
- **Offline**: "Uses mock ASL model for demo - can be replaced with trained models."

## Troubleshooting During Demo

### Camera Not Working
- "Let me refresh the page..."
- Close other apps using camera
- Try different browser tab

### No Captions Appearing
- "Let me toggle accessibility mode off and on..."
- Check that hand is visible in frame
- Ensure good lighting

### Connection Issues
- "Let me restart the backend server..."
- Check both tabs are on same room code
- Verify WebSocket connection in console (F12)

## Demo Checklist

Before starting:
- [ ] Backend running (http://localhost:8001/health returns 200)
- [ ] Frontend running (http://localhost:5173 loads)
- [ ] Camera working (test in system settings)
- [ ] Two browser tabs open
- [ ] Good lighting for camera
- [ ] Audio working (for TTS demo)
- [ ] No other apps using camera

## Quick Recovery Commands

If something breaks:

**Restart Backend:**
```bash
# Kill process
Ctrl+C

# Restart
python backend/simple_server.py
```

**Restart Frontend:**
```bash
# Kill process
Ctrl+C

# Restart
npm run dev
```

**Clear Browser Cache:**
```
Ctrl+Shift+Delete → Clear cache → Reload page
```

## Success Criteria

Demo is successful if:
- ✅ Both tabs see each other's video
- ✅ Captions appear when hand is waved
- ✅ TTS speaks captions
- ✅ Chat messages are exchanged
- ✅ No errors in browser console

## Time Allocation

| Time | Activity |
|------|----------|
| 0:00-0:15 | Introduction |
| 0:15-0:30 | Create room |
| 0:30-0:45 | Join room |
| 0:45-1:00 | Verify connection |
| 1:00-1:15 | Enable accessibility |
| 1:15-1:30 | Show ASL recognition |
| 1:30-1:45 | Demonstrate TTS |
| 1:45-2:00 | Show chat + closing |

**Total: 2:00 minutes**

---

**Practice this script 2-3 times before the actual demo!**
