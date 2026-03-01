"""Computer vision enhancement pipeline for video call quality improvements."""

from __future__ import annotations

import json
import logging
import time
import psutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from app.inference.hand_detector import HandDetector, HandDetectionResult
from app.inference.movement_tracker import MovementTracker, MovementSnapshot
from app.inference.gesture_controls import GestureController, GestureEvent
from app.inference.lighting_adjuster import LightingAdjuster


logger = logging.getLogger(__name__)


Landmark = Tuple[float, float, float]


@dataclass
class EnhancementConfig:
    """Configuration for CV enhancement pipeline."""
    
    # Feature toggles
    lighting_enabled: bool = True
    face_focus_enabled: bool = False
    background_blur_enabled: bool = False
    hand_tracking_enabled: bool = True
    gesture_detection_enabled: bool = True
    
    # Lighting parameters
    lighting_target_brightness: float = 128.0
    lighting_adjustment_strength: float = 0.5
    
    # Face focus parameters
    face_target_size: float = 0.35
    face_smoothing_frames: int = 8
    
    # Background blur parameters
    blur_intensity: int = 5
    blur_edge_smoothing: bool = True
    
    # Performance parameters
    max_processing_time_ms: float = 50.0
    enable_frame_skipping: bool = True
    target_fps: int = 20
    
    def to_dict(self) -> Dict:
        """Convert config to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> EnhancementConfig:
        """Create config from dictionary."""
        return cls(**data)
    
    def save(self, path: Path) -> None:
        """Save configuration to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Saved enhancement config to {path}")
    
    @classmethod
    def load(cls, path: Path) -> EnhancementConfig:
        """Load configuration from JSON file."""
        if not path.exists():
            logger.warning(f"Config file not found at {path}, using defaults")
            return cls()
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded enhancement config from {path}")
            return cls.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load config from {path}: {e}")
            return cls()


@dataclass
class FrameMetadata:
    """Metadata for video frames."""
    
    sequence_number: int
    timestamp: float
    width: int
    height: int
    format: str = "RGB"


@dataclass
class BrightnessAnalysis:
    """Brightness analysis results."""
    
    mean_brightness: float  # 0-255
    std_brightness: float
    histogram: np.ndarray
    is_underexposed: bool
    is_overexposed: bool
    recommended_adjustment: float  # Gamma correction factor


@dataclass
class FaceDetection:
    """Face detection result."""
    
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    confidence: float
    center: Tuple[float, float]  # Normalized (x, y)
    size_ratio: float  # Face height / frame height


@dataclass
class PerformanceMetrics:
    """Performance metrics for enhancement pipeline."""
    
    current_fps: float = 0.0
    average_processing_time_ms: float = 0.0
    frames_processed: int = 0
    frames_skipped: int = 0
    
    # Per-enhancement timing
    lighting_time_ms: float = 0.0
    face_focus_time_ms: float = 0.0
    background_blur_time_ms: float = 0.0
    hand_detection_time_ms: float = 0.0
    movement_tracking_time_ms: float = 0.0
    gesture_recognition_time_ms: float = 0.0
    
    # Resource usage
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0


@dataclass
class ProcessedFrame:
    """Complete result from enhancement pipeline."""
    
    frame: np.ndarray  # Processed RGB frame
    metadata: FrameMetadata  # Original frame metadata
    
    # Detection results
    hand_detection: Optional[HandDetectionResult] = None
    movement_snapshot: Optional[MovementSnapshot] = None
    gesture_event: Optional[GestureEvent] = None
    face_detection: Optional[FaceDetection] = None
    
    # Enhancement metadata
    lighting_applied: bool = False
    brightness_adjustment: float = 0.0
    face_focus_applied: bool = False
    background_blur_applied: bool = False
    
    # Performance metrics
    processing_time_ms: float = 0.0
    timestamp: float = 0.0


