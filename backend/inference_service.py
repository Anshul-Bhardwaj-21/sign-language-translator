#!/usr/bin/env python3
"""
Sign Language Inference Service REST API (Layer 5 - Inference Service Layer)

This module implements a FastAPI-based REST API for real-time sign language recognition.
It accepts video frames, extracts hand landmarks using MediaPipe, loads production models
from the model registry, and returns predictions with confidence scores.

Features:
- POST /predict endpoint for sign language prediction
- Video frame input via multipart/form-data
- Server-side landmark extraction using MediaPipe
- Production model loading from MLflow registry
- Confidence threshold filtering (0.7)
- GPU acceleration with CPU fallback
- Concurrent request handling
- Health check and metrics endpoints

Requirements:
- 33.1: REST API endpoint at POST /predict
- 33.2: Accept video frame sequences as input
- 33.3: Return predicted gesture labels with confidence scores
- 33.7: Filter predictions below confidence threshold (0.7)
- 33.8: Return no prediction for low-confidence results
- 33.12: Load models from Model_Registry on startup

Phase: MVP

Usage:
    # Start the inference service
    uvicorn inference_service:app --host 0.0.0.0 --port 8001
    
    # Make a prediction request
    curl -X POST http://localhost:8001/predict \
         -F "frames=@frame1.jpg" \
         -F "frames=@frame2.jpg" \
         -F "user_id=user123" \
         -F "meeting_id=meeting456"

Author: AI-Powered Meeting Platform Team
"""

import io
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import cv2
import mediapipe as mp
import numpy as np
import torch
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from models.model_registry import ModelRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Sign Language Inference Service",
    description="Real-time sign language recognition API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
model_registry: Optional[ModelRegistry] = None
production_model: Optional[torch.nn.Module] = None
landmark_detector: Optional['HandLandmarkDetector'] = None
device: str = "cpu"
confidence_threshold: float = 0.7
model_name: str = "sign-language-asl"


# Pydantic models for request/response
class PredictionResponse(BaseModel):
    """Response model for prediction endpoint."""
    gesture: Optional[str] = Field(None, description="Predicted gesture label")
    confidence: Optional[float] = Field(None, description="Prediction confidence score (0.0-1.0)")
    timestamp: datetime = Field(default_factory=datetime.now, description="Prediction timestamp")
    latency_ms: float = Field(..., description="Inference latency in milliseconds")
    strategy_used: str = Field(default="cloud", description="Processing strategy (cloud/edge)")
    message: Optional[str] = Field(None, description="Additional message (e.g., low confidence)")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field(..., description="Service status (healthy/unhealthy)")
    model_loaded: bool = Field(..., description="Whether production model is loaded")
    device: str = Field(..., description="Device being used (cpu/cuda)")
    model_name: str = Field(..., description="Name of loaded model")
    model_version: Optional[str] = Field(None, description="Version of loaded model")


class ModelInfo(BaseModel):
    """Model information."""
    name: str
    version: Optional[str]
    stage: str
    device: str
    loaded_at: Optional[datetime]


