# Sign Language Translator (Hackathon Prototype)

A local, real-time accessibility prototype that detects hand landmarks from webcam input and converts stable gesture poses into live text captions with optional spoken output.

This version is intentionally **model-free** for now:
- Uses MediaPipe Hands for landmark extraction.
- Uses heuristic movement + gesture control logic.
- Includes clean placeholder logic where an ML classifier will be integrated later.

## Features

- Streamlit interface with:
  - Large live caption panel
  - Confirmed transcript panel
  - Camera preview with debug overlay
  - Status indicator (`Running`, `Paused`, `No Hand`, `Camera Error`, `Stopped`)
  - Buttons: `Pause/Resume`, `Clear`, `Speak` (+ `Start/Stop`, `Retry Camera`)
- OpenCV camera lifecycle management (safe open/read/release)
- MediaPipe hand detection with 21-landmark extraction
- Movement state tracking (`idle`, `stable`, `moving`, `moving_fast`)
- Gesture controls with debouncing + cooldown:
  - Open palm -> Pause/Resume
  - Fist -> Confirm sentence
  - Two fingers -> Undo last word
- Safety behavior:
  - Friendly runtime error messaging
  - Last valid frame/state freeze on detection issues
  - Graceful camera failure handling

## Project Layout

```text
app/
+-- main.py
+-- UI/ui.py
+-- camera/camera.py
+-- inference/
    +-- hand_detector.py
    +-- movement_tracker.py
    +-- gesture_controls.py
    +-- debug_overlay.py
```

## Setup

1. Create and activate a virtual environment.

Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
pip install -r requirements.txt
```

3. Run the app.

```powershell
streamlit run app/main.py
```

## ML Workflow (Implemented)

The project now includes a full local training pipeline in `ml/`:

- `ml/collect_landmarks.py` -> collect labeled hand-landmark sequences
- `ml/train_landmark_model.py` -> train classifier artifact
- `ml/evaluate_landmark_model.py` -> evaluate trained model
- `ml/landmark_features.py` -> shared preprocessing/feature pipeline

Train in this order:

1. Collect samples for each label (repeat per class):

```powershell
python ml/collect_landmarks.py --label HELLO --samples 30 --frames 24 --signer-id signer_01
```

2. Train model:

```powershell
python ml/train_landmark_model.py --data-dir ml/datasets/raw --out-model ml/models/landmark_classifier.pkl
```

3. Evaluate model:

```powershell
python ml/evaluate_landmark_model.py --model-path ml/models/landmark_classifier.pkl --data-dir ml/datasets/raw
```

4. Run app:
   - `app/main.py` will auto-load `ml/models/landmark_classifier.pkl` when present.
   - If model file is missing/invalid, app falls back to heuristic placeholder mode.

## How To Use

1. Press `Start`.
2. Keep one hand centered and well lit.
3. Use gestures:
   - Open palm -> pause/resume
   - Fist -> confirm current live words as a sentence
   - Two fingers -> undo last word
4. Press `Speak` to read current transcript via browser speech synthesis.
5. Press `Clear` to reset live and confirmed captions.

## Current Limitations

- No trained sign-language classifier yet (only heuristic placeholder tokens).
- Single-process local app (no cloud sync / multi-user networking in this flow).
- Works best with one primary hand and stable lighting.
- Very low-end devices may run at reduced FPS.

## Next Steps (ML Integration)

1. Replace placeholder token logic with a trained sequence classifier over landmark windows.
2. Add temporal decoding (CTC/beam search or language model post-processing).
3. Add per-user calibration for hand size/orientation and camera placement.
4. Add domain vocabulary packs for calls (healthcare, education, customer support).
5. Add automated tests for gesture controls and movement-state transitions.
