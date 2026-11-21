from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from schemas.leaves import LeaveRequestCreate, LeaveReviewRequest
from core.db import get_db_connection
from services.leave_service import LeaveService

leave_service = LeaveService()
router = APIRouter(tags=["Leaves"])

@router.get("/employees/{employee_id}/leave-balance")
def get_employee_leave_balance(employee_id: int, db: Session = Depends(get_db_connection)):
    return leave_service.check_leave_balance(employee_id, db)

@router.post("/leave-requests")
def submit_leave(request_data: LeaveRequestCreate, db: Session = Depends(get_db_connection)):
    return leave_service.submit_leave_request(
        employee_id=request_data.employee_id,
        start_date=request_data.start_date,
        end_date=request_data.end_date,
        leave_type=request_data.leave_type,
        db=db
    )

@router.get("/leave-requests")
def list_leave_requests(db: Session = Depends(get_db_connection)):
    return leave_service.get_all_requests(db)

@router.get("/leave-requests/{request_id}")
def get_leave_request(request_id: int, db: Session = Depends(get_db_connection)):
    return leave_service.get_leave_request_status(request_id, db)

@router.put("/leave-requests/{request_id}/review")
def review_leave(request_id: int, review_data: LeaveReviewRequest, db: Session = Depends(get_db_connection)):
    return leave_service.review_leave_request(
        request_id=request_id,
        status=review_data.status,
        approver_id=review_data.approver_id,
        db=db
    )

