from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.auth import router as auth_router
from routers.employees import router as employee_router
from routers.leaves import router as leave_router
from routers.admin import router as admin_router
from routers.chat import router as chat_router

app = FastAPI(
    title="AI Employee HR Assistant",
    description="Beginner-friendly, production-ready AI HR Assistant API",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(auth_router)
app.include_router(employee_router)
app.include_router(leave_router)
app.include_router(chat_router)
app.include_router(admin_router)

@app.get("/")
def home():
    return {"message": "AI HR Assistant is running!"}

@app.get("/health")
def health():
    return {"status": "healthy"}
