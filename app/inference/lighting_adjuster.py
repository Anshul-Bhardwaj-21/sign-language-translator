"""Automatic brightness and exposure adjustment for video frames."""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from typing import Deque, Tuple

import cv2
import numpy as np


logger = logging.getLogger(__name__)


@dataclass
class BrightnessAnalysis:
    """Brightness analysis results."""
    
    mean_brightness: float  # 0-255
    std_brightness: float
    histogram: np.ndarray
    is_underexposed: bool
    is_overexposed: bool
    recommended_adjustment: float  # Gamma correction factor


class LightingAdjuster:
    """Automatic brightness and exposure adjustment."""
    
    def __init__(
        self,
        target_brightness: float = 128.0,
        adjustment_strength: float = 0.5,
        smoothing_frames: int = 5,
    ):
        """
        Initialize lighting adjuster with target brightness and adjustment parameters.
        
        Args:
            target_brightness: Target mean brightness (0-255 scale), default 128.0
            adjustment_strength: Adjustment intensity (0.0-1.0), default 0.5
            smoothing_frames: Number of frames for temporal smoothing (3-5), default 5
        """
        self.target_brightness = target_brightness
        self.adjustment_strength = max(0.0, min(1.0, adjustment_strength))
        self.smoothing_frames = max(3, min(10, smoothing_frames))
        
        # Temporal smoothing buffer for gamma values
        self._gamma_buffer: Deque[float] = deque(maxlen=self.smoothing_frames)
        
        # Initialize with neutral gamma
        for _ in range(self.smoothing_frames):
            self._gamma_buffer.append(1.0)
        
        logger.info(
            f"LightingAdjuster initialized: target={target_brightness}, "
            f"strength={adjustment_strength}, smoothing={smoothing_frames}"
        )
    
    def adjust(self, frame: np.ndarray) -> np.ndarray:
        """
        Adjust frame brightness and exposure.
        
        Args:
            frame: RGB frame as numpy array (H, W, 3)
            
        Returns:
            Brightness-adjusted frame with same shape and dtype
        """
        if frame.size == 0:
            logger.warning("Empty frame received, returning unchanged")
            return frame
        
        try:
            # Analyze current brightness
            analysis = self.analyze_brightness(frame)
            
            # Calculate target gamma correction
            target_gamma = analysis.recommended_adjustment
            
            # Apply adjustment strength to moderate the correction
            # gamma = 1.0 means no change
            # Move gamma toward target by adjustment_strength factor
            adjusted_gamma = 1.0 + (target_gamma - 1.0) * self.adjustment_strength
            
            # Add to smoothing buffer
            self._gamma_buffer.append(adjusted_gamma)
            
            # Calculate smoothed gamma (average of recent frames)
            smoothed_gamma = sum(self._gamma_buffer) / len(self._gamma_buffer)
            
            # Apply gamma correction if needed
            if abs(smoothed_gamma - 1.0) > 0.01:  # Only apply if meaningful change
                adjusted_frame = self._apply_gamma_correction(frame, smoothed_gamma)
                
                # Verify histogram spread preservation
                if not self._verify_histogram_spread(frame, adjusted_frame):
                    logger.debug("Histogram spread not preserved, using lighter correction")
                    # Use a more conservative gamma
                    conservative_gamma = 1.0 + (smoothed_gamma - 1.0) * 0.5
                    adjusted_frame = self._apply_gamma_correction(frame, conservative_gamma)
                
                return adjusted_frame
            else:
                return frame
                
        except Exception as e:
            logger.error(f"Brightness adjustment failed: {e}")
            return frame
    
    def analyze_brightness(self, frame: np.ndarray) -> BrightnessAnalysis:
        """
        Analyze frame brightness characteristics.
        
        Args:
            frame: RGB frame as numpy array
            
        Returns:
            BrightnessAnalysis with mean, histogram, and recommendations
        """
        # Convert to grayscale for brightness analysis
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        else:
            gray = frame
        
        # Calculate brightness statistics
        mean_brightness = float(np.mean(gray))
        std_brightness = float(np.std(gray))
        
        # Calculate histogram
        histogram = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
        
        # Determine exposure status
        is_underexposed = mean_brightness < 80
        is_overexposed = mean_brightness > 200
        
        # Calculate recommended gamma correction
        recommended_adjustment = self._calculate_gamma_correction(
            mean_brightness,
            self.target_brightness,
        )
        
        return BrightnessAnalysis(
            mean_brightness=mean_brightness,
            std_brightness=std_brightness,
            histogram=histogram,
            is_underexposed=is_underexposed,
            is_overexposed=is_overexposed,
            recommended_adjustment=recommended_adjustment,
        )
    
    def _calculate_gamma_correction(
        self,
        current_brightness: float,
        target_brightness: float,
    ) -> float:
        """
        Calculate gamma correction factor to move current brightness toward target.
        
        Args:
            current_brightness: Current mean brightness (0-255)
            target_brightness: Target mean brightness (0-255)
            
        Returns:
            Gamma correction factor (typically 0.5-2.0)
        """
        # Avoid division by zero
        if current_brightness < 1.0:
            current_brightness = 1.0
        if target_brightness < 1.0:
            target_brightness = 1.0
        
        # Calculate gamma using the relationship: output = input^(1/gamma)
        # For mean brightness: target/255 = (current/255)^(1/gamma)
        # Solving for gamma: gamma = log(current/255) / log(target/255)
        
        # Normalize to 0-1 range
        current_norm = current_brightness / 255.0
        target_norm = target_brightness / 255.0
        
        # Calculate gamma
        try:
            gamma = np.log(current_norm) / np.log(target_norm)
        except (ValueError, ZeroDivisionError):
            gamma = 1.0
        
        # Clamp gamma to reasonable range
        gamma = max(0.5, min(2.0, gamma))
        
        return gamma
    
    def _apply_gamma_correction(
        self,
        frame: np.ndarray,
        gamma: float,
    ) -> np.ndarray:
        """
        Apply gamma correction to frame while preserving color balance.
        
        Args:
            frame: RGB frame as numpy array
            gamma: Gamma correction factor
            
        Returns:
            Gamma-corrected frame
        """
        # Build lookup table for gamma correction
        inv_gamma = 1.0 / gamma
        table = np.array([
            ((i / 255.0) ** inv_gamma) * 255
            for i in range(256)
        ]).astype(np.uint8)
        
        # Apply lookup table to all channels (preserves color balance)
        corrected = cv2.LUT(frame, table)
        
        return corrected
    
    def _verify_histogram_spread(
        self,
        original: np.ndarray,
        adjusted: np.ndarray,
        tolerance: float = 0.15,
    ) -> bool:
        """
        Verify that histogram spread is preserved within tolerance.
        
        Args:
            original: Original frame
            adjusted: Adjusted frame
            tolerance: Maximum allowed decrease in std deviation (0.15 = 15%)
            
        Returns:
            True if histogram spread is preserved, False otherwise
        """
        # Convert to grayscale for analysis
        if len(original.shape) == 3 and original.shape[2] == 3:
            gray_original = cv2.cvtColor(original, cv2.COLOR_RGB2GRAY)
            gray_adjusted = cv2.cvtColor(adjusted, cv2.COLOR_RGB2GRAY)
        else:
            gray_original = original
            gray_adjusted = adjusted
        
        # Calculate standard deviations
        std_original = float(np.std(gray_original))
        std_adjusted = float(np.std(gray_adjusted))
        
        # Check if spread decreased too much
        if std_original > 0:
            spread_ratio = std_adjusted / std_original
            return spread_ratio >= (1.0 - tolerance)
        
        return True
