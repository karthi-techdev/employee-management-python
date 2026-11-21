import os
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.db import get_db_connection
from services.rag_service import RagService
from services.auth_service import AuthService
from repository.documents import DocumentRepository
from repository.audits import AuditRepository

router = APIRouter(tags=["Admin"])
rag_service = RagService()
auth_service = AuthService()
document_repository = DocumentRepository()
audit_repository = AuditRepository()

class AdminActionRequest(BaseModel):
    admin_employee_id: int

@router.post("/api/admin/documents/upload-file")
async def upload_document_file_api(
    admin_employee_id: int = Form(...),
    title: str = Form(...),
    version: str = Form("1.0"),
    effective_date: str = Form("2026-01-01"),
    access_level: str = Form("Employee"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db_connection)
):
    # 1. RBAC: Only HR Admin can upload policy documents
    if not auth_service.check_is_hr_admin(admin_employee_id, db):
        raise HTTPException(
            status_code=403,
            detail="Access denied: Only HR Admin can upload policy documents"
        )

    # 2. Validate file format (.pdf or .docx only)
    filename = file.filename or "policy.pdf"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".pdf", ".docx"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Only .pdf and .docx documents are supported."
        )

    # 3. Save uploaded file to disk
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "documents", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    saved_file_path = os.path.join(uploads_dir, filename)

    with open(saved_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 4. Extract text, generate HuggingFace embeddings, and save vectors in Pinecone and metadata in DB
    try:
        result = rag_service.process_and_embed_document_file(
            file_path=saved_file_path,
            title=title,
            version=version,
            effective_date=effective_date,
            access_level=access_level,
            db=db
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process and embed document: {str(e)}"
        )

    # 5. Log audit event
    try:
        audit_repository.log_event(
            actor_id=admin_employee_id,
            action="UPLOAD_POLICY_FILE",
            result=f"HR Admin #{admin_employee_id} uploaded policy '{title}' ({filename}) - {result.get('chunks_count', 0)} sections indexed",
            trace_id="admin",
            db=db
        )
    except Exception as audit_err:
        print("Audit log notice:", audit_err)

    return result

@router.delete("/api/admin/documents/{document_id}")
def delete_policy_document_api(
    document_id: int,
    admin_employee_id: int,
    db: Session = Depends(get_db_connection)
):
    # RBAC: Only HR Admin can delete policy documents
    if not auth_service.check_is_hr_admin(admin_employee_id, db):
        raise HTTPException(
            status_code=403,
            detail="Access denied: Only HR Admin can delete policy documents"
        )

    success = rag_service.delete_single_policy(document_id, db)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Policy document #{document_id} not found"
        )

    audit_repository.log_event(
        actor_id=admin_employee_id,
        action="DELETE_POLICY_DOC",
        result=f"HR Admin #{admin_employee_id} deleted document #{document_id} from repository",
        trace_id="admin",
        db=db
    )

    return {
        "status": "success",
        "message": f"Policy document #{document_id} deleted successfully from policy repository."
    }

@router.post("/api/admin/documents/clear-all")
def clear_all_policies_api(
    request: AdminActionRequest,
    db: Session = Depends(get_db_connection)
):
    # RBAC: Only HR Admin can clear all policy documents
    if not auth_service.check_is_hr_admin(request.admin_employee_id, db):
        raise HTTPException(
            status_code=403,
            detail="Access denied: Only HR Admin can clear policy documents"
        )

    rag_service.clear_all_policies(db)

    audit_repository.log_event(
        actor_id=request.admin_employee_id,
        action="CLEAR_ALL_POLICY_DOCS",
        result=f"HR Admin #{request.admin_employee_id} cleared all company policy documents",
        trace_id="admin",
        db=db
    )

    return {
        "status": "success",
        "message": "All policy documents have been deleted from policy repository."
    }

@router.get("/api/admin/documents")
def get_documents_api(db: Session = Depends(get_db_connection)):
    docs = document_repository.get_all(db)
    return {
        "documents": [
            {
                "document_id": d.document_id,
                "title": d.title,
                "version": d.version,
                "section": d.section,
                "effective_date": d.effective_date,
                "access_level": d.access_level,
                "file_path": d.file_path,
                "created_at": d.created_at
            }
            for d in docs
        ]
    }

@router.get("/api/admin/audit-events")
def get_audit_events_api(limit: int = 50, db: Session = Depends(get_db_connection)):
    events = audit_repository.get_recent(limit, db)
    return {
        "audit_events": [
            {
                "event_id": e.event_id,
                "actor_id": e.actor_id,
                "action": e.action,
                "event_timestamp": e.event_timestamp,
                "result": e.result,
                "trace_id": e.trace_id
            }
            for e in events
        ]
    }

