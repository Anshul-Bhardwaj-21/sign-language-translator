# ML Data Schema Documentation

This document defines the data formats and schemas used throughout the ML pipeline for the Sign Language Accessibility application.

## Overview

The ML pipeline processes hand landmark sequences to recognize sign language gestures. Data flows through collection → preprocessing → training → inference.

---

## 1. Hand Landmark Format

### MediaPipe Hand Landmarks

Each hand is represented by 21 3D landmarks:

```
Landmark Index | Name
---------------|------------------
0              | Wrist
1-4            | Thumb (CMC, MCP, IP, TIP)
5-8            | Index finger (MCP, PIP, DIP, TIP)
9-12           | Middle finger (MCP, PIP, DIP, TIP)
13-16          | Ring finger (MCP, PIP, DIP, TIP)
17-20          | Pinky finger (MCP, PIP, DIP, TIP)
```

### Coordinate System

- **X**: Horizontal position (0.0 = left, 1.0 = right)
- **Y**: Vertical position (0.0 = top, 1.0 = bottom)
- **Z**: Depth (negative = closer to camera)

Coordinates are normalized relative to image dimensions.

### Raw Landmark Array

```python
landmarks: np.ndarray
# Shape: (21, 3)
# dtype: float32
# Range: X,Y in [0.0, 1.0], Z in [-1.0, 1.0]
```

---

## 2. Sequence Format

### Temporal Sequence

A gesture is represented as a sequence of landmark frames:

```python
sequence: np.ndarray
# Shape: (T, 21, 3)
# T = number of frames (typically 24)
# 21 = number of landmarks
# 3 = coordinates (x, y, z)
```

### Sequence Length

- **Training**: Fixed length (default: 24 frames)
- **Collection**: Variable length (resampled to fixed)
- **Inference**: Sliding window of fixed length

---

## 3. Dataset File Format

### NPZ File Structure

Each sample is stored as a `.npz` file:

```python
{
    'landmarks': np.ndarray,      # (T, 21, 3) - landmark sequence
    'label': str,                 # Gesture class name
    'signer_id': str,             # Unique signer identifier
    'timestamp': float,           # Unix timestamp
    'metadata': dict              # Optional metadata
}
```

### Directory Structure

```
data_dir/
├── HELLO/
│   ├── sample_001.npz
│   ├── sample_002.npz
│   └── ...
├── YES/
│   ├── sample_001.npz
│   └── ...
└── annotations.csv (optional)
```

### Annotations CSV (Optional)

```csv
filename,label,signer_id,timestamp,duration_frames,quality_score
HELLO/sample_001.npz,HELLO,signer_01,1708041600.0,24,0.95
HELLO/sample_002.npz,HELLO,signer_01,1708041620.0,26,0.92
...
```

---

## 4. Preprocessed Features

### Normalized Landmarks

After preprocessing:

```python
normalized_landmarks: np.ndarray
# Shape: (T, 21, 3)
# Centered around wrist (landmark 0)
# Scaled by hand size
# Range: approximately [-1.0, 1.0]
```

### Flattened Features

For model input:

```python
features: np.ndarray
# Shape: (T, 63)
# 63 = 21 landmarks * 3 coordinates
# Flattened from (T, 21, 3)
```

### Augmented Features (Training Only)

Augmentations applied:
- Random rotation (±15°)
- Random scaling (0.9-1.1x)
- Gaussian noise (σ=0.01)

---

## 5. Model Input/Output

### Model Input

```python
input_tensor: torch.Tensor
# Shape: (batch_size, sequence_length, 63)
# dtype: torch.float32
# Normalized and preprocessed landmarks
```

### Model Output

```python
output_tensor: torch.Tensor
# Shape: (batch_size, num_classes)
# dtype: torch.float32
# Logits (pre-softmax scores)
```

### Prediction

```python
probabilities = torch.softmax(output_tensor, dim=1)
predicted_class = torch.argmax(probabilities, dim=1)
confidence = probabilities[0, predicted_class]
```

---

## 6. Training Checkpoint Format

### Checkpoint Dictionary

```python
checkpoint = {
    'epoch': int,                          # Training epoch
    'model_state_dict': OrderedDict,       # Model weights
    'optimizer_state_dict': OrderedDict,   # Optimizer state
    'val_acc': float,                      # Validation accuracy
    'val_loss': float,                     # Validation loss
    'classes': List[str],                  # Class names
    'sequence_length': int,                # Sequence length
    'model_type': str,                     # 'conv_lstm' or 'tcn'
    'hidden_dim': int,                     # Hidden dimension
    'incremental_updates': int             # Number of incremental updates
}
```

### File Extension

- PyTorch models: `.pth`
- Legacy models: `.pkl` (pickle format)

---

## 7. Correction Data Format

### User Correction

When user corrects a misrecognition:

```python
correction = {
    'original_text': str,           # Misrecognized text
    'corrected_text': str,          # Correct text
    'landmark_sequence': np.ndarray, # (T, 21, 3)
    'timestamp': float,             # Unix timestamp
    'user_id': str,                 # User identifier
    'confidence': float             # Original prediction confidence
}
```

### Correction NPZ File

```python
{
    'landmarks': np.ndarray,        # (T, 21, 3)
    'corrected_label': str,         # Correct class name
    'original_label': str,          # Misrecognized class
    'user_id': str,
    'timestamp': float
}
```

---

## 8. Firebase Data Schema

