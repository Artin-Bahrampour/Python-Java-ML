import logging
from sqlalchemy.orm import Session
from app.models import TelemetryRecord, AnomalyDecision
from app.repository import TelemetryRepository
from app.ml import AnomalyDetector

logger = logging.getLogger(__name__)


class ReliabilityService:
    def __init__(self, session: Session, detector: AnomalyDetector):
        self.repo = TelemetryRepository(session)
        self.detector = detector

    def ingest(self, payload):
        record = TelemetryRecord(**payload.model_dump())
        return self.repo.add(record)

    def train(self, limit=5000):
        records = self.repo.recent(limit)
        records.reverse()
        version = self.detector.train(records)
        logger.info("trained anomaly model version=%s samples=%d", version, len(records))
        return version

    def score_recent(self, limit=100):
        records = self.repo.recent(limit)
        records.reverse()
        scores = self.detector.score(records)
        decisions = []
        for record, (score, is_anomaly) in zip(records, scores):
            decision = AnomalyDecision(
                telemetry_id=record.id,
                score=score,
                is_anomaly=int(is_anomaly),
                model_version=self.detector.version,
            )
            decisions.append(self.repo.add_decision(decision))
        logger.info("scored telemetry samples=%d anomalies=%d",
                    len(decisions), sum(d.is_anomaly for d in decisions))
        return decisions

    def summary(self, service, hours):
        records = self.repo.recent_for_service(service, hours)
        if not records:
            return {
                "service": service,
                "samples": 0,
                "average_latency_ms": 0,
                "average_error_rate": 0,
                "max_cpu_percent": 0,
                "anomalies": 0,
            }
        ids = [r.id for r in records]
        return {
            "service": service,
            "samples": len(records),
            "average_latency_ms": round(sum(r.latency_ms for r in records) / len(records), 2),
            "average_error_rate": round(sum(r.error_rate for r in records) / len(records), 4),
            "max_cpu_percent": max(r.cpu_percent for r in records),
            "anomalies": self.repo.anomaly_count_for(ids),
        }
