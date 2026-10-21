from pydantic import BaseModel, Field, field_validator


class Telemetry(BaseModel):
    asset_id: str = Field(min_length=1, max_length=64)
    asset_type: str
    operating_hours: float = Field(ge=0, le=500_000)
    mean_vibration_mm_s: float = Field(ge=0, le=100)
    temperature_c: float = Field(ge=-40, le=250)
    pressure_bar: float = Field(ge=0, le=1000)
    starts_24h: int = Field(ge=0, le=1000)
    lubricant_age_days: int = Field(ge=0, le=3650)

    @field_validator("asset_type")
    @classmethod
    def valid_asset_type(cls, value: str) -> str:
        if value not in {"centrifugal_pump", "positive_displacement_pump"}:
            raise ValueError("asset_type must be centrifugal_pump or positive_displacement_pump")
        return value


class RiskResponse(BaseModel):
    asset_id: str
    failure_risk_14d: float
    intervention_threshold: float
    schedule_inspection: bool
    model_version: str
