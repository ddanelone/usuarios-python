# routers/user.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate, UserUpdatePassword
from app.crud.user import get_user, get_user_by_email, get_users, create_user, update_user, delete_user
from app.db.session import get_session
from app.core.dependencies import get_current_user
from app.services.users import update_user_password

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(user_in: UserCreate, db: AsyncSession = Depends(get_session)):
    existing = await get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await create_user(db, user_in)

@router.get("/", response_model=List[UserRead])
async def read_users(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    return await get_users(db, skip, limit)

@router.get("/{user_id}", response_model=UserRead)
async def read_user(user_id: int, db: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserRead)
async def update_user_endpoint(
    user_id: int,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your own profile")
    user = await update_user(db, user_id, user_in)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own profile")
    success = await delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return None

@router.patch("/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
async def update_password_endpoint(
    user_id: int,
    passwords: UserUpdatePassword,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sólo puedes cambiar tu propia contraseña")
    await update_user_password(db, user_id, passwords.current_password, passwords.new_password)
    return None
