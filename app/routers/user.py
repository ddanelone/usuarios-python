# routers/user.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import cast 
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate, UserUpdatePassword
from app.db.session import get_session
from app.core.dependencies import get_current_user
from app.services.users import (
    create_user_service,
    get_users_service,
    get_user_service,
    update_user_password,
    update_user_service,
    delete_user_service,
)

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(user_in: UserCreate, db: AsyncSession = Depends(get_session)):
    user = await create_user_service(db, user_in)
    logging.info(f"[ALTA USUARIO] Se creó el usuario {user.email} con rol {user.rol}.")
    return user

@router.get("/", response_model=List[UserRead])
async def read_users(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    return await get_users_service(db, skip, limit)

@router.get("/{user_id}", response_model=UserRead)
async def read_user(user_id: int, db: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    user = await get_user_service(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserRead)
async def update_user_endpoint(
    user_id: int,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: UserRead = Depends(get_current_user)
):
    if current_user.id != user_id and current_user.rol.upper() != "ADMIN":
        raise HTTPException(status_code=403, detail="No tienes permisos para actualizar a otros usuarios")

    user = await update_user_service(db, user_id, user_in)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: UserRead = Depends(get_current_user)
):
    if current_user.rol.upper() == "ADMIN":
        if user_id == current_user.id:
            raise HTTPException(status_code=403, detail="Un administrador no puede eliminarse a sí mismo")
    else:
        if user_id != current_user.id:
            raise HTTPException(status_code=403, detail="No tienes permisos para eliminar a otros usuarios")

    success = await delete_user_service(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    logging.warning(f"[BAJA USUARIO] Usuario {user_id} eliminado por {current_user.email}.")

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

    logging.info(f"[PASSWORD] Usuario {current_user.email} actualizó su contraseña.")

    return None

