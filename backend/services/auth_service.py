from fastapi import HTTPException
from sqlalchemy.orm import Session
from repository.employees import EmployeeRepository
from repository.audits import AuditRepository
from core.security import verify_password, hash_password

employee_repository = EmployeeRepository()
audit_repository = AuditRepository()

class AuthService:
    def __init__(self):
        pass

    def login(self, login_data, db: Session):
        # 1. Look up user by email and verify password using bcrypt
        user = employee_repository.get_by_email(login_data.email, db)
        if not user or not verify_password(login_data.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # Automatically upgrade legacy plaintext password to bcrypt
        if user.password and not user.password.startswith(("$2a$", "$2b$", "$2y$")):
            user.password = hash_password(login_data.password)
            db.commit()
            db.refresh(user)

        # 2. Log login event in audit log
        audit_repository.log_event(
            actor_id=user.employee_id,
            action="LOGIN",
            result=f"User {user.email} logged in successfully as {user.role}",
            trace_id="auth",
            db=db
        )

        # 3. Return user info
        return {
            "message": "Login successful",
            "user": {
                "employee_id": user.employee_id,
                "name": user.name,
                "email": user.email,
                "department": user.department,
                "role": user.role,
                "status": user.status
            }
        }

    def check_is_hr_admin(self, employee_id: int, db: Session):
        employee = employee_repository.get_by_id(employee_id, db)
        if not employee:
            return False

        role = employee.role or ""
        department = employee.department or ""

        # HR Admin can be Admin, HR Staff, or HR Manager
        if role == "Admin":
            return True
        if role == "HR Staff":
            return True
        if department == "HR" and role == "Manager":
            return True

        return False

    def check_is_manager_or_hr(self, employee_id: int, db: Session):
        employee = employee_repository.get_by_id(employee_id, db)
        if not employee:
            return False

        role = employee.role or ""

        # Only Managers, Admins, or HR Staff can approve/reject leaves
        if role == "Manager":
            return True
        if role == "Admin":
            return True
        if role == "HR Staff":
            return True

        return False
