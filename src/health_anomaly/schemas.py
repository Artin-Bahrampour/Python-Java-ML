from pydantic import BaseModel, Field


class Telemetry(BaseModel):
    latency_ms: float = Field(gt=0)
    error_rate: float = Field(ge=0, le=1)
    cpu_percent: float = Field(ge=0, le=100)
    requests_per_minute: float = Field(ge=0)


class TrainingRequest(BaseModel):
    observations: list[Telemetry] = Field(min_length=5)


class TrainingResponse(BaseModel):
    trained: bool
    samples: int


class ScoreRequest(BaseModel):
    observations: list[Telemetry] = Field(min_length=1)


class AnomalyResult(BaseModel):
    anomaly: bool
    score: float


class ScoreResponse(BaseModel):
    results: list[AnomalyResult]


class HealthResponse(BaseModel):
    status: str
    model_ready: bool
