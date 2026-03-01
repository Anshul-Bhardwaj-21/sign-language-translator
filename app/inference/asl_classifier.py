"""
ASL Alphabet Classifier

Loads trained MobileNetV2 model and performs real-time ASL alphabet recognition.
Implements 7-frame stability buffer for robust predictions.
"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Deque, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Class names (A-Z, space, del, nothing)
CLASS_NAMES = [chr(i) for i in range(65, 91)] + ['space', 'del', 'nothing']

# Model configuration
IMG_SIZE = 224
CONFIDENCE_THRESHOLD = 0.85
STABILITY_FRAMES = 7


@dataclass
class ASLPrediction:
    """Single frame ASL prediction result."""
    
    letter: str
    confidence: float
    is_stable: bool = False
    all_probabilities: Optional[np.ndarray] = None


class ASLClassifier:
    """
    ASL Alphabet classifier with stability buffer.
    
    Features:
    - MobileNetV2-based recognition
    - 7-frame stability buffer
    - Confidence thresholding (≥0.85)
    - Graceful handling when model not found
    """
    
    def __init__(
        self,
        model_path: str,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
        stability_frames: int = STABILITY_FRAMES
    ):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.stability_frames = stability_frames
        
        self.model: Optional[object] = None
        self.model_loaded = False
        
        # Stability buffer
        self._prediction_buffer: Deque[str] = deque(maxlen=stability_frames)
        self._confidence_buffer: Deque[float] = deque(maxlen=stability_frames)
        
        # Load model
        self._load_model()
    
    def _load_model(self) -> None:
        """Load TensorFlow model from disk."""
        try:
            import tensorflow as tf
            
            if not Path(self.model_path).exists():
                logger.warning(
                    f"ASL model not found at {self.model_path}. "
                    "Run backend/train_asl_model.py to train the model."
                )
                return
            
            logger.info(f"Loading ASL model from {self.model_path}...")
            self.model = tf.keras.models.load_model(self.model_path)
            self.model_loaded = True
            logger.info("✓ ASL model loaded successfully")
            
        except ImportError:
            logger.error(
                "TensorFlow not installed. Install with: pip install tensorflow"
            )
        except Exception as exc:
            logger.error(f"Failed to load ASL model: {exc}")
    
    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess frame for model inference.
        
        Args:
            frame: RGB frame (any size)
        
        Returns:
            Preprocessed frame (1, 224, 224, 3) normalized to [0, 1]
        """
        # Resize to model input size
        resized = cv2.resize(frame, (IMG_SIZE, IMG_SIZE))
        
        # Normalize to [0, 1]
        normalized = resized.astype(np.float32) / 255.0
        
        # Add batch dimension
        batched = np.expand_dims(normalized, axis=0)
        
        return batched
    
    def predict(self, frame: np.ndarray) -> ASLPrediction:
        """
        Predict ASL letter from frame.
        
        Args:
            frame: RGB frame containing hand gesture
        
        Returns:
            ASLPrediction with letter, confidence, and stability status
        """
        # Check if model is loaded
        if not self.model_loaded or self.model is None:
            return ASLPrediction(
                letter="nothing",
                confidence=0.0,
                is_stable=False
            )
        
        try:
            # Preprocess frame
            input_tensor = self.preprocess_frame(frame)
            
            # Run inference
            predictions = self.model.predict(input_tensor, verbose=0)[0]
            
            # Get top prediction
            class_idx = int(np.argmax(predictions))
            confidence = float(predictions[class_idx])
            letter = CLASS_NAMES[class_idx]
            
            # Apply confidence threshold
            if confidence < self.confidence_threshold:
                letter = "nothing"
                confidence = 0.0
            
            # Update stability buffer
            self._prediction_buffer.append(letter)
            self._confidence_buffer.append(confidence)
            
            # Check stability
            is_stable = self._check_stability()
            
            return ASLPrediction(
                letter=letter,
                confidence=confidence,
                is_stable=is_stable,
                all_probabilities=predictions
            )
        
        except Exception as exc:
            logger.error(f"ASL prediction failed: {exc}")
            return ASLPrediction(
                letter="nothing",
                confidence=0.0,
                is_stable=False
            )
    
    def _check_stability(self) -> bool:
        """
        Check if prediction is stable across buffer.
        
        Returns:
            True if same letter predicted for stability_frames consecutive frames
        """
        if len(self._prediction_buffer) < self.stability_frames:
            return False
        
        # Check if all predictions in buffer are the same
        predictions = list(self._prediction_buffer)
        first_prediction = predictions[0]
        
        # Ignore "nothing" predictions
        if first_prediction == "nothing":
            return False
        
        # Check if all predictions match
        return all(p == first_prediction for p in predictions)
    
    def get_stable_prediction(self) -> Optional[Tuple[str, float]]:
        """
        Get stable prediction if available.
        
        Returns:
            (letter, confidence) if stable, None otherwise
        """
        if not self._check_stability():
            return None
        
        letter = self._prediction_buffer[-1]
        avg_confidence = float(np.mean(list(self._confidence_buffer)))
        
        return letter, avg_confidence
    
    def reset_buffer(self) -> None:
        """Clear stability buffer."""
        self._prediction_buffer.clear()
        self._confidence_buffer.clear()
    
    def is_ready(self) -> bool:
        """Check if classifier is ready for inference."""
        return self.model_loaded and self.model is not None


def create_asl_classifier(
    model_path: str = "backend/models/asl_mobilenetv2.h5",
    confidence_threshold: float = CONFIDENCE_THRESHOLD,
    stability_frames: int = STABILITY_FRAMES
) -> ASLClassifier:
    """Factory function for creating ASL classifier."""
    return ASLClassifier(
        model_path=model_path,
        confidence_threshold=confidence_threshold,
        stability_frames=stability_frames
    )
