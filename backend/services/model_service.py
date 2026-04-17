from __future__ import annotations

import logging
from dataclasses import dataclass

from backend.core.config import Settings
from backend.ml.engines.base import BaseModelEngine, EnginePrediction
from backend.ml.engines.cloud import CloudAIEngine
from backend.ml.engines.heuristic import HeuristicSignModelEngine
from backend.ml.engines.local import LocalSignModelEngine
from backend.ml.hand_detection import HandDetectionResult, HandDetector, decode_frame
from backend.ml.quality import FrameQualityGate
from backend.schemas.predict import OverlayBounds, OverlayPoint, PredictionData, PredictionOverlay, PredictionQuality, PredictionRequest
from backend.services.caption_service import CaptionService

logger = logging.getLogger(__name__)


@dataclass
class ModelServiceResult:
    data: PredictionData


class ModelService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._caption_service = CaptionService()
        self._heuristic_engine = HeuristicSignModelEngine()
        self._local_engine = LocalSignModelEngine(settings.local_model_dir)
        self._cloud_engine = CloudAIEngine(settings.cloud_provider, settings.cloud_api_key)

        # If USE_FALLBACK_SIGN_MODEL=1, always use heuristic regardless of MODEL_ENGINE
        if settings.use_fallback_sign_model:
            logger.info("USE_FALLBACK_SIGN_MODEL=1 — using heuristic fallback engine.")
            self._preferred_engine = self._heuristic_engine
        else:
            self._preferred_engine = self._resolve_engine(settings.model_engine)

        self._hand_detector = self._create_hand_detector()

    def predict(self, request: PredictionRequest) -> ModelServiceResult:
        frame_rgb = decode_frame(request.image_base64)
        hand_result = self._detect_hand(frame_rgb)
        quality_gate = FrameQualityGate(
            blur_threshold=self._settings.frame_blur_threshold,
            luminance_threshold=self._settings.frame_luminance_threshold,
            detection_confidence_threshold=self._settings.hand_confidence_threshold,
        )
        quality = quality_gate.check(frame_rgb, hand_result)

        prediction = self._predict_with_fallback(frame_rgb, hand_result)
        session_key = f"{request.room_id or 'solo'}:{request.participant_id or 'anonymous'}"
        caption = self._caption_service.update(
            session_key=session_key,
            label=prediction.label,
            confidence=prediction.confidence,
            stable=prediction.stable and quality.passed,
        )

        result = PredictionData(
            label=prediction.label,
            confidence=round(prediction.confidence, 4),
            engine=prediction.engine,
            engine_ready=self.engine_ready(),
            fallback_used=prediction.engine != self._preferred_engine.name,
            hand_detected=hand_result.hand_detected,
            handedness=hand_result.handedness,
            live_caption=caption.live_caption,
            confirmed_caption=caption.confirmed_caption,
            caption_history=caption.history,
            quality=PredictionQuality(
                passed=quality.passed,
                reason=quality.rejection_reason,
                blur_score=round(quality.laplacian_variance, 4),
                luminance=round(quality.mean_luminance, 4),
                detection_confidence=round(quality.detection_confidence, 4),
            ),
            overlay=self._build_overlay(hand_result),
            diagnostics={
                **prediction.diagnostics,
                "hand_error": hand_result.error_message or None,
            },
        )
        return ModelServiceResult(data=result)

    def primary_engine_name(self) -> str:
        return self._preferred_engine.name

    def engine_ready(self) -> bool:
        return self._preferred_engine.is_ready() or self._heuristic_engine.is_ready()

    def shutdown(self) -> None:
        if self._hand_detector is not None:
            self._hand_detector.close()

    def _predict_with_fallback(
        self,
        frame_rgb,
        hand_result: HandDetectionResult,
    ) -> EnginePrediction:
        if self._preferred_engine.is_ready():
            prediction = self._preferred_engine.predict(frame_rgb, hand_result)
            if prediction.confidence > 0 or prediction.label != "idle":
                return prediction

        return self._heuristic_engine.predict(frame_rgb, hand_result)

    def _resolve_engine(self, requested_engine: str) -> BaseModelEngine:
        engine_map: dict[str, BaseModelEngine] = {
            "local": self._local_engine,
            "cloud": self._cloud_engine,
            "heuristic": self._heuristic_engine,
        }
        return engine_map.get(requested_engine.lower(), self._heuristic_engine)

    def _create_hand_detector(self) -> HandDetector | None:
        if not self._settings.enable_mediapipe:
            logger.warning("MediaPipe is disabled by configuration.")
            return None
        try:
            return HandDetector(task_model_path=self._settings.mediapipe_task_path)
        except Exception as exc:
            logger.warning("MediaPipe hand detector unavailable: %s", exc)
            return None

    def _detect_hand(self, frame_rgb) -> HandDetectionResult:
        if self._hand_detector is None:
            return HandDetectionResult(error_message="MediaPipe detector not available.")
        return self._hand_detector.detect(frame_rgb)

    @staticmethod
    def _build_overlay(hand_result: HandDetectionResult) -> PredictionOverlay | None:
        landmarks = hand_result.primary_landmarks or []
        if not landmarks:
            return PredictionOverlay()

        x_values = [point[0] for point in landmarks]
        y_values = [point[1] for point in landmarks]

        return PredictionOverlay(
            hand_landmarks=[OverlayPoint(x=x, y=y, z=z) for x, y, z in landmarks],
            hand_bounds=OverlayBounds(
                x_min=min(x_values),
                y_min=min(y_values),
                x_max=max(x_values),
                y_max=max(y_values),
            ),
        )
