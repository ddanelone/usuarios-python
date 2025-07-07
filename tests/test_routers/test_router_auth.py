# tests/test_routers/test_router_auth.py
from datetime import date
import pytest

from app.schemas.user import UserCreate, UserRole
from app.crud.user import create_user
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

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
