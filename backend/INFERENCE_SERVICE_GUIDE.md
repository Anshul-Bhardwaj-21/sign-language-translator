# Sign Language Inference Service Guide

## Overview

The Sign Language Inference Service is a FastAPI-based REST API that provides real-time sign language recognition. It accepts video frames, extracts hand landmarks using MediaPipe, loads production models from the MLflow model registry, and returns predictions with confidence scores.

**Phase:** MVP  
**Requirements:** 33.1, 33.2, 33.3, 33.7, 33.8, 33.12

## Features

- **POST /predict** - Sign language prediction endpoint
- **Video frame input** - Accepts frames via multipart/form-data
- **Server-side landmark extraction** - Uses MediaPipe on the server
- **Production model loading** - Loads models from MLflow registry
- **Confidence filtering** - Filters predictions below 0.7 threshold
- **GPU acceleration** - Uses GPU when available, falls back to CPU
- **Health checks** - Provides health endpoint for load balancers
- **Model management** - List, view, and deploy models

## Architecture

```
Client → POST /predict → Inference Service
                          ↓
                    1. Decode frames
                    2. Extract landmarks (MediaPipe)
                    3. Preprocess (normalize, pad/truncate)
                    4. Run inference (PyTorch model)
                    5. Apply confidence threshold (0.7)
                    6. Return prediction
```

## Prerequisites

1. **MLflow tracking server** running with model registry
2. **Production model** registered and tagged as "Production"
3. **MediaPipe hand landmarker model** downloaded
4. **Python dependencies** installed

### Setup

```bash
# 1. Install dependencies
pip install fastapi uvicorn python-multipart opencv-python mediapipe torch mlflow

# 2. Download MediaPipe model
python backend/storage/datasets/download_mediapipe_model.py

# 3. Ensure MLflow is running
python backend/setup_mlflow.py
bash backend/start_mlflow.sh

# 4. Register a production model (if not already done)
# Train a model and register it with "Production" tag
python backend/models/train_model.py --config backend/models/training_config_example.yaml
```

## Running the Service

### Development Mode

```bash
# Start with auto-reload
python backend/inference_service.py --reload

# Or using uvicorn directly
uvicorn inference_service:app --host 0.0.0.0 --port 8001 --reload
```

### Production Mode

```bash
# Start without reload
python backend/inference_service.py --host 0.0.0.0 --port 8001

# Or with gunicorn for production
gunicorn inference_service:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001
```

The service will be available at `http://localhost:8001`

## API Endpoints

### POST /predict

Predict sign language gesture from video frames.

**Request:**

```bash
curl -X POST http://localhost:8001/predict \
  -F "frames=@frame1.jpg" \
  -F "frames=@frame2.jpg" \
  -F "frames=@frame3.jpg" \
  -F "user_id=user123" \
  -F "meeting_id=meeting456" \
  -F "sign_language=ASL"
```

**Parameters:**
- `frames` (required): List of image files (JPEG/PNG)
- `user_id` (required): User ID making the request
- `meeting_id` (required): Meeting ID
- `sign_language` (optional): Sign language type (ASL/BSL), default: ASL

**Response (High Confidence):**

```json
{
  "gesture": "hello",
  "confidence": 0.85,
  "timestamp": "2024-01-15T10:30:45.123456",
  "latency_ms": 145.2,
  "strategy_used": "cloud",
  "message": null
}
```

**Response (Low Confidence - Filtered):**

```json
{
  "gesture": null,
  "confidence": null,
  "timestamp": "2024-01-15T10:30:45.123456",
  "latency_ms": 132.8,
  "strategy_used": "cloud",
  "message": "Prediction confidence below threshold (0.7)"
}
```

**Response (No Landmarks Detected):**

```json
{
  "gesture": null,
  "confidence": null,
  "timestamp": "2024-01-15T10:30:45.123456",
  "latency_ms": 98.5,
  "strategy_used": "cloud",
  "message": "No hand landmarks detected in frames"
}
```

### GET /health

Health check endpoint for load balancers.

**Request:**

```bash
curl http://localhost:8001/health
```

**Response:**

```json
{
  "status": "healthy",
  "model_loaded": true,
  "device": "cuda",
  "model_name": "sign-language-asl",
  "model_version": "3"
}
```

### GET /models

List all registered model versions.

**Request:**

```bash
curl http://localhost:8001/models
```

**Response:**

```json
{
  "models": [
    {
      "name": "sign-language-asl",
      "version": 3,
      "stage": "Production",
      "run_id": "abc123...",
      "created_at": 1705315845000,
      "status": "READY"
    },
    {
      "name": "sign-language-asl",
      "version": 2,
      "stage": "Archived",
      "run_id": "def456...",
      "created_at": 1705229445000,
      "status": "READY"
    }
  ],
  "total": 2
}
```

