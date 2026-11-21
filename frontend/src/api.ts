const API_BASE = "http://127.0.0.1:8000";

export async function loginUser(email: string, password: string) {
  const res = await fetch(`${API_BASE}/api/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const json = await res.json();
  if (!res.ok) {
    throw new Error(json.detail || "Invalid email or password");
  }
  return json;
}

export async function fetchEmployees() {
  const res = await fetch(`${API_BASE}/employees`);
  if (!res.ok) throw new Error("Failed to fetch employees");
  return res.json();
}

export async function fetchLeaveBalance(employeeId: number) {
  const res = await fetch(`${API_BASE}/employees/${employeeId}/leave-balance`);
  if (!res.ok) {
    if (res.status === 404) return [];
    throw new Error("Failed to fetch leave balance");
  }
  return res.json();
}

export async function fetchLeaveRequests() {
  const res = await fetch(`${API_BASE}/leave-requests`);
  if (!res.ok) throw new Error("Failed to fetch leave requests");
  return res.json();
}

export async function submitLeaveRequest(data: {
  employee_id: number;
  start_date: string;
  end_date: string;
  leave_type: string;
}) {
  const res = await fetch(`${API_BASE}/leave-requests`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const json = await res.json();
  if (!res.ok) {
    throw new Error(json.detail || "Failed to submit leave request");
  }
  return json;
}

export async function reviewLeaveRequest(
  requestId: number,
  status: "approved" | "rejected",
  approverId: number
) {
  const res = await fetch(`${API_BASE}/leave-requests/${requestId}/review`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status, approver_id: approverId }),
  });
  const json = await res.json();
  if (!res.ok) {
    throw new Error(json.detail || "Failed to review leave request");
  }
  return json;
}

export async function sendChatMessage(
  message: string,
  employeeId: number,
  history: Array<{ role: string; content: string }>
) {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      employee_id: employeeId,
      history,
    }),
  });
  const json = await res.json();
  if (!res.ok) {
    throw new Error(json.detail || "Failed to get AI response");
  }
  return json;
}

export async function fetchDocuments() {
  const res = await fetch(`${API_BASE}/api/admin/documents`);
  if (!res.ok) throw new Error("Failed to fetch documents");
  return res.json();
}

export async function uploadPolicyFile(formData: FormData) {
  const res = await fetch(`${API_BASE}/api/admin/documents/upload-file`, {
    method: "POST",
    body: formData,
  });
  const json = await res.json();
  if (!res.ok) {
    throw new Error(json.detail || "Failed to upload and embed document");
  }
  return json;
}

export async function deletePolicyDocument(documentId: number, adminEmployeeId: number) {
  const res = await fetch(
    `${API_BASE}/api/admin/documents/${documentId}?admin_employee_id=${adminEmployeeId}`,
    {
      method: "DELETE",
    }
  );
  const json = await res.json();
  if (!res.ok) {
    throw new Error(json.detail || "Failed to delete policy document");
  }
  return json;
}

export async function clearAllPolicies(adminEmployeeId: number) {
  const res = await fetch(`${API_BASE}/api/admin/documents/clear-all`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ admin_employee_id: adminEmployeeId }),
  });
  const json = await res.json();
  if (!res.ok) {
    throw new Error(json.detail || "Failed to clear policy documents");
  }
  return json;
}

export async function fetchAuditEvents() {
  const res = await fetch(`${API_BASE}/api/admin/audit-events?limit=30`);
  if (!res.ok) throw new Error("Failed to fetch audit events");
  return res.json();
}
