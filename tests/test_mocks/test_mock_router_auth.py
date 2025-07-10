# tests/mocks/test_mock_router_auth.py
from datetime import date
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from app.schemas.user import UserRead, UserRole
from app.schemas.token import Token
from app.main import app

fake_user = UserRead(
    id=1,
    nombres="Mock",
    apellidos="User",
    dni="12345678",
    fecha_nacimiento=date(1990,1,1),
    email="mock@example.com",
    rol=UserRole.ADMIN,
)

fake_token = "fake.token.value"

@pytest.mark.asyncio
@patch("app.routers.auth.login_user", new_callable=AsyncMock)
async def test_login_success_mock(mock_login_user):
    # Mock login_user para que retorne un Token con valores fakes
    mock_login_user.return_value = Token(
        access_token=fake_token,
        token_type="bearer",
        user_id=fake_user.id,
        user_role=fake_user.rol,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/auth/login", json={"email": fake_user.email, "password": "fakepass"})

    assert response.status_code == 200
    json_data = response.json()
    assert json_data["access_token"] == fake_token
    assert json_data["token_type"] == "bearer"
    assert json_data["user_id"] == fake_user.id
    assert json_data["user_role"] == fake_user.rol.value

@pytest.mark.asyncio
@patch("app.routers.auth.forgot_password_process", new_callable=AsyncMock)
async def test_forgot_password_success_mock(mock_forgot_password):
    mock_forgot_password.return_value = {"message": "Se envió un email con instrucciones (simulado)."}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/auth/forgot-password", json={"email": fake_user.email})

    assert response.status_code == 200
    assert "se envió un email" in response.json()["message"].lower()

@pytest.mark.asyncio
@patch("app.routers.auth.reset_password_process", new_callable=AsyncMock)
async def test_reset_password_success_mock(mock_reset_password):
    mock_reset_password.return_value = {"message": "Contraseña actualizada exitosamente"}

    payload = {"token": "valid.token", "new_password": "NewPass123"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/auth/reset-password", json=payload)

    assert response.status_code == 200
    assert "contraseña actualizada" in response.json()["message"].lower()

@pytest.mark.asyncio
@patch("app.routers.auth.login_user", new_callable=AsyncMock)
async def test_login_wrong_credentials_mock(mock_login_user):
    # Simulamos que el login falla lanzando HTTPException con 401
    from fastapi import HTTPException
    mock_login_user.side_effect = HTTPException(status_code=401, detail="Incorrect email or password")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/auth/login", json={"email": "wrong@example.com", "password": "badpass"})

    assert response.status_code == 401
    assert "incorrect email or password" in response.json()["detail"].lower()

@pytest.mark.asyncio
@patch("app.routers.auth.forgot_password_process", new_callable=AsyncMock)
async def test_forgot_password_nonexistent_email_mock(mock_forgot_password):
    from fastapi import HTTPException
    mock_forgot_password.side_effect = HTTPException(status_code=404, detail="Usuario no registrado")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/auth/forgot-password", json={"email": "noexiste@example.com"})

    assert response.status_code == 404
    assert "usuario no registrado" in response.json()["detail"].lower()

@pytest.mark.asyncio
@patch("app.routers.auth.reset_password_process", new_callable=AsyncMock)
async def test_reset_password_invalid_token_mock(mock_reset_password):
    from fastapi import HTTPException
    mock_reset_password.side_effect = HTTPException(status_code=400, detail="Token inválido o expirado")

    payload = {"token": "invalid.token.value", "new_password": "Whatever123"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/auth/reset-password", json=payload)

    assert response.status_code == 400
    assert "token inválido" in response.json()["detail"].lower()
