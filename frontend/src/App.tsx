import React, { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./App.css";
import {
  loginUser,
  fetchLeaveBalance,
  fetchLeaveRequests,
  submitLeaveRequest,
  reviewLeaveRequest,
  sendChatMessage,
  fetchDocuments,
  uploadPolicyFile,
  deletePolicyDocument,
  clearAllPolicies,
  fetchAuditEvents,
} from "./api";
import {
  Building2,
  Bot,
  CalendarDays,
  CheckSquare,
  FileText,
  Shield,
  Upload,
  Trash2,
  Send,
  CheckCircle2,
  XCircle,
  Clock,
  User,
  Cpu,
  Info,
  Lock,
  LogOut,
  Activity,
} from "lucide-react";

interface UserProfile {
  employee_id: number;
  name: string;
  email: string;
  department: string;
  role: string;
  status: string;
}

interface LeaveBalance {
  leave_type: string;
  balance: number;
  as_of_date: string;
}

interface LeaveRequestItem {
  request_id: number;
  employee_id: number;
  employee_name?: string;
  start_date: string;
  end_date: string;
  leave_type: string;
  status: string;
  approver_id: number | null;
  created_at: string;
}

/** Convert any date string (YYYY-MM-DD or ISO) to DD/MM/YYYY */
function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  const dd = String(d.getDate()).padStart(2, "0");
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const yyyy = d.getFullYear();
  return `${dd}/${mm}/${yyyy}`;
}

/** Convert an ISO timestamp to DD/MM/YYYY HH:mm:ss */
function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  const dd = String(d.getDate()).padStart(2, "0");
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const yyyy = d.getFullYear();
  const hh = String(d.getHours()).padStart(2, "0");
  const min = String(d.getMinutes()).padStart(2, "0");
  const ss = String(d.getSeconds()).padStart(2, "0");
  return `${dd}/${mm}/${yyyy} ${hh}:${min}:${ss}`;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  citations?: string[];
  tools?: string[];
}

