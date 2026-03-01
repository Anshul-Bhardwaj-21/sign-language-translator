# 🚀 RUN ME FIRST

## Welcome!

You have a **complete, working React + Python video meeting system** ready to run.

## What You Need

- ✅ Node.js 18+ installed
- ✅ Python 3.10+ installed

Check:
```bash
node --version
python --version
```

## Run It Now (Copy & Paste)

### Step 1: Install Frontend Dependencies

```bash
cd frontend
npm install
```

### Step 2: Start Backend (New Terminal)

```bash
python backend/enhanced_server.py
```

### Step 3: Start Frontend (New Terminal)

```bash
cd frontend
npm run dev
```

### Step 4: Open Browser

```
http://localhost:3000
```

## What You'll See

1. **Landing Page** - Click "Create New Room"
2. **Pre-Join Lobby** - See your room code, configure settings
3. **Video Call** - Your video meeting with ML-powered captions!

## Try This

1. Click "Create New Room"
2. Click "Turn on camera preview" (optional)
3. Click "Join Meeting"
4. Click the 🧏 button (accessibility mode)
5. Show your hand to camera
6. See "Hand Detected" status
7. See captions appear!

## Need Help?

- **Quick Start:** Read `GETTING_STARTED.md`
- **Full Guide:** Read `START_HERE.md`
- **Documentation:** Read `README.md`

## Troubleshooting

### "npm: command not found"
Install Node.js: https://nodejs.org/

### "Module not found: mediapipe"
```bash
pip install mediapipe opencv-python numpy fastapi uvicorn
```

### Camera not working
- Allow camera permission in browser
- Chrome: chrome://settings/content/camera

## Success!

If you see the landing page and can create a room, **you're all set!** 🎉

The system is working correctly.

---

**Next:** Read `GETTING_STARTED.md` for more details.

