# tests/test_routers/test_router_auth.py
from datetime import date
import pytest
from app.schemas.user import UserCreate, UserRole
from app.crud.user import create_user
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token
from unittest.mock import AsyncMock, patch
from unittest.mock import ANY


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, async_db: AsyncSession):
    user_data = UserCreate(
        nombres="Login",
        apellidos="Tester",
        dni="98765432",
        fecha_nacimiento=date(1990, 1, 1),
        email="login@example.com",
        password="Password123",
        rol=UserRole.ADMIN,
    )

    await create_user(async_db, user_data)

    login_payload = {
        "email": "login@example.com",
        "password": "Password123"
    }

    response = await async_client.post("/auth/login", json=login_payload)

    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user_id"] > 0
    assert data["user_role"] == "ADMIN"

@pytest.mark.asyncio
@patch("app.services.auth.publish_email_message", new_callable=AsyncMock)
async def test_forgot_password_success(mock_publish_email, async_client: AsyncClient, async_db: AsyncSession):
    mock_publish_email.return_value = "mock-correlation-id"

    user_data = UserCreate(
        nombres="Forgot",
        apellidos="User",
        dni="22222222",
        fecha_nacimiento=date(1991, 2, 2),
        email="forgot@example.com",
        password="Forgot123",
        rol=UserRole.ALUMNO,
    )
    await create_user(async_db, user_data)

    response = await async_client.post("/auth/forgot-password", json={"email": "forgot@example.com"})

    assert response.status_code == 200
    assert response.json()["message"].lower().startswith("se envió un email con instrucciones.")

    mock_publish_email.assert_called_once_with(
        to="forgot@example.com",
        token=ANY,
        type_="reset_password"
    )

@pytest.mark.asyncio
async def test_forgot_password_nonexistent_email(async_client: AsyncClient):
    response = await async_client.post("/auth/forgot-password", json={"email": "noexiste@example.com"})
    assert response.status_code == 404
    assert "usuario no registrado" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_reset_password_success(async_client: AsyncClient, async_db: AsyncSession):
    user_data = UserCreate(
        nombres="Reset",
        apellidos="User",
        dni="33333333",
        fecha_nacimiento=date(1989, 3, 3),
        email="reset@example.com",
        password="OldPass123",
        rol=UserRole.ALUMNO,
    )
    user = await create_user(async_db, user_data)

    token = create_access_token({"sub": user.email, "scope": "password_reset"})

    payload = {
        "token": token,
        "new_password": "NewSecure123"
    }

    response = await async_client.post("/auth/reset-password", json=payload)
    assert response.status_code == 200
    assert "contraseña actualizada exitosamente" in response.json()["message"].lower()

@pytest.mark.asyncio
async def test_reset_password_invalid_token(async_client: AsyncClient):
    payload = {
        "token": "invalid.token.value",
        "new_password": "Whatever123"
    }
    response = await async_client.post("/auth/reset-password", json=payload)
    assert response.status_code == 400
    assert "token inválido" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_login_wrong_credentials(async_client: AsyncClient, async_db: AsyncSession):
    user_data = UserCreate(
        nombres="Wrong",
        apellidos="Login",
        dni="44444444",
        fecha_nacimiento=date(1992, 4, 4),
        email="wronglogin@example.com",
        password="Correct123",
        rol=UserRole.ALUMNO,
    )
    await create_user(async_db, user_data)

    login_payload = {
        "email": "wronglogin@example.com",
        "password": "IncorrectPassword"
    }

    response = await async_client.post("/auth/login", json=login_payload)
    assert response.status_code == 401
    assert "incorrect email or password" in response.json()["detail"].lower()


