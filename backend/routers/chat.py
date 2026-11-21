from fastapi import APIRouter
from schemas.chat import ChatRequest
from services.langgraph_workflow import run_langgraph_chat

router = APIRouter(tags=["Chat"])

@router.post("/api/chat")
def chat_endpoint(request: ChatRequest):
    result = run_langgraph_chat(
        user_message=request.message,
        employee_id=request.employee_id,
        conversation_history=request.history or []
    )
    return result

