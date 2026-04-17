from __future__ import annotations

from collections import deque
from typing import Deque, Tuple

import numpy as np

from backend.ml.engines.base import BaseModelEngine, EnginePrediction
from backend.ml.hand_detection import HandDetectionResult, Landmark


class HeuristicSignModelEngine(BaseModelEngine):
    name = "heuristic"

    def __init__(self) -> None:
        self._history: Deque[str] = deque(maxlen=5)

    def is_ready(self) -> bool:
        return True

    def predict(self, frame_rgb: np.ndarray, hand_result: HandDetectionResult) -> EnginePrediction:
        _ = frame_rgb

        if not hand_result.hand_detected or not hand_result.primary_landmarks:
            self._history.clear()
            return EnginePrediction(label="idle", confidence=0.0, stable=False, engine=self.name)

        landmarks = hand_result.primary_landmarks
        extended_fingers = _count_extended_fingers(landmarks)
        thumb_index_distance = _distance(landmarks[4], landmarks[8])
        palm_height = abs(landmarks[0][1] - landmarks[12][1])

        label, confidence = self._classify(extended_fingers, thumb_index_distance, palm_height)
        self._history.append(label)
        stable = len(self._history) == self._history.maxlen and len(set(self._history)) == 1

        return EnginePrediction(
            label=label,
            confidence=confidence,
            stable=stable,
            engine=self.name,
            diagnostics={
                "extended_fingers": extended_fingers,
                "thumb_index_distance": round(thumb_index_distance, 4),
                "palm_height": round(palm_height, 4),
            },
        )

    @staticmethod
    def _classify(
        extended_fingers: int,
        thumb_index_distance: float,
        palm_height: float,
    ) -> Tuple[str, float]:
        if extended_fingers == 0:
            return "yes", 0.78
        if extended_fingers == 1:
            return "help", 0.72
        if extended_fingers == 2:
            return ("no", 0.74) if thumb_index_distance < 0.12 else ("peace", 0.81)
        if extended_fingers == 3:
            return "thanks", 0.69
        if extended_fingers == 4:
            return "please", 0.67
        if extended_fingers >= 5:
            return ("hello", 0.86) if palm_height > 0.18 else ("ready", 0.66)
        return "idle", 0.0


def _distance(a: Landmark, b: Landmark) -> float:
    return float(np.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2))


def _count_extended_fingers(landmarks: list[Landmark]) -> int:
    finger_pairs = [(8, 6), (12, 10), (16, 14), (20, 18)]
    extended = 0
    for tip_index, joint_index in finger_pairs:
        if landmarks[tip_index][1] < landmarks[joint_index][1] - 0.03:
            extended += 1
    if landmarks[4][0] > landmarks[3][0] + 0.02 or landmarks[4][0] < landmarks[3][0] - 0.02:
        extended += 1
    return extended

