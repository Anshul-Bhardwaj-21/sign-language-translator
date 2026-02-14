"""Unit tests for hand detector module."""

import pytest
import numpy as np
from app.inference.hand_detector import HandDetector, HandDetectionResult, create_hand_detector


def test_hand_detection_result_defaults():
    """Test default HandDetectionResult."""
    result = HandDetectionResult()
    assert not result.hand_detected
    assert result.primary_landmarks is None
    assert len(result.all_landmarks) == 0
    assert result.confidence == 0.0


def test_hand_detector_initialization():
    """Test hand detector initialization."""
    try:
        detector = create_hand_detector()
        assert detector is not None
        detector.close()
    except RuntimeError as exc:
        # MediaPipe not available is acceptable in some environments
        assert "MediaPipe" in str(exc)


def test_hand_detector_custom_params():
    """Test hand detector with custom parameters."""
    try:
        detector = HandDetector(
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.6
        )
        assert detector is not None
        detector.close()
    except RuntimeError:
        pytest.skip("MediaPipe not available")


def test_hand_detector_invalid_frame():
    """Test hand detector with invalid frame."""
    try:
        detector = create_hand_detector()
    except RuntimeError:
        pytest.skip("MediaPipe not available")
    
    # Test with None
    result = detector.detect(None)
    assert not result.hand_detected
    assert result.error_message != ""
    
    # Test with empty array
    empty_frame = np.array([])
    result = detector.detect(empty_frame)
    assert not result.hand_detected
    
    detector.close()


def test_hand_detector_valid_frame_no_hand():
    """Test hand detector with valid frame but no hand."""
    try:
        detector = create_hand_detector()
    except RuntimeError:
        pytest.skip("MediaPipe not available")
    
    # Create blank frame (no hand)
    blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    result = detector.detect(blank_frame)
    
    # Should process without error, but no hand detected
    assert result.error_message == ""
    assert not result.hand_detected
    
    detector.close()


def test_hand_detector_landmark_extraction():
    """Test landmark extraction from detection result."""
    result = HandDetectionResult()
    result.hand_detected = True
    result.primary_landmarks = [(0.5, 0.5, 0.0) for _ in range(21)]
    
    assert len(result.primary_landmarks) == 21
    assert all(len(lm) == 3 for lm in result.primary_landmarks)


def test_hand_detector_close():
    """Test hand detector cleanup."""
    try:
        detector = create_hand_detector()
        detector.close()
        # Should not crash on double close
        detector.close()
    except RuntimeError:
        pytest.skip("MediaPipe not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
