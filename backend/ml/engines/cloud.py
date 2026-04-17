from __future__ import annotations

import numpy as np

from backend.ml.engines.base import BaseModelEngine, EnginePrediction
from backend.ml.hand_detection import HandDetectionResult


class CloudAIEngine(BaseModelEngine):
    name = "cloud"

    def __init__(self, provider: str, api_key: str | None) -> None:
        self._provider = provider
        self._api_key = api_key

    def is_ready(self) -> bool:
        return bool(self._provider and self._provider != "disabled" and self._api_key)

    def predict(self, frame_rgb: np.ndarray, hand_result: HandDetectionResult) -> EnginePrediction:
        _ = frame_rgb
        _ = hand_result
        return EnginePrediction(
            label="idle",
            confidence=0.0,
            stable=False,
            engine=self.name,
            diagnostics={
                "provider": self._provider,
                "reason": "Cloud engine is scaffolded but disabled by default.",
            },
        )

