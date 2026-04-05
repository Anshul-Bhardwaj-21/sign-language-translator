"""Face detection and automatic framing for video frames."""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from typing import Deque, Optional, Tuple

import cv2
import numpy as np


logger = logging.getLogger(__name__)


@dataclass
class FaceDetection:
    """Face detection result."""
    
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    confidence: float
    center: Tuple[float, float]  # Normalized (x, y)
    size_ratio: float  # Face height / frame height


class FaceFocuser:
    """Face detection and automatic framing."""
    
    def __init__(
        self,
        target_face_size: float = 0.35,
        smoothing_frames: int = 8,
        face_detector_model: str = "haarcascade",
    ):
        """
        Initialize face focuser with face detection model and framing parameters.
        
        Args:
            target_face_size: Target face size as ratio of frame height (0.25-0.40), default 0.35
            smoothing_frames: Number of frames for temporal smoothing (5-10), default 8
            face_detector_model: Face detection model to use, default "haarcascade"
        """
        self.target_face_size = max(0.25, min(0.40, target_face_size))
        self.smoothing_frames = max(5, min(10, smoothing_frames))
        self.face_detector_model = face_detector_model
        
        # Initialize face detector
        self._face_cascade = None
        self._initialize_detector()
        
        # Temporal smoothing buffers
        self._center_buffer: Deque[Tuple[float, float]] = deque(maxlen=self.smoothing_frames)
        self._zoom_buffer: Deque[float] = deque(maxlen=self.smoothing_frames)
        
        # Initialize with default values (center of frame, 1.0x zoom)
        for _ in range(self.smoothing_frames):
            self._center_buffer.append((0.5, 0.5))
            self._zoom_buffer.append(1.0)
        
        # Timeout tracking
        self._frames_without_face = 0
        self._timeout_threshold = 60  # 2 seconds at 30 FPS
        self._return_frames = 30  # Frames to return to default
        
        logger.info(
            f"FaceFocuser initialized: target_size={target_face_size}, "
            f"smoothing={smoothing_frames}, model={face_detector_model}"
        )
    
    def _initialize_detector(self) -> None:
        """Initialize OpenCV Haar Cascade face detector."""
        try:
            # Load Haar Cascade classifier for face detection
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self._face_cascade = cv2.CascadeClassifier(cascade_path)
            
            if self._face_cascade.empty():
                raise RuntimeError("Failed to load Haar Cascade classifier")
            
            logger.info("Face detector initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize face detector: {e}")
            self._face_cascade = None
    
    def process(self, frame: np.ndarray) -> Tuple[np.ndarray, Optional[FaceDetection]]:
        """
        Detect face and apply digital pan/zoom.
        
        Args:
            frame: RGB frame as numpy array (H, W, 3)
            
        Returns:
            Tuple of (focused frame, face detection result)
        """
        if frame.size == 0:
            logger.warning("Empty frame received, returning unchanged")
            return frame, None
        
        if self._face_cascade is None:
            logger.warning("Face detector not initialized, returning unchanged frame")
            return frame, None
        
        try:
            # Detect face
            face_detection = self.detect_face(frame)
            
            if face_detection is not None:
                # Reset timeout counter
                self._frames_without_face = 0
                
                # Calculate target center and zoom
                target_center = face_detection.center
                target_zoom = self._calculate_target_zoom(face_detection.size_ratio)
                
                # Add to smoothing buffers
                self._center_buffer.append(target_center)
                self._zoom_buffer.append(target_zoom)
            else:
                # Increment timeout counter
                self._frames_without_face += 1
                
                # If timeout exceeded, gradually return to default
                if self._frames_without_face > self._timeout_threshold:
                    # Calculate progress toward default (0 to 1)
                    progress = min(
                        1.0,
                        (self._frames_without_face - self._timeout_threshold) / self._return_frames
                    )
                    
                    # Interpolate toward default values
                    default_center = (0.5, 0.5)
                    default_zoom = 1.0
                    
                    current_center = self._center_buffer[-1]
                    current_zoom = self._zoom_buffer[-1]
                    
                    target_center = (
                        current_center[0] + (default_center[0] - current_center[0]) * progress,
                        current_center[1] + (default_center[1] - current_center[1]) * progress,
                    )
                    target_zoom = current_zoom + (default_zoom - current_zoom) * progress
                    
                    self._center_buffer.append(target_center)
                    self._zoom_buffer.append(target_zoom)
            
            # Calculate smoothed center and zoom
            smoothed_center = self._calculate_smoothed_center()
            smoothed_zoom = self._calculate_smoothed_zoom()
            
            # Apply digital pan/zoom
            focused_frame = self._apply_pan_zoom(frame, smoothed_center, smoothed_zoom)
            
            return focused_frame, face_detection
            
        except Exception as e:
            logger.error(f"Face focusing failed: {e}")
            return frame, None
    
    def detect_face(self, frame: np.ndarray) -> Optional[FaceDetection]:
        """
        Detect primary face in frame.
        
        Args:
            frame: RGB frame as numpy array
            
        Returns:
            FaceDetection with bounding box and confidence, or None
        """
        if self._face_cascade is None:
            return None
        
        try:
            # Convert to grayscale for face detection
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            else:
                gray = frame
            
            # Detect faces
            faces = self._face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            if len(faces) == 0:
                return None
            
            # Select largest face by area
            largest_face = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = largest_face
            
            # Calculate normalized center
            frame_height, frame_width = frame.shape[:2]
            center_x = (x + w / 2) / frame_width
            center_y = (y + h / 2) / frame_height
            
            # Calculate size ratio
            size_ratio = h / frame_height
            
            # Confidence is not provided by Haar Cascade, use 1.0
            confidence = 1.0
            
            return FaceDetection(
                bbox=(int(x), int(y), int(w), int(h)),
                confidence=confidence,
                center=(center_x, center_y),
                size_ratio=size_ratio,
            )
            
        except Exception as e:
            logger.error(f"Face detection failed: {e}")
            return None
    
    def _calculate_target_zoom(self, current_size_ratio: float) -> float:
        """
        Calculate target zoom level to achieve target face size.
        
        Args:
            current_size_ratio: Current face height / frame height
            
        Returns:
            Target zoom factor
        """
        if current_size_ratio <= 0:
            return 1.0
        
        # Calculate zoom needed to reach target size
        # If face is too small, zoom in; if too large, zoom out
        target_zoom = self.target_face_size / current_size_ratio
        
        # Clamp zoom to reasonable range (0.8x to 3.0x)
        target_zoom = max(0.8, min(3.0, target_zoom))
        
        return target_zoom
    
    def _calculate_smoothed_center(self) -> Tuple[float, float]:
        """
        Calculate smoothed center position from buffer.
        
        Returns:
            Smoothed (x, y) center position (normalized)
        """
        if not self._center_buffer:
            return (0.5, 0.5)
        
        # Average all positions in buffer
        avg_x = sum(c[0] for c in self._center_buffer) / len(self._center_buffer)
        avg_y = sum(c[1] for c in self._center_buffer) / len(self._center_buffer)
        
        return (avg_x, avg_y)
    
    def _calculate_smoothed_zoom(self) -> float:
        """
        Calculate smoothed zoom level from buffer.
        
        Returns:
            Smoothed zoom factor
        """
        if not self._zoom_buffer:
            return 1.0
        
        # Average all zoom levels in buffer
        avg_zoom = sum(self._zoom_buffer) / len(self._zoom_buffer)
        
        return avg_zoom
    
    def _apply_pan_zoom(
        self,
        frame: np.ndarray,
        center: Tuple[float, float],
        zoom: float,
    ) -> np.ndarray:
        """
        Apply digital pan and zoom to frame while preserving aspect ratio.
        
        Args:
            frame: RGB frame as numpy array
            center: Target center position (normalized x, y)
            zoom: Zoom factor (1.0 = no zoom)
            
        Returns:
            Pan/zoomed frame with same dimensions as input
        """
        frame_height, frame_width = frame.shape[:2]
        
        # Calculate crop dimensions
        crop_width = int(frame_width / zoom)
        crop_height = int(frame_height / zoom)
        
        # Ensure crop dimensions are valid
        crop_width = max(1, min(crop_width, frame_width))
        crop_height = max(1, min(crop_height, frame_height))
        
        # Calculate crop position to center on target
        center_x = int(center[0] * frame_width)
        center_y = int(center[1] * frame_height)
        
        crop_x = center_x - crop_width // 2
        crop_y = center_y - crop_height // 2
        
        # Clamp crop position to frame boundaries
        crop_x = max(0, min(crop_x, frame_width - crop_width))
        crop_y = max(0, min(crop_y, frame_height - crop_height))
        
        # Crop the frame
        cropped = frame[crop_y:crop_y + crop_height, crop_x:crop_x + crop_width]
        
        # Resize back to original dimensions (preserves aspect ratio)
        resized = cv2.resize(cropped, (frame_width, frame_height), interpolation=cv2.INTER_LINEAR)
        
        return resized
