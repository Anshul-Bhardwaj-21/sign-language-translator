# Project Structure

## Overview

This is a React + Python video meeting system with ML-powered sign language recognition.

## Directory Structure

```
sign-language-translator/
│
├── frontend/                    # React + TypeScript frontend
│   ├── src/
│   │   ├── pages/
│   │   │   ├── LandingPage.tsx          # Create/join rooms
│   │   │   ├── PreJoinLobby.tsx         # Camera preview, settings
│   │   │   └── VideoCallPage.tsx        # Video call with ML
│   │   ├── services/
│   │   │   ├── api.ts                   # API client
│   │   │   └── FrameCaptureManager.ts   # ML frame capture
│   │   ├── styles/
│   │   │   └── index.css                # Global styles
│   │   ├── App.tsx                      # Main app with routing
│   │   └── main.tsx                     # Entry point
│   ├── package.json                     # Dependencies
│   ├── vite.config.ts                   # Build config
│   ├── tsconfig.json                    # TypeScript config
│   ├── tailwind.config.js               # Tailwind config
│   └── index.html                       # HTML template
│
├── backend/                     # Python + FastAPI backend
│   ├── enhanced_server.py               # ML-integrated server
│   ├── server.py                        # Original WebSocket server
│   └── firebase_integration.py          # Firebase client (optional)
│
├── app/                         # Your existing ML code
│   ├── inference/
│   │   ├── hand_detector.py             # MediaPipe hand detection
│   │   ├── movement_tracker.py          # Motion tracking
│   │   ├── gesture_controls.py          # Gesture controls
│   │   └── debug_overlay.py             # Debug overlay
│   ├── camera/
│   │   └── camera.py                    # Camera management
│   ├── server/
│   │   ├── call_manager.py              # Call management
│   │   ├── messaging.py                 # Messaging
│   │   └── video_stream_manager.py      # Video streaming
│   ├── metrics.py                       # Performance metrics
│   ├── error_handler.py                 # Error handling
│   ├── tts.py                           # Text-to-speech
│   └── call_session.py                  # Call sessions
│
├── ml/                          # ML models and training
│   ├── model.py                         # PyTorch models
│   ├── train.py                         # Training script
│   ├── evaluate.py                      # Evaluation
│   ├── dataset_loader.py                # Dataset utilities
│   ├── preprocess.py                    # Preprocessing
│   ├── incremental_learning.py          # Online learning
│   ├── dummy_data_generator.py          # Test data
│   └── checkpoints/                     # Model checkpoints
│
├── tests/                       # Test suite
│   ├── test_camera.py
│   ├── test_ml_pipeline.py
│   ├── test_backend.py
│   └── test_smoothing.py
│
├── docs/                        # Documentation
│   ├── EDGE_CASES.md                    # Edge case handling
│   ├── FIREBASE_SETUP.md                # Firebase setup
│   ├── UI_GUIDE.md                      # UI guide
│   └── UI_QUICK_REFERENCE.md            # Quick reference
│
├── docs_archive/                # Archived documentation
│   └── (old architecture docs)
│
├── old_streamlit_app/           # Old Streamlit UI (archived)
│   └── (old UI files)
│
├── configs/
│   └── config.yaml                      # Configuration
│
├── logs/                        # Log files
│
├── README.md                    # Main documentation
├── GETTING_STARTED.md           # Quick start guide
├── START_HERE.md                # Detailed getting started
├── SETUP_INSTRUCTIONS.md        # Setup guide
├── REACT_IMPLEMENTATION_README.md  # React docs
├── IMPLEMENTATION_GUIDE.md      # Implementation guide
├── IMPLEMENTATION_SUMMARY.md    # What was built
├── WHATS_IMPLEMENTED.md         # Feature checklist
├── requirements.txt             # Python dependencies
└── start-dev.bat                # Windows startup script
```

## Key Files

### Frontend Entry Points
- `frontend/src/main.tsx` - Application entry point
- `frontend/src/App.tsx` - Main app with routing
- `frontend/index.html` - HTML template

### Backend Entry Points
- `backend/enhanced_server.py` - Main server (use this one)
- `backend/server.py` - Original server (legacy)

### ML Integration
- `app/inference/hand_detector.py` - Hand detection
- `app/inference/movement_tracker.py` - Movement tracking
- `frontend/src/services/FrameCaptureManager.ts` - Frame capture

### Configuration
- `frontend/.env` - Frontend environment variables
- `configs/config.yaml` - Application configuration
- `frontend/vite.config.ts` - Build configuration

## What to Run

### Development
```bash
# Backend
python backend/enhanced_server.py

# Frontend
cd frontend && npm run dev
```

### Production Build
```bash
# Build frontend
cd frontend && npm run build

# Serve with any static server
```

## What to Modify

### To Change UI
- Edit files in `frontend/src/pages/`
- Modify styles in `frontend/src/styles/`
- Update Tailwind config in `frontend/tailwind.config.js`

### To Change ML Logic
- Edit `backend/enhanced_server.py` (process_frame function)
- Modify `app/inference/` files
- Update ML models in `ml/`

### To Add Features
- Add new pages in `frontend/src/pages/`
- Add new API endpoints in `backend/enhanced_server.py`
- Add new services in `frontend/src/services/`

## Archived Files

### docs_archive/
Old architecture documentation (for reference only)

### old_streamlit_app/
Old Streamlit UI (replaced by React)

## Documentation

### Getting Started
1. **GETTING_STARTED.md** - 5-minute quick start
2. **START_HERE.md** - Detailed getting started
3. **SETUP_INSTRUCTIONS.md** - Step-by-step setup

### Implementation
4. **REACT_IMPLEMENTATION_README.md** - Complete React docs
5. **IMPLEMENTATION_GUIDE.md** - Architecture guide
6. **IMPLEMENTATION_SUMMARY.md** - What was built
7. **WHATS_IMPLEMENTED.md** - Feature checklist

### Reference
8. **docs/EDGE_CASES.md** - Edge case handling
9. **docs/FIREBASE_SETUP.md** - Firebase setup
10. **docs/UI_GUIDE.md** - UI guide

## Clean Structure

The repository is now organized as:
1. **frontend/** - All React code
2. **backend/** - All Python server code
3. **app/** - ML and inference code
4. **ml/** - ML models and training
5. **docs/** - Current documentation
6. **docs_archive/** - Old documentation
7. **old_streamlit_app/** - Old UI (archived)

This structure clearly separates:
- Frontend (React) from Backend (Python)
- Current code from archived code
- Documentation from implementation

