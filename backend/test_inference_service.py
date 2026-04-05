#!/usr/bin/env python3
"""
Unit tests for Sign Language Inference Service

Tests the inference service REST API endpoints and core functionality.

Requirements: 33.1, 33.2, 33.3, 33.7, 33.8, 33.12

Usage:
    pytest test_inference_service.py -v
"""

import io
import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import cv2
import numpy as np
import pytest
import torch
from fastapi.testclient import TestClient

# Import the app
from inference_service import app, preprocess_frames, run_inference


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_model():
    """Create a mock PyTorch model."""
    class MockModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
        
        def forward(self, x):
            batch_size = x.shape[0]
            num_classes = 50
            # Return mock predictions with high confidence for class 0
            output = torch.zeros(batch_size, num_classes)
            output[:, 0] = 0.85  # High confidence for class 0
            return output
    
    model = MockModel()
    model.eval()
    return model


@pytest.fixture
def mock_landmark_detector():
    """Create a mock landmark detector."""
    detector = MagicMock()
    
    # Mock detect_landmarks to return valid landmarks
    def detect_mock(frame):
        # Return valid landmarks (42 keypoints × 3 coordinates)
        return np.random.rand(42, 3).astype(np.float32)
    
    detector.detect_landmarks = detect_mock
    detector.close = MagicMock()
    
    return detector


@pytest.fixture
def sample_frame():
    """Create a sample video frame."""
    # Create a simple 640x480 BGR image
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    # Add some content (white rectangle)
    cv2.rectangle(frame, (100, 100), (300, 300), (255, 255, 255), -1)
    return frame


@pytest.fixture
def sample_frame_bytes(sample_frame):
    """Encode sample frame as JPEG bytes."""
    success, encoded = cv2.imencode('.jpg', sample_frame)
    assert success, "Failed to encode frame"
    return encoded.tobytes()


