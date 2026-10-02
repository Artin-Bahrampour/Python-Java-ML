from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase): pass
class DriftReport(Base):
    __tablename__ = "drift_reports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    reference_rows: Mapped[int] = mapped_column(Integer)
    current_rows: Mapped[int] = mapped_column(Integer)
    drifted_features: Mapped[int] = mapped_column(Integer)
    total_features: Mapped[int] = mapped_column(Integer)
    summary_json: Mapped[str] = mapped_column(Text)
