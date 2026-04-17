from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from backend.ml.hand_detection import HandDetectionResult


@dataclass
class EnginePrediction:
    label: str = "idle"
    confidence: float = 0.0
    stable: bool = False
    engine: str = "unknown"
    diagnostics: dict[str, Any] = field(default_factory=dict)


class BaseModelEngine(ABC):
    name: str = "base"

    @abstractmethod
    def is_ready(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def predict(self, frame_rgb: np.ndarray, hand_result: HandDetectionResult) -> EnginePrediction:
        raise NotImplementedError

