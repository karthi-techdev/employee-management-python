from fastapi import HTTPException
from sqlalchemy.orm import Session
from repository.leaves import LeaveRepository
from repository.employees import EmployeeRepository
from repository.audits import AuditRepository
from services.auth_service import AuthService

leave_repository = LeaveRepository()
employee_repository = EmployeeRepository()
audit_repository = AuditRepository()
auth_service = AuthService()

class LeaveService:
    def __init__(self):
        pass

    def check_leave_balance(self, employee_id: int, db: Session):
        # 1. Check if employee exists
        employee = employee_repository.get_by_id(employee_id, db)
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        # 2. Return leave balances
        balances = leave_repository.get_balances(employee_id, db)
        return [
            {
                "leave_type": b.leave_type,
                "balance": b.balance,
                "as_of_date": b.as_of_date
            }
            for b in balances
        ]

    def submit_leave_request(self, employee_id: int, start_date, end_date, leave_type: str, db: Session):
        # 1. Check if employee exists
        employee = employee_repository.get_by_id(employee_id, db)
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        # 2. Check if dates are valid
        if str(end_date) < str(start_date):
            raise HTTPException(status_code=400, detail="End date cannot be before start date")

        # 3. Check leave balance
        balances = leave_repository.get_balances(employee_id, db)
        leave_balance = None
        for item in balances:
            if item.leave_type.lower() == leave_type.lower():
                leave_balance = item.balance
                break

        if leave_balance is None:
            raise HTTPException(status_code=400, detail="Invalid leave type")

        if leave_balance <= 0:
            raise HTTPException(status_code=400, detail="Insufficient leave balance")

        # 4. Create the leave request
        request_id = leave_repository.create_request(employee_id, start_date, end_date, leave_type, db)

        # 5. Log audit event
        audit_repository.log_event(
            actor_id=employee_id,
            action="SUBMIT_LEAVE",
            result=f"Leave request #{request_id} submitted for {leave_type}",
            trace_id="leave",
            db=db
        )

        return {
            "message": "Leave request submitted successfully",
            "request_id": request_id,
            "status": "pending"
        }

    def get_leave_request_status(self, request_id: int, db: Session):
        request = leave_repository.get_request_by_id(request_id, db)
        if not request:
            raise HTTPException(status_code=404, detail="Leave request not found")
        return {
            "request_id": request.request_id,
            "employee_id": request.employee_id,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "leave_type": request.leave_type,
            "status": request.status,
            "approver_id": request.approver_id,
            "created_at": request.created_at
        }

    def get_all_requests(self, db: Session):
        requests = leave_repository.get_all_requests(db)
        emp_map = {e.employee_id: e.name for e in employee_repository.get_all(db)}
        return [
            {
                "request_id": r.request_id,
                "employee_id": r.employee_id,
                "employee_name": emp_map.get(r.employee_id, f"Employee #{r.employee_id}"),
                "start_date": str(r.start_date),
                "end_date": str(r.end_date),
                "leave_type": r.leave_type,
                "status": r.status,
                "approver_id": r.approver_id,
                "created_at": str(r.created_at) if r.created_at else None
            }
            for r in requests
        ]

    def review_leave_request(self, request_id: int, status: str, approver_id: int, db: Session):
        clean_status = status.lower()
        if clean_status not in ["approved", "rejected"]:
            raise HTTPException(status_code=400, detail="Status must be either 'approved' or 'rejected'")

        # Check if approver exists
        approver = employee_repository.get_by_id(approver_id, db)
        if not approver:
            raise HTTPException(status_code=404, detail="Approver employee not found")

        # RBAC: Check if approver is manager or HR
        if not auth_service.check_is_manager_or_hr(approver_id, db):
            raise HTTPException(
                status_code=403,
                detail="Access denied: Only Managers or HR staff can approve or reject leave requests"
            )

        # Check if leave request exists
        request = leave_repository.get_request_by_id(request_id, db)
        if not request:
            raise HTTPException(status_code=404, detail="Leave request not found")

        # Employee cannot approve their own leave request
        if request.employee_id == approver_id:
            raise HTTPException(status_code=400, detail="Employees cannot approve their own leave request")

        if request.status != "pending":
            raise HTTPException(status_code=400, detail=f"Leave request is already {request.status}")

        # Update status
        leave_repository.update_status(request_id, clean_status, approver_id, db)

        # Log audit event
        audit_repository.log_event(
            actor_id=approver_id,
            action="REVIEW_LEAVE",
            result=f"Request #{request_id} was {clean_status} by Approver #{approver_id}",
            trace_id="leave",
            db=db
        )

        return {
            "message": f"Leave request {clean_status} successfully",
            "request_id": request_id,
            "status": clean_status,
            "approver_id": approver_id
        }
