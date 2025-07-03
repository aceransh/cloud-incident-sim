from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime, timezone

Base = declarative_base()

class IncidentRun(Base):
    __tablename__ = "incident_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_name = Column(String, nullable=False)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="Pending")
    logs = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)
    report_s3 = Column(String, nullable=True)