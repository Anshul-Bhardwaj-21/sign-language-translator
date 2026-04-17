from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import numpy as np

from backend.ml.hand_detection import HandDetectionResult


@dataclass
class QualityCheckResult:
    passed: bool
    rejection_reason: str
    laplacian_variance: float
    mean_luminance: float
    detection_confidence: float


class FrameQualityGate:
    def __init__(
        self,
        blur_threshold: float,
        luminance_threshold: float,
        detection_confidence_threshold: float,
    ) -> None:
        self._blur_threshold = blur_threshold
        self._luminance_threshold = luminance_threshold
        self._detection_confidence_threshold = detection_confidence_threshold

    def check(self, frame_rgb: np.ndarray, hand_result: HandDetectionResult) -> QualityCheckResult:
        blur_score = self._blur_metric(frame_rgb)
        luminance = self._luminance_metric(frame_rgb, hand_result)
        confidence = hand_result.confidence if hand_result.hand_detected else 0.0

        passed = True
        reason = ""

        if blur_score < self._blur_threshold:
            passed = False
            reason = "blur"
        elif luminance < self._luminance_threshold:
            passed = False
            reason = "darkness"
        elif hand_result.hand_detected and confidence < self._detection_confidence_threshold:
            passed = False
            reason = "low_confidence"

        return QualityCheckResult(
            passed=passed,
            rejection_reason=reason,
            laplacian_variance=blur_score,
            mean_luminance=luminance,
            detection_confidence=confidence,
        )

    @staticmethod
    def _blur_metric(frame_rgb: np.ndarray) -> float:
        gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())

    @staticmethod
    def _luminance_metric(frame_rgb: np.ndarray, hand_result: HandDetectionResult) -> float:
        ycrcb = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2YCrCb)
        y_channel = ycrcb[:, :, 0]
        bbox = _hand_bounding_box(frame_rgb, hand_result)
        if bbox is not None:
            x1, y1, x2, y2 = bbox
            region = y_channel[y1:y2, x1:x2]
            if region.size > 0:
                return float(np.mean(region))
        return float(np.mean(y_channel))


def _hand_bounding_box(
    frame_rgb: np.ndarray,
    hand_result: HandDetectionResult,
) -> Optional[Tuple[int, int, int, int]]:
    landmarks = hand_result.primary_landmarks
    if not landmarks:
        return None

    height, width = frame_rgb.shape[:2]
    xs = [landmark[0] * width for landmark in landmarks]
    ys = [landmark[1] * height for landmark in landmarks]

    x1 = max(0, int(min(xs)))
    y1 = max(0, int(min(ys)))
    x2 = min(width, int(max(xs)) + 1)
    y2 = min(height, int(max(ys)) + 1)

    if x1 >= x2 or y1 >= y2:
        return None

    return x1, y1, x2, y2

