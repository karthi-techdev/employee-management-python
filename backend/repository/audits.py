from models.audits import AuditEvent
from sqlalchemy.orm import Session
from core.config import Base, engine

Base.metadata.create_all(bind=engine)

class AuditRepository:
    def __init__(self):
        pass

    def log_event(self, actor_id: int, action: str, result: str, trace_id: str, db: Session):
        event = AuditEvent(
            actor_id=actor_id,
            action=action,
            result=result,
            trace_id=trace_id
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    def get_recent(self, limit: int, db: Session):
        return db.query(AuditEvent).order_by(AuditEvent.event_id.desc()).limit(limit).all()

