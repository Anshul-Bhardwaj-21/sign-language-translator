from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes.health import router as health_router
from backend.api.routes.predict import router as predict_router
from backend.api.routes.rooms import router as rooms_router
from backend.core.config import settings
from backend.core.errors import register_exception_handlers
from backend.core.logging import configure_logging
from backend.realtime.manager import RealtimeManager
from backend.realtime.websocket import router as websocket_router
from backend.services.model_service import ModelService
from backend.services.room_service import RoomService


def create_application() -> FastAPI:
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Production-minded backend for realtime sign-language communication rooms.",
    )

    app.state.started_at = datetime.now(timezone.utc)
    app.state.room_service = RoomService(
        default_capacity=settings.default_room_capacity,
        max_capacity=settings.max_room_capacity,
    )
    app.state.model_service = ModelService(settings)
    app.state.realtime_manager = RealtimeManager()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    register_exception_handlers(app)
    app.include_router(health_router, tags=["health"])
    app.include_router(rooms_router, prefix="/rooms", tags=["rooms"])
    app.include_router(predict_router, tags=["predict"])
    app.include_router(websocket_router, tags=["realtime"])

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        app.state.model_service.shutdown()

    return app

