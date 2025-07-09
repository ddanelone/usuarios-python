# routers/user.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import cast 
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate, UserUpdatePassword
from app.crud.user import get_user, get_user_by_dni, get_user_by_email, get_users, create_user, update_user, delete_user
from app.db.session import get_session
from app.core.dependencies import get_current_user
from app.services.email import send_welcome_email
from app.services.users import update_user_password

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(user_in: UserCreate, db: AsyncSession = Depends(get_session)):
    # Validación de email duplicado
    existing_email = await get_user_by_email(db, user_in.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Validación de DNI duplicado
    existing_dni = await get_user_by_dni(db, user_in.dni)
    if existing_dni:
        raise HTTPException(status_code=400, detail="DNI already registered")

    # Crear usuario
    user = await create_user(db, user_in)

    # Enviar mail de bienvenida
    await send_welcome_email(user.email, user.nombres)

    logging.info(f"[ALTA USUARIO] Se creó el usuario {user.email} con rol {user.rol}.")

    return user


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
    current_user: UserRead = Depends(get_current_user)   # <--- Pydantic UserRead
):
    # Ya current_user.id es int y current_user.rol es str, podés usar directo
    if current_user.id != user_id and current_user.rol.upper() != "ADMIN":
        raise HTTPException(status_code=403, detail="No tienes permisos para actualizar a otros usuarios")

    user = await update_user(db, user_id, user_in)
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
            raise HTTPException(
                status_code=403,
                detail="Un administrador no puede eliminarse a sí mismo"
            )
        # Admin puede eliminar a otros
    else:
        # No admin solo puede eliminarse a sí mismo
        if user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para eliminar a otros usuarios"
            )
    
    success = await delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    logging.warning(f"[BAJA USUARIO] Usuario {user_id} eliminado por {current_user.email}.")

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

    logging.info(f"[PASSWORD] Usuario {current_user.email} actualizó su contraseña.")

    return None

