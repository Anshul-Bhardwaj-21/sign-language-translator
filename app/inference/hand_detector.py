"""MediaPipe hand detection wrapper with robust error handling."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

import cv2
import numpy as np

try:
    import mediapipe as mp
except Exception:  # pragma: no cover - handled explicitly at runtime.
    mp = None  # type: ignore[assignment]


Landmark = Tuple[float, float, float]


@dataclass
class HandDetectionResult:
    """Single frame hand detection output."""

    hand_detected: bool = False
    primary_landmarks: Optional[List[Landmark]] = None
    all_landmarks: List[List[Landmark]] = field(default_factory=list)
    handedness: Optional[str] = None
    confidence: float = 0.0
    frame_with_landmarks: Optional[np.ndarray] = None
    error_message: str = ""


class HandDetector:
    """Manages MediaPipe Hands lifecycle and frame inference."""

    def __init__(
        self,
        max_num_hands: int = 1,
        min_detection_confidence: float = 0.6,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        if mp is None:
            raise RuntimeError(
                "MediaPipe is not installed. Install dependencies from requirements.txt."
            )

        solutions = getattr(mp, "solutions", None)
        if solutions is None or not hasattr(solutions, "hands"):
            raise RuntimeError(
                "MediaPipe install is missing Hands solutions API. "
                "Reinstall with `pip install mediapipe>=0.10.8,<0.11`."
            )

        self._mp_hands = solutions.hands
        self._mp_drawing = solutions.drawing_utils
        self._mp_drawing_styles = solutions.drawing_styles
        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

    def detect(self, frame_rgb: np.ndarray, draw_landmarks: bool = True) -> HandDetectionResult:
        """Run MediaPipe hand inference on one RGB frame."""
        result = HandDetectionResult(frame_with_landmarks=frame_rgb)

        if frame_rgb is None or frame_rgb.size == 0:
            result.error_message = "Invalid frame received for hand detection."
            return result

        try:
            inference = self._hands.process(frame_rgb)
        except Exception as exc:
            result.error_message = f"MediaPipe processing failed: {exc}"
            return result

        if not inference.multi_hand_landmarks:
            return result

        handedness_items: Sequence = inference.multi_handedness or []
        result.all_landmarks = [self._extract_landmarks(hand) for hand in inference.multi_hand_landmarks]

        best_idx = 0
        best_score = 0.0
        best_label: Optional[str] = None

        for idx in range(len(result.all_landmarks)):
            label, score = self._extract_handedness(handedness_items, idx)
            if score >= best_score:
                best_score = score
                best_label = label
                best_idx = idx

        result.hand_detected = True
        result.primary_landmarks = result.all_landmarks[best_idx]
        result.handedness = best_label
        result.confidence = best_score

        if draw_landmarks:
            annotated = frame_rgb.copy()
            for hand_landmarks in inference.multi_hand_landmarks:
                self._mp_drawing.draw_landmarks(
                    annotated,
                    hand_landmarks,
                    self._mp_hands.HAND_CONNECTIONS,
                    self._mp_drawing_styles.get_default_hand_landmarks_style(),
                    self._mp_drawing_styles.get_default_hand_connections_style(),
                )
            result.frame_with_landmarks = annotated

        return result

    def close(self) -> None:
        try:
            self._hands.close()
        except Exception:
            # MediaPipe can throw if already closed; safe to ignore for cleanup.
            pass

    @staticmethod
    def _extract_landmarks(hand_landmarks: object) -> List[Landmark]:
        points: List[Landmark] = []
        for point in hand_landmarks.landmark:
            # x/y are normalized and can go slightly out of range when partially out of frame.
            x = float(min(max(point.x, -0.2), 1.2))
            y = float(min(max(point.y, -0.2), 1.2))
            z = float(point.z)
            points.append((x, y, z))
        return points

    @staticmethod
    def _extract_handedness(items: Sequence, idx: int) -> Tuple[Optional[str], float]:
        try:
            item = items[idx]
            classification = item.classification[0]
            return str(classification.label), float(classification.score)
        except Exception:
            return None, 0.0


def create_hand_detector(
    static_image_mode: bool = False,
    max_num_hands: int = 1,
    min_detection_confidence: float = 0.6,
    min_tracking_confidence: float = 0.5,
) -> HandDetector:
    """
    Factory used by app runtime and legacy modules.

    `static_image_mode` is accepted for API compatibility and ignored because
    this app targets continuous video streams.
    """
    _ = static_image_mode
    return HandDetector(
        max_num_hands=max_num_hands,
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
    )


# ---------------------------------------------------------------------------
# Legacy compatibility API
# ---------------------------------------------------------------------------

def detect_hand(
    frame_rgb: np.ndarray,
    hands: Optional[HandDetector],
) -> Tuple[bool, Optional[HandDetectionResult]]:
    """
    Backward-compatible wrapper expected by older modules.
    """
    if hands is None:
        return False, None
    result = hands.detect(frame_rgb, draw_landmarks=False)
    return result.hand_detected, result


def extract_landmarks(
    results: Optional[HandDetectionResult],
    frame_width: int = 640,
    frame_height: int = 480,
) -> Tuple[List[List[Landmark]], List[str]]:
    """
    Backward-compatible landmark extraction wrapper.
    """
    _ = frame_width
    _ = frame_height
    if results is None or not results.hand_detected:
        return [], []
    landmarks = results.all_landmarks if results.all_landmarks else []
    handedness = []
    if results.handedness:
        handedness = [results.handedness for _ in landmarks]
    return landmarks, handedness


def draw_landmarks(
    frame_rgb: np.ndarray,
    results: Optional[HandDetectionResult],
) -> np.ndarray:
    """
    Backward-compatible drawing wrapper.
    """
    if frame_rgb is None or results is None:
        return frame_rgb

    if results.frame_with_landmarks is not None:
        return results.frame_with_landmarks

    if not results.primary_landmarks:
        return frame_rgb

    canvas = frame_rgb.copy()
    height, width = canvas.shape[:2]
    for x, y, _ in results.primary_landmarks:
        px = int(min(max(x, 0.0), 1.0) * width)
        py = int(min(max(y, 0.0), 1.0) * height)
        cv2.circle(canvas, (px, py), 3, (0, 255, 0), thickness=-1)
    return canvas


def close_hand_detector(hands: Optional[HandDetector]) -> bool:
    """
    Backward-compatible close wrapper.
    """
    if hands is None:
        return True
    try:
        hands.close()
        return True
    except Exception:
        return False
