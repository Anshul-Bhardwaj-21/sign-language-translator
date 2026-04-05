"""
Unit tests for ASL Classifier module.
"""

import pytest
import numpy as np
from pathlib import Path
from app.inference.asl_classifier import (
    ASLClassifier,
    create_asl_classifier,
    CLASS_NAMES,
    IMG_SIZE,
    CONFIDENCE_THRESHOLD,
    STABILITY_FRAMES
)


class TestASLClassifier:
    """Test suite for ASL Classifier."""
    
    def test_class_names(self):
        """Test that class names are correctly defined."""
        assert len(CLASS_NAMES) == 29
        assert 'A' in CLASS_NAMES
        assert 'Z' in CLASS_NAMES
        assert 'space' in CLASS_NAMES
        assert 'del' in CLASS_NAMES
        assert 'nothing' in CLASS_NAMES
    
    def test_create_classifier_without_model(self):
        """Test classifier creation when model doesn't exist."""
        classifier = create_asl_classifier(model_path="nonexistent.h5")
        assert classifier is not None
        assert not classifier.is_ready()
    
    def test_preprocess_frame(self):
        """Test frame preprocessing."""
        classifier = create_asl_classifier()
        
        # Create test frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Preprocess
        processed = classifier.preprocess_frame(frame)
        
        # Check shape
        assert processed.shape == (1, IMG_SIZE, IMG_SIZE, 3)
        
        # Check normalization
        assert processed.min() >= 0.0
        assert processed.max() <= 1.0
    
    def test_predict_without_model(self):
        """Test prediction when model is not loaded."""
        classifier = create_asl_classifier(model_path="nonexistent.h5")
        
        # Create test frame
        frame = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        
        # Predict
        prediction = classifier.predict(frame)
        
        # Should return "nothing" with 0 confidence
        assert prediction.letter == "nothing"
        assert prediction.confidence == 0.0
        assert not prediction.is_stable
    
    def test_stability_buffer(self):
        """Test stability buffer logic."""
        classifier = create_asl_classifier()
        
        # Fill buffer with same prediction
        for _ in range(STABILITY_FRAMES):
            classifier._prediction_buffer.append("A")
            classifier._confidence_buffer.append(0.9)
        
        # Check stability
        assert classifier._check_stability()
        
        # Add different prediction
        classifier._prediction_buffer.append("B")
        classifier._confidence_buffer.append(0.9)
        
        # Should not be stable anymore
        assert not classifier._check_stability()
    
    def test_stability_ignores_nothing(self):
        """Test that stability check ignores 'nothing' predictions."""
        classifier = create_asl_classifier()
        
        # Fill buffer with "nothing"
        for _ in range(STABILITY_FRAMES):
            classifier._prediction_buffer.append("nothing")
            classifier._confidence_buffer.append(0.0)
        
        # Should not be stable
        assert not classifier._check_stability()
    
    def test_get_stable_prediction(self):
        """Test getting stable prediction."""
        classifier = create_asl_classifier()
        
        # No stable prediction initially
        assert classifier.get_stable_prediction() is None
        
        # Fill buffer with stable prediction
        for _ in range(STABILITY_FRAMES):
            classifier._prediction_buffer.append("A")
            classifier._confidence_buffer.append(0.9)
        
        # Get stable prediction
        letter, confidence = classifier.get_stable_prediction()
        assert letter == "A"
        assert confidence == 0.9
    
    def test_reset_buffer(self):
        """Test buffer reset."""
        classifier = create_asl_classifier()
        
        # Fill buffer
        for _ in range(5):
            classifier._prediction_buffer.append("A")
            classifier._confidence_buffer.append(0.9)
        
        # Reset
        classifier.reset_buffer()
        
        # Check buffers are empty
        assert len(classifier._prediction_buffer) == 0
        assert len(classifier._confidence_buffer) == 0
    
    def test_confidence_threshold(self):
        """Test custom confidence threshold."""
        classifier = create_asl_classifier(confidence_threshold=0.9)
        assert classifier.confidence_threshold == 0.9
    
    def test_stability_frames_config(self):
        """Test custom stability frames."""
        classifier = create_asl_classifier(stability_frames=10)
        assert classifier.stability_frames == 10
        assert classifier._prediction_buffer.maxlen == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
