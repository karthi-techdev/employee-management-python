from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class DocumentResponse(BaseModel):
    document_id: int
    title: str
    version: Optional[str] = None
    section: Optional[str] = None
    effective_date: Optional[date] = None
    access_level: Optional[str] = None
    file_path: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class DocumentUploadResponse(BaseModel):
    status: str
    message: str
    document_id: int
    chunks_indexed: int

class ClearPoliciesRequest(BaseModel):
    admin_employee_id: int
