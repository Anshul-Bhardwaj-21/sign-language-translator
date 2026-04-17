from __future__ import annotations

from fastapi import APIRouter, Request

from backend.schemas.predict import PredictionRequest, PredictionResponse

router = APIRouter()


@router.post("/predict", response_model=PredictionResponse)
async def predict(request_body: PredictionRequest, request: Request) -> PredictionResponse:
    model_service = request.app.state.model_service
    result = model_service.predict(request_body)
    return PredictionResponse(data=result.data)

