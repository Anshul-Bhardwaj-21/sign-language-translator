# How to Run the Complete Sign Language Video Call App

## 🚀 Quick Start (Recommended)

### 1. Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Or use minimal requirements for basic functionality
pip install -r requirements-minimal.txt
```

### 2. Run the App with Lobby
```bash
# Navigate to project root
cd /path/to/sign-language-translator

# Run the Meet-style UI with lobby
streamlit run app/main_meet.py
```

### 3. Use the App
1. **Lobby Screen**: App starts with a professional lobby interface
2. **Enter Room Code**: Type any room code (e.g., "demo-room-123")
3. **Join Meeting**: Click "Join Meeting" button
4. **Camera Access**: Allow camera permissions when prompted
5. **Start Recognition**: Click the camera button to start sign language detection

## 📋 Complete Setup Instructions

### Prerequisites
- Python 3.8+ (tested with Python 3.14)
- Webcam/camera device
- Modern web browser (Chrome, Firefox, Edge)

### Step-by-Step Setup

#### 1. Environment Setup
```bash
# Clone or navigate to project directory
cd sign-language-translator

# Create virtual environment (recommended)
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

#### 2. Install Dependencies
```bash
# Full installation (includes ML training, Firebase, etc.)
pip install -r requirements.txt

# OR minimal installation (just for running the app)
pip install streamlit opencv-python mediapipe numpy pyttsx3
```

#### 3. Verify Installation
```bash
# Test the lobby implementation
python -m pytest tests/test_lobby.py -v

# Should show: 4 passed
```

## 🎯 Running Different Versions

### Option 1: Meet-Style UI with Lobby (Recommended)
```bash
streamlit run app/main_meet.py
```
- **Features**: Professional lobby, Meet-style interface, accessibility mode
- **URL**: http://localhost:8501
- **Best for**: Demos, production use, professional presentations

### Option 2: Demo Version (Alternative)
```bash
streamlit run app/demo_meet.py
```
- **Features**: Direct access to video call interface
- **URL**: http://localhost:8501
- **Best for**: Quick testing, development

### Option 3: Original UI (Legacy)
```bash
streamlit run old_streamlit_app/main.py
```
- **Features**: Original interface without Meet styling
- **Best for**: Fallback option

## 🔧 Troubleshooting

### Camera Issues
```bash
# Test camera access
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.read()[0] else 'Camera Error'); cap.release()"
```

### Import Errors
```bash
# Install missing dependencies
pip install streamlit opencv-python mediapipe numpy

# Check Python version
python --version  # Should be 3.8+
```

### Port Issues
```bash
# Run on different port
streamlit run app/main_meet.py --server.port 8502
```

## 🎮 Using the App

### Lobby Screen
1. **Room Code**: Enter any text (validation is visual only)
2. **Join Button**: Disabled until room code is entered
3. **Accessibility**: Preview toggle (enabled after joining)

### Video Call Interface
1. **Camera Control**: Start/stop video feed
2. **Accessibility Mode**: Enhanced visual feedback
3. **Pause/Resume**: Control recognition processing
4. **Clear Captions**: Remove all text
5. **Speak**: Text-to-speech for captions

### Gesture Recognition
- **Supported Gestures**: Hello, Fist, and other trained signs
- **Real-time Translation**: Live captions appear as you sign
- **Confidence Indicators**: Visual feedback on recognition quality

## 📊 Performance Tips

### Optimal Settings
- **Resolution**: 640x480 or 1280x720
- **Lighting**: Good, even lighting on hands
- **Background**: Contrasting background for better hand detection
- **Distance**: 2-3 feet from camera

### System Requirements
- **CPU**: Modern multi-core processor
- **RAM**: 4GB+ available
- **Camera**: 720p+ webcam
- **Browser**: Chrome/Firefox with WebRTC support

## 🔍 Features Overview

### ✅ Implemented Features
- **Professional Lobby**: Meet-style entry screen
- **Real-time Recognition**: Live sign language detection
- **Accessibility Mode**: Enhanced visual feedback
- **Text-to-Speech**: Audio output of captions
- **Dark Theme**: Professional video call appearance
- **Responsive Design**: Works on different screen sizes

### 🚧 Optional Features (Require Additional Setup)
- **Firebase Integration**: User accounts, session storage
- **WebRTC**: Multi-user video calls
- **ML Training**: Custom gesture training
- **Backend API**: REST API for integrations

## 📝 Quick Commands Reference

```bash
# Start the app
streamlit run app/main_meet.py

# Run tests
python -m pytest tests/ -v

# Install dependencies
pip install -r requirements.txt

# Check camera
python -c "import cv2; print('Camera:', cv2.VideoCapture(0).read()[0])"

# Different port
streamlit run app/main_meet.py --server.port 8502
```

## 🎉 Success!

If everything is working correctly, you should see:
1. Streamlit app opens in browser
2. Professional lobby screen appears
3. Room code input and join button work
4. After joining, camera access is requested
5. Video feed shows with sign language recognition

The app is now ready for use! The lobby provides a professional entry point, and the Meet-style interface offers a familiar video call experience with real-time sign language translation.