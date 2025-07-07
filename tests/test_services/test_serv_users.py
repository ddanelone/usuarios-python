# test_serv_users.py
from datetime import date
import pytest
from app.services.users import (
    get_user_by_email,
    create_user,
    update_user_password,
    update_user_password_by_email
)
from app.schemas.user import UserCreate, UserRole
from app.core.security import verify_password

@pytest.mark.asyncio
async def test_get_user_by_email(async_db, test_user):
    user = await get_user_by_email(async_db, test_user.email)
    assert user is not None
    assert user.email == test_user.email

@pytest.mark.asyncio
async def test_create_user_success(async_db):
    user_data = UserCreate(
        nombres="Login",
        apellidos="Tester",
        dni="98765432",
        fecha_nacimiento=date(1990, 1, 1),
        email="login@example.com",
        password="Password123",
        rol=UserRole.ADMIN
    )
    user = await create_user(async_db, user_data)
    assert user.email == "login@example.com"
    assert user.dni == "98765432"

@pytest.mark.asyncio
async def test_create_user_duplicate_email(async_db, test_user):
    user_data = UserCreate(
        nombres="Login",
        apellidos="Tester",
        dni="98765432",
        fecha_nacimiento=date(1990, 1, 1),
        email=test_user.email,  # 💡 mismo email para provocar duplicado
        password="Password123",
        rol=UserRole.ADMIN
    )
    with pytest.raises(Exception) as exc_info:
        await create_user(async_db, user_data)
    assert "Email ya registrado" in str(exc_info.value)

@pytest.mark.asyncio
async def test_update_user_password_success(async_db, test_user):
    await update_user_password(
        async_db,
        test_user.id,
        "Password123",  # Cambiado aquí
        "new_secret"
    )
    await async_db.refresh(test_user)
    assert verify_password("new_secret", test_user.password_hash)

@pytest.mark.asyncio
async def test_update_user_password_wrong_current(async_db, test_user):
    with pytest.raises(Exception) as exc_info:
        await update_user_password(
            async_db,
            test_user.id,
            "wrong",
            "new_secret"
        )
    assert "Contraseña actual incorrecta" in str(exc_info.value)

@pytest.mark.asyncio
async def test_update_user_password_by_email(async_db, test_user):
    await update_user_password_by_email(
        async_db,
        test_user.email,
        "new_secret"
    )
    await async_db.refresh(test_user)
    assert verify_password("new_secret", test_user.password_hash)
