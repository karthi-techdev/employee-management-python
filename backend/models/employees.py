from sqlalchemy import Integer, Column, String
from core.config import Base

class Employee(Base):
    __tablename__ = "employees"

    employee_id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    department = Column(String)
    role = Column(String)
    password = Column(String)
    manager_id = Column(Integer, nullable=True)
    status = Column(String)