export default function App() {
  // Authentication state
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(() => {
    const saved = localStorage.getItem("hr_user");
    return saved ? JSON.parse(saved) : null;
  });

  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);

  // App Navigation state
  const [activeTab, setActiveTab] = useState<"chat" | "leaves" | "approvals" | "policies" | "audits">("chat");

  // Leave balances & requests
  const [balances, setBalances] = useState<LeaveBalance[]>([]);
  const [allRequests, setAllRequests] = useState<LeaveRequestItem[]>([]);
  const [leaveForm, setLeaveForm] = useState({
    start_date: "",
    end_date: "",
    leave_type: "Casual",
  });
  const [formMsg, setFormMsg] = useState<{ text: string; error: boolean } | null>(null);

  // Chat state
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  // Admin & documents state
  const [documents, setDocuments] = useState<any[]>([]);
  const [auditEvents, setAuditEvents] = useState<any[]>([]);

  // File Upload state (PDF / DOCX)
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadVersion, setUploadVersion] = useState("");
  const [uploadEffectiveDate, setUploadEffectiveDate] = useState("");
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState<{ text: string; error: boolean } | null>(null);

  // Check RBAC roles
  const isHrAdmin =
    currentUser?.role === "Admin" ||
    currentUser?.role === "HR Staff" ||
    (currentUser?.department === "HR" && currentUser?.role === "Manager");

  const isApprover =
    currentUser?.role === "Manager" ||
    currentUser?.role === "Admin" ||
    currentUser?.role === "HR Staff";

  // Audit logs are visible strictly to HR Admin, Manager, and Admin (never to Employees)
  const canViewAuditLogs =
    currentUser?.role === "HR Staff" ||
    currentUser?.role === "Manager" ||
    currentUser?.role === "Admin";

  // Pending count for approvals badge
  const pendingCount = allRequests.filter((r) => r.status === "pending").length;

  // Guard tab access: redirect employees away from management/audit tabs
  useEffect(() => {
    if (currentUser?.role === "Employee") {
      if (activeTab === "audits" || activeTab === "approvals" || activeTab === "policies") {
        setActiveTab("chat");
      }
    }
  }, [currentUser, activeTab]);

  // Initial greeting when user logs in
  useEffect(() => {
    if (currentUser) {
      setMessages([
        {
          role: "assistant",
          content: `Welcome back, ${currentUser.name}. I am your AI HR Assistant. You are logged in as ${currentUser.role} in the ${currentUser.department} department. How can I assist you today?`,
        },
      ]);
    }
  }, [currentUser]);

  // Load data when tab or user changes
  useEffect(() => {
    if (currentUser) {
      fetchLeaveBalance(currentUser.employee_id).then(setBalances).catch(console.error);
      fetchLeaveRequests().then(setAllRequests).catch(console.error);
    }
  }, [currentUser, activeTab]);

  useEffect(() => {
    if (currentUser && (activeTab === "policies" || activeTab === "audits")) {
      if (isHrAdmin && activeTab === "policies") {
        fetchDocuments().then((d) => setDocuments(d.documents)).catch(console.error);
      }
      if (canViewAuditLogs && activeTab === "audits") {
        fetchAuditEvents().then((a) => setAuditEvents(a.audit_events)).catch(console.error);
      }
    }
  }, [currentUser, activeTab, isHrAdmin, canViewAuditLogs]);

  // Handle Login
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError("");
    setLoginLoading(true);

    try {
      const data = await loginUser(loginEmail, loginPassword);
      setCurrentUser(data.user);
      localStorage.setItem("hr_user", JSON.stringify(data.user));
    } catch (err: any) {
      setLoginError(err.message || "Invalid email or password");
    } finally {
      setLoginLoading(false);
    }
  };

  // Handle Logout
  const handleLogout = () => {
    localStorage.removeItem("hr_user");
    setCurrentUser(null);
    setMessages([]);
  };

  // Handle Chat Send
  const handleSendChat = async (textToSend?: string) => {
    if (!currentUser) return;
    const text = textToSend || chatInput;
    if (!text.trim() || chatLoading) return;

    const userMsg: ChatMessage = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setChatInput("");
    setChatLoading(true);

    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const response = await sendChatMessage(text, currentUser.employee_id, history);

      const aiMsg: ChatMessage = {
        role: "assistant",
        content: response.reply,
        citations: response.citations,
        tools: response.tool_calls?.map((t: any) => t.tool),
      };
      setMessages((prev) => [...prev, aiMsg]);

      // Refresh balances or requests
      fetchLeaveBalance(currentUser.employee_id).then(setBalances);
      fetchLeaveRequests().then(setAllRequests);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Unable to complete request: ${err.message || "Service error occurred"}`,
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  // Handle Submit Leave Request
  const handleLeaveSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentUser) return;
    setFormMsg(null);

    try {
      const res = await submitLeaveRequest({
        employee_id: currentUser.employee_id,
        start_date: leaveForm.start_date,
        end_date: leaveForm.end_date,
        leave_type: leaveForm.leave_type,
      });
      setFormMsg({ text: res.message || "Leave request submitted successfully.", error: false });
      setLeaveForm({ start_date: "", end_date: "", leave_type: "Casual" });
      fetchLeaveRequests().then(setAllRequests);
      fetchLeaveBalance(currentUser.employee_id).then(setBalances);
    } catch (err: any) {
      setFormMsg({ text: err.message, error: true });
    }
  };

  // Handle Review Leave Request (Manager / HR only)
  const handleReview = async (requestId: number, status: "approved" | "rejected") => {
    if (!currentUser) return;
    try {
      await reviewLeaveRequest(requestId, status, currentUser.employee_id);
      fetchLeaveRequests().then(setAllRequests);
    } catch (err: any) {
      alert(err.message);
    }
  };

  // Handle PDF / DOCX File Upload (HR Admin only)
  const handleUploadFile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentUser || !uploadFile) {
      alert("Please select a PDF (.pdf) or Word (.docx) document.");
      return;
    }
    setUploadMsg(null);
    setUploadLoading(true);

    const formData = new FormData();
    formData.append("file", uploadFile);
    formData.append("admin_employee_id", currentUser.employee_id.toString());
    formData.append("title", uploadTitle);
    formData.append("version", uploadVersion);
    formData.append("effective_date", uploadEffectiveDate);
    formData.append("access_level", "Employee");

    try {
      const res = await uploadPolicyFile(formData);
      setUploadMsg({ text: res.message, error: false });
      setUploadFile(null);
      setUploadTitle("");
      const fileInput = document.getElementById("policy-file-input") as HTMLInputElement;
      if (fileInput) fileInput.value = "";

      fetchDocuments().then((d) => setDocuments(d.documents));
      fetchAuditEvents().then((a) => setAuditEvents(a.audit_events));
    } catch (err: any) {
      setUploadMsg({ text: err.message, error: true });
    } finally {
      setUploadLoading(false);
    }
  };

  // Handle Delete Single Policy Document (HR Admin only)
  const handleDeletePolicy = async (documentId: number) => {
    if (!currentUser) return;
    const confirmDelete = window.confirm(
      `Delete policy #${documentId} from the document repository?`
    );
    if (!confirmDelete) return;

    try {
      const res = await deletePolicyDocument(documentId, currentUser.employee_id);
      alert(res.message);
      fetchDocuments().then((d) => setDocuments(d.documents));
      fetchAuditEvents().then((a) => setAuditEvents(a.audit_events));
    } catch (err: any) {
      alert(err.message);
    }
  };

  // Handle Clear All Policies (HR Admin only)
  const handleClearAllPolicies = async () => {
    if (!currentUser) return;
    const confirmClear = window.confirm(
      "Confirm permanent removal of all indexed policy documents?"
    );
    if (!confirmClear) return;

    try {
      const res = await clearAllPolicies(currentUser.employee_id);
      alert(res.message);
      fetchDocuments().then((d) => setDocuments(d.documents));
      fetchAuditEvents().then((a) => setAuditEvents(a.audit_events));
    } catch (err: any) {
      alert(err.message);
    }
  };

  const samplePrompts = isApprover
    ? [
        "Show me the available leave balance of Arun Kumar (Employee)",
        "Who are all asked for leave approval?",
        "What is the casual leave policy?",
        "How many casual leaves do I have?",
        "What is the work from home policy?",
      ]
    : [
        "What is the casual leave policy?",
        "How many casual leaves do I have?",
        "What is the work from home policy?",
        "Can you submit a Casual leave request for 2026-11-20 to 2026-11-21?",
        "What is Priya's leave balance?",
      ];

  // --------------------------------------------------------------------------
  // SCREEN 1: LOGIN PAGE (Admin Console Aesthetic)
  // --------------------------------------------------------------------------
  if (!currentUser) {
    return (
      <div className="login-screen">
        <div className="login-box">
          <div className="login-brand-header">
            <div className="login-logo">
              <Building2 size={24} />
            </div>
            <h2>HR Admin Console</h2>
            <p>Enterprise Employee & Operations Portal</p>
          </div>

          {loginError && (
            <div
              style={{
                background: "#fee2e2",
                border: "1px solid #fca5a5",
                padding: "10px 14px",
                borderRadius: "6px",
                fontSize: "13px",
                color: "#991b1b",
                marginBottom: "16px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <XCircle size={16} />
              <span>{loginError}</span>
            </div>
          )}

          <form onSubmit={handleLogin}>
            <div className="form-field" style={{ marginBottom: "14px" }}>
              <label>Work Email</label>
              <input
                type="email"
                required
                placeholder="name@company.com"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
              />
            </div>

            <div className="form-field" style={{ marginBottom: "18px" }}>
              <label>Password</label>
              <input
                type="password"
                required
                placeholder="Enter password"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
              />
            </div>

            <button
              type="submit"
              className="btn-primary"
              disabled={loginLoading}
              style={{ width: "100%", justifyContent: "center", padding: "10px" }}
            >
              <Lock size={15} />
              {loginLoading ? "Authenticating..." : "Sign In to Console"}
            </button>
          </form>

          {/* Real System Accounts Reference */}
          <div style={{ marginTop: "20px", padding: "14px", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "8px", fontSize: "12.5px", color: "#475569" }}>
            <div style={{ fontWeight: 700, color: "#0f172a", marginBottom: "6px" }}>Database Accounts (Password: password123)</div>
            <div style={{ lineHeight: "1.7" }}>
              &bull; <strong>Employee:</strong> <code>arun@company.com</code><br/>
              &bull; <strong>HR Staff / Admin:</strong> <code>priya@company.com</code><br/>
              &bull; <strong>Manager:</strong> <code>sanjay@company.com</code><br/>
              &bull; <strong>System Admin:</strong> <code>admin@company.com</code>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // --------------------------------------------------------------------------
  // SCREEN 2: ADMIN PANEL WORKSPACE
  // --------------------------------------------------------------------------
  return (
    <div className="admin-layout">
      {/* 1. Left Sidebar */}
      <aside className="admin-sidebar">
        <div className="sidebar-header">
          <div className="brand-icon-box">
            <Building2 size={20} />
          </div>
          <div className="brand-text">
            <h1>CoreHR Admin</h1>
            <span>Operations Console</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-title">Navigation</div>

          <button
            className={`nav-item ${activeTab === "chat" ? "active" : ""}`}
            onClick={() => setActiveTab("chat")}
          >
            <div className="nav-item-left">
              <Bot size={18} className="nav-icon" />
              <span>AI Assistant</span>
            </div>
          </button>

          <button
            className={`nav-item ${activeTab === "leaves" ? "active" : ""}`}
            onClick={() => setActiveTab("leaves")}
          >
            <div className="nav-item-left">
              <CalendarDays size={18} className="nav-icon" />
              <span>Leave Management</span>
            </div>
          </button>

          {isApprover && (
            <button
              className={`nav-item ${activeTab === "approvals" ? "active" : ""}`}
              onClick={() => setActiveTab("approvals")}
            >
              <div className="nav-item-left">
                <CheckSquare size={18} className="nav-icon" />
                <span>Manager Approvals</span>
              </div>
              {pendingCount > 0 && <span className="nav-badge amber">{pendingCount}</span>}
            </button>
          )}

          {canViewAuditLogs && (
            <>
              <div className="nav-section-title" style={{ marginTop: "12px" }}>Administration</div>

              {isHrAdmin && (
                <button
                  className={`nav-item ${activeTab === "policies" ? "active" : ""}`}
                  onClick={() => setActiveTab("policies")}
                >
                  <div className="nav-item-left">
                    <FileText size={18} className="nav-icon" />
                    <span>Policy Documents</span>
                  </div>
                  <span className="nav-badge blue">Docs</span>
                </button>
              )}

              <button
                className={`nav-item ${activeTab === "audits" ? "active" : ""}`}
                onClick={() => setActiveTab("audits")}
              >
                <div className="nav-item-left">
                  <Shield size={18} className="nav-icon" />
                  <span>Audit Logs</span>
                </div>
              </button>
            </>
          )}
        </nav>

        {/* Sidebar Footer User Widget */}
        <div className="sidebar-footer">
          <div className="user-profile-widget">
            <div className="user-avatar-badge">{currentUser.name.charAt(0)}</div>
            <div className="user-details">
              <div className="user-name">{currentUser.name}</div>
              <div className="user-role-label">
                {currentUser.role} &bull; {currentUser.department}
              </div>
            </div>
            <button className="logout-icon-btn" onClick={handleLogout} title="Log out">
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      {/* 2. Main Workspace */}
      <div className="admin-main">
        {/* Top Header */}
        <header className="admin-topbar">
          <div className="topbar-breadcrumb">
            <span>Console</span>
            <span>/</span>
            <span className="breadcrumb-active">
              {activeTab === "chat" && "AI Assistant Copilot"}
              {activeTab === "leaves" && "Employee Leave Management"}
              {activeTab === "approvals" && "Manager Leave Review"}
              {activeTab === "policies" && "Policy Document Repository"}
              {activeTab === "audits" && "Security & Audit Event Trail"}
            </span>
          </div>

          <div className="topbar-actions">
            <div className="system-status-pill">
              <span className="status-dot"></span>
              <span>System Online</span>
            </div>

            <div
              className={`role-pill ${
                isHrAdmin ? "admin" : isApprover ? "manager" : "employee"
              }`}
            >
              <User size={13} />
              <span>{currentUser.role}</span>
            </div>
          </div>
        </header>

        {/* Scrollable Body */}
        <main className="admin-workspace">
          {/* TAB 1: AI COPILOT CHAT */}
          {activeTab === "chat" && (
            <div>
              <div className="page-header">
                <h2>AI Assistant Copilot</h2>
                <p>
                  Natural language enterprise assistant for company policies, leaves, and staff services.
                </p>
              </div>

              <div className="chat-console">
                <div className="chat-stream">
                  {messages.map((msg, idx) => (
                    <div key={idx} className={`chat-row ${msg.role}`}>
                      <div className={`chat-avatar ${msg.role === "user" ? "user-avatar" : "ai-avatar"}`}>
                        {msg.role === "user" ? currentUser.name[0] : <Bot size={16} />}
                      </div>
                      <div className="chat-bubble">
                        <div className="markdown-content">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {msg.content}
                          </ReactMarkdown>
                        </div>

                        {/* Citations Panel */}
                        {msg.citations && msg.citations.length > 0 && (
                          <div className="citations-panel">
                            <div className="citations-label">
                              <FileText size={12} />
                              <span>Policy References</span>
                            </div>
                            <div>
                              {msg.citations.map((cite, cIdx) => (
                                <span key={cIdx} className="citation-chip">
                                  {cite}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Tool Execution Tag */}
                        {msg.tools && msg.tools.length > 0 && (
                          <div className="tool-indicator">
                            <Cpu size={12} />
                            <span>Action: {msg.tools.map((t) => t.replace(/_/g, " ")).join(", ")}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}

                  {chatLoading && (
                    <div className="chat-row assistant">
                      <div className="chat-avatar ai-avatar">
                        <Bot size={16} />
                      </div>
                      <div className="chat-bubble" style={{ color: "#64748b" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          <Activity size={14} className="animate-spin" />
                          <span>Searching company knowledge base...</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Suggested Prompts */}
                <div className="suggested-query-chips">
                  {samplePrompts.map((p, idx) => (
                    <button key={idx} className="query-chip" onClick={() => handleSendChat(p)}>
                      {p}
                    </button>
                  ))}
                </div>

                {/* Input Field */}
                <div className="chat-input-row">
                  <input
                    type="text"
                    placeholder="Ask about company policies, leave rules, personal balance, or onboarding..."
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSendChat()}
                  />
                  <button className="btn-primary" onClick={() => handleSendChat()} disabled={chatLoading}>
                    <Send size={15} />
                    <span>Send</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: LEAVE MANAGEMENT */}
          {activeTab === "leaves" && (
            <div>
              <div className="page-header">
                <h2>Leave Management</h2>
                <p>View current available quotas and submit planned time-off requests.</p>
              </div>

              {/* Metrics Grid */}
              <div className="stats-grid">
                {balances.map((b, idx) => (
                  <div key={idx} className="stat-card">
                    <div className="stat-header">
                      <span className="stat-title">{b.leave_type} Leave</span>
                      <CalendarDays size={18} className="stat-icon" />
                    </div>
                    <div className="stat-value">{b.balance}</div>
                    <div className="stat-subtext">Days available as of {formatDate(b.as_of_date) || "today"}</div>
                  </div>
                ))}
                <div className="stat-card">
                  <div className="stat-header">
                    <span className="stat-title">Total Requests</span>
                    <Clock size={18} className="stat-icon" />
                  </div>
                  <div className="stat-value">
                    {allRequests.filter((r) => r.employee_id === currentUser.employee_id).length}
                  </div>
                  <div className="stat-subtext">Submitted applications</div>
                </div>
              </div>

              {/* Application Form */}
              <div className="admin-card">
                <div className="card-header-bar">
                  <div className="card-title-group">
                    <h3>Submit Time-Off Application</h3>
                    <p>Applications enter pending status and require manager sign-off.</p>
                  </div>
                </div>

                {formMsg && (
                  <div
                    style={{
                      padding: "10px 14px",
                      borderRadius: "6px",
                      marginBottom: "16px",
                      background: formMsg.error ? "#fee2e2" : "#dcfce7",
                      color: formMsg.error ? "#991b1b" : "#166534",
                      fontSize: "13.5px",
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                    }}
                  >
                    {formMsg.error ? <XCircle size={16} /> : <CheckCircle2 size={16} />}
                    <span>{formMsg.text}</span>
                  </div>
                )}

                <form onSubmit={handleLeaveSubmit}>
                  <div className="form-grid">
                    <div className="form-field">
                      <label>Leave Category</label>
                      <select
                        value={leaveForm.leave_type}
                        onChange={(e) => setLeaveForm({ ...leaveForm, leave_type: e.target.value })}
                      >
                        <option value="Casual">Casual Leave</option>
                        <option value="Sick">Sick Leave</option>
                      </select>
                    </div>

                    <div className="form-field">
                      <label>Applicant</label>
                      <input
                        type="text"
                        disabled
                        value={`${currentUser.name} (ID: #${currentUser.employee_id})`}
                        style={{ backgroundColor: "#f8fafc", color: "#64748b" }}
                      />
                    </div>

                    <div className="form-field">
                      <label>Start Date</label>
                      <input
                        type="date"
                        required
                        value={leaveForm.start_date}
                        onChange={(e) => setLeaveForm({ ...leaveForm, start_date: e.target.value })}
                      />
                    </div>

                    <div className="form-field">
                      <label>End Date</label>
                      <input
                        type="date"
                        required
                        value={leaveForm.end_date}
                        onChange={(e) => setLeaveForm({ ...leaveForm, end_date: e.target.value })}
                      />
                    </div>
                  </div>

                  <button type="submit" className="btn-primary">
                    <CheckCircle2 size={16} />
                    <span>Submit Application</span>
                  </button>
                </form>
              </div>

              {/* Personal Requests Table */}
              <div className="admin-card">
                <div className="card-header-bar">
                  <div className="card-title-group">
                    <h3>Application History</h3>
                    <p>Record of submitted leave requests for this account.</p>
                  </div>
                </div>

                <div className="table-responsive">
                  <table className="admin-table">
                    <thead>
                      <tr>
                        <th>Request ID</th>
                        <th>Type</th>
                        <th>Start Date</th>
                        <th>End Date</th>
                        <th>Status</th>
                        <th>Reviewer</th>
                      </tr>
                    </thead>
                    <tbody>
                      {allRequests
                        .filter((r) => r.employee_id === currentUser.employee_id)
                        .map((r) => (
                          <tr key={r.request_id}>
                            <td>#{r.request_id}</td>
                            <td>
                              <strong>{r.leave_type}</strong>
                            </td>
                            <td>{formatDate(r.start_date)}</td>
                            <td>{formatDate(r.end_date)}</td>
                            <td>
                              <span className={`status-badge ${r.status}`}>
                                {r.status === "pending" && <Clock size={12} />}
                                {r.status === "approved" && <CheckCircle2 size={12} />}
                                {r.status === "rejected" && <XCircle size={12} />}
                                {r.status}
                              </span>
                            </td>
                            <td>{r.approver_id ? `Manager #${r.approver_id}` : "Pending Review"}</td>
                          </tr>
                        ))}
                      {allRequests.filter((r) => r.employee_id === currentUser.employee_id).length === 0 && (
                        <tr>
                          <td colSpan={6} style={{ textAlign: "center", color: "#64748b", padding: "20px" }}>
                            No prior leave requests recorded.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: MANAGER APPROVALS */}
          {activeTab === "approvals" && (
            <div>
              <div className="page-header">
                <h2>Manager Approval Console</h2>
                <p>Review and act upon team member leave applications. Autonomous AI approvals are prohibited.</p>
              </div>

              {!isApprover && (
                <div
                  style={{
                    background: "#f8fafc",
                    border: "1px solid #cbd5e1",
                    padding: "12px 16px",
                    borderRadius: "8px",
                    fontSize: "13.5px",
                    color: "#475569",
                    marginBottom: "20px",
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                  }}
                >
                  <Info size={16} className="text-blue-600" />
                  <span>
                    Approval controls are reserved for Managers and HR Staff. Current view displays company requests in read-only mode.
                  </span>
                </div>
              )}

              <div className="admin-card">
                <div className="card-header-bar">
                  <div className="card-title-group">
                    <h3>Pending & Processed Requests</h3>
                    <p>Total applications: {allRequests.length} &bull; Pending: {pendingCount}</p>
                  </div>
                </div>

                <div className="table-responsive">
                  <table className="admin-table">
                    <thead>
                      <tr>
                        <th>Req #</th>
                        <th>Applicant</th>
                        <th>Category</th>
                        <th>Schedule</th>
                        <th>Status</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {allRequests.map((req) => (
                        <tr key={req.request_id}>
                          <td>#{req.request_id}</td>
                          <td>{req.employee_name || `Employee #${req.employee_id}`}</td>
                          <td>
                            <strong>{req.leave_type}</strong>
                          </td>
                          <td>
                            {formatDate(req.start_date)} &rarr; {formatDate(req.end_date)}
                          </td>
                          <td>
                            <span className={`status-badge ${req.status}`}>
                              {req.status === "pending" && <Clock size={12} />}
                              {req.status === "approved" && <CheckCircle2 size={12} />}
                              {req.status === "rejected" && <XCircle size={12} />}
                              {req.status}
                            </span>
                          </td>
                          <td>
                            {req.status === "pending" ? (
                              <div style={{ display: "flex", gap: "6px" }}>
                                <button
                                  className="btn-sm-action btn-sm-approve"
                                  disabled={!isApprover || req.employee_id === currentUser.employee_id}
                                  onClick={() => handleReview(req.request_id, "approved")}
                                  title={
                                    req.employee_id === currentUser.employee_id
                                      ? "Self-approval is prohibited"
                                      : !isApprover
                                      ? "Manager role required"
                                      : "Approve application"
                                  }
                                >
                                  <CheckCircle2 size={13} />
                                  <span>Approve</span>
                                </button>
                                <button
                                  className="btn-sm-action btn-sm-reject"
                                  disabled={!isApprover || req.employee_id === currentUser.employee_id}
                                  onClick={() => handleReview(req.request_id, "rejected")}
                                  title={
                                    req.employee_id === currentUser.employee_id
                                      ? "Self-review is prohibited"
                                      : !isApprover
                                      ? "Manager role required"
                                      : "Reject application"
                                  }
                                >
                                  <XCircle size={13} />
                                  <span>Reject</span>
                                </button>
                              </div>
                            ) : (
                              <span style={{ fontSize: "12px", color: "#64748b" }}>
                                Finalized (By #{req.approver_id || "System"})
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: POLICY DOCUMENTS */}
          {activeTab === "policies" && isHrAdmin && (
            <div>
              <div className="page-header">
                <h2>Policy Document Repository</h2>
                <p>Manage official company guidelines and HR policy documentation.</p>
              </div>

              {!isHrAdmin && (
                <div
                  style={{
                    background: "#f8fafc",
                    border: "1px solid #cbd5e1",
                    padding: "12px 16px",
                    borderRadius: "8px",
                    fontSize: "13.5px",
                    color: "#475569",
                    marginBottom: "20px",
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                  }}
                >
                  <Info size={16} className="text-blue-600" />
                  <span>
                    Document uploads and modifications are reserved for HR Administrators. Active company policies are listed below.
                  </span>
                </div>
              )}

              {/* Upload Card for HR Admin */}
              {isHrAdmin && (
                <div className="admin-card">
                  <div className="card-header-bar">
                    <div className="card-title-group">
                      <h3>Upload Policy File (PDF or DOCX)</h3>
                      <p>Upload and process official company policy documents for HR assistance.</p>
                    </div>
                  </div>

                  {uploadMsg && (
                    <div
                      style={{
                        padding: "10px 14px",
                        borderRadius: "6px",
                        marginBottom: "16px",
                        background: uploadMsg.error ? "#fee2e2" : "#dcfce7",
                        color: uploadMsg.error ? "#991b1b" : "#166534",
                        fontSize: "13.5px",
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                      }}
                    >
                      {uploadMsg.error ? <XCircle size={16} /> : <CheckCircle2 size={16} />}
                      <span>{uploadMsg.text}</span>
                    </div>
                  )}

                  <form onSubmit={handleUploadFile}>
                    <div className="form-grid">
                      <div className="form-field">
                        <label>Policy Title</label>
                        <input
                          type="text"
                          required
                          placeholder="e.g. Leave and Remote Work Policy 2026"
                          value={uploadTitle}
                          onChange={(e) => setUploadTitle(e.target.value)}
                        />
                      </div>

                      <div className="form-field">
                        <label>Select Document File (.pdf or .docx only)</label>
                        <input
                          id="policy-file-input"
                          type="file"
                          required
                          accept=".pdf,.docx"
                          onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                        />
                      </div>

                      <div className="form-field">
                        <label>Version Tag</label>
                        <input
                          type="text"
                          value={uploadVersion}
                          onChange={(e) => setUploadVersion(e.target.value)}
                        />
                      </div>

                      <div className="form-field">
                        <label>Effective Date</label>
                        <input
                          type="date"
                          value={uploadEffectiveDate}
                          onChange={(e) => setUploadEffectiveDate(e.target.value)}
                        />
                      </div>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "12px", marginTop: "12px" }}>
                      <button type="submit" className="btn-primary" disabled={uploadLoading}>
                        <Upload size={15} />
                        <span>{uploadLoading ? "Processing Document..." : "Upload Document"}</span>
                      </button>
                      <span style={{ fontSize: "12px", color: "#64748b" }}>
                        Supported formats: PDF (.pdf) and Word (.docx)
                      </span>
                    </div>
                  </form>
                </div>
              )}

              {/* Documents List */}
              <div className="admin-card">
                <div className="card-header-bar">
                  <div className="card-title-group">
                    <h3>Active Policy Documents</h3>
                    <p>Total company documents: {documents.length}</p>
                  </div>

                  <div style={{ display: "flex", gap: "8px" }}>
                    <button
                      className="btn-primary"
                      style={{ background: "#475569", padding: "6px 12px", fontSize: "12px" }}
                      onClick={() => fetchDocuments().then((d) => setDocuments(d.documents))}
                    >
                      <Activity size={13} />
                      <span>Refresh</span>
                    </button>

                    {isHrAdmin && documents.length > 0 && (
                      <button className="btn-danger" onClick={handleClearAllPolicies}>
                        <Trash2 size={14} />
                        <span>Clear All Policies</span>
                      </button>
                    )}
                  </div>
                </div>

                <div className="table-responsive">
                  <table className="admin-table">
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Document Title</th>
                        <th>Status</th>
                        <th>File Location</th>
                        <th>Version</th>
                        <th>Effective Date</th>
                        {isHrAdmin && <th>Action</th>}
                      </tr>
                    </thead>
                    <tbody>
                      {documents.map((doc) => (
                        <tr key={doc.document_id}>
                          <td>#{doc.document_id}</td>
                          <td>
                            <strong>{doc.title}</strong>
                          </td>
                          <td>
                            <span className="status-badge approved">
                              <CheckCircle2 size={12} />
                              <span>Active</span>
                            </span>
                          </td>
                          <td style={{ fontSize: "12px", color: "#64748b" }}>{doc.file_path || "Uploaded File"}</td>
                          <td>{doc.version}</td>
                          <td>{formatDate(doc.effective_date)}</td>
                          {isHrAdmin && (
                            <td>
                              <button
                                className="btn-sm-action btn-sm-delete"
                                onClick={() => handleDeletePolicy(doc.document_id)}
                                title="Delete policy document"
                              >
                                <Trash2 size={12} />
                                <span>Delete</span>
                              </button>
                            </td>
                          )}
                        </tr>
                      ))}
                      {documents.length === 0 && (
                        <tr>
                          <td
                            colSpan={isHrAdmin ? 6 : 5}
                            style={{ textAlign: "center", color: "#64748b", padding: "24px" }}
                          >
                            No policy documents currently indexed.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: AUDIT LOGS (Visible strictly to HR Admin, Manager, and Admin) */}
          {activeTab === "audits" && canViewAuditLogs && (
            <div>
              <div className="page-header">
                <h2>Security & Compliance Audit Trail</h2>
                <p>Immutable log of logins, leave actions, policy updates, and system operations.</p>
              </div>

              <div className="admin-card">
                <div className="card-header-bar">
                  <div className="card-title-group">
                    <h3>Event Stream</h3>
                    <p>Displaying recent operational audit entries from PostgreSQL.</p>
                  </div>
                </div>

                <div className="table-responsive">
                  <table className="admin-table">
                    <thead>
                      <tr>
                        <th>Event #</th>
                        <th>Actor</th>
                        <th>Action</th>
                        <th>Timestamp</th>
                        <th>Details</th>
                      </tr>
                    </thead>
                    <tbody>
                      {auditEvents.map((evt) => (
                        <tr key={evt.event_id}>
                          <td>#{evt.event_id}</td>
                          <td>{evt.actor_id ? `Employee #${evt.actor_id}` : "System"}</td>
                          <td>
                            <span className="status-badge active">{evt.action}</span>
                          </td>
                          <td style={{ fontSize: "12px", color: "#64748b" }}>
                            {evt.event_timestamp ? formatDateTime(evt.event_timestamp) : ""}
                          </td>
                          <td style={{ maxWidth: "480px", wordBreak: "break-word" }}>{evt.result}</td>
                        </tr>
                      ))}
                      {auditEvents.length === 0 && (
                        <tr>
                          <td colSpan={5} style={{ textAlign: "center", color: "#64748b", padding: "20px" }}>
                            No audit events found.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
