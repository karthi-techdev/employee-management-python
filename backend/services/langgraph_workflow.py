import os
import re
import json
from typing import TypedDict
from dotenv import load_dotenv
from groq import Groq
from langgraph.graph import StateGraph, END

from core.config import local_session
from repository.employees import EmployeeRepository
from repository.audits import AuditRepository
from mcp_server import (
    search_hr_policies as mcp_search_policies,
    get_my_employee_profile as mcp_get_profile,
    get_leave_balance as mcp_get_balance,
    get_leave_request_status as mcp_get_request_status,
    create_leave_request as mcp_create_request,
    get_pending_leave_requests as mcp_get_pending_requests
)

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("LLM_MODEL", "qwen/qwen3.8-27b")

client = Groq(api_key=GROQ_API_KEY)

employee_repository = EmployeeRepository()
audit_repository = AuditRepository()

# Tool schemas for Groq
MCP_TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "search_hr_policies",
            "description": "Search approved company HR policies, guidelines, and manuals (including onboarding checklists, leave rules, attendance, code of conduct, and holidays) in the knowledge base with citations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The HR question, policy topic, or onboarding keyword to search"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_my_employee_profile",
            "description": "Retrieve profile information (name, department, role, status). By default retrieves for the signed-in user, or for a specific employee when target_employee (name or ID) is specified (Managers, HR Staff, and Admins can view other employees' profiles).",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_employee": {
                        "type": "string",
                        "description": "Optional employee name or ID (e.g. 'Arun Kumar', '1'). Leave empty to get signed-in user's profile."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_leave_balance",
            "description": "Retrieve current leave balances (Casual, Sick). By default retrieves for the signed-in user, or for a specific employee when target_employee (name or ID) is specified. Managers, HR Staff, and Admins are authorized to view team members' and employees' leave balances.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_employee": {
                        "type": "string",
                        "description": "Optional employee name or employee ID to look up (e.g. 'Arun Kumar' or '1'). Leave empty to check signed-in user's own balance."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_leave_request_status",
            "description": "Check the status of a previously submitted leave request.",
            "parameters": {
                "type": "object",
                "properties": {
                    "request_id": {"type": "integer", "description": "Leave request ID"}
                },
                "required": ["request_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_leave_request",
            "description": "Create a pending leave request for manager approval. AI never approves leaves autonomously.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "End date YYYY-MM-DD"},
                    "leave_type": {"type": "string", "description": "Casual or Sick"}
                },
                "required": ["start_date", "end_date", "leave_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_pending_leave_requests",
            "description": "Get all pending employee leave requests requiring review and approval. Available to Managers, HR Staff, and Admins.",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

# 1. Define LangGraph State
class HRWorkflowState(TypedDict):
    messages: list
    employee_id: int
    citations: list
    tool_calls: list
    final_reply: str

def get_tool_calls_from_msg(msg):
    if isinstance(msg, dict):
        return msg.get("tool_calls") or []
    if hasattr(msg, "tool_calls") and msg.tool_calls:
        return msg.tool_calls
    return []

def extract_tool_info(tool_call):
    if isinstance(tool_call, dict):
        tool_id = tool_call.get("id", "call_1")
        func = tool_call.get("function", {})
        name = func.get("name", "")
        raw_args = func.get("arguments", "{}")
    else:
        tool_id = tool_call.id
        name = tool_call.function.name
        raw_args = tool_call.function.arguments
    try:
        args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
    except Exception:
        args = {}
    return tool_id, name, args

def parse_failed_generation(failed_gen: str):
    """Robustly parse Qwen's raw XML or JSON tool call from Groq failed_generation."""
    func_name = ""
    params = {}

    # Case A: JSON object inside <tool_call>
    json_match = re.search(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", failed_gen, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group(1))
            if "name" in parsed:
                return parsed["name"], parsed.get("arguments", {})
        except Exception:
            pass

    # Extract function name: <function=NAME>
    func_match = re.search(r"<function=([a-zA-Z0-9_]+)>", failed_gen)
    if func_match:
        func_name = func_match.group(1)

    # Case B: JSON inside <parameters>...</parameter> or <parameters>...</parameters>
    json_params_match = re.search(r"<parameters?>\s*(\{.*?\})\s*</parameters?>", failed_gen, re.DOTALL)
    if json_params_match:
        try:
            params = json.loads(json_params_match.group(1))
        except Exception:
            pass

    # Case C: Individual <parameter=key>value</parameter> tags
    if not params:
        raw_params = dict(re.findall(r"<parameter=([a-zA-Z0-9_ ]+)>\s*(.*?)\s*</parameter>", failed_gen, re.DOTALL))
        params = {k.strip().replace(" ", "_"): v.strip() for k, v in raw_params.items()}

    # If called as <function=tool> with <parameter=tool_name>
    if func_name == "tool" and "tool_name" in params:
        func_name = params.pop("tool_name").strip()

    return func_name, params

# 2. Node: Call LLM (Groq Qwen)
def call_agent_node(state: HRWorkflowState):
    messages = state["messages"]

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=MCP_TOOLS_SPEC,
            tool_choice="auto",
            temperature=0.2
        )
        assistant_message = response.choices[0].message
        messages.append(assistant_message)
        final_text = assistant_message.content or ""
        return {
            "messages": messages,
            "final_reply": final_text
        }
    except Exception as e:
        err_msg = str(e)
        failed_gen = ""
        if hasattr(e, "body") and isinstance(e.body, dict):
            failed_gen = e.body.get("error", {}).get("failed_generation", "")
        if not failed_gen and "failed_generation" in err_msg:
            match = re.search(r"'failed_generation':\s*['\"](.*?)['\"]", err_msg, re.DOTALL)
            if match:
                failed_gen = match.group(1).encode().decode("unicode_escape", errors="ignore")

        if failed_gen:
            func_name, params = parse_failed_generation(failed_gen)

            if func_name:
                assistant_message = {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_recovered_1",
                            "type": "function",
                            "function": {
                                "name": func_name,
                                "arguments": json.dumps(params)
                            }
                        }
                    ]
                }
                messages.append(assistant_message)
                return {
                    "messages": messages,
                    "final_reply": ""
                }

        raise e

# 3. Conditional Edge: Decide if tools are needed or finish
def should_continue(state: HRWorkflowState):
    last_message = state["messages"][-1]
    tool_calls = get_tool_calls_from_msg(last_message)
    if tool_calls:
        return "tools"
    return "end"

# 4. Node: Execute Tools via FastMCP
def call_tools_node(state: HRWorkflowState):
    messages = state["messages"]
    last_message = messages[-1]
    employee_id = state["employee_id"]

    citations = list(state.get("citations", []))
    executed_tools = list(state.get("tool_calls", []))

    tool_calls = get_tool_calls_from_msg(last_message)
    for tool_call in tool_calls:
        tool_id, name, args = extract_tool_info(tool_call)

        result = {}
        if name == "search_hr_policies":
            passages = mcp_search_policies(args.get("query", ""))
            result = {"policy_passages": passages}
            for p in passages:
                citations.append(p.get("citation", ""))

        elif name == "get_my_employee_profile":
            target = (
                args.get("target_employee")
                or args.get("target employee")
                or args.get("employee_name")
                or args.get("employee_id")
                or args.get("employee")
                or args.get("name")
                or ""
            )
            result = mcp_get_profile(employee_id, str(target))

        elif name == "get_leave_balance":
            target = (
                args.get("target_employee")
                or args.get("target employee")
                or args.get("employee_name")
                or args.get("employee_id")
                or args.get("employee")
                or args.get("name")
                or ""
            )
            result = mcp_get_balance(employee_id, str(target))

        elif name == "get_leave_request_status":
            req_id = args.get("request_id")
            result = mcp_get_request_status(req_id, employee_id)

        elif name == "create_leave_request":
            start_date = args.get("start_date")
            end_date = args.get("end_date")
            leave_type = args.get("leave_type")
            result = mcp_create_request(employee_id, start_date, end_date, leave_type)

        elif name == "get_pending_leave_requests":
            result = mcp_get_pending_requests(employee_id)

        executed_tools.append({
            "tool": name,
            "arguments": args,
            "result": result
        })

        messages.append({
            "role": "tool",
            "tool_call_id": tool_id,
            "content": json.dumps(result, default=str)
        })

    return {
        "messages": messages,
        "citations": citations,
        "tool_calls": executed_tools
    }

# 5. Build and compile the LangGraph workflow
def build_hr_workflow():
    graph = StateGraph(HRWorkflowState)

    graph.add_node("agent", call_agent_node)
    graph.add_node("tools", call_tools_node)

    graph.set_entry_point("agent")

    graph.add_conditional_edges("agent", should_continue, {
        "tools": "tools",
        "end": END
    })
    graph.add_edge("tools", "agent")

    return graph.compile()

hr_agent_workflow = build_hr_workflow()

# 6. Main handler function invoked by the chat endpoint
def run_langgraph_chat(user_message: str, employee_id: int = 1, conversation_history: list = None):
    if conversation_history is None:
        conversation_history = []

    db = local_session()
    try:
        user = employee_repository.get_by_id(employee_id, db)
        if user:
            user_name = user.name
            user_role = user.role
            user_dept = user.department
        else:
            user_name = "Employee"
            user_role = "Employee"
            user_dept = "General"

        is_approver = user_role in ["Manager", "HR Staff", "Admin"]

        if is_approver:
            role_instructions = f"""You are speaking with {user_name}, who is an authorized {user_role} (Employee ID: {employee_id}) in the {user_dept} department.
As a {user_role}, {user_name} is authorized to manage their team and review employee records, leave balances, and leave requests:
- Authorized access: As a {user_role}, {user_name} has full authority to view leave balances, profiles, and pending requests for employees and team members.
- When {user_name} asks about an employee's leave balance (for example: "Show me the available leave balance of Arun Kumar (Employee)", "What is Arun Kumar's leave balance?", or "Check leave balance for [name]"), you MUST call get_leave_balance with target_employee="[name or ID]".
- Present the employee's available leave balances (Casual, Sick) clearly and professionally in a neat markdown table or summary showing the employee's name, role, department, and available balances as of date.
- When {user_name} asks about leave approvals, pending leave requests, who asked for leave, or who applied for leave (for example: 'Who are all asked for leave approval?', 'Show me pending leaves', 'Who applied for leave?'), you MUST call get_pending_leave_requests.
- Present the pending requests in a neat, professional markdown table with columns: Request ID, Employee Name, Department, Leave Type, Dates, and Status.
- Mention that they can approve or reject these requests in the Manager Approvals section of the console.
- Note: AI cannot approve or reject leaves autonomously.
- If they ask for general company policies, use search_hr_policies and cite documents.
"""
        else:
            role_instructions = f"""You are speaking with {user_name}, who is an Employee (Employee ID: {employee_id}) in the {user_dept} department.
Strict Data Privacy Restrictions:
- The user can ONLY view their OWN private records (own leave balance via `get_leave_balance`, own profile via `get_my_employee_profile`, own submitted requests via `get_leave_request_status`).
- If the user asks for other employees' private leave balances, salary, or personal requests (e.g., 'What is Priya's balance?' or 'Who applied for leave?'), you MUST politely refuse:
  "Access restricted: I cannot disclose private information or leave balances for other employees. I can only assist you with your own records."
- Leave requests are created in 'pending' status for manager approval.
- Ground policy answers in evidence from `search_hr_policies` and cite documents.
"""

        system_prompt = f"""You are the AI Employee HR Assistant for the CoreHR platform.
{role_instructions}

STRICT SCOPE RESTRICTION: You MUST ONLY answer queries related to the CoreHR platform functionality:
- Employee leave management (balances, requests, approvals)
- HR policy documents and company guidelines
- Employee profile information
- Audit logs and compliance tracking
- Onboarding and company procedures

If a user asks about ANYTHING outside this scope (general knowledge, coding, math, weather, news, personal advice, other software, etc.), you MUST politely refuse with:
"I'm the CoreHR AI Assistant and can only help with platform-related queries such as leave management, HR policies, employee records, and company procedures. I cannot assist with general questions or topics outside the CoreHR platform."

Be helpful, structured, concise, and professional within your authorized scope.
Greet or address {user_name} warmly.
"""

        initial_messages = [{"role": "system", "content": system_prompt}]

        for item in conversation_history:
            initial_messages.append({"role": item.get("role"), "content": item.get("content")})

        initial_messages.append({"role": "user", "content": user_message})

        initial_state: HRWorkflowState = {
            "messages": initial_messages,
            "employee_id": employee_id,
            "citations": [],
            "tool_calls": [],
            "final_reply": ""
        }

        final_state = hr_agent_workflow.invoke(initial_state)

        unique_citations = []
        for c in final_state.get("citations", []):
            if c and c not in unique_citations:
                unique_citations.append(c)

        tools_used = [t["tool"] for t in final_state.get("tool_calls", [])]

        audit_repository.log_event(
            actor_id=employee_id,
            action="LANGGRAPH_CHAT",
            result=f"{user_name} ({user_role}): {user_message[:50]} | Tools: {tools_used}",
            trace_id="chat",
            db=db
        )

        return {
            "reply": final_state.get("final_reply", ""),
            "citations": unique_citations,
            "tool_calls": final_state.get("tool_calls", []),
            "employee_id": employee_id
        }
    finally:
        db.close()