class HandLandmarkDetector:
    """
    Hand landmark detector using MediaPipe HandLandmarker.
    
    Extracts 21 keypoints per hand (42 total for both hands) with 3D coordinates (x, y, z).
    """
    
    def __init__(self, min_detection_confidence: float = 0.8):
        """
        Initialize MediaPipe HandLandmarker.
        
        Args:
            min_detection_confidence: Minimum confidence for hand detection
        """
        # Path to MediaPipe model
        model_path = Path(__file__).parent / "storage" / "datasets" / "hand_landmarker.task"
        
        if not model_path.exists():
            logger.error(f"Hand landmarker model not found at {model_path}")
            logger.error("Please run: python backend/storage/datasets/download_mediapipe_model.py")
            raise FileNotFoundError(f"MediaPipe model not found: {model_path}")
        
        # Create HandLandmarker options
        base_options = mp.tasks.BaseOptions(model_asset_path=str(model_path))
        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_detection_confidence
        )
        self.landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)
        self.min_confidence = min_detection_confidence
        self.frame_timestamp_ms = 0
        
        logger.info(f"Initialized MediaPipe HandLandmarker with confidence: {min_detection_confidence}")
    
    def detect_landmarks(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """
        Detect hand landmarks in a single frame.
        
        Args:
            frame: BGR image frame (H, W, 3) from OpenCV
        
        Returns:
            Landmarks array of shape (42, 3) or None if detection fails
            - First 21 keypoints: left hand (or first detected hand)
            - Last 21 keypoints: right hand (or second detected hand)
            - Coordinates: (x, y, z) normalized to [0, 1]
        """
        # Convert BGR to RGB (OpenCV uses BGR, MediaPipe expects RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # Detect landmarks
        self.frame_timestamp_ms += 33  # Approximate 30 FPS
        detection_result = self.landmarker.detect_for_video(mp_image, self.frame_timestamp_ms)
        
        if not detection_result.hand_landmarks:
            return None
        
        # Initialize landmarks array (42 keypoints × 3 coordinates)
        landmarks = np.zeros((42, 3), dtype=np.float32)
        
        # Extract landmarks for detected hands (up to 2 hands)
        for hand_idx, hand_landmarks in enumerate(detection_result.hand_landmarks):
            if hand_idx >= 2:  # Only process first 2 hands
                break
            
            # Extract 21 keypoints for this hand
            for landmark_idx, landmark in enumerate(hand_landmarks):
                # Store in appropriate position (0-20 for first hand, 21-41 for second hand)
                target_idx = hand_idx * 21 + landmark_idx
                landmarks[target_idx] = [landmark.x, landmark.y, landmark.z]
        
        # Check confidence
        if detection_result.handedness:
            confidence = detection_result.handedness[0][0].score
            if confidence < self.min_confidence:
                return None
        
        return landmarks
    
    def close(self):
        """Release MediaPipe resources."""
        if self.landmarker:
            self.landmarker.close()


def load_production_model():
    """
    Load production model from model registry.
    
    Requirements:
        - 33.12: Load models from Model_Registry on startup
    """
    global production_model, model_registry, device
    
    try:
        # Initialize model registry
        model_registry = ModelRegistry()
        
        # Detect device (GPU if available, else CPU)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {device}")
        
        # Load production model
        logger.info(f"Loading production model: {model_name}")
        production_model = model_registry.load_model_by_stage(
            model_name=model_name,
            stage="Production",
            device=device
        )
        
        # Set model to evaluation mode
        production_model.eval()
        
        logger.info(f"✓ Production model loaded successfully on {device}")
        
    except Exception as e:
        logger.error(f"Failed to load production model: {e}")
        logger.warning("Service will start but predictions will fail until model is loaded")
        production_model = None


def preprocess_frames(frames: List[np.ndarray], sequence_length: int = 60) -> Optional[np.ndarray]:
    """
    Preprocess video frames by extracting landmarks and normalizing.
    
    Args:
        frames: List of video frames as numpy arrays
        sequence_length: Target sequence length (default: 60)
    
    Returns:
        Preprocessed tensor of shape (1, sequence_length, 126) or None if preprocessing fails
        where 126 = 42 keypoints × 3 coordinates
    """
    global landmark_detector
    
    if landmark_detector is None:
        raise RuntimeError("Landmark detector not initialized")
    
    # Extract landmarks from each frame
    landmarks_sequence = []
    
    for frame in frames:
        landmarks = landmark_detector.detect_landmarks(frame)
        if landmarks is not None:
            # Flatten landmarks: (42, 3) -> (126,)
            landmarks_flat = landmarks.reshape(-1)
            landmarks_sequence.append(landmarks_flat)
    
    if len(landmarks_sequence) == 0:
        logger.warning("No landmarks detected in any frame")
        return None
    
    # Convert to numpy array
    landmarks_array = np.array(landmarks_sequence, dtype=np.float32)
    
    # Pad or truncate to sequence_length
    current_length = landmarks_array.shape[0]
    
    if current_length < sequence_length:
        # Pad with zeros
        padding = np.zeros((sequence_length - current_length, 126), dtype=np.float32)
        landmarks_array = np.vstack([landmarks_array, padding])
    elif current_length > sequence_length:
        # Truncate to sequence_length
        landmarks_array = landmarks_array[:sequence_length]
    
    # Add batch dimension: (sequence_length, 126) -> (1, sequence_length, 126)
    landmarks_tensor = landmarks_array[np.newaxis, :]
    
    return landmarks_tensor


def run_inference(input_tensor: np.ndarray) -> tuple[Optional[str], Optional[float]]:
    """
    Run inference on preprocessed input tensor.
    
    Args:
        input_tensor: Preprocessed tensor of shape (1, sequence_length, 126)
    
    Returns:
        Tuple of (gesture_label, confidence) or (None, None) if prediction fails
        
    Requirements:
        - 33.3: Return predicted gesture labels with confidence scores
        - 33.7: Filter predictions below confidence threshold (0.7)
        - 33.8: Return no prediction for low-confidence results
    """
    global production_model, device, confidence_threshold
    
    if production_model is None:
        raise RuntimeError("Production model not loaded")
    
    try:
        # Convert to PyTorch tensor
        input_torch = torch.from_numpy(input_tensor).to(device)
        
        # Run inference
        with torch.no_grad():
            output = production_model(input_torch)
        
        # Get prediction and confidence
        confidence, predicted_class = torch.max(output, dim=1)
        confidence_value = confidence.item()
        predicted_label = predicted_class.item()
        
        # Apply confidence threshold (Requirement 33.7, 33.8)
        if confidence_value < confidence_threshold:
            logger.info(f"Low confidence prediction: {confidence_value:.3f} < {confidence_threshold}")
            return None, None
        
        # TODO: Map predicted_label (integer) to gesture name (string)
        # For now, return the class index as string
        # In production, load gesture vocabulary from model metadata
        gesture_name = f"gesture_{predicted_label}"
        
        return gesture_name, confidence_value
    
    except Exception as e:
        logger.error(f"Inference failed: {e}")
        return None, None


@app.on_event("startup")
async def startup_event():
    """
    Initialize service on startup.
    
    Requirements:
        - 33.12: Load models from Model_Registry on startup
    """
    global landmark_detector
    
    logger.info("Starting Sign Language Inference Service...")
    
    # Initialize landmark detector
    try:
        landmark_detector = HandLandmarkDetector(min_detection_confidence=0.8)
        logger.info("✓ Landmark detector initialized")
    except Exception as e:
        logger.error(f"Failed to initialize landmark detector: {e}")
        landmark_detector = None
    
    # Load production model
    load_production_model()
    
    logger.info("✓ Inference service ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    global landmark_detector
    
    logger.info("Shutting down inference service...")
    
    if landmark_detector:
        landmark_detector.close()
    
    logger.info("✓ Shutdown complete")


@app.post("/predict", response_model=PredictionResponse)
async def predict(
    frames: List[UploadFile] = File(..., description="Video frames (JPEG/PNG images)"),
    user_id: str = Form(..., description="User ID"),
    meeting_id: str = Form(..., description="Meeting ID"),
    sign_language: str = Form(default="ASL", description="Sign language (ASL/BSL)")
):
    """
    Predict sign language gesture from video frames.
    
    This endpoint accepts a sequence of video frames, extracts hand landmarks using MediaPipe,
    runs inference using the production model, and returns the predicted gesture with confidence.
    
    Requirements:
        - 33.1: REST API endpoint at POST /predict
        - 33.2: Accept video frame sequences as input
        - 33.3: Return predicted gesture labels with confidence scores
        - 33.4: Process inference requests with maximum latency of 200ms
        - 33.7: Filter predictions below confidence threshold (0.7)
        - 33.8: Return no prediction for low-confidence results
    
    Args:
        frames: List of uploaded image files (video frames)
        user_id: ID of the user making the request
        meeting_id: ID of the meeting
        sign_language: Sign language type (ASL/BSL)
    
    Returns:
        PredictionResponse with gesture, confidence, and metadata
    
    Raises:
        HTTPException: If prediction fails or service is not ready
    """
    start_time = time.time()
    
    # Check if service is ready
    if production_model is None:
        raise HTTPException(
            status_code=503,
            detail="Production model not loaded. Service not ready."
        )
    
    if landmark_detector is None:
        raise HTTPException(
            status_code=503,
            detail="Landmark detector not initialized. Service not ready."
        )
    
    try:
        # Read and decode frames
        frame_arrays = []
        for frame_file in frames:
            # Read file content
            content = await frame_file.read()
            
            # Decode image
            nparr = np.frombuffer(content, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                logger.warning(f"Failed to decode frame: {frame_file.filename}")
                continue
            
            frame_arrays.append(frame)
        
        if len(frame_arrays) == 0:
            raise HTTPException(
                status_code=400,
                detail="No valid frames provided"
            )
        
        logger.info(f"Received {len(frame_arrays)} frames from user {user_id}")
        
        # Preprocess frames (extract landmarks)
        input_tensor = preprocess_frames(frame_arrays)
        
        if input_tensor is None:
            # No landmarks detected - return no prediction
            latency_ms = (time.time() - start_time) * 1000
            return PredictionResponse(
                gesture=None,
                confidence=None,
                latency_ms=latency_ms,
                strategy_used="cloud",
                message="No hand landmarks detected in frames"
            )
        
        # Run inference
        gesture, confidence = run_inference(input_tensor)
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # Log prediction
        logger.info(
            f"Prediction: gesture={gesture}, confidence={confidence:.3f if confidence else 0}, "
            f"latency={latency_ms:.1f}ms, user={user_id}"
        )
        
        # Return response
        if gesture is None or confidence is None:
            # Low confidence - return no prediction (Requirement 33.8)
            return PredictionResponse(
                gesture=None,
                confidence=None,
                latency_ms=latency_ms,
                strategy_used="cloud",
                message=f"Prediction confidence below threshold ({confidence_threshold})"
            )
        else:
            # High confidence - return prediction
            return PredictionResponse(
                gesture=gesture,
                confidence=confidence,
                latency_ms=latency_ms,
                strategy_used="cloud"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for load balancer integration.
    
    Returns service status and model information.
    
    Requirements:
        - 34.4: Provide health check endpoints for load balancer integration
    """
    model_loaded = production_model is not None
    status = "healthy" if model_loaded and landmark_detector is not None else "unhealthy"
    
    # Get model version if available
    model_version = None
    if model_registry and model_loaded:
        try:
            prod_version = model_registry.get_production_model_version(model_name)
            if prod_version:
                model_version = str(prod_version.version)
        except Exception as e:
            logger.warning(f"Failed to get model version: {e}")
    
    return HealthResponse(
        status=status,
        model_loaded=model_loaded,
        device=device,
        model_name=model_name,
        model_version=model_version
    )


@app.get("/models")
async def list_models():
    """
    List available models in the registry.
    
    Returns information about registered models and their versions.
    """
    if model_registry is None:
        raise HTTPException(
            status_code=503,
            detail="Model registry not initialized"
        )
    
    try:
        # Get all versions of the model
        versions = model_registry.list_model_versions(model_name)
        
        models_info = []
        for version in versions:
            models_info.append({
                "name": model_name,
                "version": version.version,
                "stage": version.current_stage,
                "run_id": version.run_id,
                "created_at": version.creation_timestamp,
                "status": version.status
            })
        
        return {
            "models": models_info,
            "total": len(models_info)
        }
    
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list models: {str(e)}"
        )


@app.get("/models/{model_id}")
async def get_model_details(model_id: str):
    """
    Get details for a specific model version.
    
    Args:
        model_id: Model version number
    """
    if model_registry is None:
        raise HTTPException(
            status_code=503,
            detail="Model registry not initialized"
        )
    
    try:
        version = int(model_id)
        metadata = model_registry.get_model_metadata(model_name, version)
        return metadata
    
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid model version. Must be an integer."
        )
    except Exception as e:
        logger.error(f"Failed to get model details: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"Model not found: {str(e)}"
        )


@app.post("/models/{model_id}/deploy")
async def deploy_model(model_id: str):
    """
    Deploy a model version to production.
    
    This endpoint transitions a model version to Production stage and reloads it.
    
    Args:
        model_id: Model version number to deploy
    """
    if model_registry is None:
        raise HTTPException(
            status_code=503,
            detail="Model registry not initialized"
        )
    
    try:
        version = int(model_id)
        
        # Transition to production
        model_registry.transition_model_stage(
            model_name=model_name,
            version=version,
            stage="Production",
            archive_existing_versions=True
        )
        
        # Reload production model
        load_production_model()
        
        return {
            "message": f"Model version {version} deployed to production",
            "model_name": model_name,
            "version": version,
            "stage": "Production"
        }
    
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid model version. Must be an integer."
        )
    except Exception as e:
        logger.error(f"Failed to deploy model: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to deploy model: {str(e)}"
        )


@app.get("/metrics")
async def get_metrics():
    """
    Get service metrics for monitoring.
    
    Returns basic metrics about the inference service.
    
    Requirements:
        - 34.5: Log inference latency metrics for monitoring
    """
    # TODO: Implement proper metrics collection (Prometheus format)
    # For now, return basic service information
    
    return {
        "service": "inference_service",
        "model_loaded": production_model is not None,
        "device": device,
        "confidence_threshold": confidence_threshold,
        "timestamp": datetime.now().isoformat()
    }


def main():
    """Run the inference service."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sign Language Inference Service")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    logger.info(f"Starting inference service on {args.host}:{args.port}")
    
    uvicorn.run(
        "inference_service:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()
