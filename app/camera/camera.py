"""Camera capture utilities with safety-first behavior for Streamlit reruns."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import os
import time
from typing import Deque, Optional, Tuple

import cv2
import numpy as np


@dataclass
class CameraConfig:
    """Runtime camera configuration."""

    index: int = 0
    width: int = 960
    height: int = 540
    target_fps: int = 24
    buffer_size: int = 1
    warmup_frames: int = 3


class CameraManager:
    """
    Owns camera lifecycle and frame retrieval.

    This is stateful on purpose so Streamlit can keep a single camera handle
    in `st.session_state` across reruns.
    """

    def __init__(self, config: Optional[CameraConfig] = None) -> None:
        self.config = config or CameraConfig()
        self._capture: Optional[cv2.VideoCapture] = None
        self._frame_intervals: Deque[float] = deque(maxlen=30)
        self._last_read_ts: Optional[float] = None

    @property
    def is_open(self) -> bool:
        return bool(self._capture is not None and self._capture.isOpened())

    def open(self) -> Tuple[bool, str]:
        """Open camera safely and verify frame reads before success."""
        if self.is_open:
            return True, "Camera already running."

        backends = [cv2.CAP_ANY]
        if os.name == "nt":
            # On Windows, DirectShow often avoids long startup delays.
            backends = [cv2.CAP_DSHOW, cv2.CAP_ANY]

        for backend in backends:
            capture = cv2.VideoCapture(self.config.index, backend)
            if not capture.isOpened():
                capture.release()
                continue

            capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
            capture.set(cv2.CAP_PROP_FPS, self.config.target_fps)
            capture.set(cv2.CAP_PROP_BUFFERSIZE, self.config.buffer_size)

            is_valid = False
            for _ in range(self.config.warmup_frames):
                ok, frame = capture.read()
                if ok and frame is not None and frame.size > 0:
                    is_valid = True
                    break
                time.sleep(0.02)

            if is_valid:
                self._capture = capture
                self._frame_intervals.clear()
                self._last_read_ts = None
                return True, "Camera opened successfully."

            capture.release()

        return (
            False,
            "Unable to open camera. Check permission settings or close other apps "
            "that may already be using the webcam.",
        )

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray], str]:
        """
        Read and resize a frame, returning RGB output for Streamlit display.
        """
        if not self.is_open:
            return False, None, "Camera is not available."

        assert self._capture is not None
        ok, frame_bgr = self._capture.read()
        if not ok or frame_bgr is None or frame_bgr.size == 0:
            return False, None, "Frame grab failed. Camera may be disconnected or busy."

        try:
            frame_bgr = cv2.resize(
                frame_bgr,
                (self.config.width, self.config.height),
                interpolation=cv2.INTER_AREA,
            )
        except Exception:
            # Resize failure should not crash the app; continue with original frame.
            pass

        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        self._update_fps_clock()
        return True, frame_rgb, ""

    def get_fps(self) -> float:
        if not self._frame_intervals:
            return 0.0
        avg_interval = sum(self._frame_intervals) / len(self._frame_intervals)
        if avg_interval <= 0:
            return 0.0
        return 1.0 / avg_interval

    def get_dimensions(self) -> Tuple[int, int]:
        if not self.is_open:
            return self.config.width, self.config.height

        assert self._capture is not None
        width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH) or self.config.width)
        height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or self.config.height)
        return width, height

    def release(self) -> None:
        """Release camera resources safely."""
        if self._capture is not None:
            self._capture.release()
        self._capture = None
        self._frame_intervals.clear()
        self._last_read_ts = None

    def _update_fps_clock(self) -> None:
        now = time.perf_counter()
        if self._last_read_ts is not None:
            self._frame_intervals.append(max(now - self._last_read_ts, 1e-6))
        self._last_read_ts = now


def create_camera_manager(
    camera_index: int = 0,
    width: int = 960,
    height: int = 540,
    target_fps: int = 24,
) -> CameraManager:
    """Factory helper used by the app entrypoint."""
    return CameraManager(
        CameraConfig(
            index=camera_index,
            width=width,
            height=height,
            target_fps=target_fps,
        )
    )


# ---------------------------------------------------------------------------
# Legacy compatibility API
# ---------------------------------------------------------------------------

def open_camera(
    camera_index: int = 0,
    width: int = 640,
    height: int = 480,
    fps: int = 24,
) -> Optional[CameraManager]:
    """
    Backward-compatible wrapper expected by older modules.

    Returns:
        CameraManager when camera opens successfully, otherwise None.
    """
    manager = create_camera_manager(
        camera_index=camera_index,
        width=width,
        height=height,
        target_fps=fps,
    )
    ok, _ = manager.open()
    return manager if ok else None


def get_frame(cap: Optional[object]) -> Tuple[bool, Optional[np.ndarray]]:
    """
    Backward-compatible wrapper expected by older modules.
    """
    if cap is None:
        return False, None

    if isinstance(cap, CameraManager):
        ok, frame_rgb, _ = cap.read_frame()
        return ok, frame_rgb

    # Fallback support for raw cv2.VideoCapture handles.
    if isinstance(cap, cv2.VideoCapture):
        ok, frame_bgr = cap.read()
        if not ok or frame_bgr is None:
            return False, None
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        return True, frame_rgb

    return False, None


def release_camera(cap: Optional[object]) -> bool:
    """
    Backward-compatible wrapper expected by older modules.
    """
    if cap is None:
        return True

    try:
        if isinstance(cap, CameraManager):
            cap.release()
            return True
        if isinstance(cap, cv2.VideoCapture):
            cap.release()
            return True
    except Exception:
        return False
    return False
