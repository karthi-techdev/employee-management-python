from pydantic import BaseModel
from typing import Dict, Any

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    message: str
    user: Dict[str, Any]

