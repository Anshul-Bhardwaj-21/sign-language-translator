from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"

load_dotenv(REPO_ROOT / ".env")
load_dotenv(BACKEND_ROOT / ".env")


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _as_csv(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "SignBridge Backend")
    app_version: str = os.getenv("APP_VERSION", "2.0.0")
    environment: str = os.getenv("ENVIRONMENT", "development")
    host: str = os.getenv("HOST", "0.0.0.0" if os.getenv("ENVIRONMENT") == "production" else "127.0.0.1")
    port: int = _as_int(os.getenv("PORT"), 8001)
    reload: bool = _as_bool(os.getenv("RELOAD"), default=False)
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    cors_origins: list[str] = field(
        default_factory=lambda: _as_csv(
            os.getenv("CORS_ORIGINS"),
            [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ],
        )
    )
    model_engine: str = os.getenv("MODEL_ENGINE", "heuristic")
    use_fallback_sign_model: bool = _as_bool(os.getenv("USE_FALLBACK_SIGN_MODEL"), default=False)
    cloud_provider: str = os.getenv("CLOUD_PROVIDER", "disabled")
    cloud_api_key: str | None = os.getenv("CLOUD_API_KEY")
    stun_server: str = os.getenv("STUN_SERVER", "stun:stun.l.google.com:19302")
    turn_url: str | None = os.getenv("TURN_URL") or None
    turn_username: str | None = os.getenv("TURN_USERNAME") or None
    turn_password: str | None = os.getenv("TURN_PASSWORD") or None
    local_model_dir: Path = Path(
        os.getenv(
            "LOCAL_MODEL_DIR",
            str(BACKEND_ROOT / "artifacts" / "models" / "local_sign_model"),
        )
    )
    mediapipe_task_path: Path = Path(
        os.getenv(
            "MEDIAPIPE_TASK_PATH",
            str(BACKEND_ROOT / "resources" / "mediapipe" / "hand_landmarker.task"),
        )
    )
    default_room_capacity: int = _as_int(os.getenv("DEFAULT_ROOM_CAPACITY"), 2)
    max_room_capacity: int = _as_int(os.getenv("MAX_ROOM_CAPACITY"), 6)
    reconnect_grace_seconds: int = _as_int(os.getenv("RECONNECT_GRACE_SECONDS"), 20)
    enable_mediapipe: bool = _as_bool(os.getenv("ENABLE_MEDIAPIPE"), default=True)
    frame_blur_threshold: float = float(os.getenv("FRAME_BLUR_THRESHOLD", "80.0"))
    frame_luminance_threshold: float = float(os.getenv("FRAME_LUMINANCE_THRESHOLD", "32.0"))
    hand_confidence_threshold: float = float(os.getenv("HAND_CONFIDENCE_THRESHOLD", "0.6"))


settings = Settings()
