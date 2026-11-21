import os
import pytest
from fastapi.testclient import TestClient
import docx
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_login_success():
    response = client.post("/api/login", json={
        "email": "arun@company.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Login successful"
    assert data["user"]["employee_id"] == 1
    assert data["user"]["role"] == "Employee"

def test_login_invalid_password():
    response = client.post("/api/login", json={
        "email": "arun@company.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]

def test_get_leave_balance():
    response = client.get("/employees/1/leave-balance")
    assert response.status_code == 200
    balances = response.json()
    assert isinstance(balances, list)
    assert len(balances) > 0

def test_rbac_manager_approval():
    create_resp = client.post("/leave-requests", json={
        "employee_id": 1,
        "start_date": "2026-11-25",
        "end_date": "2026-11-26",
        "leave_type": "Casual"
    })
    assert create_resp.status_code == 200
    req_id = create_resp.json()["request_id"]

    # Regular employee tries to approve -> 403 Forbidden
    forbidden_resp = client.put(f"/leave-requests/{req_id}/review", json={
        "status": "approved",
        "approver_id": 3
    })
    assert forbidden_resp.status_code == 403

    # Authorized Manager approves -> 200 OK
    manager_resp = client.put(f"/leave-requests/{req_id}/review", json={
        "status": "approved",
        "approver_id": 9
    })
    assert manager_resp.status_code == 200
    assert manager_resp.json()["status"] == "approved"

def test_file_upload_docx_and_embed_in_pinecone(tmp_path):
    # 1. Create a test .docx file
    test_docx_path = tmp_path / "test_policy.docx"
    doc = docx.Document()
    doc.add_heading("Special Paternity Leave Policy", 0)
    doc.add_paragraph("Full-time employees are granted 15 days of paid paternity leave within 6 months of childbirth.")
    doc.save(str(test_docx_path))

    # 2. Regular employee attempts upload -> 403 Forbidden
    with open(test_docx_path, "rb") as f:
        deny_resp = client.post(
            "/api/admin/documents/upload-file",
            data={"admin_employee_id": 1, "title": "Test Policy"},
            files={"file": ("test_policy.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )
    assert deny_resp.status_code == 403

    # 3. HR Admin (Employee 4) uploads .docx file -> 200 OK
    with open(test_docx_path, "rb") as f:
        upload_resp = client.post(
            "/api/admin/documents/upload-file",
            data={
                "admin_employee_id": 4,
                "title": "Paternity Leave Policy",
                "version": "1.0",
                "effective_date": "2026-01-01",
                "access_level": "Employee"
            },
            files={"file": ("test_policy.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )
    assert upload_resp.status_code == 200
    upload_data = upload_resp.json()
    assert upload_data["status"] == "success"
    doc_id = upload_data["document_id"]

    # 4. Delete the policy -> 200 OK
    del_resp = client.delete(f"/api/admin/documents/{doc_id}?admin_employee_id=4")
    assert del_resp.status_code == 200

def test_langgraph_chat_policy_and_restriction():
    # 1. Arun asks for his own leave
    chat_resp = client.post("/api/chat", json={
        "message": "How many casual leaves do I have?",
        "employee_id": 1
    })
    assert chat_resp.status_code == 200
    assert "reply" in chat_resp.json()

    # 2. Arun asks for Priya's balance -> Assistant restricts information
    restrict_resp = client.post("/api/chat", json={
        "message": "What is Priya's leave balance?",
        "employee_id": 1
    })
    assert restrict_resp.status_code == 200
    reply = restrict_resp.json()["reply"].lower()
    assert any(w in reply for w in ["cannot", "restrict", "only", "own", "private", "not authorized", "unable"])

    # 3. Manager Sanjay asks for Arun Kumar's leave balance -> Assistant provides balance
    manager_resp = client.post("/api/chat", json={
        "message": "Show me the available leave balance of Arun Kumar (Employee)",
        "employee_id": 9
    })
    assert manager_resp.status_code == 200
    mgr_reply = manager_resp.json()["reply"].lower()
    assert "arun" in mgr_reply or "casual" in mgr_reply or "sick" in mgr_reply
