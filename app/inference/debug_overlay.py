"""Visual debug overlay utilities for real-time frame diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np


@dataclass
class OverlayInfo:
    fps: float = 0.0
    system_status: str = "Stopped"
    hand_detected: bool = False
    movement_state: str = "no_hand"
    gesture: str = "none"
    note: str = ""


@dataclass
class DebugInfo:
    """
    Legacy debug info structure kept for compatibility with older call modules.
    """

    fps: float = 0.0
    hand_detected: bool = False
    hand_count: int = 0
    movement_state: str = "no_hand"
    movement_magnitude: float = 0.0
    confidence: float = 0.0
    gesture: str = "none"
    status: str = "Running"
    note: str = ""


def draw_debug_overlay(frame_rgb: np.ndarray, info: OverlayInfo) -> np.ndarray:
    """Draw a compact, high-contrast debug panel on an RGB frame."""
    if frame_rgb is None or frame_rgb.size == 0:
        return frame_rgb

    canvas = frame_rgb.copy()
    _draw_panel_background(canvas)

    status_color = _status_color(info.system_status)
    hand_color = (0, 200, 0) if info.hand_detected else (220, 70, 70)
    movement_color = _movement_color(info.movement_state)

    lines = [
        (f"FPS: {info.fps:4.1f}", (250, 250, 250)),
        (f"Status: {info.system_status}", status_color),
        (f"Hand: {'Detected' if info.hand_detected else 'Not detected'}", hand_color),
        (f"Movement: {info.movement_state}", movement_color),
        (f"Gesture: {info.gesture}", (255, 215, 120)),
    ]

    y = 28
    for text, color in lines:
        cv2.putText(canvas, text, (14, y), cv2.FONT_HERSHEY_SIMPLEX, 0.52, color, 1, cv2.LINE_AA)
        y += 22

    if info.note:
        cv2.putText(canvas, info.note, (14, y + 2), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1, cv2.LINE_AA)

    return canvas


def _draw_panel_background(frame_rgb: np.ndarray) -> None:
    overlay = frame_rgb.copy()
    cv2.rectangle(overlay, (6, 6), (420, 150), (8, 8, 8), thickness=-1)
    cv2.addWeighted(overlay, 0.55, frame_rgb, 0.45, 0, frame_rgb)
    cv2.rectangle(frame_rgb, (6, 6), (420, 150), (180, 180, 180), thickness=1)


def _status_color(status: str) -> tuple[int, int, int]:
    mapping = {
        "Running": (20, 220, 120),
        "Paused": (255, 200, 0),
        "No Hand": (255, 130, 130),
        "Camera Error": (255, 100, 100),
        "Stopped": (180, 180, 180),
    }
    return mapping.get(status, (210, 210, 210))


def _movement_color(state: str) -> tuple[int, int, int]:
    mapping = {
        "idle": (190, 190, 190),
        "stable": (40, 220, 90),
        "moving": (255, 170, 60),
        "moving_fast": (255, 90, 90),
        "no_hand": (255, 130, 130),
    }
    return mapping.get(state, (190, 190, 190))


def draw_debug_info(
    frame_rgb: np.ndarray,
    debug_info: DebugInfo,
) -> np.ndarray:
    """
    Backward-compatible wrapper used by legacy call-session pipeline.
    """
    info = OverlayInfo(
        fps=debug_info.fps,
        system_status=debug_info.status or "Running",
        hand_detected=debug_info.hand_detected,
        movement_state=debug_info.movement_state,
        gesture=debug_info.gesture,
        note=debug_info.note,
    )
    return draw_debug_overlay(frame_rgb, info)
