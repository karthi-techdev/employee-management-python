from pydantic import BaseModel
from typing import Optional

class EmployeeCreate(BaseModel):
    name: str
    email: str
    department: str
    role: str
    password: str

class EmployeeUpdate(BaseModel):
    name: str
    email: str
    department: str
    role: str

class EmployeeResponse(BaseModel):
    employee_id: int
    name: str
    email: str
    department: str
    role: str
    status: Optional[str] = None

    model_config = {"from_attributes": True}
