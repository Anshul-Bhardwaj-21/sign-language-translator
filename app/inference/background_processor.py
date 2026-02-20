"""Background segmentation and blur effects for video frames."""

from __future__ import annotations

import logging
from collections import deque
from typing import Deque, Tuple

import cv2
import numpy as np


logger = logging.getLogger(__name__)


class BackgroundProcessor:
    """Background segmentation and blur effects."""
    
    def __init__(
        self,
        blur_intensity: int = 5,
        segmentation_model: str = "mediapipe_selfie",
        edge_smoothing: bool = True,
    ):
        """
        Initialize background processor with segmentation model and blur parameters.
        
        Args:
            blur_intensity: Blur intensity level (0-10 scale), default 5
            segmentation_model: Segmentation model to use, default "mediapipe_selfie"
            edge_smoothing: Whether to apply edge smoothing to reduce artifacts, default True
        """
        self.blur_intensity = max(0, min(10, blur_intensity))
        self.segmentation_model = segmentation_model
        self.edge_smoothing = edge_smoothing
        
        # Temporal smoothing buffer for blur intensity transitions
        self._blur_intensity_buffer: Deque[int] = deque(maxlen=5)  # 3-5 frames
        
        # Initialize buffer with current intensity
        for _ in range(5):
            self._blur_intensity_buffer.append(self.blur_intensity)
        
        # MediaPipe Selfie Segmentation model
        self._segmentation_model = None
        self._initialize_segmentation_model()
        
        logger.info(
            f"BackgroundProcessor initialized: blur_intensity={blur_intensity}, "
            f"model={segmentation_model}, edge_smoothing={edge_smoothing}"
        )
    
    def _initialize_segmentation_model(self) -> None:
        """Initialize MediaPipe Selfie Segmentation model."""
        try:
            import mediapipe as mp
            
            # Initialize MediaPipe Selfie Segmentation
            mp_selfie_segmentation = mp.solutions.selfie_segmentation
            self._segmentation_model = mp_selfie_segmentation.SelfieSegmentation(
                model_selection=1  # 1 for general model (supports multiple people)
            )
            
            logger.info("MediaPipe Selfie Segmentation initialized successfully")
        except ImportError:
            logger.error("MediaPipe not installed. Install with: pip install mediapipe")
            self._segmentation_model = None
        except Exception as e:
            logger.error(f"Failed to initialize MediaPipe Selfie Segmentation: {e}")
            self._segmentation_model = None
    
    def process(self, frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Segment person and blur background.
        
        Args:
            frame: RGB frame as numpy array (H, W, 3)
            
        Returns:
            Tuple of (processed frame with blurred background, segmentation mask)
        """
        if frame.size == 0:
            logger.warning("Empty frame received, returning unchanged")
            return frame, np.zeros(frame.shape[:2], dtype=np.uint8)
        
        if self._segmentation_model is None:
            logger.warning("Segmentation model not initialized, returning unchanged frame")
            return frame, np.zeros(frame.shape[:2], dtype=np.uint8)
        
        try:
            # Generate segmentation mask
            mask = self.segment(frame)
            
            # Get smoothed blur intensity
            smoothed_intensity = self._get_smoothed_blur_intensity()
            
            # If blur intensity is 0, return original frame
            if smoothed_intensity == 0:
                return frame, mask
            
            # Apply Gaussian blur to background
            blurred_frame = self._apply_background_blur(frame, mask, smoothed_intensity)
            
            return blurred_frame, mask
            
        except Exception as e:
            logger.error(f"Background processing failed: {e}")
            return frame, np.zeros(frame.shape[:2], dtype=np.uint8)
    
    def segment(self, frame: np.ndarray) -> np.ndarray:
        """
        Generate person segmentation mask.
        
        Args:
            frame: RGB frame as numpy array (H, W, 3)
            
        Returns:
            Binary mask where 1=person, 0=background (H, W) uint8 array
        """
        if self._segmentation_model is None:
            return np.zeros(frame.shape[:2], dtype=np.uint8)
        
        try:
            # MediaPipe expects RGB format
            results = self._segmentation_model.process(frame)
            
            if results.segmentation_mask is None:
                logger.warning("No segmentation mask generated")
                return np.zeros(frame.shape[:2], dtype=np.uint8)
            
            # MediaPipe returns float mask [0.0, 1.0]
            # Convert to binary mask: 1=person, 0=background
            # Use threshold of 0.5 for binary classification
            mask = (results.segmentation_mask > 0.5).astype(np.uint8)
            
            # Apply edge smoothing if enabled
            if self.edge_smoothing:
                mask = self._smooth_mask_edges(mask)
            
            return mask
            
        except Exception as e:
            logger.error(f"Segmentation failed: {e}")
            return np.zeros(frame.shape[:2], dtype=np.uint8)
    
    def set_blur_intensity(self, intensity: int) -> None:
        """
        Update blur intensity with temporal smoothing.
        
        Args:
            intensity: New blur intensity (0-10 scale)
        """
        # Clamp to valid range
        intensity = max(0, min(10, intensity))
        
        # Add to smoothing buffer
        self._blur_intensity_buffer.append(intensity)
        
        # Update current intensity
        self.blur_intensity = intensity
        
        logger.debug(f"Blur intensity updated to {intensity}")
    
    def _get_smoothed_blur_intensity(self) -> int:
        """
        Get smoothed blur intensity from buffer.
        
        Returns:
            Smoothed blur intensity (0-10)
        """
        if not self._blur_intensity_buffer:
            return self.blur_intensity
        
        # Average blur intensities in buffer and round to nearest integer
        avg_intensity = sum(self._blur_intensity_buffer) / len(self._blur_intensity_buffer)
        return int(round(avg_intensity))
    
    def _smooth_mask_edges(self, mask: np.ndarray) -> np.ndarray:
        """
        Apply edge smoothing to segmentation mask to reduce artifacts.
        
        Args:
            mask: Binary segmentation mask (H, W) uint8 array
            
        Returns:
            Smoothed mask
        """
        # Apply Gaussian blur to soften edges
        # Kernel size of 5x5 provides good balance between smoothness and detail
        smoothed = cv2.GaussianBlur(mask.astype(np.float32), (5, 5), 0)
        
        # Convert back to binary with threshold
        smoothed = (smoothed > 0.5).astype(np.uint8)
        
        return smoothed
    
    def _apply_background_blur(
        self,
        frame: np.ndarray,
        mask: np.ndarray,
        intensity: int,
    ) -> np.ndarray:
        """
        Apply Gaussian blur to background regions based on segmentation mask.
        
        Args:
            frame: RGB frame as numpy array (H, W, 3)
            mask: Binary segmentation mask where 1=person, 0=background
            intensity: Blur intensity (0-10 scale)
            
        Returns:
            Frame with blurred background
        """
        # Convert intensity (0-10) to kernel size
        # Kernel size must be odd and positive
        # Map: 0->1 (no blur), 1->5, 2->9, ..., 10->41
        kernel_size = max(1, intensity * 4 + 1)
        if kernel_size % 2 == 0:
            kernel_size += 1  # Ensure odd
        
        # Apply Gaussian blur to entire frame
        blurred = cv2.GaussianBlur(frame, (kernel_size, kernel_size), 0)
        
        # Expand mask to 3 channels to match frame
        mask_3ch = np.stack([mask] * 3, axis=2)
        
        # Blend original (foreground) and blurred (background) using mask
        # Where mask=1 (person), use original frame
        # Where mask=0 (background), use blurred frame
        result = np.where(mask_3ch == 1, frame, blurred)
        
        return result.astype(np.uint8)
    
    def __del__(self):
        """Cleanup MediaPipe resources."""
        if self._segmentation_model is not None:
            try:
                self._segmentation_model.close()
            except Exception:
                pass
