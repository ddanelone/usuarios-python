# test_serv_auth.py
import pytest
from datetime import datetime
from app.services.auth import login_user, forgot_password_process, reset_password_process
from app.schemas.token import UserLogin, ForgotPasswordRequest, ResetPasswordRequest
from app.core.security import create_password_reset_token, verify_password
from unittest.mock import patch, ANY
from app.services.auth import forgot_password_process



@pytest.mark.asyncio
async def test_login_user_success(async_db, test_user):
    login_data = UserLogin(email=test_user.email, password="Password123")  # Cambiado aquí
    result = await login_user(login_data, async_db)
    assert "access_token" in result.dict()
    assert result.token_type == "bearer"
    
@pytest.mark.asyncio
async def test_login_user_wrong_password(async_db, test_user):
    login_data = UserLogin(email=test_user.email, password="wrong")
    with pytest.raises(Exception) as exc_info:
        await login_user(login_data, async_db)
    assert "Incorrect email or password" in str(exc_info.value)

@pytest.mark.asyncio
async def test_login_user_locked_out(async_db, test_user):
    test_user.failed_login_attempts = 3
    # asignar datetime native (sin tzinfo) para que coincida con datetime.utcnow() en el service
    test_user.last_failed_login = datetime.utcnow()  
    async_db.add(test_user)
    await async_db.commit()

    login_data = UserLogin(email=test_user.email, password="Password123")
    with pytest.raises(Exception) as exc_info:
        await login_user(login_data, async_db)
    assert "Demasiados intentos fallidos" in str(exc_info.value)

@pytest.mark.asyncio
@patch("app.services.auth.send_reset_email")
async def test_forgot_password_process(mock_send_email, async_db, test_user):
    mock_send_email.return_value = None

    request = ForgotPasswordRequest(email=test_user.email)
    result = await forgot_password_process(request, async_db)

    assert "email" in request.model_dump()
    assert result["message"].lower().startswith("se envió un email")
    mock_send_email.assert_called_once_with(test_user.email, ANY)


@pytest.mark.asyncio
async def test_reset_password_process(async_db, test_user):
    token = create_password_reset_token(test_user.email)
    request = ResetPasswordRequest(token=token, new_password="new_secret")
    result = await reset_password_process(request, async_db)
    assert result["message"] == "Contraseña actualizada exitosamente"

    await async_db.refresh(test_user)
    assert verify_password("new_secret", test_user.password_hash)