### GET /models/{model_id}

Get details for a specific model version.

**Request:**

```bash
curl http://localhost:8001/models/3
```

**Response:**

```json
{
  "name": "sign-language-asl",
  "version": 3,
  "run_id": "abc123...",
  "current_stage": "Production",
  "creation_timestamp": 1705315845000,
  "description": "CNN+LSTM model trained on v1.0.0 dataset",
  "tags": {
    "accuracy": "0.87",
    "f1_score": "0.85",
    "dataset_version": "v1.0.0",
    "num_classes": "50"
  }
}
```

### POST /models/{model_id}/deploy

Deploy a model version to production.

**Request:**

```bash
curl -X POST http://localhost:8001/models/4/deploy
```

**Response:**

```json
{
  "message": "Model version 4 deployed to production",
  "model_name": "sign-language-asl",
  "version": 4,
  "stage": "Production"
}
```

### GET /metrics

Get service metrics for monitoring.

**Request:**

```bash
curl http://localhost:8001/metrics
```

**Response:**

```json
{
  "service": "inference_service",
  "model_loaded": true,
  "device": "cuda",
  "confidence_threshold": 0.7,
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

## Configuration

### Environment Variables

```bash
# MLflow tracking URI
export MLFLOW_TRACKING_URI=http://localhost:5000

# Model name to load
export MODEL_NAME=sign-language-asl

# Confidence threshold (default: 0.7)
export CONFIDENCE_THRESHOLD=0.7

# Device (auto-detected if not set)
export DEVICE=cuda  # or cpu
```

### Model Registry Configuration

The service loads models from the MLflow model registry. Ensure:

1. MLflow tracking server is running
2. A model is registered with name `sign-language-asl`
3. At least one version is tagged as "Production"

```python
# Example: Register and deploy a model
from models.model_registry import ModelRegistry

registry = ModelRegistry()

# Register model
model_version = registry.register_model(
    model_uri="runs:/abc123/model",
    model_name="sign-language-asl",
    metadata={"accuracy": 0.87, "f1_score": 0.85}
)

# Deploy to production
registry.transition_model_stage(
    model_name="sign-language-asl",
    version=model_version.version,
    stage="Production",
    archive_existing_versions=True
)
```

## Processing Pipeline

### 1. Frame Decoding

Frames are received as multipart/form-data and decoded using OpenCV:

```python
# Decode JPEG/PNG to numpy array
nparr = np.frombuffer(content, np.uint8)
frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
```

### 2. Landmark Extraction

MediaPipe HandLandmarker extracts 42 keypoints (21 per hand):

```python
# Extract landmarks
landmarks = detector.detect_landmarks(frame)
# Shape: (42, 3) - 42 keypoints × (x, y, z) coordinates
```

### 3. Preprocessing

Landmarks are normalized and padded/truncated to fixed sequence length:

```python
# Flatten landmarks: (42, 3) → (126,)
# Stack frames: [(126,), (126,), ...] → (N, 126)
# Pad/truncate: (N, 126) → (60, 126)
# Add batch: (60, 126) → (1, 60, 126)
```

### 4. Inference

PyTorch model predicts gesture class:

```python
# Run inference
output = model(input_tensor)  # (1, num_classes)
confidence, predicted_class = torch.max(output, dim=1)
```

### 5. Confidence Filtering

Predictions below 0.7 confidence are filtered:

```python
if confidence < 0.7:
    return None, None  # No prediction
else:
    return gesture_name, confidence
```

## Performance

### Latency Requirements

- **Target:** <200ms per prediction (Requirement 33.4)
- **Typical:** 100-150ms on GPU, 150-200ms on CPU

### Latency Breakdown

- Frame decoding: 10-20ms
- Landmark extraction: 30-50ms (MediaPipe)
- Preprocessing: 5-10ms
- Inference: 50-100ms (GPU) or 100-150ms (CPU)
- Response formatting: <5ms

### Optimization Tips

1. **Use GPU** - Significantly faster inference (50-100ms vs 100-150ms)
2. **Batch processing** - Process multiple requests together
3. **Model optimization** - Use TorchScript or ONNX for faster inference
4. **Reduce frame count** - Send fewer frames (e.g., 30 instead of 60)
5. **Compress frames** - Use lower JPEG quality for faster upload

## Testing

### Run Unit Tests

```bash
# Run all tests
pytest backend/test_inference_service.py -v

# Run specific test class
pytest backend/test_inference_service.py::TestPredictEndpoint -v

# Run with coverage
pytest backend/test_inference_service.py --cov=inference_service --cov-report=html
```

### Manual Testing

```bash
# 1. Start the service
python backend/inference_service.py

