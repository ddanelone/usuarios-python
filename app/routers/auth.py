# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.token import UserLogin, Token
from app.crud.user import get_user_by_email
from app.core.security import verify_password, create_access_token
from app.db.session import get_session
from typing import cast

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

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "user_role": user.rol
    }
