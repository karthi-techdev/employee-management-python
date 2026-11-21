from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class LeaveRequestCreate(BaseModel):
    employee_id: int
    start_date: str
    end_date: str
    leave_type: str

class LeaveReviewRequest(BaseModel):
    status: str
    approver_id: int

class LeaveBalanceResponse(BaseModel):
    leave_type: str
    balance: int
    as_of_date: Optional[date] = None

    model_config = {"from_attributes": True}

class LeaveRequestResponse(BaseModel):
    request_id: int
    employee_id: int
    start_date: date
    end_date: date
    leave_type: str
    status: str
    approver_id: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
