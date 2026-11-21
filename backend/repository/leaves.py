from models.leaves import LeaveBalance, LeaveRequest
from sqlalchemy.orm import Session
from core.config import Base, engine

Base.metadata.create_all(bind=engine)

class LeaveRepository:
    def __init__(self):
        pass

    def get_balances(self, employee_id: int, db: Session):
        return db.query(LeaveBalance).filter(LeaveBalance.employee_id == employee_id).all()

    def get_balance_by_type(self, employee_id: int, leave_type: str, db: Session):
        return db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.leave_type == leave_type
        ).first()

    def create_request(self, employee_id: int, start_date, end_date, leave_type: str, db: Session):
        new_request = LeaveRequest(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
            leave_type=leave_type,
            status="pending"
        )
        db.add(new_request)
        db.commit()
        db.refresh(new_request)
        return new_request.request_id

    def get_request_by_id(self, request_id: int, db: Session):
        return db.query(LeaveRequest).filter(LeaveRequest.request_id == request_id).first()

    def get_all_requests(self, db: Session):
        return db.query(LeaveRequest).order_by(LeaveRequest.request_id.desc()).all()

    def update_status(self, request_id: int, status: str, approver_id: int, db: Session):
        request = self.get_request_by_id(request_id, db)
        if request:
            request.status = status
            request.approver_id = approver_id
            db.commit()
            db.refresh(request)
            return request
        return None

