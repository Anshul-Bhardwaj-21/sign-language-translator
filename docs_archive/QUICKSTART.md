# Quick Start Guide

Get the Sign Language Accessibility Video Call Application running in 5 minutes.

## Prerequisites

- Python 3.10 or higher
- Webcam
- 4GB RAM minimum
- Windows/macOS/Linux

## Installation

### 1. Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd sign-language-accessibility

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Application

```bash
streamlit run app/main.py
```

The app will open in your browser at `http://localhost:8501`

## First Use

1. **Grant Camera Permission**: Click "Allow" when prompted
2. **Click Start**: Initialize camera and hand detection
3. **Position Your Hand**: Keep one hand visible in the camera frame
4. **Try Gesture Controls**:
   - Open palm → Pause/Resume
   - Fist → Confirm sentence
   - Peace sign → Undo last word

## Optional: Train Your Own Model

### Generate Dummy Data (for testing)

```bash
python ml/dummy_data_generator.py \
  --num-classes 10 \
  --samples-per-class 50 \
  --output-dir ml/datasets/dummy
```

### Train Model

```bash
python ml/train.py \
  --data-dir ml/datasets/dummy \
  --epochs 20 \
  --batch-size 32 \
  --output ml/models/gesture_classifier.pth
```

### Evaluate Model

```bash
python ml/evaluate.py \
  --model-path ml/models/gesture_classifier.pth \
  --data-dir ml/datasets/dummy \
  --output-dir ml/evaluation
```

## Optional: Multi-User Video Calls

### Start Backend Server

```bash
python backend/server.py
```

Backend runs at `http://localhost:8000`

### Connect Multiple Clients

1. Open app in multiple browser windows
2. Each user gets their own session
3. Captions sync in real-time

## Optional: Firebase Setup

For cloud sync and multi-device support:

1. Create Firebase project at [console.firebase.google.com](https://console.firebase.google.com)
2. Download credentials JSON
3. Place in `configs/firebase-credentials.json`
4. Update `configs/config.yaml`:
   ```yaml
   firebase:
     enabled: true
   ```

See [docs/FIREBASE_SETUP.md](docs/FIREBASE_SETUP.md) for detailed instructions.

## Troubleshooting

### Camera Not Working

- Check camera permissions in system settings
- Close other apps using the camera
- Try different camera index in `configs/config.yaml`:
  ```yaml
  camera:
    index: 1  # Try 0, 1, 2, etc.
  ```

### MediaPipe Errors

```bash
pip uninstall mediapipe
pip install mediapipe==0.10.8
```

### Low FPS

- Close other applications
- Reduce camera resolution in `configs/config.yaml`:
  ```yaml
  camera:
    width: 640
    height: 480
  ```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## Next Steps

- Read [README.md](README.md) for full documentation
- Check [docs/EDGE_CASES.md](docs/EDGE_CASES.md) for edge case handling
- Collect real sign language data for training
- Customize gesture controls in `configs/config.yaml`

## Support

- Documentation: `docs/` folder
- Issues: [GitHub Issues](link-to-issues)
- Email: [support-email]

---

**Happy Signing! 🤟**
