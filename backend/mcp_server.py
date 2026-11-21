from fastmcp import FastMCP
from sqlalchemy import func
from core.config import local_session
from models.employees import Employee
from services.rag_service import search_hr_policies as rag_search
from repository.employees import EmployeeRepository
from repository.leaves import LeaveRepository
from repository.audits import AuditRepository
from services.auth_service import AuthService

employee_repository = EmployeeRepository()
leave_repository = LeaveRepository()
audit_repository = AuditRepository()
auth_service = AuthService()

# Create FastMCP server instance for HR tools
mcp = FastMCP("HR-Assistant-MCP")

def format_dmy(date_val):
    if not date_val:
        return ""
    if hasattr(date_val, "strftime"):
        return date_val.strftime("%d/%m/%Y")
    parts = str(date_val).split("T")[0].split("-")
    if len(parts) == 3 and len(parts[0]) == 4:
        return f"{parts[2]}/{parts[1]}/{parts[0]}"
    return str(date_val)

def resolve_employee(target_str: str, fallback_employee_id: int, db):
    """Resolve an employee from an ID or name string, with fallback to current user."""
    target_clean = str(target_str or "").strip()
    if not target_clean:
        return employee_repository.get_by_id(fallback_employee_id, db)

    if target_clean.isdigit():
        return employee_repository.get_by_id(int(target_clean), db)

    # Clean up name by removing suffixes like '(Employee)', '(Manager)', etc.
    clean_name = target_clean.split("(")[0].strip()
    if not clean_name:
        clean_name = target_clean

    # 1. Exact match on name (case-insensitive)
    emp = db.query(Employee).filter(func.lower(Employee.name) == clean_name.lower()).first()
    if emp:
        return emp

    # 2. Substring match on name (case-insensitive)
    emp = db.query(Employee).filter(Employee.name.ilike(f"%{clean_name}%")).first()
    if emp:
        return emp

    # 3. Match on email
    emp = db.query(Employee).filter(Employee.email.ilike(f"%{clean_name}%")).first()
    return emp

@mcp.tool()
def search_hr_policies(query: str):
    """Search approved company HR policy documents and guides (leave, attendance, code of conduct, onboarding, holidays) in Pinecone with citations."""
    return rag_search(query, top_k=3)

@mcp.tool()
def get_my_employee_profile(employee_id: int, target_employee: str = ""):
    """Retrieve profile information (name, department, role, status).
    If target_employee is specified, the requester must be a Manager, HR Staff, or Admin to view another employee's profile."""
    db = local_session()
    try:
        target_emp = resolve_employee(target_employee, employee_id, db)
        if not target_emp:
            return {"error": f"Employee '{target_employee}' not found in company records."}

        is_self = (target_emp.employee_id == employee_id)
        is_manager = auth_service.check_is_manager_or_hr(employee_id, db)

        if not is_self and not is_manager:
            return {
                "error": "Access restricted: Only Managers, HR Staff, and Admins can view other employees' profiles."
            }

        return {
            "employee_id": target_emp.employee_id,
            "name": target_emp.name,
            "email": target_emp.email,
            "department": target_emp.department,
            "role": target_emp.role,
            "status": target_emp.status,
            "is_self": is_self
        }
    finally:
        db.close()

@mcp.tool()
def get_leave_balance(employee_id: int, target_employee: str = ""):
    """Retrieve the current leave balance (Casual, Sick).
    If target_employee is specified, the requester must be an authorized Manager, HR Staff, or Admin to view another employee's leave balance."""
    db = local_session()
    try:
        target_emp = resolve_employee(target_employee, employee_id, db)
        if not target_emp:
            return {"error": f"Employee '{target_employee}' not found in company records."}

        is_self = (target_emp.employee_id == employee_id)
        is_manager = auth_service.check_is_manager_or_hr(employee_id, db)

        if not is_self and not is_manager:
            return {
                "error": "Access restricted: Only Managers, HR Staff, and Admins are authorized to view other employees' leave balances. Regular employees can only view their own records."
            }

        balances = leave_repository.get_balances(target_emp.employee_id, db)
        return {
            "employee_id": target_emp.employee_id,
            "employee_name": target_emp.name,
            "department": target_emp.department,
            "role": target_emp.role,
            "is_self": is_self,
            "balances": [
                {
                    "leave_type": b.leave_type,
                    "balance": b.balance,
                    "as_of_date": format_dmy(b.as_of_date) if b.as_of_date else None
                }
                for b in balances
            ]
        }
    finally:
        db.close()