# 2. Check health
curl http://localhost:8001/health

# 3. Test prediction with sample frames
# (Requires actual video frames)
curl -X POST http://localhost:8001/predict \
  -F "frames=@test_frame1.jpg" \
  -F "frames=@test_frame2.jpg" \
  -F "user_id=test_user" \
  -F "meeting_id=test_meeting"
```

### Load Testing

```bash
# Install locust
pip install locust

# Create locustfile.py
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between

class InferenceUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def predict(self):
        files = {
            'frames': ('frame.jpg', open('test_frame.jpg', 'rb'), 'image/jpeg')
        }
        data = {
            'user_id': 'load_test_user',
            'meeting_id': 'load_test_meeting'
        }
        self.client.post("/predict", files=files, data=data)
EOF

# Run load test
locust -f locustfile.py --host http://localhost:8001
```

## Troubleshooting

### Model Not Loading

**Error:** "Production model not loaded. Service not ready."

**Solutions:**
1. Check MLflow is running: `curl http://localhost:5000/health`
2. Verify model exists: `curl http://localhost:8001/models`
3. Check model has "Production" tag
4. Review logs for detailed error messages

### MediaPipe Model Not Found

**Error:** "MediaPipe model not found"

**Solution:**
```bash
python backend/storage/datasets/download_mediapipe_model.py
```

### Low Inference Performance

**Issue:** Latency >200ms

**Solutions:**
1. Use GPU: Check `device` in `/health` endpoint
2. Reduce frame count: Send fewer frames per request
3. Optimize model: Use TorchScript or quantization
4. Scale horizontally: Deploy multiple service instances

### No Landmarks Detected

**Issue:** All predictions return "No hand landmarks detected"

**Solutions:**
1. Check frame quality: Ensure hands are visible
2. Adjust lighting: MediaPipe works best with good lighting
3. Lower confidence threshold: Reduce `min_detection_confidence`
4. Check frame format: Ensure frames are valid JPEG/PNG

## Deployment

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ backend/

# Download MediaPipe model
RUN python backend/storage/datasets/download_mediapipe_model.py

# Expose port
EXPOSE 8001

# Run service
CMD ["uvicorn", "backend.inference_service:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inference-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: inference-service
  template:
    metadata:
      labels:
        app: inference-service
    spec:
      containers:
      - name: inference-service
        image: inference-service:latest
        ports:
        - containerPort: 8001
        env:
        - name: MLFLOW_TRACKING_URI
          value: "http://mlflow:5000"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: inference-service
spec:
  selector:
    app: inference-service
  ports:
  - port: 8001
    targetPort: 8001
  type: LoadBalancer
```

## Monitoring

### Prometheus Metrics

TODO: Implement Prometheus metrics endpoint

```python
# Future implementation
from prometheus_client import Counter, Histogram

prediction_counter = Counter('predictions_total', 'Total predictions')
prediction_latency = Histogram('prediction_latency_seconds', 'Prediction latency')
```

### Logging

Logs are written to stdout in structured format:

```
2024-01-15 10:30:45 - INFO - Initialized MediaPipe HandLandmarker
2024-01-15 10:30:46 - INFO - Loading production model: sign-language-asl
2024-01-15 10:30:47 - INFO - ✓ Production model loaded successfully on cuda
2024-01-15 10:30:48 - INFO - Received 30 frames from user user123
2024-01-15 10:30:48 - INFO - Prediction: gesture=hello, confidence=0.850, latency=145.2ms
```

## Requirements Mapping

| Requirement | Implementation |
|-------------|----------------|
| 33.1 | POST /predict endpoint |
| 33.2 | Accept video frames via multipart/form-data |
| 33.3 | Return gesture label and confidence in PredictionResponse |
| 33.7 | confidence_threshold = 0.7 |
| 33.8 | Return None when confidence < threshold |
| 33.12 | load_production_model() on startup |

## Next Steps

1. **Implement drift detection** - Log predictions for monitoring
2. **Add Prometheus metrics** - Expose metrics for Grafana
3. **Optimize inference** - Use TorchScript or ONNX
4. **Add batch processing** - Process multiple requests together
5. **Implement caching** - Cache model and MediaPipe detector
6. **Add A/B testing** - Support multiple model versions
7. **Implement gesture vocabulary** - Map class indices to gesture names

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MediaPipe Hand Landmarker](https://developers.google.com/mediapipe/solutions/vision/hand_landmarker)
- [MLflow Model Registry](https://mlflow.org/docs/latest/model-registry.html)
- [PyTorch Inference](https://pytorch.org/tutorials/beginner/saving_loading_models.html)
