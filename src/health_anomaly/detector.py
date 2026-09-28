from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .config import settings
from .features import to_matrix
from .schemas import AnomalyResult, Telemetry

logger = logging.getLogger(__name__)


@dataclass
class ModelState:
    model: Pipeline | None = None
    samples: int = 0


class AnomalyDetector:
    def __init__(self) -> None:
        self._state = ModelState()

    @property
    def ready(self) -> bool:
        return self._state.model is not None

    @property
    def samples(self) -> int:
        return self._state.samples

    def train(self, observations: list[Telemetry]) -> int:
        matrix = to_matrix(observations)

        if matrix.shape[0] < 5:
            raise ValueError("At least five observations are required for training.")

        pipeline = Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "detector",
                    IsolationForest(
                        contamination=settings.contamination,
                        random_state=settings.random_state,
                    ),
                ),
            ]
        )

        pipeline.fit(matrix)
        self._state = ModelState(model=pipeline, samples=len(observations))
        logger.info("Anomaly model trained with %d observations", len(observations))
        return len(observations)

    def score(self, observations: list[Telemetry]) -> list[AnomalyResult]:
        if not self.ready:
            raise RuntimeError("Model has not been trained.")

        matrix = to_matrix(observations)
        model = self._state.model
        assert model is not None

        predictions = model.predict(matrix)
        scores = model.decision_function(matrix)

        return [
            AnomalyResult(
                anomaly=int(prediction) == -1,
                score=float(score),
            )
            for prediction, score in zip(predictions, scores, strict=True)
        ]
