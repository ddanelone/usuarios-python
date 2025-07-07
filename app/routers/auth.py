# app/router/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.token import UserLogin, Token, ForgotPasswordRequest, ResetPasswordRequest
from app.db.session import get_session
from app.services.auth import (
    login_user,
    forgot_password_process,
    reset_password_process,
)
from app.services.users import update_user_password_by_email  # si lo usás en servicios

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=Token)
async def login(form_data: UserLogin, db: AsyncSession = Depends(get_session)):
    return await login_user(form_data, db)

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: AsyncSession = Depends(get_session)):
    return await forgot_password_process(request, db)

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: AsyncSession = Depends(get_session)):
    return await reset_password_process(request, db)
