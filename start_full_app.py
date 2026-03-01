#!/usr/bin/env python3
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