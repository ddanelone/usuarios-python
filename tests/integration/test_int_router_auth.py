# tests/integration/test_int_router_auth.py
import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from jose import jwt
from unittest.mock import patch, ANY
from app.core.security import SECRET_KEY, ALGORITHM
from app.db.models.user import User


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, test_user: User):
    payload = {"email": test_user.email, "password": "Password123"}
    response = await async_client.post("/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user_id"] == test_user.id
    assert data["user_role"] == test_user.rol


@pytest.mark.asyncio
async def test_login_invalid_password(async_client: AsyncClient, test_user: User):
    payload = {"email": test_user.email, "password": "WrongPass"}
    response = await async_client.post("/auth/login", json=payload)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.text


@pytest.mark.asyncio
async def test_login_unregistered_user(async_client: AsyncClient):
    payload = {"email": "noexiste@example.com", "password": "whatever"}
    response = await async_client.post("/auth/login", json=payload)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.text


@pytest.mark.asyncio
@patch("app.services.auth.send_reset_email")
async def test_forgot_password_valid_email(mock_send_email, async_client: AsyncClient, test_user: User):
    mock_send_email.return_value = None

    payload = {"email": test_user.email}
    response = await async_client.post("/auth/forgot-password", json=payload)

    assert response.status_code == 200
    assert "email con instrucciones" in response.text.lower()
    mock_send_email.assert_called_once_with(test_user.email, ANY)


@pytest.mark.asyncio
async def test_forgot_password_unknown_email(async_client: AsyncClient):
    payload = {"email": "no@existe.com"}
    response = await async_client.post("/auth/forgot-password", json=payload)
    assert response.status_code == 404
    assert "Usuario no registrado" in response.text


@pytest.mark.asyncio
async def test_reset_password_valid_token(async_client: AsyncClient, test_user: User):
    token = jwt.encode(
        {
            "sub": test_user.email,
            "exp": datetime.utcnow() + timedelta(minutes=5),
            "scope": "password_reset"
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    payload = {"token": token, "new_password": "NewPassword123"}
    response = await async_client.post("/auth/reset-password", json=payload)
    assert response.status_code == 200
    assert "Contraseña actualizada" in response.text


@pytest.mark.asyncio
async def test_reset_password_invalid_token(async_client: AsyncClient):
    fake_token = jwt.encode(
        {
            "sub": "alguien@example.com",
            "exp": datetime.utcnow() - timedelta(minutes=1),  # Expirado
            "scope": "password_reset"
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    payload = {"token": fake_token, "new_password": "NewPassword123"}
    response = await async_client.post("/auth/reset-password", json=payload)
    assert response.status_code == 400
    assert "Token inválido" in response.text or "expirado" in response.text.lower()
