from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class PredictionRequest(BaseModel):
    image_base64: str = Field(..., description="Raw base64 image or data URL.")
    room_id: str | None = None
    participant_id: str | None = None
    frame_id: str | None = None
    timestamp_ms: int | None = None

    @field_validator("image_base64")
    @classmethod
    def validate_frame_size(cls, value: str) -> str:
        if len(value) > 3_000_000:
            raise ValueError("Frame payload is too large.")
        return value


class PredictionQuality(BaseModel):
    passed: bool
    reason: str
    blur_score: float
    luminance: float
    detection_confidence: float


class OverlayPoint(BaseModel):
    x: float
    y: float
    z: float


class OverlayBounds(BaseModel):
    x_min: float
    y_min: float
    x_max: float
    y_max: float


class PredictionOverlay(BaseModel):
    hand_landmarks: list[OverlayPoint] = Field(default_factory=list)
    hand_bounds: OverlayBounds | None = None
    guidance_mode: str = "vision_assist"
    show_face_frame_guide: bool = True


class PredictionData(BaseModel):
    label: str
    confidence: float
    engine: str
    engine_ready: bool
    fallback_used: bool
    hand_detected: bool
    handedness: str | None = None
    live_caption: str = ""
    confirmed_caption: str | None = None
    caption_history: list[str] = Field(default_factory=list)
    quality: PredictionQuality
    overlay: PredictionOverlay | None = None
    diagnostics: dict[str, float | str | bool | None] = Field(default_factory=dict)


class PredictionResponse(BaseModel):
    success: bool = True
    message: str = "Prediction completed."
    data: PredictionData
