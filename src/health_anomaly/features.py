from __future__ import annotations

import numpy as np

from .schemas import Telemetry

FEATURE_NAMES = (
    "latency_ms",
    "error_rate",
    "cpu_percent",
    "requests_per_minute",
)


def to_matrix(observations: list[Telemetry]) -> np.ndarray:
    if not observations:
        raise ValueError("At least one telemetry observation is required.")

    return np.asarray(
        [
            [
                item.latency_ms,
                item.error_rate,
                item.cpu_percent,
                item.requests_per_minute,
            ]
            for item in observations
        ],
        dtype=float,
    )
