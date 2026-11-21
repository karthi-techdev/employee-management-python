from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from schemas.employees import EmployeeCreate, EmployeeUpdate
from core.db import get_db_connection
from services.employee_service import EmployeeService

employee_service = EmployeeService()
router = APIRouter(tags=["Employees"])

@router.get("/employees")
def get_all_employees(db: Session = Depends(get_db_connection)):
    return employee_service.get_all(db)

@router.get("/employees/{employee_id}")
def get_employee(employee_id: int, db: Session = Depends(get_db_connection)):
    return employee_service.get_by_id(employee_id, db)

@router.post("/employees")
def create_employee(employee_data: EmployeeCreate, db: Session = Depends(get_db_connection)):
    return employee_service.create(employee_data, db)

@router.put("/employees/{employee_id}")
def update_employee(employee_id: int, employee_data: EmployeeUpdate, db: Session = Depends(get_db_connection)):
    return employee_service.update(employee_id, employee_data, db)

@router.delete("/employees/{employee_id}")
def delete_employee(employee_id: int, db: Session = Depends(get_db_connection)):
    return employee_service.delete(employee_id, db)

