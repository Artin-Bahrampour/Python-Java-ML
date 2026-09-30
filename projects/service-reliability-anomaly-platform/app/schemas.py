from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class TelemetryIn(BaseModel):
    service: str = Field(min_length=2, max_length=120)
    timestamp: datetime
    latency_ms: float = Field(ge=0)
    error_rate: float = Field(ge=0, le=1)
    requests_per_minute: float = Field(ge=0)
    cpu_percent: float = Field(ge=0, le=100)
    memory_percent: float = Field(ge=0, le=100)


class TelemetryOut(TelemetryIn):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ScoreOut(BaseModel):
    telemetry_id: int
    score: float
    is_anomaly: bool
    model_version: str


class SummaryOut(BaseModel):
    service: str
    samples: int
    average_latency_ms: float
    average_error_rate: float
    max_cpu_percent: float
    anomalies: int