@mcp.tool()
def get_leave_request_status(request_id: int, employee_id: int):
    """Check the status of a leave request with privacy verification."""
    db = local_session()
    try:
        req = leave_repository.get_request_by_id(request_id, db)
        if not req:
            return {"error": f"Leave request #{request_id} not found."}

        # Privacy check: Only owner or Manager/HR can view
        is_owner = (req.employee_id == employee_id)
        is_manager = auth_service.check_is_manager_or_hr(employee_id, db)
        if not is_owner and not is_manager:
            return {"error": "Access restricted: You can only view your own leave requests."}

        return {
            "request_id": req.request_id,
            "employee_id": req.employee_id,
            "start_date": str(req.start_date),
            "end_date": str(req.end_date),
            "leave_type": req.leave_type,
            "status": req.status,
            "approver_id": req.approver_id,
            "created_at": str(req.created_at) if req.created_at else None
        }
    finally:
        db.close()

@mcp.tool()
def create_leave_request(employee_id: int, start_date: str, end_date: str, leave_type: str):
    """Create a new leave request in 'pending' status for manager approval. AI never approves leaves."""
    db = local_session()
    try:
        emp = employee_repository.get_by_id(employee_id, db)
        if not emp:
            return {"error": f"Employee with ID {employee_id} not found."}

        if str(end_date) < str(start_date):
            return {"error": "End date cannot be before start date."}

        balances = leave_repository.get_balances(employee_id, db)
        matching_balance = None
        for item in balances:
            if item.leave_type.lower() == leave_type.lower():
                matching_balance = item.balance
                break

        if matching_balance is None:
            return {"error": f"Invalid leave type '{leave_type}'. Available types: Casual, Sick."}

        if matching_balance <= 0:
            return {"error": f"Insufficient leave balance for {leave_type}. Current balance is {matching_balance}."}

        req_id = leave_repository.create_request(employee_id, start_date, end_date, leave_type, db)

        audit_repository.log_event(
            actor_id=employee_id,
            action="CREATE_LEAVE_REQUEST",
            result=f"Created request #{req_id} ({leave_type}: {start_date} to {end_date})",
            trace_id="mcp",
            db=db
        )

        return {
            "success": True,
            "message": "Leave request submitted successfully. It is pending manager approval.",
            "request_id": req_id,
            "status": "pending",
            "employee_id": employee_id,
            "leave_type": leave_type,
            "start_date": str(start_date),
            "end_date": str(end_date)
        }
    finally:
        db.close()

@mcp.tool()
def get_pending_leave_requests(approver_employee_id: int):
    """Retrieve all pending employee leave requests requiring manager or HR approval. Only accessible by Managers or HR Staff."""
    db = local_session()
    try:
        is_approver = auth_service.check_is_manager_or_hr(approver_employee_id, db)
        if not is_approver:
            return {
                "error": "Access restricted: Only Managers and HR staff have permission to view pending employee leave approvals."
            }

        all_reqs = leave_repository.get_all_requests(db)
        pending = [r for r in all_reqs if r.status == "pending"]

        results = []
        for p in pending:
            emp = employee_repository.get_by_id(p.employee_id, db)
            results.append({
                "request_id": p.request_id,
                "employee_id": p.employee_id,
                "employee_name": emp.name if emp else f"Employee #{p.employee_id}",
                "department": emp.department if emp else "General",
                "leave_type": p.leave_type,
                "start_date": format_dmy(p.start_date),
                "end_date": format_dmy(p.end_date),
                "status": p.status,
                "created_at": format_dmy(p.created_at)
            })

        return {
            "pending_count": len(results),
            "pending_requests": results
        }
    finally:
        db.close()

if __name__ == "__main__":
    mcp.run()
