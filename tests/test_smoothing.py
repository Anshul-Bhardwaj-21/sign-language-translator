"""Unit tests for movement tracking and smoothing."""

import pytest
import numpy as np
from app.inference.movement_tracker import MovementTracker, MovementSnapshot


def test_movement_tracker_initialization():
    """Test movement tracker initialization."""
    tracker = MovementTracker()
    assert tracker is not None


def test_movement_tracker_no_hand():
    """Test movement tracker with no hand."""
    tracker = MovementTracker()
    snapshot = tracker.update(None)
    
    assert not snapshot.has_hand
    assert snapshot.state == "no_hand"
    assert snapshot.velocity == 0.0


def test_movement_tracker_stable_hand():
    """Test movement tracker with stable hand."""
    tracker = MovementTracker()
    
    # Same landmarks for multiple frames
    landmarks = [(0.5, 0.5, 0.0) for _ in range(21)]
    
    for _ in range(10):
        snapshot = tracker.update(landmarks)
    
    assert snapshot.has_hand
    assert snapshot.state in ["idle", "stable"]
    assert snapshot.velocity < 0.02


def test_movement_tracker_moving_hand():
    """Test movement tracker with moving hand."""
    tracker = MovementTracker()
    
    # Moving landmarks
    for i in range(10):
        landmarks = [(0.5 + i * 0.01, 0.5, 0.0) for _ in range(21)]
        snapshot = tracker.update(landmarks)
    
    assert snapshot.has_hand
    assert snapshot.state in ["moving", "moving_fast"]
    assert snapshot.velocity > 0.0


def test_movement_tracker_velocity_calculation():
    """Test velocity calculation."""
    tracker = MovementTracker()
    
    # First frame
    landmarks1 = [(0.5, 0.5, 0.0) for _ in range(21)]
    tracker.update(landmarks1)
    
    # Second frame with movement
    landmarks2 = [(0.6, 0.6, 0.0) for _ in range(21)]
    snapshot = tracker.update(landmarks2)
    
    assert snapshot.velocity > 0.0


def test_movement_snapshot_defaults():
    """Test MovementSnapshot defaults."""
    snapshot = MovementSnapshot()
    assert not snapshot.has_hand
    assert snapshot.state == "no_hand"
    assert snapshot.velocity == 0.0
    assert snapshot.frames_in_state == 0


def test_movement_tracker_state_transitions():
    """Test state transitions."""
    tracker = MovementTracker()
    
    # Start with stable hand
    landmarks = [(0.5, 0.5, 0.0) for _ in range(21)]
    for _ in range(10):
        tracker.update(landmarks)
    
    # Move hand quickly
    for i in range(5):
        landmarks = [(0.5 + i * 0.1, 0.5, 0.0) for _ in range(21)]
        snapshot = tracker.update(landmarks)
    
    assert snapshot.state in ["moving", "moving_fast"]
    
    # Stop moving
    landmarks = [(0.9, 0.5, 0.0) for _ in range(21)]
    for _ in range(10):
        snapshot = tracker.update(landmarks)
    
    assert snapshot.state in ["idle", "stable"]


def test_movement_tracker_reset_on_no_hand():
    """Test tracker resets when hand disappears."""
    tracker = MovementTracker()
    
    # Track hand
    landmarks = [(0.5, 0.5, 0.0) for _ in range(21)]
    for _ in range(5):
        tracker.update(landmarks)
    
    # Hand disappears
    snapshot = tracker.update(None)
    
    assert not snapshot.has_hand
    assert snapshot.state == "no_hand"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
