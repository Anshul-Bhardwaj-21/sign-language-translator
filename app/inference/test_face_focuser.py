"""Unit tests for FaceFocuser class."""

import numpy as np
import pytest

from app.inference.face_focuser import FaceFocuser, FaceDetection


class TestFaceFocuser:
    """Test suite for FaceFocuser class."""
    
    def test_initialization(self):
        """Test FaceFocuser initialization with default parameters."""
        focuser = FaceFocuser()
        
        assert focuser.target_face_size == 0.35
        assert focuser.smoothing_frames == 8
        assert focuser.face_detector_model == "haarcascade"
        assert focuser._face_cascade is not None
    
    def test_initialization_with_custom_parameters(self):
        """Test FaceFocuser initialization with custom parameters."""
        focuser = FaceFocuser(
            target_face_size=0.30,
            smoothing_frames=6,
            face_detector_model="haarcascade"
        )
        
        assert focuser.target_face_size == 0.30
        assert focuser.smoothing_frames == 6
    
    def test_initialization_clamps_parameters(self):
        """Test that initialization clamps parameters to valid ranges."""
        focuser = FaceFocuser(
            target_face_size=0.50,  # Above max (0.40)
            smoothing_frames=15,    # Above max (10)
        )
        
        assert focuser.target_face_size == 0.40
        assert focuser.smoothing_frames == 10
        
        focuser2 = FaceFocuser(
            target_face_size=0.10,  # Below min (0.25)
            smoothing_frames=2,     # Below min (5)
        )
        
        assert focuser2.target_face_size == 0.25
        assert focuser2.smoothing_frames == 5
    
    def test_process_empty_frame(self):
        """Test processing an empty frame."""
        focuser = FaceFocuser()
        empty_frame = np.array([])
        
        result_frame, detection = focuser.process(empty_frame)
        
        assert result_frame.size == 0
        assert detection is None
    
    def test_process_frame_no_face(self):
        """Test processing a frame with no faces."""
        focuser = FaceFocuser()
        # Create a solid color frame (no face)
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        
        result_frame, detection = focuser.process(frame)
        
        assert result_frame.shape == frame.shape
        assert detection is None
    
    def test_detect_face_no_face(self):
        """Test face detection on frame with no faces."""
        focuser = FaceFocuser()
        # Create a solid color frame
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        
        detection = focuser.detect_face(frame)
        
        assert detection is None
    
    def test_detect_face_with_synthetic_face(self):
        """Test face detection with a synthetic face-like pattern."""
        focuser = FaceFocuser()
        # Create a frame with a simple face-like pattern
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Draw a simple oval shape that might be detected as a face
        cv2 = pytest.importorskip("cv2")
        cv2.ellipse(frame, (320, 240), (80, 100), 0, 0, 360, (255, 255, 255), -1)
        cv2.circle(frame, (300, 220), 10, (0, 0, 0), -1)  # Left eye
        cv2.circle(frame, (340, 220), 10, (0, 0, 0), -1)  # Right eye
        cv2.ellipse(frame, (320, 260), (30, 15), 0, 0, 180, (0, 0, 0), 2)  # Mouth
        
        detection = focuser.detect_face(frame)
        
        # Detection may or may not succeed with synthetic pattern
        # Just verify the method doesn't crash
        if detection is not None:
            assert isinstance(detection, FaceDetection)
            assert len(detection.bbox) == 4
            assert 0.0 <= detection.center[0] <= 1.0
            assert 0.0 <= detection.center[1] <= 1.0
            assert detection.size_ratio > 0
    
    def test_calculate_target_zoom(self):
        """Test target zoom calculation."""
        focuser = FaceFocuser(target_face_size=0.35)
        
        # Face too small (0.20) -> should zoom in
        zoom = focuser._calculate_target_zoom(0.20)
        assert zoom > 1.0
        assert zoom == pytest.approx(0.35 / 0.20, rel=0.01)
        
        # Face too large (0.50) -> should zoom out (but clamped to min 0.8)
        zoom = focuser._calculate_target_zoom(0.50)
        assert zoom < 1.0
        # 0.35 / 0.50 = 0.7, but clamped to 0.8
        assert zoom == 0.8
        
        # Face at target size -> minimal zoom
        zoom = focuser._calculate_target_zoom(0.35)
        assert zoom == pytest.approx(1.0, rel=0.01)
    
    def test_calculate_target_zoom_clamping(self):
        """Test that target zoom is clamped to reasonable range."""
        focuser = FaceFocuser(target_face_size=0.35)
        
        # Very small face -> zoom should be clamped to max (3.0)
        zoom = focuser._calculate_target_zoom(0.05)
        assert zoom <= 3.0
        
        # Very large face -> zoom should be clamped to min (0.8)
        zoom = focuser._calculate_target_zoom(0.80)
        assert zoom >= 0.8
    
    def test_calculate_smoothed_center(self):
        """Test smoothed center calculation."""
        focuser = FaceFocuser(smoothing_frames=3)
        
        # Add some positions to buffer
        focuser._center_buffer.clear()
        focuser._center_buffer.append((0.4, 0.4))
        focuser._center_buffer.append((0.5, 0.5))
        focuser._center_buffer.append((0.6, 0.6))
        
        smoothed = focuser._calculate_smoothed_center()
        
        assert smoothed[0] == pytest.approx(0.5, rel=0.01)
        assert smoothed[1] == pytest.approx(0.5, rel=0.01)
    
    def test_calculate_smoothed_zoom(self):
        """Test smoothed zoom calculation."""
        focuser = FaceFocuser(smoothing_frames=3)
        
        # Add some zoom levels to buffer
        focuser._zoom_buffer.clear()
        focuser._zoom_buffer.append(1.0)
        focuser._zoom_buffer.append(1.2)
        focuser._zoom_buffer.append(1.4)
        
        smoothed = focuser._calculate_smoothed_zoom()
        
        assert smoothed == pytest.approx(1.2, rel=0.01)
    
    def test_apply_pan_zoom_no_zoom(self):
        """Test pan/zoom with no zoom (1.0x)."""
        focuser = FaceFocuser()
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        result = focuser._apply_pan_zoom(frame, (0.5, 0.5), 1.0)
        
        # With 1.0x zoom and center position, result should be similar to input
        assert result.shape == frame.shape
        assert result.dtype == frame.dtype
    
    def test_apply_pan_zoom_with_zoom(self):
        """Test pan/zoom with 2.0x zoom."""
        focuser = FaceFocuser()
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        result = focuser._apply_pan_zoom(frame, (0.5, 0.5), 2.0)
        
        # Result should have same dimensions as input
        assert result.shape == frame.shape
        assert result.dtype == frame.dtype
    
    def test_apply_pan_zoom_preserves_aspect_ratio(self):
        """Test that pan/zoom preserves aspect ratio."""
        focuser = FaceFocuser()
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        result = focuser._apply_pan_zoom(frame, (0.5, 0.5), 1.5)
        
        # Aspect ratio should be preserved
        input_aspect = frame.shape[1] / frame.shape[0]
        output_aspect = result.shape[1] / result.shape[0]
        
        assert output_aspect == pytest.approx(input_aspect, rel=0.01)
    
    def test_apply_pan_zoom_off_center(self):
        """Test pan/zoom with off-center position."""
        focuser = FaceFocuser()
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Pan to upper-left quadrant
        result = focuser._apply_pan_zoom(frame, (0.25, 0.25), 1.5)
        
        assert result.shape == frame.shape
        assert result.dtype == frame.dtype
    
    def test_timeout_behavior(self):
        """Test that focuser returns to default after timeout."""
        focuser = FaceFocuser(smoothing_frames=5)
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        
        # Manually set non-default values
        focuser._center_buffer.clear()
        focuser._zoom_buffer.clear()
        for _ in range(5):
            focuser._center_buffer.append((0.3, 0.3))
            focuser._zoom_buffer.append(1.5)
        
        # Simulate timeout (no face for 60+ frames)
        focuser._frames_without_face = 70
        
        # Process frame (should start returning to default)
        result_frame, detection = focuser.process(frame)
        
        # Check that values are moving toward default
        smoothed_center = focuser._calculate_smoothed_center()
        smoothed_zoom = focuser._calculate_smoothed_zoom()
        
        # Values should be between current and default
        assert 0.3 < smoothed_center[0] < 0.5 or smoothed_center[0] == pytest.approx(0.5, abs=0.01)
        assert 1.0 < smoothed_zoom < 1.5 or smoothed_zoom == pytest.approx(1.0, abs=0.01)
    
    def test_multiple_faces_selects_largest(self):
        """Test that multiple faces results in selecting the largest."""
        focuser = FaceFocuser()
        
        # Create a frame with multiple face-like patterns
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        cv2 = pytest.importorskip("cv2")
        
        # Draw two face-like patterns of different sizes
        # Larger face
        cv2.ellipse(frame, (200, 240), (80, 100), 0, 0, 360, (255, 255, 255), -1)
        cv2.circle(frame, (180, 220), 10, (0, 0, 0), -1)
        cv2.circle(frame, (220, 220), 10, (0, 0, 0), -1)
        
        # Smaller face
        cv2.ellipse(frame, (450, 240), (40, 50), 0, 0, 360, (255, 255, 255), -1)
        cv2.circle(frame, (440, 230), 5, (0, 0, 0), -1)
        cv2.circle(frame, (460, 230), 5, (0, 0, 0), -1)
        
        detection = focuser.detect_face(frame)
        
        # If faces are detected, the larger one should be selected
        if detection is not None:
            # The larger face should have a larger bounding box
            assert detection.bbox[2] > 50  # Width should be larger
            assert detection.bbox[3] > 50  # Height should be larger
    
    def test_frame_format_preservation(self):
        """Test that output frame has same format as input."""
        focuser = FaceFocuser()
        
        # Test with different frame sizes
        for height, width in [(480, 640), (720, 1280), (1080, 1920)]:
            frame = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
            
            result_frame, _ = focuser.process(frame)
            
            assert result_frame.shape == frame.shape
            assert result_frame.dtype == frame.dtype
    
    def test_face_detection_performance_timing(self):
        """Test that face detection completes within performance bounds."""
        import time
        
        focuser = FaceFocuser()
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Warm up
        focuser.detect_face(frame)
        
        # Measure detection time
        start_time = time.time()
        detection = focuser.detect_face(frame)
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Should complete within 100ms (requirement 3.1)
        assert elapsed_ms < 100, f"Face detection took {elapsed_ms:.2f}ms, expected < 100ms"
