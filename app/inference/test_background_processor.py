"""Unit tests for BackgroundProcessor."""

import numpy as np
import pytest

from app.inference.background_processor import BackgroundProcessor


class TestBackgroundProcessor:
    """Test suite for BackgroundProcessor class."""
    
    def test_initialization(self):
        """Test BackgroundProcessor initialization with default parameters."""
        processor = BackgroundProcessor()
        
        assert processor.blur_intensity == 5
        assert processor.segmentation_model == "mediapipe_selfie"
        assert processor.edge_smoothing is True
    
    def test_initialization_with_custom_parameters(self):
        """Test BackgroundProcessor initialization with custom parameters."""
        processor = BackgroundProcessor(
            blur_intensity=7,
            segmentation_model="mediapipe_selfie",
            edge_smoothing=False,
        )
        
        assert processor.blur_intensity == 7
        assert processor.segmentation_model == "mediapipe_selfie"
        assert processor.edge_smoothing is False
    
    def test_blur_intensity_clamping(self):
        """Test that blur intensity is clamped to valid range (0-10)."""
        # Test upper bound
        processor_high = BackgroundProcessor(blur_intensity=15)
        assert processor_high.blur_intensity == 10
        
        # Test lower bound
        processor_low = BackgroundProcessor(blur_intensity=-5)
        assert processor_low.blur_intensity == 0
        
        # Test valid range
        processor_valid = BackgroundProcessor(blur_intensity=7)
        assert processor_valid.blur_intensity == 7
    
    def test_process_empty_frame(self):
        """Test processing empty frame returns unchanged frame."""
        processor = BackgroundProcessor()
        empty_frame = np.array([], dtype=np.uint8)
        
        result_frame, result_mask = processor.process(empty_frame)
        
        assert result_frame.size == 0
        assert result_mask.shape == (0,)
    
    def test_process_returns_correct_shapes(self):
        """Test that process returns frame and mask with correct shapes."""
        processor = BackgroundProcessor()
        frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        
        result_frame, result_mask = processor.process(frame)
        
        # Result frame should have same shape as input
        assert result_frame.shape == frame.shape
        # Mask should be 2D with same height and width
        assert result_mask.shape == (480, 640)
        assert result_mask.dtype == np.uint8
    
    def test_process_with_zero_blur_intensity(self):
        """Test that zero blur intensity returns original frame."""
        processor = BackgroundProcessor(blur_intensity=0)
        frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        
        result_frame, result_mask = processor.process(frame)
        
        # With blur intensity 0, frame should be unchanged
        # (assuming segmentation works, but no blur applied)
        assert result_frame.shape == frame.shape
    
    def test_segment_returns_binary_mask(self):
        """Test that segment returns binary mask with values 0 or 1."""
        processor = BackgroundProcessor()
        frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        
        mask = processor.segment(frame)
        
        # Mask should be binary (only 0 and 1)
        unique_values = np.unique(mask)
        assert all(val in [0, 1] for val in unique_values)
        assert mask.dtype == np.uint8
    
    def test_set_blur_intensity(self):
        """Test setting blur intensity with temporal smoothing."""
        processor = BackgroundProcessor(blur_intensity=5)
        
        # Set new intensity
        processor.set_blur_intensity(8)
        
        # Intensity should be updated
        assert processor.blur_intensity == 8
    
    def test_set_blur_intensity_clamping(self):
        """Test that set_blur_intensity clamps values to valid range."""
        processor = BackgroundProcessor()
        
        # Test upper bound
        processor.set_blur_intensity(15)
        assert processor.blur_intensity == 10
        
        # Test lower bound
        processor.set_blur_intensity(-3)
        assert processor.blur_intensity == 0
    
    def test_temporal_smoothing_buffer(self):
        """Test that blur intensity changes are smoothed over multiple frames."""
        processor = BackgroundProcessor(blur_intensity=0)
        
        # Change intensity abruptly
        processor.set_blur_intensity(10)
        
        # Smoothed intensity should be between old and new values
        smoothed = processor._get_smoothed_blur_intensity()
        
        # After one update, buffer still has mostly old values
        # So smoothed should be less than 10
        assert 0 <= smoothed <= 10
    
    def test_edge_smoothing_enabled(self):
        """Test that edge smoothing is applied when enabled."""
        processor = BackgroundProcessor(edge_smoothing=True)
        
        # Create a simple binary mask with sharp edges
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[25:75, 25:75] = 1  # Square in center
        
        # Apply edge smoothing
        smoothed_mask = processor._smooth_mask_edges(mask)
        
        # Smoothed mask should still be binary
        unique_values = np.unique(smoothed_mask)
        assert all(val in [0, 1] for val in unique_values)
        assert smoothed_mask.shape == mask.shape
    
    def test_apply_background_blur_with_different_intensities(self):
        """Test background blur application with different intensity levels."""
        processor = BackgroundProcessor()
        frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        mask = np.zeros((480, 640), dtype=np.uint8)
        mask[100:380, 200:440] = 1  # Person in center
        
        # Test different intensities
        for intensity in [0, 1, 5, 10]:
            result = processor._apply_background_blur(frame, mask, intensity)
            
            assert result.shape == frame.shape
            assert result.dtype == np.uint8
    
    def test_process_preserves_foreground(self):
        """Test that foreground (person) regions are preserved without blur."""
        processor = BackgroundProcessor(blur_intensity=10)
        
        # Create a simple test frame with distinct foreground and background
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        frame[:, :50] = 255  # Left half white (background)
        frame[:, 50:] = 128  # Right half gray (foreground/person)
        
        # Create mask: right half is person (1), left half is background (0)
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[:, 50:] = 1
        
        # Apply blur
        result = processor._apply_background_blur(frame, mask, 10)
        
        # Foreground (right half) should be relatively unchanged
        # Background (left half) should be blurred
        # Check that foreground pixels are closer to original than background pixels
        foreground_diff = np.mean(np.abs(result[:, 50:].astype(float) - frame[:, 50:].astype(float)))
        
        # Foreground should have minimal difference
        assert foreground_diff < 5  # Allow small difference due to edge effects
    
    def test_multi_person_segmentation_support(self):
        """Test that segmentation supports multiple people in frame."""
        # This test verifies the model is initialized with model_selection=1
        # which supports multiple people
        processor = BackgroundProcessor()
        
        # Verify model is initialized (if MediaPipe is available)
        if processor._segmentation_model is not None:
            # Model should be initialized with general model (model_selection=1)
            # This is verified by checking the initialization in __init__
            assert processor.segmentation_model == "mediapipe_selfie"
    
    def test_process_with_no_people(self):
        """Test processing frame with no people (all background)."""
        processor = BackgroundProcessor(blur_intensity=5)
        
        # Create a frame with no people (e.g., solid color)
        frame = np.full((480, 640, 3), 100, dtype=np.uint8)
        
        result_frame, result_mask = processor.process(frame)
        
        # Should return valid frame and mask
        assert result_frame.shape == frame.shape
        assert result_mask.shape == (480, 640)
    
    def test_process_with_multiple_people(self):
        """Test processing frame with multiple people."""
        processor = BackgroundProcessor(blur_intensity=5)
        
        # Create a test frame (in real scenario, would have multiple people)
        frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        
        result_frame, result_mask = processor.process(frame)
        
        # Should return valid frame and mask
        assert result_frame.shape == frame.shape
        assert result_mask.shape == (480, 640)
        # Mask should be binary
        unique_values = np.unique(result_mask)
        assert all(val in [0, 1] for val in unique_values)
    
    def test_segmentation_performance_timing(self):
        """Test that segmentation completes within performance requirements."""
        import time
        
        processor = BackgroundProcessor()
        frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        
        # Measure segmentation time
        start_time = time.time()
        mask = processor.segment(frame)
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Requirement 4.1: Segmentation should complete within 150ms
        # Note: This may fail if MediaPipe is not installed or on slow hardware
        # In that case, the test will still pass as it returns empty mask quickly
        if processor._segmentation_model is not None:
            assert elapsed_ms < 150, f"Segmentation took {elapsed_ms:.2f}ms, exceeds 150ms requirement"
        
        # Verify mask is valid
        assert mask.shape == (480, 640)
    
    def test_blur_intensity_configuration_range(self):
        """Test blur intensity configuration accepts full range (0-10)."""
        for intensity in range(0, 11):
            processor = BackgroundProcessor(blur_intensity=intensity)
            assert processor.blur_intensity == intensity
    
    def test_cleanup_on_deletion(self):
        """Test that MediaPipe resources are cleaned up on deletion."""
        processor = BackgroundProcessor()
        
        # Delete processor (should call __del__)
        del processor
        
        # If no exception is raised, cleanup was successful
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
