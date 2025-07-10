# app/services/auth.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.user import get_user_by_email
from app.core.security import (
    verify_password,
    create_access_token,
    create_password_reset_token,
    verify_password_reset_token,
)
from fastapi import HTTPException, status
from typing import cast
import logging
from datetime import datetime, timedelta
import os
from app.services.users import update_user_password_by_email
from app.services.messaging import publish_email_message


MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", 3))
LOCKOUT_TIME = timedelta(minutes=int(os.getenv("LOCKOUT_MINUTES", 15)))


async def login_user(form_data, db: AsyncSession):
    user = await get_user_by_email(db, form_data.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    # Chequeo de intentos fallidos previos
    if getattr(user, "failed_login_attempts", 0) >= MAX_ATTEMPTS:
        last_fail = getattr(user, "last_failed_login", None)
        if last_fail and datetime.utcnow() - last_fail < LOCKOUT_TIME:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Demasiados intentos fallidos. Intenta de nuevo en unos minutos."
            )
        else:
            # Se venció el castigo
            user.failed_login_attempts = 0
            user.last_failed_login = None

    # Verificar contraseña
    hashed_password = cast(str, user.password_hash)
    if not verify_password(form_data.password, hashed_password):
        user.failed_login_attempts = getattr(user, "failed_login_attempts", 0) + 1
        user.last_failed_login = datetime.utcnow()
        db.add(user)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    # Login exitoso → resetear contador y actualizar login
    user.failed_login_attempts = 0
    user.last_failed_login = None
    user.last_login = datetime.utcnow()
    db.add(user)
    await db.commit()

    logging.info(f"[LOGIN] Usuario {user.email} inició sesión exitosamente a las {user.last_login}.")

    token_data = {
        "sub": user.email,
        "user_id": user.id,
        "user_role": user.rol
    }
    access_token = create_access_token(data=token_data)

    from app.schemas.token import Token
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        user_role=user.rol
    )

async def forgot_password_process(request, db: AsyncSession):
    user = await get_user_by_email(db, request.email.lower())
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no registrado")

    token = create_password_reset_token(user.email)

    await publish_email_message(to=user.email, token=token, type_="reset_password")

    return {"message": "Se envió un email con instrucciones."}



async def reset_password_process(request, db: AsyncSession):
    email = verify_password_reset_token(request.token)
    if not email:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")

    await update_user_password_by_email(db, email, request.new_password)
    return {"message": "Contraseña actualizada exitosamente"}
