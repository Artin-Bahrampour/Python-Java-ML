from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models import TelemetryRecord, AnomalyDecision


class TelemetryRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, record: TelemetryRecord) -> TelemetryRecord:
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def recent(self, limit: int = 500):
        return list(
            self.session.scalars(
                select(TelemetryRecord)
                .order_by(TelemetryRecord.timestamp.desc())
                .limit(limit)
            )
        )

    def recent_for_service(self, service: str, hours: int):
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        return list(
            self.session.scalars(
                select(TelemetryRecord)
                .where(
                    TelemetryRecord.service == service,
                    TelemetryRecord.timestamp >= since,
                )
                .order_by(TelemetryRecord.timestamp.desc())
            )
        )

    def add_decision(self, decision: AnomalyDecision) -> AnomalyDecision:
        self.session.add(decision)
        self.session.commit()
        self.session.refresh(decision)
        return decision

    def anomaly_count_for(self, telemetry_ids: list[int]) -> int:
        if not telemetry_ids:
            return 0
        return self.session.scalar(
            select(func.count())
            .select_from(AnomalyDecision)
            .where(
                AnomalyDecision.telemetry_id.in_(telemetry_ids),
                AnomalyDecision.is_anomaly == 1,
            )
        ) or 0
