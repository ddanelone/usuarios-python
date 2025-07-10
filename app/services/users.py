# services/users.py
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from app.core.security import verify_password
from app.db.models.user import User
from app.schemas.user import UserCreate
from datetime import datetime
from app.crud.user import (
    get_user_by_email as crud_get_user_by_email,
    get_user_by_dni,
    get_users,
    get_user,
    create_user as crud_create_user,
    update_user,
    delete_user
)
from app.schemas.user import UserCreate, UserUpdate
from app.services.messaging import publish_email_message

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    normalized_email = email.lower()
    result = await db.execute(select(User).where(User.email == normalized_email))
    return result.scalars().first()

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    user_data = user_in.model_dump(exclude={"password"})
    user_data["email"] = user_data["email"].lower()
    hashed_password = pwd_context.hash(user_in.password)
    user_data["password_hash"] = hashed_password
    db_user = User(**user_data)
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
    except IntegrityError as e:
        await db.rollback()
        detail = "Error al crear usuario."
        if "dni" in str(e.orig).lower():
            detail = "DNI ya registrado."
        elif "email" in str(e.orig).lower():
            detail = "Email ya registrado."
        raise HTTPException(status_code=400, detail=detail)
    return db_user

async def update_user_password(
    db: AsyncSession,
    user_id: int,
    current_password: str,
    new_password: str
):
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not verify_password(current_password, user.password_hash):
        raise HTTPException(status_code=403, detail="Contraseña actual incorrecta")

    user.password_hash = pwd_context.hash(new_password)
    user.last_password_change = datetime.utcnow()  # ⬅️ acá se actualiza el campo
    db.add(user)
    await db.commit()
    await db.refresh(user)

async def update_user_password_by_email(db: AsyncSession, email: str, new_password: str):
    user = await get_user_by_email(db, email.lower())  # 👈 normalizar
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    hashed_new = pwd_context.hash(new_password)
    user.password_hash = hashed_new  # type: ignore
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def create_user_service(db: AsyncSession, user_in: UserCreate) -> User:
    existing_email = await crud_get_user_by_email(db, user_in.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    existing_dni = await get_user_by_dni(db, user_in.dni)
    if existing_dni:
        raise HTTPException(status_code=400, detail="DNI already registered")
     
    await publish_email_message(to=user_in.email, token="", type_="welcome_email")

    return await crud_create_user(db, user_in)

async def get_users_service(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[User]:
    return await get_users(db, skip, limit)

async def get_user_service(db: AsyncSession, user_id: int) -> User | None:
    return await get_user(db, user_id)

async def update_user_service(db: AsyncSession, user_id: int, user_in: UserUpdate) -> User | None:
    return await update_user(db, user_id, user_in)

async def delete_user_service(db: AsyncSession, user_id: int) -> bool:
    return await delete_user(db, user_id)
