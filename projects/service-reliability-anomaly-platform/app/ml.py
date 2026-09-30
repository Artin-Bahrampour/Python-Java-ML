from pathlib import Path
from datetime import datetime, timezone
import hashlib
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest


FEATURES = [
    "latency_ms",
    "error_rate",
    "requests_per_minute",
    "cpu_percent",
    "memory_percent",
]


class AnomalyDetector:
    def __init__(self, model_path: str, contamination: float = 0.05):
        self.model_path = Path(model_path)
        self.contamination = contamination
        self.model = None
        self.version = "untrained"

    def _matrix(self, records):
        return np.asarray(
            [[getattr(r, feature) for feature in FEATURES] for r in records],
            dtype=float,
        )

    def train(self, records):
        if len(records) < 20:
            raise ValueError("At least 20 telemetry records are required to train the detector.")
        self.model = IsolationForest(
            n_estimators=200,
            contamination=self.contamination,
            random_state=42,
        )
        self.model.fit(self._matrix(records))
        payload = f"{datetime.now(timezone.utc).isoformat()}-{len(records)}".encode()
        self.version = hashlib.sha256(payload).hexdigest()[:12]
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": self.model, "version": self.version}, self.model_path)
        return self.version

    def load(self):
        if not self.model_path.exists():
            raise FileNotFoundError("No trained model found. Run the train command first.")
        payload = joblib.load(self.model_path)
        self.model = payload["model"]
        self.version = payload["version"]

    def score(self, records):
        if self.model is None:
            self.load()
        matrix = self._matrix(records)
        raw = self.model.decision_function(matrix)
        predictions = self.model.predict(matrix)
        # Higher score means more anomalous for the API consumer.
        anomaly_scores = -raw
        return [
            (float(score), bool(prediction == -1))
            for score, prediction in zip(anomaly_scores, predictions)
        ]
