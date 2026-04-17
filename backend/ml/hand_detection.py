from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import numpy as np

try:
    import cv2
    import mediapipe as mp
except Exception:  # pragma: no cover
    cv2 = None  # type: ignore[assignment]
    mp = None  # type: ignore[assignment]


Landmark = Tuple[float, float, float]


@dataclass
class HandDetectionResult:
    hand_detected: bool = False
    primary_landmarks: Optional[List[Landmark]] = None
    all_landmarks: List[List[Landmark]] = field(default_factory=list)
    handedness: Optional[str] = None
    confidence: float = 0.0
    error_message: str = ""


class HandDetector:
    def __init__(
        self,
        max_num_hands: int = 1,
        min_detection_confidence: float = 0.6,
        min_tracking_confidence: float = 0.5,
        task_model_path: Path | None = None,
    ) -> None:
        if mp is None:
            raise RuntimeError("MediaPipe is not available in this environment.")

        solutions = getattr(mp, "solutions", None)
        self._mode = "solutions"
        self._mp_hands = None
        self._hands = None
        self._landmarker = None

        if solutions is not None and hasattr(solutions, "hands"):
            self._mp_hands = solutions.hands
            self._hands = self._mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=max_num_hands,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
            )
            return

        tasks = getattr(mp, "tasks", None)
        if tasks is None or not hasattr(tasks, "vision"):
            raise RuntimeError("MediaPipe Hands solution is unavailable.")

        model_path = task_model_path or (
            Path(__file__).resolve().parents[1] / "resources" / "mediapipe" / "hand_landmarker.task"
        )
        if not model_path.exists():
            raise RuntimeError(f"MediaPipe hand landmarker model missing at {model_path}.")

        vision = tasks.vision
        self._mode = "tasks"
        options = vision.HandLandmarkerOptions(
            base_options=tasks.BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.IMAGE,
            num_hands=max_num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)

    def detect(self, frame_rgb: np.ndarray) -> HandDetectionResult:
        result = HandDetectionResult()
        if frame_rgb is None or frame_rgb.size == 0:
            result.error_message = "Invalid frame."
            return result

        if self._mode == "solutions":
            inference = self._hands.process(frame_rgb)
            if not inference.multi_hand_landmarks:
                return result
            handedness_items: Sequence = inference.multi_handedness or []
            all_landmarks = [self._extract_landmarks(hand) for hand in inference.multi_hand_landmarks]
        else:
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            inference = self._landmarker.detect(mp_image)
            if not inference.hand_landmarks:
                return result
            handedness_items = inference.handedness or []
            all_landmarks = [self._extract_landmarks(hand) for hand in inference.hand_landmarks]

        best_idx = 0
        best_label: str | None = None
        best_score = 0.0

        for index in range(len(all_landmarks)):
            label, score = self._extract_handedness(handedness_items, index)
            if score >= best_score:
                best_idx = index
                best_score = score
                best_label = label

        result.hand_detected = True
        result.all_landmarks = all_landmarks
        result.primary_landmarks = all_landmarks[best_idx]
        result.handedness = best_label
        result.confidence = best_score
        return result

    def close(self) -> None:
        try:
            if self._hands is not None:
                self._hands.close()
            if self._landmarker is not None:
                self._landmarker.close()
        except Exception:
            pass

    @staticmethod
    def _extract_landmarks(hand_landmarks: object) -> List[Landmark]:
        points: List[Landmark] = []
        source = getattr(hand_landmarks, "landmark", hand_landmarks)
        for point in source:
            points.append((float(point.x), float(point.y), float(point.z)))
        return points

    @staticmethod
    def _extract_handedness(items: Sequence, index: int) -> Tuple[str | None, float]:
        try:
            item = items[index]
            if hasattr(item, "classification"):
                classification = item.classification[0]
                return str(classification.label), float(classification.score)
            classification = item[0]
            label = getattr(classification, "category_name", None) or getattr(classification, "display_name", None)
            score = getattr(classification, "score", 0.0)
            return str(label), float(score)
        except Exception:
            return None, 0.0


def decode_frame(image_base64: str) -> np.ndarray:
    if cv2 is None:
        raise RuntimeError("OpenCV is not available in this environment.")

    import base64

    if "," in image_base64:
        image_base64 = image_base64.split(",", 1)[1]

    image_bytes = base64.b64decode(image_base64)
    frame_array = np.frombuffer(image_bytes, dtype=np.uint8)
    frame_bgr = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
    if frame_bgr is None:
        raise ValueError("Unable to decode image payload.")
    return cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
