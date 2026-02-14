"""Unit tests for camera module."""

import pytest
import numpy as np
from app.camera.camera import CameraManager, CameraConfig


def test_camera_config_defaults():
    """Test default camera configuration."""
    config = CameraConfig()
    assert config.index == 0
    assert config.width == 960
    assert config.height == 540
    assert config.target_fps == 24


def test_camera_manager_initialization():
    """Test camera manager initialization."""
    manager = CameraManager()
    assert manager is not None
    assert not manager.is_open


def test_camera_manager_custom_config():
    """Test camera manager with custom config."""
    config = CameraConfig(width=640, height=480, target_fps=30)
    manager = CameraManager(config)
    assert manager.config.width == 640
    assert manager.config.height == 480
    assert manager.config.target_fps == 30


@pytest.mark.skipif(not pytest.config.getoption("--run-camera-tests"),
                    reason="Camera tests require physical camera")
def test_camera_open():
    """Test camera opening (requires physical camera)."""
    manager = CameraManager()
    success, message = manager.open()
    
    if success:
        assert manager.is_open
        assert "success" in message.lower()
        manager.release()
    else:
        # Camera not available is acceptable in CI
        assert "unable" in message.lower() or "permission" in message.lower()


@pytest.mark.skipif(not pytest.config.getoption("--run-camera-tests"),
                    reason="Camera tests require physical camera")
def test_camera_read_frame():
    """Test frame reading (requires physical camera)."""
    manager = CameraManager()
    success, _ = manager.open()
    
    if not success:
        pytest.skip("Camera not available")
    
    ok, frame, error = manager.read_frame()
    
    if ok:
        assert frame is not None
        assert isinstance(frame, np.ndarray)
        assert frame.ndim == 3
        assert frame.shape[2] == 3  # RGB
    
    manager.release()


def test_camera_release():
    """Test camera release."""
    manager = CameraManager()
    manager.release()  # Should not crash even if not opened
    assert not manager.is_open


def test_camera_fps_tracking():
    """Test FPS calculation."""
    manager = CameraManager()
    fps = manager.get_fps()
    assert fps == 0.0  # No frames read yet


def test_camera_dimensions():
    """Test dimension retrieval."""
    config = CameraConfig(width=640, height=480)
    manager = CameraManager(config)
    width, height = manager.get_dimensions()
    assert width == 640
    assert height == 480


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
