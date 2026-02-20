# ASL Sign Language Video Call System - Setup Guide

Complete setup instructions for the ASL (American Sign Language) recognition system integrated into the video call application.

## 🎯 Overview

This system provides real-time ASL alphabet recognition with:
- **29 classes**: A-Z letters, space, del, nothing
- **MobileNetV2 architecture**: Fast, accurate recognition
- **7-frame stability buffer**: Robust predictions
- **Text generation**: Letter → Word → Sentence
- **TTS synthesis**: Automatic audio generation
- **WebSocket streaming**: Real-time frame processing

## 📋 Prerequisites

### System Requirements
- Python 3.11+
- Node.js 18+
- Webcam (for video capture)
- 4GB+ RAM
- GPU (optional, for faster training)

### Required Accounts
- **Kaggle Account** (for dataset download)
  - Sign up at https://www.kaggle.com
  - Generate API token at https://www.kaggle.com/settings/account
  - Download `kaggle.json` credentials

## 🚀 Installation

### 1. Install Python Dependencies

```bash
# Install all dependencies including TensorFlow and gTTS
pip install -r requirements.txt
```

Key packages installed:
- `tensorflow>=2.13.0` - ASL model training/inference
- `gtts>=2.5.0` - Text-to-speech audio generation
- `kaggle>=1.6.0` - Dataset download
- `opencv-python>=4.8` - Image processing
- `mediapipe==0.10.32` - Hand detection

### 2. Configure Kaggle API

```bash
# Create Kaggle config directory
mkdir -p ~/.kaggle

# Copy your kaggle.json credentials
cp /path/to/kaggle.json ~/.kaggle/kaggle.json

# Set permissions (Linux/Mac)
chmod 600 ~/.kaggle/kaggle.json
```

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

## 🎓 Training the ASL Model

### Option 1: Automatic Training (Recommended)

```bash
# Run training script (downloads dataset automatically)
python backend/train_asl_model.py
```

This will:
1. Download ASL Alphabet dataset from Kaggle (~1.1GB)
2. Extract to `backend/data/asl_alphabet_train/`
3. Train MobileNetV2 model (20 epochs, ~30 minutes)
4. Save model to `backend/models/asl_mobilenetv2.h5`

### Option 2: Manual Dataset Download

If automatic download fails:

1. Visit: https://www.kaggle.com/datasets/grassknoted/asl-alphabet
2. Download dataset ZIP
3. Extract to: `backend/data/asl_alphabet_train/`
4. Run training: `python backend/train_asl_model.py`

### Training Configuration

Edit `backend/train_asl_model.py` to customize:

```python
IMG_SIZE = 224          # Input image size
BATCH_SIZE = 32         # Batch size for training
EPOCHS = 20             # Number of training epochs
LEARNING_RATE = 0.001   # Initial learning rate
```

### Expected Training Results

- **Training Accuracy**: ~98%
- **Validation Accuracy**: ~95%
- **Top-3 Accuracy**: ~99%
- **Model Size**: ~14MB
- **Inference Time**: <50ms per frame

## 🏃 Running the System

### 1. Start Backend Server

```bash
# Start FastAPI backend with CV pipeline
python backend/server.py
```

Backend runs on: `http://localhost:8000`

WebSocket endpoints:
- `/ws/{session_id}/{user_id}` - General signaling
- `/ws/cv/{session_id}/{user_id}` - ASL recognition

### 2. Start Frontend

```bash
cd frontend
npm run dev
```

Frontend runs on: `http://localhost:3000`

### 3. Use ASL Mode

1. Join a video call
2. Click the **Eye icon** in the control bar to enable ASL mode
3. Position your hand in front of the camera
4. Sign ASL letters (A-Z)
5. Use gestures:
   - **Open palm**: Space (confirm word)
   - **Fist**: Confirm sentence (triggers TTS)
   - **Two fingers**: Delete last letter

## 🎮 ASL Recognition Flow

### Letter Recognition
1. Camera captures frames at 24 FPS
2. Frames throttled to 10 FPS for processing
3. Hand detection via MediaPipe
4. ASL classification via MobileNetV2
5. 7-frame stability buffer ensures accuracy
6. Letter added to current word

### Word Confirmation
- **Space gesture**: Confirms current word
- **1.5s idle**: Auto-confirms sentence

### Sentence Confirmation
- **Fist gesture**: Confirms sentence
- Triggers TTS audio generation
- Sends audio to all participants

## 📊 WebSocket Message Schema

### Client → Server (Video Frame)

```json
{
  "type": "video_frame",
  "frame_id": 123,
  "timestamp": 1234567890,
  "image": "<base64-jpeg>",
  "session_id": "room-abc",
  "user_id": "user-123"
}
```

### Server → Client (Caption)

```json
{
  "type": "caption",
  "level": "live | word | sentence",
  "text": "HELLO",
  "confidence": 0.95,
  "timestamp": 1234567890
}
```

### Server → Client (Audio)

```json
{
  "type": "audio",
  "format": "mp3",
  "data": "<base64-mp3>",
  "timestamp": 1234567890
}
```

### Server → Client (Error)

```json
{
  "type": "error",
  "code": "MODEL_NOT_FOUND",
  "message": "ASL model not found",
  "severity": "fatal",
  "timestamp": 1234567890
}
```

## 🔧 Configuration

### Backend Configuration

Edit `backend/server.py`:

