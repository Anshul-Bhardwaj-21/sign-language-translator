"""Unit tests for LightingAdjuster."""

import numpy as np
import pytest

from app.inference.lighting_adjuster import LightingAdjuster, BrightnessAnalysis


class TestLightingAdjuster:
    """Test suite for LightingAdjuster class."""
    
    def test_initialization(self):
        """Test LightingAdjuster initialization with default parameters."""
        adjuster = LightingAdjuster()
        
        assert adjuster.target_brightness == 128.0
        assert adjuster.adjustment_strength == 0.5
        assert adjuster.smoothing_frames == 5
        assert len(adjuster._gamma_buffer) == 5
    
    def test_initialization_with_custom_params(self):
        """Test LightingAdjuster initialization with custom parameters."""
        adjuster = LightingAdjuster(
            target_brightness=140.0,
            adjustment_strength=0.7,
            smoothing_frames=4,
        )
        
        assert adjuster.target_brightness == 140.0
        assert adjuster.adjustment_strength == 0.7
        assert adjuster.smoothing_frames == 4
    
    def test_adjustment_strength_clamping(self):
        """Test that adjustment strength is clamped to 0.0-1.0 range."""
        adjuster1 = LightingAdjuster(adjustment_strength=-0.5)
        assert adjuster1.adjustment_strength == 0.0
        
        adjuster2 = LightingAdjuster(adjustment_strength=1.5)
        assert adjuster2.adjustment_strength == 1.0
    
    def test_analyze_brightness_normal_frame(self):
        """Test brightness analysis on a normal frame."""
        adjuster = LightingAdjuster()
        
        # Create a frame with medium brightness (128)
        frame = np.full((480, 640, 3), 128, dtype=np.uint8)
        
        analysis = adjuster.analyze_brightness(frame)
        
        assert isinstance(analysis, BrightnessAnalysis)
        assert analysis.mean_brightness == pytest.approx(128.0, abs=1.0)
        assert not analysis.is_underexposed
        assert not analysis.is_overexposed
        assert len(analysis.histogram) == 256
    
    def test_analyze_brightness_dark_frame(self):
        """Test brightness analysis on an underexposed frame."""
        adjuster = LightingAdjuster()
        
        # Create a dark frame (brightness 50)
        frame = np.full((480, 640, 3), 50, dtype=np.uint8)
        
        analysis = adjuster.analyze_brightness(frame)
        
        assert analysis.mean_brightness == pytest.approx(50.0, abs=1.0)
        assert analysis.is_underexposed
        assert not analysis.is_overexposed
        assert analysis.recommended_adjustment > 1.0  # Should brighten
    
    def test_analyze_brightness_bright_frame(self):
        """Test brightness analysis on an overexposed frame."""
        adjuster = LightingAdjuster()
        
        # Create a bright frame (brightness 220)
        frame = np.full((480, 640, 3), 220, dtype=np.uint8)
        
        analysis = adjuster.analyze_brightness(frame)
        
        assert analysis.mean_brightness == pytest.approx(220.0, abs=1.0)
        assert not analysis.is_underexposed
        assert analysis.is_overexposed
        assert analysis.recommended_adjustment < 1.0  # Should darken
    
    def test_adjust_dark_frame_increases_brightness(self):
        """Test that adjusting a dark frame increases brightness."""
        adjuster = LightingAdjuster(adjustment_strength=1.0)
        
        # Create a dark frame
        frame = np.full((480, 640, 3), 50, dtype=np.uint8)
        
        adjusted = adjuster.adjust(frame)
        
        # Check that brightness increased
        original_mean = np.mean(frame)
        adjusted_mean = np.mean(adjusted)
        
        assert adjusted_mean > original_mean
        assert adjusted.shape == frame.shape
        assert adjusted.dtype == frame.dtype
    
    def test_adjust_bright_frame_decreases_brightness(self):
        """Test that adjusting a bright frame decreases brightness."""
        adjuster = LightingAdjuster(adjustment_strength=1.0)
        
        # Create a bright frame
        frame = np.full((480, 640, 3), 220, dtype=np.uint8)
        
        adjusted = adjuster.adjust(frame)
        
        # Check that brightness decreased
        original_mean = np.mean(frame)
        adjusted_mean = np.mean(adjusted)
        
        assert adjusted_mean < original_mean
        assert adjusted.shape == frame.shape
        assert adjusted.dtype == frame.dtype
    
    def test_adjust_normal_frame_minimal_change(self):
        """Test that adjusting a well-exposed frame makes minimal changes."""
        adjuster = LightingAdjuster(target_brightness=128.0)
        
        # Create a frame with target brightness
        frame = np.full((480, 640, 3), 128, dtype=np.uint8)
        
        adjusted = adjuster.adjust(frame)
        
        # Check that brightness is similar
        original_mean = np.mean(frame)
        adjusted_mean = np.mean(adjusted)
        
        assert abs(adjusted_mean - original_mean) < 5.0
    
    def test_temporal_smoothing(self):
        """Test that temporal smoothing works over multiple frames."""
        adjuster = LightingAdjuster(smoothing_frames=3, adjustment_strength=1.0)
        
        # Create a dark frame
        frame = np.full((480, 640, 3), 50, dtype=np.uint8)
        
        # Process multiple frames
        adjustments = []
        for _ in range(5):
            adjusted = adjuster.adjust(frame)
            adjustments.append(np.mean(adjusted))
        
        # Check that adjustments converge (later frames should be more stable)
        # The difference between consecutive frames should decrease
        diff1 = abs(adjustments[1] - adjustments[0])
        diff2 = abs(adjustments[3] - adjustments[2])
        
        # Later differences should be smaller (more stable)
        assert diff2 <= diff1 or abs(diff2 - diff1) < 2.0
    
    def test_empty_frame_handling(self):
        """Test that empty frames are handled gracefully."""
        adjuster = LightingAdjuster()
        
        # Create an empty frame
        frame = np.array([], dtype=np.uint8).reshape(0, 0, 3)
        
        adjusted = adjuster.adjust(frame)
        
        # Should return the frame unchanged
        assert adjusted.shape == frame.shape
    
    def test_color_balance_preservation(self):
        """Test that gamma correction preserves color balance."""
        adjuster = LightingAdjuster(adjustment_strength=1.0)
        
        # Create a frame with specific color ratios
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:, :, 0] = 100  # R
        frame[:, :, 1] = 150  # G
        frame[:, :, 2] = 50   # B
        
        adjusted = adjuster.adjust(frame)
        
        # Calculate color ratios
        original_r_mean = np.mean(frame[:, :, 0])
        original_g_mean = np.mean(frame[:, :, 1])
        original_b_mean = np.mean(frame[:, :, 2])
        
        adjusted_r_mean = np.mean(adjusted[:, :, 0])
        adjusted_g_mean = np.mean(adjusted[:, :, 1])
        adjusted_b_mean = np.mean(adjusted[:, :, 2])
        
        # Calculate ratios
        original_rg_ratio = original_r_mean / original_g_mean if original_g_mean > 0 else 0
        adjusted_rg_ratio = adjusted_r_mean / adjusted_g_mean if adjusted_g_mean > 0 else 0
        
        # Ratios should be preserved within 5% tolerance
        if original_rg_ratio > 0:
            ratio_diff = abs(adjusted_rg_ratio - original_rg_ratio) / original_rg_ratio
            assert ratio_diff < 0.05
    
    def test_all_black_frame(self):
        """Test handling of all-black frames."""
        adjuster = LightingAdjuster()
        
        # Create an all-black frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        adjusted = adjuster.adjust(frame)
        
        # Should handle gracefully and return a frame
        assert adjusted.shape == frame.shape
        assert adjusted.dtype == frame.dtype
    
    def test_all_white_frame(self):
        """Test handling of all-white frames."""
        adjuster = LightingAdjuster()
        
        # Create an all-white frame
        frame = np.full((480, 640, 3), 255, dtype=np.uint8)
        
        adjusted = adjuster.adjust(frame)
        
        # Should handle gracefully
        assert adjusted.shape == frame.shape
        assert adjusted.dtype == frame.dtype
    
    def test_single_color_frame(self):
        """Test handling of single-color frames."""
        adjuster = LightingAdjuster()
        
        # Create a single-color frame (red)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:, :, 0] = 128  # Red channel only
        
        adjusted = adjuster.adjust(frame)
        
        # Should handle gracefully
        assert adjusted.shape == frame.shape
        assert adjusted.dtype == frame.dtype
        
        # Red channel should still be the dominant channel
        assert np.mean(adjusted[:, :, 0]) > np.mean(adjusted[:, :, 1])
        assert np.mean(adjusted[:, :, 0]) > np.mean(adjusted[:, :, 2])
    
    def test_histogram_spread_preservation(self):
        """Test that histogram spread is preserved during adjustment."""
        adjuster = LightingAdjuster(adjustment_strength=0.5)
        
        # Create a frame with good contrast (varied brightness)
        frame = np.random.randint(30, 100, size=(480, 640, 3), dtype=np.uint8)
        
        # Calculate original histogram spread
        gray_original = np.mean(frame, axis=2).astype(np.uint8)
        std_original = np.std(gray_original)
        
        adjusted = adjuster.adjust(frame)
        
        # Calculate adjusted histogram spread
        gray_adjusted = np.mean(adjusted, axis=2).astype(np.uint8)
        std_adjusted = np.std(gray_adjusted)
        
        # Spread should not decrease by more than 15%
        if std_original > 0:
            spread_ratio = std_adjusted / std_original
            assert spread_ratio >= 0.85
