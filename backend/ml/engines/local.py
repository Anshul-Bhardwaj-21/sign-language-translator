from __future__ import annotations

from pathlib import Path

import numpy as np

from backend.inference_model import LocalModelBundle
from backend.ml.engines.base import BaseModelEngine, EnginePrediction
from backend.ml.hand_detection import HandDetectionResult


class LocalSignModelEngine(BaseModelEngine):
    name = "local"

    def __init__(self, model_dir: Path) -> None:
        self._bundle = LocalModelBundle.load_if_available(model_dir)

    def is_ready(self) -> bool:
        return self._bundle is not None

    def predict(self, frame_rgb: np.ndarray, hand_result: HandDetectionResult) -> EnginePrediction:
        if self._bundle is None or not hand_result.hand_detected:
            return EnginePrediction(label="idle", confidence=0.0, stable=False, engine=self.name)

        label, confidence = self._bundle.predict(frame_rgb)
        return EnginePrediction(
            label=label,
            confidence=confidence,
            stable=confidence >= 0.72,
            engine=self.name,
            diagnostics={"artifact_dir": str(self._bundle.model_dir)},
        )

