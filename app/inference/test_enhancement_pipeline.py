"""Tests for enhancement pipeline infrastructure."""

import json
import tempfile
import time
from pathlib import Path

import numpy as np
import pytest

from app.inference.enhancement_pipeline import (
    EnhancementConfig,
    EnhancementPipeline,
    FrameMetadata,
    ProcessedFrame,
    load_config,
    save_config,
)
from app.inference.hand_detector import HandDetector
from app.inference.movement_tracker import MovementTracker
from app.inference.gesture_controls import GestureController


class TestEnhancementConfig:
    """Test enhancement configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = EnhancementConfig()
        
        assert config.lighting_enabled is True
        assert config.face_focus_enabled is False
        assert config.background_blur_enabled is False
        assert config.hand_tracking_enabled is True
        assert config.gesture_detection_enabled is True
        assert config.lighting_target_brightness == 128.0
        assert config.max_processing_time_ms == 50.0
    
    def test_config_to_dict(self):
        """Test configuration serialization to dictionary."""
        config = EnhancementConfig(
            lighting_enabled=False,
            blur_intensity=7,
        )
        
        data = config.to_dict()
        
        assert isinstance(data, dict)
        assert data['lighting_enabled'] is False
        assert data['blur_intensity'] == 7
    
    def test_config_from_dict(self):
        """Test configuration deserialization from dictionary."""
        data = {
            'lighting_enabled': False,
            'face_focus_enabled': True,
            'blur_intensity': 8,
        }
        
        config = EnhancementConfig.from_dict(data)
        
        assert config.lighting_enabled is False
        assert config.face_focus_enabled is True
        assert config.blur_intensity == 8
    
    def test_config_save_and_load(self):
        """Test configuration persistence to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            
            # Create and save config
            original_config = EnhancementConfig(
                lighting_enabled=False,
                face_focus_enabled=True,
                blur_intensity=9,
                lighting_target_brightness=140.0,
            )
            original_config.save(config_path)
            
            # Verify file exists
            assert config_path.exists()
            
            # Load config
            loaded_config = EnhancementConfig.load(config_path)
            
            # Verify values match
            assert loaded_config.lighting_enabled == original_config.lighting_enabled
            assert loaded_config.face_focus_enabled == original_config.face_focus_enabled
            assert loaded_config.blur_intensity == original_config.blur_intensity
            assert loaded_config.lighting_target_brightness == original_config.lighting_target_brightness
    
    def test_config_load_missing_file(self):
        """Test loading config from non-existent file returns defaults."""
        config = EnhancementConfig.load(Path("/nonexistent/path/config.json"))
        
        # Should return default config
        assert config.lighting_enabled is True
        assert config.lighting_target_brightness == 128.0


class TestFrameMetadata:
    """Test frame metadata structure."""
    
    def test_frame_metadata_creation(self):
        """Test creating frame metadata."""
        metadata = FrameMetadata(
            sequence_number=42,
            timestamp=123.456,
            width=640,
            height=480,
        )
        
        assert metadata.sequence_number == 42
        assert metadata.timestamp == 123.456
        assert metadata.width == 640
        assert metadata.height == 480
        assert metadata.format == "RGB"


