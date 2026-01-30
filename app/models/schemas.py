from pydantic import BaseModel
from typing import Optional


class HealthResponse(BaseModel):
    status: str
    uptime: float
    version: Optional[str] = None


class PredictionRequest(BaseModel):
    # placeholder schema; expand with real features later
    features: dict


class PredictionResponse(BaseModel):
    score: float
    label: str
