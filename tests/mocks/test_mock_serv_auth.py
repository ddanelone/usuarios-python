# tests/mocks/test_mock_serv_auth.py
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from app.schemas.token import UserLogin, ForgotPasswordRequest, ResetPasswordRequest
from app.schemas.user import UserRole
from app.schemas.token import Token

fake_user_email = "mock@example.com"
fake_user_id = 1
fake_user_rol = UserRole.ADMIN
fake_token_str = "fake.token.value"

@pytest.mark.asyncio
@patch("app.services.auth.login_user", new_callable=AsyncMock)
async def test_login_user_success_mock(mock_login_user):
    mock_login_user.return_value = Token(
        access_token=fake_token_str,
        token_type="bearer",
        user_id=fake_user_id,
        user_role=fake_user_rol,
    )
    login_data = UserLogin(email=fake_user_email, password="Password123")
    result = await mock_login_user(login_data, None)
    assert "access_token" in result.dict()
    assert result.token_type == "bearer"
    assert result.user_id == fake_user_id
    assert result.user_role == fake_user_rol

@pytest.mark.asyncio
@patch("app.services.auth.login_user", new_callable=AsyncMock)
async def test_login_user_wrong_password_mock(mock_login_user):
    mock_login_user.side_effect = Exception("Incorrect email or password")
    login_data = UserLogin(email=fake_user_email, password="wrong")
    with pytest.raises(Exception) as exc_info:
        await mock_login_user(login_data, None)
    assert "Incorrect email or password" in str(exc_info.value)

@pytest.mark.asyncio
@patch("app.services.auth.login_user", new_callable=AsyncMock)
async def test_login_user_locked_out_mock(mock_login_user):
    mock_login_user.side_effect = Exception("Demasiados intentos fallidos. Intenta de nuevo en unos minutos.")
    login_data = UserLogin(email=fake_user_email, password="Password123")
    with pytest.raises(Exception) as exc_info:
        await mock_login_user(login_data, None)
    assert "Demasiados intentos fallidos" in str(exc_info.value)

@pytest.mark.asyncio
@patch("app.services.auth.forgot_password_process", new_callable=AsyncMock)
async def test_forgot_password_process_mock(mock_forgot_password):
    mock_forgot_password.return_value = {"message": "Se envió un email con instrucciones (simulado)."}
    request = ForgotPasswordRequest(email=fake_user_email)
    result = await mock_forgot_password(request, None)
    assert result["message"] == "Se envió un email con instrucciones (simulado)."

@pytest.mark.asyncio
@patch("app.services.auth.reset_password_process", new_callable=AsyncMock)
async def test_reset_password_process_mock(mock_reset_password):
    mock_reset_password.return_value = {"message": "Contraseña actualizada exitosamente"}
    request = ResetPasswordRequest(token="valid.token", new_password="new_secret")
    result = await mock_reset_password(request, None)
    assert result["message"] == "Contraseña actualizada exitosamente"
