from sqlalchemy import Integer, Column, String, Date, DateTime
from datetime import datetime
from core.config import Base

class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, index=True)
    leave_type = Column(String)
    balance = Column(Integer, default=0)
    as_of_date = Column(Date, nullable=True)

class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    request_id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, index=True)
    start_date = Column(Date)
    end_date = Column(Date)
    leave_type = Column(String)
    status = Column(String, default="pending")
    approver_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

