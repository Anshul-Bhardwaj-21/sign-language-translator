# 🚀 Complete React + Python Sign Language Video Call App

## Architecture Overview

- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: Python FastAPI with ML integration
- **ML**: MediaPipe hand detection + gesture recognition
- **Real-time**: WebSocket communication
- **Features**: Meeting lobby, video calls, live captions, accessibility mode

## 📋 Prerequisites

- **Node.js** 18+ (for React frontend)
- **Python** 3.8+ (for FastAPI backend)
- **Webcam** (for video capture)
- **Modern browser** (Chrome, Firefox, Edge)

## 🛠️ Setup Instructions

### 1. Backend Setup (Python FastAPI)

```bash
# Navigate to project root
cd sign-language-translator

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Or minimal installation:
pip install fastapi uvicorn opencv-python mediapipe numpy pydantic websockets
```

### 2. Frontend Setup (React)

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Or using yarn:
yarn install
```

### 3. Environment Configuration

Create environment file for frontend:

```bash
# In frontend/.env
VITE_API_URL=http://localhost:8000
```

## 🚀 Running the Application

### Method 1: Start Both Services Manually

**Terminal 1 - Backend:**
```bash
# From project root
python backend/enhanced_server.py

# Or using uvicorn directly:
uvicorn backend.enhanced_server:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
# From frontend directory
cd frontend
npm run dev

# Or using yarn:
yarn dev
```

### Method 2: Quick Start Script

Create a startup script:

<function_calls>
<invoke name="fsWrite">
<parameter name="path">start_full_app.py!/usr/bin/env python3
"""
Complete app startup script for React + Python architecture.
Starts both backend and frontend services.
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are available."""
    missing = []
    
    # Check Python dependencies
    try:
        import fastapi, uvicorn, cv2, mediapipe
    except ImportError as e:
        missing.append(f"Python: {e}")
    
    # Check Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            missing.append("Node.js not found")
    except FileNotFoundError:
        missing.append("Node.js not found")
    
    # Check if frontend dependencies are installed
    if not Path("frontend/node_modules").exists():
        missing.append("Frontend dependencies not installed (run: cd frontend && npm install)")
    
    return missing

def start_backend():
    """Start the Python FastAPI backend."""
    print("🐍 Starting Python backend...")
    
    backend_cmd = [
        sys.executable, "backend/enhanced_server.py"
    ]
    
    return subprocess.Popen(
        backend_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )

def start_frontend():
    """Start the React frontend."""
    print("⚛️  Starting React frontend...")
    
    frontend_cmd = ["npm", "run", "dev"]
    
    return subprocess.Popen(
        frontend_cmd,
        cwd="frontend",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )

def main():
    """Main startup function."""
    print("🤟 Sign Language Video Call App - Full Stack")
    print("=" * 50)
    
    # Check dependencies
    print("Checking dependencies...")
    missing = check_dependencies()
    
    if missing:
        print("❌ Missing dependencies:")
        for item in missing:
            print(f"  - {item}")
        print("\nPlease install missing dependencies and try again.")
        return 1
    
    print("✅ All dependencies found")
    
    # Start services
    backend_process = None
    frontend_process = None
    
    try:
        # Start backend
        backend_process = start_backend()
        time.sleep(3)  # Give backend time to start
        
        # Check if backend started successfully
        if backend_process.poll() is not None:
            print("❌ Backend failed to start")
            return 1
        
        print("✅ Backend started on http://localhost:8000")
        
        # Start frontend
        frontend_process = start_frontend()
        time.sleep(5)  # Give frontend time to start
        
        # Check if frontend started successfully
        if frontend_process.poll() is not None:
            print("❌ Frontend failed to start")
            return 1
        
        print("✅ Frontend started on http://localhost:5173")
        print("\n🎉 App is ready!")
        print("📱 Open your browser to: http://localhost:5173")
        print("🔧 Backend API: http://localhost:8000")
        print("\nPress Ctrl+C to stop both services")
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if backend_process.poll() is not None:
                print("❌ Backend process stopped unexpectedly")
                break
            
            if frontend_process.poll() is not None:
                print("❌ Frontend process stopped unexpectedly")
                break
    
    except KeyboardInterrupt:
        print("\n👋 Shutting down services...")
    
    finally:
        # Clean up processes
        if backend_process:
            backend_process.terminate()
            backend_process.wait()
        
        if frontend_process:
            frontend_process.terminate()
            frontend_process.wait()
        
        print("✅ Services stopped")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())