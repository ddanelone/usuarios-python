# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.token import UserLogin, Token,  ForgotPasswordRequest, ResetPasswordRequest
from app.crud.user import get_user_by_email
from app.core.security import verify_password, create_access_token, create_password_reset_token, verify_password_reset_token
from app.db.session import get_session
from typing import cast
import logging

from app.services.users import update_user_password_by_email


router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=Token)
async def login(form_data: UserLogin, db: AsyncSession = Depends(get_session)):
    user = await get_user_by_email(db, form_data.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
   
    hashed_password = cast(str, user.password_hash)
    if not verify_password(form_data.password, hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    token_data = {
        "sub": user.email,
        "user_id": user.id,
        "user_role": user.rol
    }
    access_token = create_access_token(data=token_data)
    
    logging.info(f"[LOGIN] Usuario {user.email} inició sesión exitosamente.")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "user_role": user.rol
    }

@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_session)
):
    user = await get_user_by_email(db, request.email.lower())
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no registrado")
    
    token = create_password_reset_token(user.email) # type: ignore

    # Enviar por email (en producción). Por ahora lo mostramos por consola:
    logging.warning(f"[RECUPERAR CONTRASEÑA] Token para {user.email}: {token}")

    return {"message": "Se envió un email con instrucciones (simulado)."}


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_session)
):
    email = verify_password_reset_token(request.token)
    if not email:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")
    
    await update_user_password_by_email(db, email, request.new_password)
    return {"message": "Contraseña actualizada exitosamente"}
