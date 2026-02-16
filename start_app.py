#!/usr/bin/env python3
"""
Simple startup script for the Sign Language Video Call app.

This script provides an easy way to start the app with proper error handling
and helpful messages for common issues.
"""

import sys
import subprocess
import os
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = ['streamlit', 'cv2', 'mediapipe', 'numpy']
    missing = []
    
    for package in required_packages:
        try:
            if package == 'cv2':
                import cv2
            elif package == 'streamlit':
                import streamlit
            elif package == 'mediapipe':
                import mediapipe
            elif package == 'numpy':
                import numpy
        except ImportError:
            missing.append(package)
    
    return missing

def main():
    """Main startup function."""
    print("🤟 Sign Language Video Call App")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("app/main_meet.py").exists():
        print("❌ Error: app/main_meet.py not found")
        print("Please run this script from the project root directory")
        return 1
    
    # Check dependencies
    print("Checking dependencies...")
    missing = check_dependencies()
    
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("\nTo install dependencies, run:")
        print("  pip install -r requirements-minimal.txt")
        print("  OR")
        print("  pip install -r requirements.txt")
        return 1
    
    print("✅ All dependencies found")
    
    # Start the app
    print("\n🚀 Starting the app...")
    print("The app will open in your browser at: http://localhost:8501")
    print("Press Ctrl+C to stop the app")
    print("-" * 40)
    
    try:
        # Run streamlit
        result = subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "app/main_meet.py",
            "--server.headless", "true",
            "--server.address", "localhost",
            "--server.port", "8501"
        ])
        return result.returncode
    except KeyboardInterrupt:
        print("\n👋 App stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Error starting app: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())