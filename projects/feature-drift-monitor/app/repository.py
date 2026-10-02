from sqlalchemy.orm import Session
from app.models import DriftReport
class DriftRepository:
    def __init__(self, session: Session): self.session=session
    def create(self, report):
        self.session.add(report); self.session.commit(); self.session.refresh(report); return report
    def recent(self, limit=50): return list(self.session.query(DriftReport).order_by(DriftReport.id.desc()).limit(limit))
    def get(self, report_id): return self.session.get(DriftReport, report_id)
