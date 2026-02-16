"""Movement analysis for hand stability and motion-state classification."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, List, Optional, Tuple

import numpy as np


Landmark = Tuple[float, float, float]


@dataclass
class MovementSnapshot:
    """Current movement state after one update cycle."""

    state: str
    movement: float
    average_movement: float
    stable_frames: int
    has_hand: bool


@dataclass
class MovementConfig:
    """Thresholds tuned for normalized MediaPipe coordinates."""

    idle_threshold: float = 0.004
    stable_threshold: float = 0.012
    fast_threshold: float = 0.05
    stable_required_frames: int = 7
    idle_required_frames: int = 14
    smoothing_alpha: float = 0.45
    history_size: int = 30


class MovementTracker:
    """Tracks frame-to-frame landmark movement with smoothing."""

    def __init__(
        self,
        config: Optional[MovementConfig] = None,
        history_size: Optional[int] = None,
    ) -> None:
        if config is not None:
            self.config = config
        else:
            self.config = MovementConfig()
            if history_size is not None:
                self.config.history_size = history_size
        self._history: Deque[float] = deque(maxlen=self.config.history_size)
        self._prev_landmarks: Optional[np.ndarray] = None
        self._smoothed_movement: float = 0.0
        self._stable_frames: int = 0
        self._last_state: str = "no_hand"

    def update(self, landmarks: Optional[List[Landmark]]) -> MovementSnapshot:
        """Update movement state with current landmarks."""
        if landmarks is None or len(landmarks) < 21:
            self._prev_landmarks = None
            self._stable_frames = 0
            self._smoothed_movement *= 0.5
            self._history.append(self._smoothed_movement)
            snapshot = MovementSnapshot(
                state="no_hand",
                movement=self._smoothed_movement,
                average_movement=self.average_movement(),
                stable_frames=self._stable_frames,
                has_hand=False,
            )
            self._last_state = snapshot.state
            return snapshot

        current = np.asarray(landmarks, dtype=np.float32)
        instant_movement = 0.0

        if self._prev_landmarks is not None and self._prev_landmarks.shape == current.shape:
            deltas = current[:, :2] - self._prev_landmarks[:, :2]
            instant_movement = float(np.linalg.norm(deltas, axis=1).mean())

        self._prev_landmarks = current
        alpha = self.config.smoothing_alpha
        self._smoothed_movement = (alpha * instant_movement) + ((1.0 - alpha) * self._smoothed_movement)
        self._history.append(self._smoothed_movement)

        if self._smoothed_movement <= self.config.stable_threshold:
            self._stable_frames += 1
        else:
            self._stable_frames = 0

        state = self._classify_state()
        snapshot = MovementSnapshot(
            state=state,
            movement=self._smoothed_movement,
            average_movement=self.average_movement(),
            stable_frames=self._stable_frames,
            has_hand=True,
        )
        self._last_state = snapshot.state
        return snapshot

    def reset(self) -> None:
        self._history.clear()
        self._prev_landmarks = None
        self._smoothed_movement = 0.0
        self._stable_frames = 0
        self._last_state = "no_hand"

    def average_movement(self, window: int = 10) -> float:
        if not self._history:
            return 0.0
        values = list(self._history)[-window:]
        return float(sum(values) / len(values))

    def get_current_movement(self) -> float:
        return float(self._smoothed_movement)

    def _classify_state(self) -> str:
        movement = self._smoothed_movement
        cfg = self.config

        if movement >= cfg.fast_threshold:
            return "moving_fast"

        if movement <= cfg.idle_threshold and self._stable_frames >= cfg.idle_required_frames:
            return "idle"

        if movement <= cfg.stable_threshold and self._stable_frames >= cfg.stable_required_frames:
            return "stable"

        return "moving"


# ---------------------------------------------------------------------------
# Legacy compatibility API
# ---------------------------------------------------------------------------

def classify_hand_state(
    landmarks: Optional[List[Landmark]],
    tracker: MovementTracker,
) -> str:
    # Older code paths call `update()` before this function. We only perform an
    # update when no history exists yet.
    if landmarks is not None and not tracker._history:
        tracker.update(landmarks)
    return tracker._last_state


def is_hand_idle(
    landmarks: Optional[List[Landmark]],
    tracker: MovementTracker,
) -> bool:
    state = classify_hand_state(landmarks, tracker)
    return state == "idle"


def is_hand_stable(
    landmarks: Optional[List[Landmark]],
    tracker: MovementTracker,
) -> bool:
    state = classify_hand_state(landmarks, tracker)
    return state in {"stable", "idle"}
