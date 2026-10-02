import json
import pandas as pd
from app.drift import analyze
from app.models import DriftReport
from app.repository import DriftRepository
from app.config import get_settings
class DriftService:
    def __init__(self, session): self.repo=DriftRepository(session); self.settings=get_settings()
    def run(self, reference_rows, current_rows):
        ref, cur = pd.DataFrame(reference_rows), pd.DataFrame(current_rows)
        results=analyze(ref,cur,self.settings.numeric_threshold,self.settings.categorical_threshold,self.settings.bins)
        payload=[r.__dict__ for r in results]
        report=self.repo.create(DriftReport(reference_rows=len(ref),current_rows=len(cur),drifted_features=sum(r["drifted"] for r in payload),total_features=len(payload),summary_json=json.dumps(payload)))
        return report,payload
    def get(self, report_id): return self.repo.get(report_id)
