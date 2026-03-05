#!/bin/bash
# Start Sign Language Inference Service
# Usage: bash start_inference_service.sh [--reload]

set -e

echo "=========================================="
echo "Sign Language Inference Service Startup"
echo "=========================================="
echo ""

# Check if MediaPipe model exists
MEDIAPIPE_MODEL="backend/storage/datasets/hand_landmarker.task"
if [ ! -f "$MEDIAPIPE_MODEL" ]; then
    echo "⚠️  MediaPipe hand landmarker model not found"
    echo "Downloading model..."
    python backend/storage/datasets/download_mediapipe_model.py
    echo ""
fi

# Check if MLflow is running
echo "Checking MLflow connection..."
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "✓ MLflow is running"
else
    echo "⚠️  MLflow is not running"
    echo "Please start MLflow first:"
    echo "  bash backend/start_mlflow.sh"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Set environment variables
export MLFLOW_TRACKING_URI=http://localhost:5000
export MODEL_NAME=sign-language-asl
export CONFIDENCE_THRESHOLD=0.7

echo ""
echo "Configuration:"
echo "  MLflow URI: $MLFLOW_TRACKING_URI"
echo "  Model Name: $MODEL_NAME"
echo "  Confidence Threshold: $CONFIDENCE_THRESHOLD"
echo ""

# Check for reload flag
RELOAD_FLAG=""
if [ "$1" == "--reload" ]; then
    RELOAD_FLAG="--reload"
    echo "Starting with auto-reload enabled..."
else
    echo "Starting in production mode..."
fi

echo ""
echo "=========================================="
echo "Starting inference service on port 8001"
echo "=========================================="
echo ""

# Start the service
cd backend
python inference_service.py --host 0.0.0.0 --port 8001 $RELOAD_FLAG
