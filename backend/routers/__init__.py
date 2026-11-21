from routers.auth import router as auth_router
from routers.employees import router as employee_router
from routers.leaves import router as leave_router
from routers.admin import router as admin_router
from routers.chat import router as chat_router

__all__ = [
    "auth_router",
    "employee_router",
    "leave_router",
    "admin_router",
    "chat_router"
]

