from models.employees import Employee
from sqlalchemy.orm import Session
from core.config import Base, engine
from core.security import verify_password, hash_password

Base.metadata.create_all(bind=engine)

class EmployeeRepository:
    def __init__(self):
        pass

    def get_all(self, db: Session):
        return db.query(Employee).order_by(Employee.employee_id.asc()).all()

    def get_by_id(self, employee_id: int, db: Session):
        return db.query(Employee).filter(Employee.employee_id == employee_id).first()

    def get_by_email(self, email: str, db: Session):
        return db.query(Employee).filter(Employee.email == email.strip().lower()).first()

    def get_by_email_and_password(self, email: str, password: str, db: Session):
        user = self.get_by_email(email, db)
        if user and verify_password(password, user.password):
            return user
        return None

    def create(self, name: str, email: str, department: str, role: str, password: str, db: Session):
        hashed_password = (
            hash_password(password)
            if password and not password.startswith(("$2a$", "$2b$", "$2y$"))
            else password
        )
        new_employee = Employee(
            name=name,
            email=email.strip().lower(),
            department=department,
            role=role,
            password=hashed_password
        )
        db.add(new_employee)
        db.commit()
        db.refresh(new_employee)
        return new_employee

    def update(self, employee_id: int, name: str, email: str, department: str, role: str, db: Session):
        employee = self.get_by_id(employee_id, db)
        if employee:
            employee.name = name
            employee.email = email.strip().lower()
            employee.department = department
            employee.role = role
            db.commit()
            db.refresh(employee)
        return employee

    def delete(self, employee_id: int, db: Session):
        employee = self.get_by_id(employee_id, db)
        if employee:
            db.delete(employee)
            db.commit()
            return True
        return False

