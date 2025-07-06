# services/users.py
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError

from app.crud.user import get_user
from app.db.models.user import User
from app.schemas.user import UserCreate

from typing import cast

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

async def update_user_password(db: AsyncSession, user_id: int, current_password: str, new_password: str):
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # cast para que PyLance entienda que es un str (valor de la columna)
    password_hash = cast(str, user.password_hash)

    if not pwd_context.verify(current_password, password_hash):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")

    hashed_new = pwd_context.hash(new_password)

    # Asignar el hash nuevo
    user.password_hash = hashed_new  #type: ignore

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