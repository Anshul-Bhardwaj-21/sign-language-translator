"""Gesture-based app controls with debouncing and cooldown protection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


Landmark = Tuple[float, float, float]

# MediaPipe landmark indices.
THUMB_TIP = 4
THUMB_IP = 3
INDEX_TIP = 8
INDEX_PIP = 6
MIDDLE_TIP = 12
MIDDLE_PIP = 10
RING_TIP = 16
RING_PIP = 14
PINKY_TIP = 20
PINKY_PIP = 18


@dataclass
class GestureEvent:
    """Output of gesture controller for the current frame."""

    gesture: str = "none"
    confidence: float = 0.0
    confirmed: bool = False
    action: str = "none"


class GestureController:
    """Converts raw landmark gestures into safe control actions."""

    def __init__(
        self,
        hold_frames: int = 6,
        cooldown_frames: int = 20,
        min_confidence: float = 0.78,
    ) -> None:
        self.hold_frames = hold_frames
        self.cooldown_frames = cooldown_frames
        self.min_confidence = min_confidence
        self._active_candidate = "none"
        self._candidate_frames = 0
        self._cooldown_remaining = 0

    def update(
        self,
        landmarks: Optional[List[Landmark]],
        movement_state: str,
        handedness: Optional[str],
    ) -> GestureEvent:
        """Return a debounced gesture event for current landmarks."""
        if self._cooldown_remaining > 0:
            self._cooldown_remaining -= 1

        if landmarks is None or len(landmarks) < 21:
            self._reset_candidate()
            return GestureEvent()

        raw_gesture, confidence = detect_control_gesture(landmarks, handedness)

        # Ignore controls while hand is in transition to avoid accidental triggers.
        if movement_state not in {"stable", "idle"}:
            raw_gesture = "none"
            confidence = 0.0

        if confidence < self.min_confidence:
            raw_gesture = "none"
            confidence = 0.0

        if raw_gesture == "none":
            self._reset_candidate()
            return GestureEvent()

        if raw_gesture == self._active_candidate:
            self._candidate_frames += 1
        else:
            self._active_candidate = raw_gesture
            self._candidate_frames = 1

        event = GestureEvent(gesture=raw_gesture, confidence=confidence)

        if (
            self._candidate_frames >= self.hold_frames
            and self._cooldown_remaining == 0
        ):
            event.confirmed = True
            event.action = gesture_to_action(raw_gesture)
            self._cooldown_remaining = self.cooldown_frames
            self._reset_candidate()

        return event

    def reset(self) -> None:
        self._cooldown_remaining = 0
        self._reset_candidate()

    def _reset_candidate(self) -> None:
        self._active_candidate = "none"
        self._candidate_frames = 0


def detect_control_gesture(
    landmarks: List[Landmark], handedness: Optional[str] = None
) -> Tuple[str, float]:
    """Detect one of the required control gestures."""
    finger_state = get_finger_state(landmarks, handedness)

    if is_open_palm(finger_state):
        return "open_palm", 0.92

    if is_fist(finger_state):
        return "fist", 0.9

    if is_two_fingers(finger_state):
        return "two_fingers", 0.88

    return "none", 0.0


def get_finger_state(landmarks: List[Landmark], handedness: Optional[str]) -> Dict[str, bool]:
    """Return per-finger extended/curl state."""
    thumb_extended = is_thumb_extended(landmarks, handedness)
    index_extended = is_finger_extended(landmarks, INDEX_TIP, INDEX_PIP)
    middle_extended = is_finger_extended(landmarks, MIDDLE_TIP, MIDDLE_PIP)
    ring_extended = is_finger_extended(landmarks, RING_TIP, RING_PIP)
    pinky_extended = is_finger_extended(landmarks, PINKY_TIP, PINKY_PIP)

    return {
        "thumb": thumb_extended,
        "index": index_extended,
        "middle": middle_extended,
        "ring": ring_extended,
        "pinky": pinky_extended,
    }


def is_finger_extended(
    landmarks: List[Landmark],
    tip_idx: int,
    pip_idx: int,
    margin: float = 0.025,
) -> bool:
    """Finger is extended when tip sits above PIP in normalized y."""
    tip_y = landmarks[tip_idx][1]
    pip_y = landmarks[pip_idx][1]
    return (pip_y - tip_y) > margin


def is_thumb_extended(
    landmarks: List[Landmark], handedness: Optional[str], margin: float = 0.02
) -> bool:
    """Handedness-aware thumb extension check."""
    thumb_tip_x = landmarks[THUMB_TIP][0]
    thumb_ip_x = landmarks[THUMB_IP][0]

    if handedness == "Right":
        return (thumb_ip_x - thumb_tip_x) > margin
    if handedness == "Left":
        return (thumb_tip_x - thumb_ip_x) > margin

    # Fallback when handedness is unavailable.
    return abs(thumb_tip_x - thumb_ip_x) > margin


def is_open_palm(state: Dict[str, bool]) -> bool:
    extended_count = sum(1 for value in state.values() if value)
    return extended_count >= 4 and state["index"] and state["middle"]


def is_fist(state: Dict[str, bool]) -> bool:
    return not state["index"] and not state["middle"] and not state["ring"] and not state["pinky"]


def is_two_fingers(state: Dict[str, bool]) -> bool:
    return (
        state["index"]
        and state["middle"]
        and not state["ring"]
        and not state["pinky"]
    )


def gesture_to_action(gesture: str) -> str:
    mapping = {
        "open_palm": "toggle_pause",
        "fist": "confirm_sentence",
        "two_fingers": "undo_last_word",
    }
    return mapping.get(gesture, "none")


def action_feedback(action: str) -> str:
    messages = {
        "toggle_pause": "Open palm detected: pause/resume toggled.",
        "confirm_sentence": "Fist detected: sentence confirmed.",
        "undo_last_word": "Two fingers detected: last word removed.",
    }
    return messages.get(action, "")


# ---------------------------------------------------------------------------
# Legacy compatibility API
# ---------------------------------------------------------------------------

class GestureDetector:
    """
    Backward-compatible wrapper around `GestureController`.
    """

    def __init__(self, debounce_frames: int = 6, confidence_threshold: float = 0.78) -> None:
        self._controller = GestureController(
            hold_frames=debounce_frames,
            min_confidence=confidence_threshold,
        )

    def detect(
        self,
        landmarks: Optional[List[Landmark]],
    ) -> Tuple[str, float, bool]:
        event = self._controller.update(
            landmarks=landmarks,
            movement_state="stable",
            handedness=None,
        )
        legacy_name = {
            "open_palm": "pause",
            "fist": "confirm",
            "two_fingers": "undo",
            "none": "none",
        }.get(event.gesture, "none")
        return legacy_name, event.confidence, event.confirmed

    def reset(self) -> None:
        self._controller.reset()
