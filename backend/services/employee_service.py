from fastapi import HTTPException
from sqlalchemy.orm import Session
from repository.employees import EmployeeRepository

employee_repository = EmployeeRepository()

class EmployeeService:
    def __init__(self):
        pass

    def get_all(self, db: Session):
        employees = employee_repository.get_all(db)
        return [
            {
                "employee_id": emp.employee_id,
                "name": emp.name,
                "email": emp.email,
                "department": emp.department,
                "role": emp.role,
                "status": emp.status
            }
            for emp in employees
        ]

    def get_by_id(self, employee_id: int, db: Session):
        emp = employee_repository.get_by_id(employee_id, db)
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        return {
            "employee_id": emp.employee_id,
            "name": emp.name,
            "email": emp.email,
            "department": emp.department,
            "role": emp.role,
            "status": emp.status
        }

    def create(self, employee_data, db: Session):
        existing = employee_repository.get_by_email(employee_data.email, db)
        if existing:
            raise HTTPException(status_code=400, detail="Employee with this email already exists")

        new_emp = employee_repository.create(
            name=employee_data.name,
            email=employee_data.email,
            department=employee_data.department,
            role=employee_data.role,
            password=employee_data.password,
            db=db
        )
        return {"message": "Employee created successfully", "employee_id": new_emp.employee_id}

    def update(self, employee_id: int, employee_data, db: Session):
        emp = employee_repository.get_by_id(employee_id, db)
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")

        updated_emp = employee_repository.update(
            employee_id=employee_id,
            name=employee_data.name,
            email=employee_data.email,
            department=employee_data.department,
            role=employee_data.role,
            db=db
        )
        return {"message": "Employee updated successfully"}

    def delete(self, employee_id: int, db: Session):
        emp = employee_repository.get_by_id(employee_id, db)
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")

        employee_repository.delete(employee_id, db)
        return {"message": "Employee deleted successfully"}
