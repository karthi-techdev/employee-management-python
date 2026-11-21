from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AuditResponse(BaseModel):
    event_id: int
    actor_id: Optional[int] = None
    action: str
    event_timestamp: Optional[datetime] = None
    result: str
    trace_id: Optional[str] = None

    model_config = {"from_attributes": True}