class EnhancementPipeline:
    """Orchestrates CV enhancement processing for video frames."""
    
    def __init__(
        self,
        config: Optional[EnhancementConfig] = None,
        hand_detector: Optional[HandDetector] = None,
        movement_tracker: Optional[MovementTracker] = None,
        gesture_controller: Optional[GestureController] = None,
    ):
        """Initialize pipeline with configuration and existing modules."""
        self.config = config or EnhancementConfig()
        
        # Existing ML modules
        self._hand_detector = hand_detector
        self._movement_tracker = movement_tracker
        self._gesture_controller = gesture_controller
        
        # Enhancement processors
        self._lighting_adjuster = None
        self._face_focuser = None
        self._background_processor = None
        
        # Initialize processors based on config
        self._initialize_processors()
        
        # Performance tracking
        self._metrics = PerformanceMetrics()
        self._frame_times: List[float] = []
        self._last_fps_update = time.time()
        
        # Frame queue for skipping logic
        self._frame_queue_depth = 0
        self._frame_skip_threshold = 3
        
        # Resource monitoring
        self._process = psutil.Process()
        
        # Adaptive quality reduction
        self._cpu_samples: List[float] = []
        self._fps_samples: List[float] = []
        self._degradation_active = False
        self._degradation_level = 0  # 0 = no degradation, 1-3 = increasing degradation
        self._last_degradation_check = time.time()
        self._degradation_check_interval = 1.0  # Check every second
        
        logger.info("EnhancementPipeline initialized")
    
    def _initialize_processors(self) -> None:
        """Initialize enhancement processors based on configuration."""
        # Initialize LightingAdjuster
        if self.config.lighting_enabled:
            try:
                self._lighting_adjuster = LightingAdjuster(
                    target_brightness=self.config.lighting_target_brightness,
                    adjustment_strength=self.config.lighting_adjustment_strength,
                    smoothing_frames=5,
                )
                logger.info("LightingAdjuster initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize LightingAdjuster: {e}")
        
        # Initialize FaceFocuser
        if self.config.face_focus_enabled:
            try:
                from app.inference.face_focuser import FaceFocuser
                self._face_focuser = FaceFocuser(
                    target_face_size=self.config.face_target_size,
                    smoothing_frames=self.config.face_smoothing_frames,
                )
                logger.info("FaceFocuser initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize FaceFocuser: {e}")
        
        # Initialize BackgroundProcessor
        if self.config.background_blur_enabled:
            try:
                from app.inference.background_processor import BackgroundProcessor
                self._background_processor = BackgroundProcessor(
                    blur_intensity=self.config.blur_intensity,
                    edge_smoothing=self.config.blur_edge_smoothing,
                )
                logger.info("BackgroundProcessor initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize BackgroundProcessor: {e}")
    
    def process_frame(
        self,
        frame: np.ndarray,
        metadata: FrameMetadata,
    ) -> ProcessedFrame:
        """
        Process a single frame through the enhancement pipeline.
        
        Processing order: lighting → face focus → hand detection → movement tracking → 
                         gesture recognition → background blur
        
        Args:
            frame: RGB frame as numpy array (H, W, 3)
            metadata: Frame timestamp and sequence number
            
        Returns:
            ProcessedFrame with enhanced image and detection results
        """
        start_time = time.time()
        
        # Check frame skipping logic
        if self.config.enable_frame_skipping and self._frame_queue_depth > self._frame_skip_threshold:
            self._metrics.frames_skipped += 1
            logger.debug(f"Skipping frame {metadata.sequence_number} due to queue depth {self._frame_queue_depth}")
            # Return unprocessed frame
            return ProcessedFrame(
                frame=frame.copy(),
                metadata=metadata,
                timestamp=start_time,
                processing_time_ms=0.0,
            )
        
        # Increment queue depth
        self._frame_queue_depth += 1
        
        # Initialize result
        result = ProcessedFrame(
            frame=frame.copy(),
            metadata=metadata,
            timestamp=start_time,
        )
        
        # Start with original frame
        current_frame = frame.copy()
        
        try:
            # 1. Lighting adjustment (if enabled)
            if self.config.lighting_enabled and self._lighting_adjuster is not None:
                lighting_start = time.time()
                try:
                    current_frame = self._lighting_adjuster.adjust(current_frame)
                    result.lighting_applied = True
                    self._metrics.lighting_time_ms = (time.time() - lighting_start) * 1000
                except Exception as e:
                    logger.error(f"Lighting adjustment failed for frame {metadata.sequence_number}: {e}")
                    # Fallback: continue with unprocessed frame
            
            # 2. Face focus (if enabled)
            if self.config.face_focus_enabled and self._face_focuser is not None:
                face_start = time.time()
                try:
                    current_frame, face_det = self._face_focuser.process(current_frame)
                    result.face_detection = face_det
                    result.face_focus_applied = face_det is not None
                    self._metrics.face_focus_time_ms = (time.time() - face_start) * 1000
                except Exception as e:
                    logger.error(f"Face focus failed for frame {metadata.sequence_number}: {e}")
                    # Fallback: continue with current frame state
            
            # 3. Hand detection (if enabled)
            if self.config.hand_tracking_enabled and self._hand_detector is not None:
                hand_start = time.time()
                try:
                    hand_result = self._hand_detector.detect(current_frame, draw_landmarks=False)
                    result.hand_detection = hand_result
                    self._metrics.hand_detection_time_ms = (time.time() - hand_start) * 1000
                    
                    # 4. Movement tracking (if hand detected)
                    if self._movement_tracker is not None:
                        movement_start = time.time()
                        try:
                            if hand_result.hand_detected:
                                movement_snapshot = self._movement_tracker.update(hand_result.primary_landmarks)
                            else:
                                # Update tracker with no hand
                                movement_snapshot = self._movement_tracker.update(None)
                            result.movement_snapshot = movement_snapshot
                            self._metrics.movement_tracking_time_ms = (time.time() - movement_start) * 1000
                            
                            # 5. Gesture recognition (if enabled and hand detected)
                            if self.config.gesture_detection_enabled and self._gesture_controller is not None and hand_result.hand_detected:
                                gesture_start = time.time()
                                try:
                                    gesture_event = self._gesture_controller.update(
                                        landmarks=hand_result.primary_landmarks,
                                        movement_state=movement_snapshot.state,
                                        handedness=hand_result.handedness,
                                    )
                                    result.gesture_event = gesture_event
                                    self._metrics.gesture_recognition_time_ms = (time.time() - gesture_start) * 1000
                                except Exception as e:
                                    logger.error(f"Gesture recognition failed for frame {metadata.sequence_number}: {e}")
                                    # Fallback: continue without gesture event
                        except Exception as e:
                            logger.error(f"Movement tracking failed for frame {metadata.sequence_number}: {e}")
                            # Fallback: continue without movement data
                
                except Exception as e:
                    logger.error(f"Hand detection failed for frame {metadata.sequence_number}: {e}")
                    # Fallback: continue without hand detection
            
            # 6. Background blur (if enabled) - applied last
            if self.config.background_blur_enabled and self._background_processor is not None:
                blur_start = time.time()
                try:
                    current_frame, _ = self._background_processor.process(current_frame)
                    result.background_blur_applied = True
                    self._metrics.background_blur_time_ms = (time.time() - blur_start) * 1000
                except Exception as e:
                    logger.error(f"Background blur failed for frame {metadata.sequence_number}: {e}")
                    # Fallback: continue with current frame state
            
            # Update result with processed frame
            result.frame = current_frame
            
        except Exception as e:
            logger.error(f"Frame processing failed for frame {metadata.sequence_number}: {e}")
            # Return original frame on critical error
            result.frame = frame
        
        # Update performance metrics
        processing_time = (time.time() - start_time) * 1000
        result.processing_time_ms = processing_time
        self._update_metrics(processing_time)
        
        # Log performance warning if threshold exceeded
        if processing_time > self.config.max_processing_time_ms:
            logger.warning(
                f"Frame {metadata.sequence_number} processing time {processing_time:.2f}ms "
                f"exceeds threshold {self.config.max_processing_time_ms}ms"
            )
        
        # Decrement queue depth
        self._frame_queue_depth = max(0, self._frame_queue_depth - 1)
        
        return result
    
    def update_config(self, config: EnhancementConfig) -> None:
        """Update pipeline configuration at runtime."""
        self.config = config
        # Reinitialize processors with new config
        self._initialize_processors()
        logger.info("Pipeline configuration updated")
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Return current performance statistics."""
        return self._metrics
    
    def _update_metrics(self, processing_time_ms: float) -> None:
        """Update performance metrics with latest frame timing."""
        self._metrics.frames_processed += 1
        self._frame_times.append(processing_time_ms)
        
        # Keep only recent frame times (last 30 frames)
        if len(self._frame_times) > 30:
            self._frame_times.pop(0)
        
        # Calculate average processing time
        if self._frame_times:
            self._metrics.average_processing_time_ms = sum(self._frame_times) / len(self._frame_times)
        
        # Calculate FPS
        current_time = time.time()
        time_delta = current_time - self._last_fps_update
        if time_delta >= 1.0:  # Update FPS every second
            frames_in_period = len([t for t in self._frame_times if t > 0])
            self._metrics.current_fps = frames_in_period / time_delta if time_delta > 0 else 0
            self._last_fps_update = current_time
        
        # Update CPU and memory usage
        try:
            self._metrics.cpu_usage_percent = self._process.cpu_percent(interval=None)
            memory_info = self._process.memory_info()
            self._metrics.memory_usage_mb = memory_info.rss / (1024 * 1024)  # Convert bytes to MB
        except Exception as e:
            logger.debug(f"Failed to update resource metrics: {e}")
        
        # Check for adaptive quality reduction
        self._check_adaptive_quality_reduction()
    
    def _check_adaptive_quality_reduction(self) -> None:
        """
        Check if adaptive quality reduction should be triggered.
        
        Monitors CPU usage and FPS to automatically reduce enhancement quality:
        - If CPU > 80% for sustained period: reduce quality
        - If FPS < 15 for sustained period: disable enhancements in priority order
        """
        current_time = time.time()
        
        # Only check periodically (every second)
        if current_time - self._last_degradation_check < self._degradation_check_interval:
            return
        
        self._last_degradation_check = current_time
        
        # Collect CPU and FPS samples
        self._cpu_samples.append(self._metrics.cpu_usage_percent)
        self._fps_samples.append(self._metrics.current_fps)
        
        # Keep only recent samples (last 10 seconds) - trim before checking
        while len(self._cpu_samples) > 10:
            self._cpu_samples.pop(0)
        while len(self._fps_samples) > 10:
            self._fps_samples.pop(0)
        
        # Need at least 3 samples to make a decision
        if len(self._cpu_samples) < 3 or len(self._fps_samples) < 3:
            return
        
        # Calculate average CPU and FPS
        avg_cpu = sum(self._cpu_samples) / len(self._cpu_samples)
        avg_fps = sum(self._fps_samples) / len(self._fps_samples)
        
        # Determine if degradation is needed
        should_degrade = False
        degradation_reason = ""
        
        # Check CPU threshold (80%)
        if avg_cpu > 80.0:
            should_degrade = True
            degradation_reason = f"CPU usage {avg_cpu:.1f}% exceeds 80%"
        
        # Check FPS threshold (15 FPS)
        if avg_fps > 0 and avg_fps < 15.0:
            should_degrade = True
            degradation_reason = f"FPS {avg_fps:.1f} below 15"
        
        # Apply degradation if needed
        if should_degrade and not self._degradation_active:
            self._apply_quality_degradation(degradation_reason)
        elif not should_degrade and self._degradation_active:
            # Conditions improved, restore quality
            self._restore_quality()
    
    def _apply_quality_degradation(self, reason: str) -> None:
        """
        Apply quality degradation by disabling enhancements in priority order.
        
        Priority order (disable in this order):
        1. Background blur (most expensive)
        2. Face focus (moderate cost)
        3. Lighting adjustment (least expensive)
        
        Args:
            reason: Reason for degradation (for logging)
        """
        if self._degradation_active:
            return
        
        self._degradation_active = True
        self._degradation_level = 1
        
        logger.warning(f"Applying adaptive quality degradation: {reason}")
        
        # Level 1: Disable background blur
        if self.config.background_blur_enabled:
            self.config.background_blur_enabled = False
            logger.info("Degradation level 1: Disabled background blur")
            return
        
        # Level 2: Disable face focus
        if self.config.face_focus_enabled:
            self.config.face_focus_enabled = False
            self._degradation_level = 2
            logger.info("Degradation level 2: Disabled face focus")
            return
        
        # Level 3: Disable lighting adjustment
        if self.config.lighting_enabled:
            self.config.lighting_enabled = False
            self._degradation_level = 3
            logger.info("Degradation level 3: Disabled lighting adjustment")
            return
        
        logger.info("All enhancements already disabled")
    
    def _restore_quality(self) -> None:
        """
        Restore quality by re-enabling enhancements.
        
        Re-enables enhancements in reverse priority order.
        """
        if not self._degradation_active:
            return
        
        logger.info("Performance improved, restoring enhancement quality")
        
        # Restore based on degradation level
        if self._degradation_level >= 3:
            self.config.lighting_enabled = True
            logger.info("Re-enabled lighting adjustment")
        
        if self._degradation_level >= 2:
            self.config.face_focus_enabled = True
            logger.info("Re-enabled face focus")
        
        if self._degradation_level >= 1:
            self.config.background_blur_enabled = True
            logger.info("Re-enabled background blur")
        
        self._degradation_active = False
        self._degradation_level = 0
        
        # Clear samples to avoid immediate re-degradation
        self._cpu_samples.clear()
        self._fps_samples.clear()


def get_default_config_path() -> Path:
    """Get default path for enhancement configuration."""
    return Path.home() / ".kiro" / "cv_enhancement_config.json"


def load_config(path: Optional[Path] = None) -> EnhancementConfig:
    """Load enhancement configuration from file or use defaults."""
    config_path = path or get_default_config_path()
    return EnhancementConfig.load(config_path)


def save_config(config: EnhancementConfig, path: Optional[Path] = None) -> None:
    """Save enhancement configuration to file."""
    config_path = path or get_default_config_path()
    config.save(config_path)