```python
# Frame queue depth (drop oldest if full)
FRAME_QUEUE_MAX = 3

# Confidence threshold for ASL predictions
CONFIDENCE_THRESHOLD = 0.85

# Stability frames required
STABILITY_FRAMES = 7
```

### Frontend Configuration

Edit `frontend/src/services/ASLCaptureService.ts`:

```typescript
const config = {
  captureFrameRate: 24,  // FPS for capture
  sendFrameRate: 10,     // FPS for sending
  jpegQuality: 0.8,      // JPEG quality (0-1)
  reconnectAttempts: 3,  // Max reconnection attempts
  reconnectDelay: 2000   // Delay between reconnects (ms)
};
```

## 🐛 Troubleshooting

### Model Not Found Error

**Error**: `ASL model not found at backend/models/asl_mobilenetv2.h5`

**Solution**:
```bash
# Train the model
python backend/train_asl_model.py
```

### Kaggle API Error

**Error**: `Could not find kaggle.json`

**Solution**:
```bash
# Configure Kaggle credentials
mkdir -p ~/.kaggle
cp kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
```

### TensorFlow Import Error

**Error**: `No module named 'tensorflow'`

**Solution**:
```bash
# Install TensorFlow
pip install tensorflow>=2.13.0
```

### Camera Access Denied

**Error**: `Failed to access camera`

**Solution**:
- Grant camera permissions in browser
- Check if camera is in use by another app
- Try HTTPS instead of HTTP (required by some browsers)

### Low Recognition Accuracy

**Solutions**:
- Ensure good lighting
- Position hand clearly in frame
- Sign letters distinctly
- Wait for stability indicator (7 frames)
- Retrain model with more data

### WebSocket Connection Failed

**Error**: `Failed to connect to ws://localhost:8000`

**Solution**:
```bash
# Ensure backend is running
python backend/server.py

# Check backend logs for errors
```

## 📈 Performance Optimization

### Backend Optimization

1. **Use GPU for inference**:
   ```bash
   # Install TensorFlow GPU
   pip install tensorflow-gpu>=2.13.0
   ```

2. **Adjust frame queue depth**:
   ```python
   # Increase for smoother processing
   FRAME_QUEUE_MAX = 5
   ```

3. **Reduce confidence threshold** (if too strict):
   ```python
   CONFIDENCE_THRESHOLD = 0.80
   ```

### Frontend Optimization

1. **Reduce send frame rate** (lower bandwidth):
   ```typescript
   sendFrameRate: 5  // Instead of 10
   ```

2. **Lower JPEG quality** (faster encoding):
   ```typescript
   jpegQuality: 0.6  // Instead of 0.8
   ```

## 🧪 Testing

### Test ASL Classifier

```bash
# Test classifier with sample image
python -c "
from app.inference.asl_classifier import create_asl_classifier
import cv2

classifier = create_asl_classifier()
frame = cv2.imread('test_image.jpg')
frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
prediction = classifier.predict(frame_rgb)
print(f'Letter: {prediction.letter}, Confidence: {prediction.confidence}')
"
```

### Test Text Generator

```bash
# Test text generation
python -c "
from app.inference.text_generator import create_text_generator

generator = create_text_generator()
generator.add_letter('H')
generator.add_letter('E')
generator.add_letter('L')
generator.add_letter('L')
generator.add_letter('O')
print(f'Current word: {generator.get_live_caption()}')
"
```

### Test WebSocket Connection

```bash
# Test WebSocket endpoint
python -c "
import asyncio
import websockets
import json

async def test():
    uri = 'ws://localhost:8000/ws/cv/test-session/test-user'
    async with websockets.connect(uri) as ws:
        print('Connected!')
        # Send test frame
        await ws.send(json.dumps({
            'type': 'video_frame',
            'frame_id': 1,
            'timestamp': 1234567890,
            'image': 'base64-data-here',
            'session_id': 'test-session',
            'user_id': 'test-user'
        }))
        response = await ws.recv()
        print(f'Response: {response}')

asyncio.run(test())
"
```

## 📚 Additional Resources

### ASL Alphabet Reference
- [ASL Alphabet Chart](https://www.startasl.com/american-sign-language-alphabet/)
- [ASL Fingerspelling Practice](https://www.lifeprint.com/asl101/fingerspelling/)

### Dataset Information
- [Kaggle ASL Alphabet Dataset](https://www.kaggle.com/datasets/grassknoted/asl-alphabet)
- 87,000 images across 29 classes
- 200x200 RGB images
- Diverse backgrounds and lighting

### Model Architecture
- **Base**: MobileNetV2 (ImageNet pre-trained)
- **Input**: 224x224 RGB
- **Output**: 29 classes (softmax)
- **Layers**: GlobalAveragePooling → Dense(256) → Dense(29)

## 🤝 Contributing

To improve ASL recognition:

1. **Collect more training data**:
   ```bash
   # Use data collection script
   python ml/collect_landmarks.py
   ```

2. **Fine-tune model**:
   - Adjust learning rate
   - Add data augmentation
   - Increase training epochs

3. **Add new gestures**:
   - Extend `CLASS_NAMES` in `asl_classifier.py`
   - Retrain model with new classes

## 📝 License

This ASL recognition system is part of the Sign Language Accessibility project.

## 🆘 Support

For issues or questions:
1. Check troubleshooting section above
2. Review backend logs: `backend/server.py` output
3. Check browser console for frontend errors
4. Verify model file exists: `backend/models/asl_mobilenetv2.h5`

---

**Ready to use ASL recognition!** 🎉

Start the backend, train the model, and enable ASL mode in your video calls.