### Captions Collection

```javascript
{
  session_id: string,
  user_id: string,
  text: string,
  timestamp: number,
  is_confirmed: boolean,
  created_at: Timestamp
}
```

### Corrections Collection

```javascript
{
  user_id: string,
  original_text: string,
  corrected_text: string,
  landmark_sequence: array,  // Serialized
  timestamp: number,
  created_at: Timestamp,
  processed: boolean
}
```

### Sessions Collection

```javascript
{
  session_id: string,
  participants: array<string>,
  accessibility_mode: boolean,
  created_at: Timestamp,
  active: boolean,
  ended_at: Timestamp (optional)
}
```

---

## 9. Real-time Inference Format

### Landmark Buffer

During inference, landmarks are buffered:

```python
landmark_buffer: List[List[Tuple[float, float, float]]]
# List of frames, each frame is list of 21 landmarks
# Each landmark is (x, y, z) tuple
# Buffer size: sequence_length * 3 (for sliding window)
```

### Prediction Result

```python
prediction = {
    'label': str,              # Predicted class
    'confidence': float,       # Confidence score [0, 1]
    'latency_ms': float,       # Inference time
    'timestamp': float         # Prediction timestamp
}
```

---

## 10. Data Validation Rules

### Landmark Validation

```python
def validate_landmarks(landmarks: np.ndarray) -> bool:
    """Validate landmark array."""
    # Check shape
    if landmarks.shape != (21, 3):
        return False
    
    # Check coordinate ranges
    if not (0.0 <= landmarks[:, 0].min() and landmarks[:, 0].max() <= 1.0):
        return False
    if not (0.0 <= landmarks[:, 1].min() and landmarks[:, 1].max() <= 1.0):
        return False
    
    # Check for NaN/Inf
    if np.isnan(landmarks).any() or np.isinf(landmarks).any():
        return False
    
    return True
```

### Sequence Validation

```python
def validate_sequence(sequence: np.ndarray, min_length: int = 10) -> bool:
    """Validate sequence array."""
    # Check shape
    if sequence.ndim != 3 or sequence.shape[1:] != (21, 3):
        return False
    
    # Check minimum length
    if sequence.shape[0] < min_length:
        return False
    
    # Validate each frame
    for frame in sequence:
        if not validate_landmarks(frame):
            return False
    
    return True
```

---

## 11. Data Augmentation Parameters

### Default Augmentation Config

```yaml
augmentation:
  rotation_range: 15.0        # degrees
  scale_range: [0.9, 1.1]     # min, max
  noise_std: 0.01             # Gaussian noise
  temporal_jitter: 0.1        # Frame timing variation
  flip_horizontal: false      # Not recommended for signs
```

---

## 12. Feature Engineering

### Derived Features (Future)

Additional features that can be extracted:

```python
# Velocity features
velocities = np.diff(landmarks, axis=0)  # (T-1, 21, 3)

# Acceleration features
accelerations = np.diff(velocities, axis=0)  # (T-2, 21, 3)

# Hand angles
angles = compute_hand_angles(landmarks)  # (T, num_angles)

# Hand openness
openness = compute_hand_openness(landmarks)  # (T,)

# Finger spread
spread = compute_finger_spread(landmarks)  # (T,)
```

---

## 13. Data Quality Metrics

### Quality Score

Each sample can have a quality score:

```python
quality_score = {
    'visibility': float,        # Fraction of landmarks visible
    'stability': float,         # Motion smoothness
    'confidence': float,        # Detection confidence
    'lighting': float,          # Lighting quality estimate
    'overall': float            # Weighted average
}
```

### Filtering Criteria

- Minimum visibility: 0.8 (80% of landmarks visible)
- Minimum confidence: 0.6
- Maximum velocity: 0.5 (normalized units)

---

## 14. Version Control

### Data Version

```python
data_version = {
    'schema_version': '1.0.0',
    'collection_date': '2026-02-14',
    'num_samples': 1000,
    'num_classes': 10,
    'signers': ['signer_01', 'signer_02', ...],
    'sequence_length': 24
}
```

---

## 15. Example Usage

### Loading a Sample

```python
import numpy as np

# Load sample
data = np.load('HELLO/sample_001.npz')
landmarks = data['landmarks']  # (T, 21, 3)
label = str(data['label'])     # 'HELLO'

# Validate
assert landmarks.shape[1:] == (21, 3)
assert label in VALID_CLASSES
```

### Creating a Sample

```python
import numpy as np
import time

# Collect landmarks (from MediaPipe)
landmarks_list = []
for frame in video_frames:
    landmarks = detect_hand(frame)  # (21, 3)
    landmarks_list.append(landmarks)

sequence = np.array(landmarks_list)  # (T, 21, 3)

# Save
np.savez(
    'output/HELLO/sample_001.npz',
    landmarks=sequence,
    label='HELLO',
    signer_id='signer_01',
    timestamp=time.time()
)
```

---

## 16. Data Privacy

### PII Handling

- No personally identifiable information in landmark data
- Signer IDs are anonymized (e.g., 'signer_01')
- Timestamps are Unix timestamps (no timezone info)
- No video/image data stored (only landmarks)

### GDPR Compliance

- Users can request data deletion
- Data is stored locally by default
- Firebase sync is optional
- Clear data retention policies

---

**Schema Version**: 1.0.0  
**Last Updated**: 2026-02-14  
**Maintained By**: ML Team