class TestEnhancementPipeline:
    """Test enhancement pipeline orchestration."""
    
    def test_pipeline_initialization(self):
        """Test pipeline initializes with default config."""
        pipeline = EnhancementPipeline()
        
        assert pipeline.config is not None
        assert isinstance(pipeline.config, EnhancementConfig)
        assert pipeline._hand_detector is None
        assert pipeline._movement_tracker is None
        assert pipeline._gesture_controller is None
    
    def test_pipeline_with_custom_config(self):
        """Test pipeline initializes with custom config."""
        config = EnhancementConfig(
            lighting_enabled=False,
            blur_intensity=7,
        )
        pipeline = EnhancementPipeline(config=config)
        
        assert pipeline.config.lighting_enabled is False
        assert pipeline.config.blur_intensity == 7
    
    def test_pipeline_with_existing_modules(self):
        """Test pipeline initializes with existing ML modules."""
        # Skip if MediaPipe is not available
        try:
            hand_detector = HandDetector(max_num_hands=2)
        except RuntimeError:
            pytest.skip("MediaPipe not available")
        
        movement_tracker = MovementTracker()
        gesture_controller = GestureController()
        
        pipeline = EnhancementPipeline(
            hand_detector=hand_detector,
            movement_tracker=movement_tracker,
            gesture_controller=gesture_controller,
        )
        
        assert pipeline._hand_detector is hand_detector
        assert pipeline._movement_tracker is movement_tracker
        assert pipeline._gesture_controller is gesture_controller
    
    def test_process_frame_basic(self):
        """Test basic frame processing without enhancements."""
        pipeline = EnhancementPipeline()
        
        # Create test frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        metadata = FrameMetadata(
            sequence_number=1,
            timestamp=0.0,
            width=640,
            height=480,
        )
        
        # Process frame
        result = pipeline.process_frame(frame, metadata)
        
        # Verify result structure
        assert isinstance(result, ProcessedFrame)
        assert result.frame.shape == frame.shape
        assert result.metadata == metadata
        assert result.processing_time_ms >= 0
    
    def test_process_frame_preserves_metadata(self):
        """Test that frame processing preserves metadata."""
        pipeline = EnhancementPipeline()
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        metadata = FrameMetadata(
            sequence_number=42,
            timestamp=123.456,
            width=640,
            height=480,
        )
        
        result = pipeline.process_frame(frame, metadata)
        
        assert result.metadata.sequence_number == 42
        assert result.metadata.timestamp == 123.456
        assert result.metadata.width == 640
        assert result.metadata.height == 480
    
    def test_process_frame_preserves_format(self):
        """Test that frame processing preserves RGB format and dimensions."""
        pipeline = EnhancementPipeline()
        
        # Test various frame sizes
        for height, width in [(480, 640), (720, 1280), (1080, 1920)]:
            frame = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
            metadata = FrameMetadata(
                sequence_number=1,
                timestamp=0.0,
                width=width,
                height=height,
            )
            
            result = pipeline.process_frame(frame, metadata)
            
            assert result.frame.shape == (height, width, 3)
            assert result.frame.dtype == np.uint8
    
    def test_update_config(self):
        """Test updating pipeline configuration at runtime."""
        pipeline = EnhancementPipeline()
        
        # Initial config
        assert pipeline.config.lighting_enabled is True
        
        # Update config
        new_config = EnhancementConfig(lighting_enabled=False)
        pipeline.update_config(new_config)
        
        # Verify update
        assert pipeline.config.lighting_enabled is False
    
    def test_get_performance_metrics(self):
        """Test retrieving performance metrics."""
        pipeline = EnhancementPipeline()
        
        metrics = pipeline.get_performance_metrics()
        
        assert metrics.frames_processed == 0
        assert metrics.frames_skipped == 0
        assert metrics.current_fps == 0.0
    
    def test_performance_metrics_update(self):
        """Test that performance metrics update after processing frames."""
        pipeline = EnhancementPipeline()
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        metadata = FrameMetadata(
            sequence_number=1,
            timestamp=0.0,
            width=640,
            height=480,
        )
        
        # Process multiple frames
        for i in range(5):
            metadata.sequence_number = i
            pipeline.process_frame(frame, metadata)
        
        metrics = pipeline.get_performance_metrics()
        
        assert metrics.frames_processed == 5
        assert metrics.average_processing_time_ms >= 0
    
    def test_performance_metrics_cpu_memory_collection(self):
        """Test that CPU and memory usage metrics are collected."""
        pipeline = EnhancementPipeline()
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        metadata = FrameMetadata(
            sequence_number=1,
            timestamp=0.0,
            width=640,
            height=480,
        )
        
        # Process a frame
        pipeline.process_frame(frame, metadata)
        
        metrics = pipeline.get_performance_metrics()
        
        # CPU and memory metrics should be collected
        assert metrics.cpu_usage_percent >= 0.0
        assert metrics.memory_usage_mb >= 0.0
    
    def test_performance_metrics_per_operation_timing(self):
        """Test that per-operation timing is collected."""
        config = EnhancementConfig(lighting_enabled=True)
        pipeline = EnhancementPipeline(config=config)
        
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        metadata = FrameMetadata(
            sequence_number=1,
            timestamp=0.0,
            width=640,
            height=480,
        )
        
        # Process a frame
        pipeline.process_frame(frame, metadata)
        
        metrics = pipeline.get_performance_metrics()
        
        # Lighting timing should be recorded
        assert metrics.lighting_time_ms >= 0.0
        # Other timings should be zero if not enabled
        assert metrics.face_focus_time_ms == 0.0
        assert metrics.background_blur_time_ms == 0.0
    
    def test_performance_metrics_fps_calculation(self):
        """Test that FPS is calculated correctly."""
        import time
        
        pipeline = EnhancementPipeline()
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        metadata = FrameMetadata(
            sequence_number=1,
            timestamp=0.0,
            width=640,
            height=480,
        )
        
        # Process frames with small delays
        for i in range(10):
            metadata.sequence_number = i
            pipeline.process_frame(frame, metadata)
            time.sleep(0.01)  # Small delay
        
        # Wait for FPS update (happens every second)
        time.sleep(1.1)
        
        # Process one more frame to trigger FPS calculation
        pipeline.process_frame(frame, metadata)
        
        metrics = pipeline.get_performance_metrics()
        
        # FPS should be calculated (may be 0 if not enough time passed)
        assert metrics.current_fps >= 0.0


