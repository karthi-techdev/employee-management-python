from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from schemas.auth import LoginRequest
from core.db import get_db_connection
from services.auth_service import AuthService

auth_service = AuthService()
router = APIRouter(tags=["Authentication"])

@router.post("/api/login")
def login(credentials: LoginRequest, db: Session = Depends(get_db_connection)):
    return auth_service.login(credentials, db)

@router.post("/login")
def login_alias(credentials: LoginRequest, db: Session = Depends(get_db_connection)):
    return auth_service.login(credentials, db)

