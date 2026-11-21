from sqlalchemy import Integer, Column, String, DateTime, Text
from datetime import datetime
from core.config import Base

class AuditEvent(Base):
    __tablename__ = "audit_events"

    event_id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, nullable=True)
    action = Column(String)
    event_timestamp = Column(DateTime, default=datetime.utcnow)
    result = Column(Text)
    trace_id = Column(String, nullable=True)