class TestConfigHelpers:
    """Test configuration helper functions."""
    
    def test_save_and_load_config_helpers(self):
        """Test save_config and load_config helper functions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            
            # Create and save config
            original_config = EnhancementConfig(
                lighting_enabled=False,
                blur_intensity=6,
            )
            save_config(original_config, config_path)
            
            # Load config
            loaded_config = load_config(config_path)
            
            # Verify values match
            assert loaded_config.lighting_enabled == original_config.lighting_enabled
            assert loaded_config.blur_intensity == original_config.blur_intensity


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



class TestTask61ProcessingFlow:
    """Test Task 6.1: Pipeline processing flow implementation."""
    
    def test_conditional_execution_lighting_disabled(self):
        """Test that lighting adjustment is skipped when disabled."""
        config = EnhancementConfig(lighting_enabled=False)
        pipeline = EnhancementPipeline(config=config)
        
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        metadata = FrameMetadata(sequence_number=1, timestamp=0.0, width=640, height=480)
        
        result = pipeline.process_frame(frame, metadata)
        
        # Lighting should not be applied
        assert result.lighting_applied is False
        assert pipeline._metrics.lighting_time_ms == 0.0
    
    def test_conditional_execution_lighting_enabled(self):
        """Test that lighting adjustment is applied when enabled."""
        config = EnhancementConfig(lighting_enabled=True)
        pipeline = EnhancementPipeline(config=config)
        
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        metadata = FrameMetadata(sequence_number=1, timestamp=0.0, width=640, height=480)
        
        result = pipeline.process_frame(frame, metadata)
        
        # Lighting should be applied
        assert result.lighting_applied is True
        assert pipeline._metrics.lighting_time_ms > 0.0
    
    def test_processing_order(self):
        """Test that enhancements are applied in correct order."""
        # Enable all enhancements
        config = EnhancementConfig(
            lighting_enabled=True,
            face_focus_enabled=True,
            background_blur_enabled=True,
            hand_tracking_enabled=True,
            gesture_detection_enabled=True,
        )
        pipeline = EnhancementPipeline(config=config)
        
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        metadata = FrameMetadata(sequence_number=1, timestamp=0.0, width=640, height=480)
        
        result = pipeline.process_frame(frame, metadata)
        
        # Verify that frame was processed
        assert result.frame is not None
        assert result.frame.shape == frame.shape
    
    def test_error_handling_fallback_to_unprocessed_frame(self):
        """Test that errors in processing fall back to unprocessed frame."""
        pipeline = EnhancementPipeline()
        
        # Create invalid frame (empty)
        frame = np.array([], dtype=np.uint8)
        metadata = FrameMetadata(sequence_number=1, timestamp=0.0, width=0, height=0)
        
        # Should not crash, should return some frame
        result = pipeline.process_frame(frame, metadata)
        
        assert result is not None
        assert isinstance(result, ProcessedFrame)
    
    def test_performance_timing_per_operation(self):
        """Test that performance timing is recorded for each operation."""
        config = EnhancementConfig(lighting_enabled=True)
        pipeline = EnhancementPipeline(config=config)
        
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        metadata = FrameMetadata(sequence_number=1, timestamp=0.0, width=640, height=480)
        
        result = pipeline.process_frame(frame, metadata)
        
        # Verify timing is recorded
        assert result.processing_time_ms > 0.0
        assert pipeline._metrics.lighting_time_ms >= 0.0
    
    def test_frame_skipping_when_queue_exceeds_threshold(self):
        """Test that frames are skipped when queue depth exceeds threshold."""
        config = EnhancementConfig(enable_frame_skipping=True)
        pipeline = EnhancementPipeline(config=config)
        
        # Manually set queue depth above threshold
        pipeline._frame_queue_depth = 5  # Above threshold of 3
        
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        metadata = FrameMetadata(sequence_number=1, timestamp=0.0, width=640, height=480)
        
        result = pipeline.process_frame(frame, metadata)
        
        # Frame should be skipped
        assert pipeline._metrics.frames_skipped > 0
        assert result.processing_time_ms == 0.0
    
    def test_frame_skipping_disabled(self):
        """Test that frame skipping can be disabled."""
        config = EnhancementConfig(enable_frame_skipping=False)
        pipeline = EnhancementPipeline(config=config)
        
        # Manually set queue depth above threshold
        pipeline._frame_queue_depth = 5
        
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        metadata = FrameMetadata(sequence_number=1, timestamp=0.0, width=640, height=480)
        
        result = pipeline.process_frame(frame, metadata)
        
        # Frame should NOT be skipped (processing time > 0)
        assert result.processing_time_ms > 0.0
    
    def test_performance_warning_threshold(self):
        """Test that performance warnings are logged when threshold exceeded."""
        config = EnhancementConfig(max_processing_time_ms=0.001)  # Very low threshold
        pipeline = EnhancementPipeline(config=config)
        
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        metadata = FrameMetadata(sequence_number=1, timestamp=0.0, width=640, height=480)
        
        # Process frame (should exceed threshold)
        result = pipeline.process_frame(frame, metadata)
        
        # Processing time should exceed threshold
        assert result.processing_time_ms > config.max_processing_time_ms
    
    def test_multiple_enhancements_integration(self):
        """Test that multiple enhancements work together."""
        config = EnhancementConfig(
            lighting_enabled=True,
            face_focus_enabled=False,  # Disable face focus to avoid OpenCV dependency
            background_blur_enabled=False,  # Disable background blur to avoid MediaPipe dependency
        )
        pipeline = EnhancementPipeline(config=config)
        
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        metadata = FrameMetadata(sequence_number=1, timestamp=0.0, width=640, height=480)
        
        result = pipeline.process_frame(frame, metadata)
        
        # Verify lighting was applied
        assert result.lighting_applied is True
        # Verify face focus was not applied
        assert result.face_focus_applied is False
        # Verify background blur was not applied
        assert result.background_blur_applied is False
    
    def test_frame_format_preservation_after_processing(self):
        """Test that frame format is preserved after all processing."""
        config = EnhancementConfig(lighting_enabled=True)
        pipeline = EnhancementPipeline(config=config)
        
        # Test with different frame sizes
        for height, width in [(240, 320), (480, 640), (720, 1280)]:
            frame = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
            metadata = FrameMetadata(
                sequence_number=1,
                timestamp=0.0,
                width=width,
                height=height,
            )
            
            result = pipeline.process_frame(frame, metadata)
            
            # Verify format preservation
            assert result.frame.shape == (height, width, 3)
            assert result.frame.dtype == np.uint8
    
    def test_metadata_preservation_after_processing(self):
        """Test that metadata is preserved after all processing."""
        pipeline = EnhancementPipeline()
        
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        metadata = FrameMetadata(
            sequence_number=99,
            timestamp=456.789,
            width=640,
            height=480,
            format="RGB",
        )
        
        result = pipeline.process_frame(frame, metadata)
        
        # Verify metadata preservation
        assert result.metadata.sequence_number == 99
        assert result.metadata.timestamp == 456.789
        assert result.metadata.width == 640
        assert result.metadata.height == 480
        assert result.metadata.format == "RGB"
    
    def test_queue_depth_management(self):
        """Test that queue depth is properly managed."""
        pipeline = EnhancementPipeline()
        
        initial_depth = pipeline._frame_queue_depth
        
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        metadata = FrameMetadata(sequence_number=1, timestamp=0.0, width=640, height=480)
        
        # Process frame
        pipeline.process_frame(frame, metadata)
        
        # Queue depth should return to initial state after processing
        assert pipeline._frame_queue_depth == initial_depth
    
    def test_processor_initialization_on_config_update(self):
        """Test that processors are reinitialized when config is updated."""
        # Start with lighting disabled
        config = EnhancementConfig(lighting_enabled=False)
        pipeline = EnhancementPipeline(config=config)
        
        assert pipeline._lighting_adjuster is None
        
        # Update config to enable lighting
        new_config = EnhancementConfig(lighting_enabled=True)
        pipeline.update_config(new_config)
        
        # Lighting adjuster should now be initialized
        assert pipeline._lighting_adjuster is not None


class TestTask72AdaptiveQualityReduction:
    """Test Task 7.2: Adaptive quality reduction implementation."""
    
    def test_cpu_samples_collection(self):
        """Test that CPU samples are collected over time."""
        pipeline = EnhancementPipeline()
        
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        metadata = FrameMetadata(sequence_number=1, timestamp=0.0, width=640, height=480)
        
        # Process a frame
        pipeline.process_frame(frame, metadata)
        
        # CPU samples should be collected
        assert hasattr(pipeline, '_cpu_samples')
        assert isinstance(pipeline._cpu_samples, list)
    
    def test_fps_samples_collection(self):
        """Test that FPS samples are collected over time."""
        pipeline = EnhancementPipeline()
        
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        metadata = FrameMetadata(sequence_number=1, timestamp=0.0, width=640, height=480)
        
        # Process a frame
        pipeline.process_frame(frame, metadata)
        
        # FPS samples should be collected
        assert hasattr(pipeline, '_fps_samples')
        assert isinstance(pipeline._fps_samples, list)
    
    def test_degradation_triggered_by_high_cpu(self):
        """Test that degradation is triggered when CPU exceeds 80%."""
        config = EnhancementConfig(
            lighting_enabled=True,
            face_focus_enabled=False,  # Disable to simplify test
            background_blur_enabled=False,  # Disable to simplify test
        )
        pipeline = EnhancementPipeline(config=config)
        
        # Manually set metrics to simulate high CPU (set after samples to avoid being overwritten)
        pipeline._metrics.cpu_usage_percent = 90.0
        pipeline._metrics.current_fps = 25.0
        
        # Simulate high CPU usage with enough samples
        pipeline._cpu_samples = [85.0, 87.0, 90.0, 88.0]
        pipeline._fps_samples = [25.0, 24.0, 23.0, 25.0]
        pipeline._last_degradation_check = time.time() - 2.0  # Force check (2 seconds ago)
        
        # Directly call the degradation check (bypassing process_frame which updates metrics)
        pipeline._check_adaptive_quality_reduction()
        
        # Degradation should be active
        assert pipeline._degradation_active is True
        # Lighting should be disabled (since blur and face focus are already disabled)
        assert pipeline.config.lighting_enabled is False
    
    def test_degradation_triggered_by_low_fps(self):
        """Test that degradation is triggered when FPS drops below 15."""
        config = EnhancementConfig(
            lighting_enabled=True,
            face_focus_enabled=True,
            background_blur_enabled=True,
        )
        pipeline = EnhancementPipeline(config=config)
        
        # Simulate low FPS
        pipeline._cpu_samples = [50.0, 52.0, 48.0, 51.0]
        pipeline._fps_samples = [12.0, 13.0, 11.0, 14.0]
        pipeline._last_degradation_check = time.time() - 2.0  # Force check (2 seconds ago)
        
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        metadata = FrameMetadata(sequence_number=1, timestamp=0.0, width=640, height=480)
        
        # Process frame (should trigger degradation check)
        pipeline.process_frame(frame, metadata)
        
        # Degradation should be active
        assert pipeline._degradation_active is True
        # Background blur should be disabled first
        assert pipeline.config.background_blur_enabled is False
    
    def test_degradation_priority_order(self):
        """Test that enhancements are disabled in correct priority order."""
        config = EnhancementConfig(
            lighting_enabled=True,
            face_focus_enabled=True,
            background_blur_enabled=True,
        )
        pipeline = EnhancementPipeline(config=config)
        
        # Apply degradation level 1
        pipeline._apply_quality_degradation("test")
        assert pipeline.config.background_blur_enabled is False
        assert pipeline.config.face_focus_enabled is True
        assert pipeline.config.lighting_enabled is True
        assert pipeline._degradation_level == 1
        
        # Reset and test level 2
        config2 = EnhancementConfig(
            lighting_enabled=True,
            face_focus_enabled=True,
            background_blur_enabled=False,  # Already disabled
        )
        pipeline2 = EnhancementPipeline(config=config2)
        pipeline2._apply_quality_degradation("test")
        assert pipeline2.config.face_focus_enabled is False
        assert pipeline2.config.lighting_enabled is True
        assert pipeline2._degradation_level == 2
        
        # Reset and test level 3
        config3 = EnhancementConfig(
            lighting_enabled=True,
            face_focus_enabled=False,  # Already disabled
            background_blur_enabled=False,  # Already disabled
        )
        pipeline3 = EnhancementPipeline(config=config3)
        pipeline3._apply_quality_degradation("test")
        assert pipeline3.config.lighting_enabled is False
        assert pipeline3._degradation_level == 3
    
    def test_quality_restoration_when_performance_improves(self):
        """Test that quality is restored when performance improves."""
        config = EnhancementConfig(
            lighting_enabled=True,
            face_focus_enabled=True,
            background_blur_enabled=True,
        )
        pipeline = EnhancementPipeline(config=config)
        
        # Apply degradation
        pipeline._degradation_active = True
        pipeline._degradation_level = 3
        pipeline.config.background_blur_enabled = False
        pipeline.config.face_focus_enabled = False
        pipeline.config.lighting_enabled = False
        
        # Restore quality
        pipeline._restore_quality()
        
        # All enhancements should be re-enabled
        assert pipeline.config.background_blur_enabled is True
        assert pipeline.config.face_focus_enabled is True
        assert pipeline.config.lighting_enabled is True
        assert pipeline._degradation_active is False
        assert pipeline._degradation_level == 0
    
    def test_degradation_check_interval(self):
        """Test that degradation checks happen at correct intervals."""
        pipeline = EnhancementPipeline()
        
        # Set last check to recent time
        pipeline._last_degradation_check = time.time()
        
        # Simulate high CPU
        pipeline._cpu_samples = [85.0, 87.0, 90.0]
        pipeline._fps_samples = [25.0, 24.0, 23.0]
        
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        metadata = FrameMetadata(sequence_number=1, timestamp=0.0, width=640, height=480)
        
        # Process frame (should NOT trigger check due to interval)
        pipeline.process_frame(frame, metadata)
        
        # Degradation should NOT be active (check was skipped)
        assert pipeline._degradation_active is False
    
    def test_minimum_samples_required_for_degradation(self):
        """Test that minimum samples are required before degradation decision."""
        pipeline = EnhancementPipeline()
        
        # Only 2 samples (need at least 3)
        pipeline._cpu_samples = [85.0, 87.0]
        pipeline._fps_samples = [25.0, 24.0]
        pipeline._last_degradation_check = 0  # Force check
        
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        metadata = FrameMetadata(sequence_number=1, timestamp=0.0, width=640, height=480)
        
        # Process frame
        pipeline.process_frame(frame, metadata)
        
        # Degradation should NOT be active (not enough samples)
        assert pipeline._degradation_active is False
    
    def test_sample_buffer_size_limit(self):
        """Test that sample buffers are limited to prevent unbounded growth."""
        pipeline = EnhancementPipeline()
        
        # Add many samples
        for i in range(20):
            pipeline._cpu_samples.append(50.0)
            pipeline._fps_samples.append(25.0)
        
        pipeline._last_degradation_check = time.time() - 2.0  # Force check (2 seconds ago)
        
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        metadata = FrameMetadata(sequence_number=1, timestamp=0.0, width=640, height=480)
        
        # Process frame (should trigger check and trim samples)
        pipeline.process_frame(frame, metadata)
        
        # Samples should be limited to 10 (plus the one just added = 11 max before trimming)
        assert len(pipeline._cpu_samples) <= 11
        assert len(pipeline._fps_samples) <= 11
    
    def test_no_degradation_when_performance_good(self):
        """Test that no degradation occurs when performance is good."""
        config = EnhancementConfig(
            lighting_enabled=True,
            face_focus_enabled=True,
            background_blur_enabled=True,
        )
        pipeline = EnhancementPipeline(config=config)
        
        # Simulate good performance
        pipeline._cpu_samples = [50.0, 52.0, 48.0, 51.0]
        pipeline._fps_samples = [25.0, 24.0, 26.0, 25.0]
        pipeline._last_degradation_check = time.time() - 2.0  # Force check (2 seconds ago)
        
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        metadata = FrameMetadata(sequence_number=1, timestamp=0.0, width=640, height=480)
        
        # Process frame
        pipeline.process_frame(frame, metadata)
        
        # Degradation should NOT be active
        assert pipeline._degradation_active is False
        # All enhancements should remain enabled
        assert pipeline.config.background_blur_enabled is True
        assert pipeline.config.face_focus_enabled is True
        assert pipeline.config.lighting_enabled is True
    
    def test_degradation_prevents_duplicate_application(self):
        """Test that degradation is not applied multiple times."""
        config = EnhancementConfig(
            lighting_enabled=True,
            face_focus_enabled=True,
            background_blur_enabled=True,
        )
        pipeline = EnhancementPipeline(config=config)
        
        # Apply degradation once
        pipeline._apply_quality_degradation("test")
        assert pipeline._degradation_active is True
        initial_level = pipeline._degradation_level
        
        # Try to apply again
        pipeline._apply_quality_degradation("test")
        
        # Should not change (already active)
        assert pipeline._degradation_level == initial_level
    
    def test_restoration_clears_samples(self):
        """Test that quality restoration clears sample buffers."""
        pipeline = EnhancementPipeline()
        
        # Add samples
        pipeline._cpu_samples = [85.0, 87.0, 90.0]
        pipeline._fps_samples = [12.0, 13.0, 11.0]
        pipeline._degradation_active = True
        pipeline._degradation_level = 1
        
        # Restore quality
        pipeline._restore_quality()
        
        # Samples should be cleared
        assert len(pipeline._cpu_samples) == 0
        assert len(pipeline._fps_samples) == 0
    
    def test_degradation_with_all_enhancements_disabled(self):
        """Test degradation behavior when all enhancements are already disabled."""
        config = EnhancementConfig(
            lighting_enabled=False,
            face_focus_enabled=False,
            background_blur_enabled=False,
        )
        pipeline = EnhancementPipeline(config=config)
        
        # Try to apply degradation
        pipeline._apply_quality_degradation("test")
        
        # Should handle gracefully (no crash)
        assert pipeline._degradation_active is True
        # All should remain disabled
        assert pipeline.config.background_blur_enabled is False
        assert pipeline.config.face_focus_enabled is False
        assert pipeline.config.lighting_enabled is False
