from pydantic import BaseModel, Field
from typing import Any
class ObservationSet(BaseModel):
    columns: list[str] = Field(min_length=1)
    rows: list[dict[str, Any]] = Field(min_length=1)
class DriftRequest(BaseModel):
    reference: ObservationSet
    current: ObservationSet
class FeatureDrift(BaseModel):
    feature: str; kind: str; metric: float; threshold: float; drifted: bool
class DriftResponse(BaseModel):
    report_id: int; reference_rows: int; current_rows: int; drifted_features: int; total_features: int; features: list[FeatureDrift]