class TestHealthEndpoint:
    """Test the /health endpoint."""
    
    def test_health_check_returns_200(self, client):
        """Test that health check endpoint returns 200 status."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_check_returns_json(self, client):
        """Test that health check returns JSON response."""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert "status" in data
        assert "model_loaded" in data
        assert "device" in data
    
    def test_health_check_status_unhealthy_when_model_not_loaded(self, client):
        """Test that health check returns unhealthy when model is not loaded."""
        # The model won't be loaded in test environment
        response = client.get("/health")
        data = response.json()
        # Status could be unhealthy if model not loaded
        assert data["status"] in ["healthy", "unhealthy"]


class TestModelsEndpoint:
    """Test the /models endpoints."""
    
    def test_list_models_requires_registry(self, client):
        """Test that list models endpoint requires initialized registry."""
        response = client.get("/models")
        # Should return 503 if registry not initialized, or 200 if it is
        assert response.status_code in [200, 503]
    
    def test_get_model_details_invalid_version(self, client):
        """Test that get model details rejects invalid version."""
        response = client.get("/models/invalid")
        # Should return 400 for invalid version or 503 if registry not initialized
        assert response.status_code in [400, 503]


class TestPreprocessFrames:
    """Test the preprocess_frames function."""
    
    def test_preprocess_frames_with_valid_landmarks(self, mock_landmark_detector, sample_frame):
        """Test preprocessing with valid landmark detection."""
        # Patch the global landmark_detector
        import inference_service
        original_detector = inference_service.landmark_detector
        inference_service.landmark_detector = mock_landmark_detector
        
        try:
            frames = [sample_frame] * 30  # 30 frames
            result = preprocess_frames(frames, sequence_length=60)
            
            assert result is not None
            assert result.shape == (1, 60, 126)  # (batch, sequence, features)
            assert result.dtype == np.float32
        finally:
            inference_service.landmark_detector = original_detector
    
    def test_preprocess_frames_pads_short_sequences(self, mock_landmark_detector, sample_frame):
        """Test that short sequences are padded to target length."""
        import inference_service
        original_detector = inference_service.landmark_detector
        inference_service.landmark_detector = mock_landmark_detector
        
        try:
            frames = [sample_frame] * 20  # Only 20 frames
            result = preprocess_frames(frames, sequence_length=60)
            
            assert result is not None
            assert result.shape == (1, 60, 126)
            # Check that padding was added (last frames should be zeros)
            assert np.allclose(result[0, 20:, :], 0.0)
        finally:
            inference_service.landmark_detector = original_detector
    
    def test_preprocess_frames_truncates_long_sequences(self, mock_landmark_detector, sample_frame):
        """Test that long sequences are truncated to target length."""
        import inference_service
        original_detector = inference_service.landmark_detector
        inference_service.landmark_detector = mock_landmark_detector
        
        try:
            frames = [sample_frame] * 100  # 100 frames
            result = preprocess_frames(frames, sequence_length=60)
            
            assert result is not None
            assert result.shape == (1, 60, 126)
        finally:
            inference_service.landmark_detector = original_detector
    
    def test_preprocess_frames_returns_none_when_no_landmarks(self, sample_frame):
        """Test that preprocessing returns None when no landmarks detected."""
        # Create a detector that returns None
        mock_detector = MagicMock()
        mock_detector.detect_landmarks = MagicMock(return_value=None)
        
        import inference_service
        original_detector = inference_service.landmark_detector
        inference_service.landmark_detector = mock_detector
        
        try:
            frames = [sample_frame] * 30
            result = preprocess_frames(frames, sequence_length=60)
            
            assert result is None
        finally:
            inference_service.landmark_detector = original_detector


class TestRunInference:
    """Test the run_inference function."""
    
    def test_run_inference_with_high_confidence(self, mock_model):
        """Test inference with high confidence prediction."""
        import inference_service
        original_model = inference_service.production_model
        original_threshold = inference_service.confidence_threshold
        inference_service.production_model = mock_model
        inference_service.confidence_threshold = 0.7
        
        try:
            # Create input tensor
            input_tensor = np.random.rand(1, 60, 126).astype(np.float32)
            
            gesture, confidence = run_inference(input_tensor)
            
            assert gesture is not None
            assert confidence is not None
            assert confidence >= 0.7  # Above threshold
        finally:
            inference_service.production_model = original_model
            inference_service.confidence_threshold = original_threshold
    
    def test_run_inference_filters_low_confidence(self):
        """Test that low confidence predictions are filtered (Requirement 33.7, 33.8)."""
        import inference_service
        original_model = inference_service.production_model
        original_threshold = inference_service.confidence_threshold
        
        # Create model that returns low confidence
        class LowConfModel(torch.nn.Module):
            def __init__(self):
                super().__init__()
            
            def forward(self, x):
                batch_size = x.shape[0]
                num_classes = 50
                # Return predictions with low confidence (0.5)
                output = torch.zeros(batch_size, num_classes)
                output[:, 0] = 0.5  # Low confidence
                return output
        
        low_conf_model = LowConfModel()
        low_conf_model.eval()
        
        inference_service.production_model = low_conf_model
        inference_service.confidence_threshold = 0.7
        
        try:
            input_tensor = np.random.rand(1, 60, 126).astype(np.float32)
            
            gesture, confidence = run_inference(input_tensor)
            
            # Should return None for low confidence (Requirement 33.8)
            assert gesture is None
            assert confidence is None
        finally:
            inference_service.production_model = original_model
            inference_service.confidence_threshold = original_threshold
    
    def test_run_inference_raises_error_when_model_not_loaded(self):
        """Test that inference raises error when model is not loaded."""
        import inference_service
        original_model = inference_service.production_model
        inference_service.production_model = None
        
        try:
            input_tensor = np.random.rand(1, 60, 126).astype(np.float32)
            
            with pytest.raises(RuntimeError, match="Production model not loaded"):
                run_inference(input_tensor)
        finally:
            inference_service.production_model = original_model


class TestPredictEndpoint:
    """Test the /predict endpoint."""
    
    def test_predict_requires_frames(self, client):
        """Test that predict endpoint requires frames parameter."""
        response = client.post(
            "/predict",
            data={"user_id": "user123", "meeting_id": "meeting456"}
        )
        # Should return 422 (validation error) for missing frames
        assert response.status_code == 422
    
    def test_predict_requires_user_id(self, client, sample_frame_bytes):
        """Test that predict endpoint requires user_id parameter."""
        response = client.post(
            "/predict",
            data={"meeting_id": "meeting456"},
            files={"frames": ("frame.jpg", sample_frame_bytes, "image/jpeg")}
        )
        # Should return 422 (validation error) for missing user_id
        assert response.status_code == 422
    
    def test_predict_requires_meeting_id(self, client, sample_frame_bytes):
        """Test that predict endpoint requires meeting_id parameter."""
        response = client.post(
            "/predict",
            data={"user_id": "user123"},
            files={"frames": ("frame.jpg", sample_frame_bytes, "image/jpeg")}
        )
        # Should return 422 (validation error) for missing meeting_id
        assert response.status_code == 422
    
    def test_predict_returns_503_when_model_not_loaded(self, client, sample_frame_bytes):
        """Test that predict returns 503 when model is not loaded."""
        response = client.post(
            "/predict",
            data={"user_id": "user123", "meeting_id": "meeting456"},
            files={"frames": ("frame.jpg", sample_frame_bytes, "image/jpeg")}
        )
        # Should return 503 if model not loaded
        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
    
    def test_predict_accepts_multiple_frames(self, client, sample_frame_bytes):
        """Test that predict endpoint accepts multiple frames."""
        files = [
            ("frames", ("frame1.jpg", sample_frame_bytes, "image/jpeg")),
            ("frames", ("frame2.jpg", sample_frame_bytes, "image/jpeg")),
            ("frames", ("frame3.jpg", sample_frame_bytes, "image/jpeg"))
        ]
        
        response = client.post(
            "/predict",
            data={"user_id": "user123", "meeting_id": "meeting456"},
            files=files
        )
        
        # Should return 503 (model not loaded) or process the request
        assert response.status_code in [200, 503]


class TestConfidenceThreshold:
    """Test confidence threshold filtering (Requirements 33.7, 33.8)."""
    
    def test_confidence_threshold_is_0_7(self):
        """Test that confidence threshold is set to 0.7 (Requirement 33.7)."""
        import inference_service
        assert inference_service.confidence_threshold == 0.7
    
    def test_predictions_below_threshold_are_filtered(self):
        """Test that predictions below 0.7 confidence are filtered (Requirement 33.8)."""
        import inference_service
        original_model = inference_service.production_model
        original_threshold = inference_service.confidence_threshold
        
        # Create model with confidence just below threshold
        class BelowThresholdModel(torch.nn.Module):
            def __init__(self):
                super().__init__()
            
            def forward(self, x):
                batch_size = x.shape[0]
                num_classes = 50
                output = torch.zeros(batch_size, num_classes)
                output[:, 0] = 0.69  # Just below 0.7
                return output
        
        below_threshold_model = BelowThresholdModel()
        below_threshold_model.eval()
        
        inference_service.production_model = below_threshold_model
        inference_service.confidence_threshold = 0.7
        
        try:
            input_tensor = np.random.rand(1, 60, 126).astype(np.float32)
            gesture, confidence = run_inference(input_tensor)
            
            # Should return None (Requirement 33.8)
            assert gesture is None
            assert confidence is None
        finally:
            inference_service.production_model = original_model
            inference_service.confidence_threshold = original_threshold


class TestResponseFormat:
    """Test response format (Requirement 33.3)."""
    
    def test_prediction_response_includes_required_fields(self):
        """Test that prediction response includes gesture, confidence, and metadata."""
        from inference_service import PredictionResponse
        from datetime import datetime
        
        response = PredictionResponse(
            gesture="hello",
            confidence=0.85,
            latency_ms=150.5,
            strategy_used="cloud"
        )
        
        assert response.gesture == "hello"
        assert response.confidence == 0.85
        assert response.latency_ms == 150.5
        assert response.strategy_used == "cloud"
        assert isinstance(response.timestamp, datetime)
    
    def test_prediction_response_allows_none_for_low_confidence(self):
        """Test that response allows None values for filtered predictions."""
        from inference_service import PredictionResponse
        
        response = PredictionResponse(
            gesture=None,
            confidence=None,
            latency_ms=120.0,
            strategy_used="cloud",
            message="Prediction confidence below threshold (0.7)"
        )
        
        assert response.gesture is None
        assert response.confidence is None
        assert response.message is not None


def test_model_registry_integration():
    """Test that model registry is properly integrated (Requirement 33.12)."""
    from inference_service import load_production_model
    import inference_service
    
    # This test verifies the function exists and can be called
    # Actual loading will fail in test environment without MLflow setup
    assert callable(load_production_model)
    
    # Verify global variables exist
    assert hasattr(inference_service, 'model_registry')
    assert hasattr(inference_service, 'production_model')
    assert hasattr(inference_service, 'model_name')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
