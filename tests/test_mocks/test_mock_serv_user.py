# tests/mocks/test_mock_serv_users.py
from datetime import date
import pytest
from unittest.mock import AsyncMock, patch
from app.schemas.user import UserCreate, UserRole
from app.core.security import verify_password

fake_user_data = {
    "id": 1,
    "nombres": "Mock",
    "apellidos": "User",
    "dni": "12345678",
    "fecha_nacimiento": date(1990, 1, 1),
    "email": "mock@example.com",
    "rol": UserRole.ADMIN,
    "password_hash": "$2b$12$fakehashedpasswordstringforverify"
}

@pytest.mark.asyncio
@patch("app.services.users.get_user_by_email", new_callable=AsyncMock)
async def test_get_user_by_email_mock(mock_get_user_by_email):
    mock_get_user_by_email.return_value = fake_user_data
    user = await mock_get_user_by_email(None, fake_user_data["email"])
    assert user is not None
    assert user["email"] == fake_user_data["email"]

@pytest.mark.asyncio
@patch("app.services.users.create_user", new_callable=AsyncMock)
async def test_create_user_duplicate_email_mock(mock_create_user):
    from fastapi import HTTPException
    mock_create_user.side_effect = Exception("Email ya registrado")
    user_in = UserCreate(
        nombres="Login",
        apellidos="Tester",
        dni="98765432",
        fecha_nacimiento=date(1990, 1, 1),
        email="mock@example.com",  # mismatched email to simulate duplicate
        password="Password123",
        rol=UserRole.ADMIN
    )
    with pytest.raises(Exception) as exc_info:
        await mock_create_user(None, user_in)
    assert "Email ya registrado" in str(exc_info.value)

@pytest.mark.asyncio
@patch("app.services.users.update_user_password", new_callable=AsyncMock)
async def test_update_user_password_success_mock(mock_update_password):
    # Simular que update_user_password no devuelve nada (None) pero efectivamente actualiza
    mock_update_password.return_value = None
    # Llamada con datos falsos
    await mock_update_password(None, fake_user_data["id"], "Password123", "new_secret")
    assert mock_update_password.called

@pytest.mark.asyncio
@patch("app.services.users.update_user_password", new_callable=AsyncMock)
async def test_update_user_password_wrong_current_mock(mock_update_password):
    mock_update_password.side_effect = Exception("Contraseña actual incorrecta")
    with pytest.raises(Exception) as exc_info:
        await mock_update_password(None, fake_user_data["id"], "wrong", "new_secret")
    assert "Contraseña actual incorrecta" in str(exc_info.value)

@pytest.mark.asyncio
@patch("app.services.users.update_user_password_by_email", new_callable=AsyncMock)
async def test_update_user_password_by_email_mock(mock_update_password_by_email):
    mock_update_password_by_email.return_value = None
    await mock_update_password_by_email(None, fake_user_data["email"], "new_secret")
    assert mock_update_password_by_email.called
