from datetime import date
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from app.schemas.user import UserRead, UserRole
import sys
import os
from app.main import app
from app.core.dependencies import get_current_user
from app.services.email import send_welcome_email


sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Usuario simulado
fake_user = UserRead(
    id=1,
    nombres="Ana",
    apellidos="Gómez",
    dni="87654321",
    fecha_nacimiento=date(1995, 5, 5),
    email="ana@example.com",
    rol=UserRole.DOCENTE,
)

# Mock de autenticación
@pytest.fixture(autouse=True)
def override_current_user():
    async def _mocked_current_user():
        return fake_user
    app.dependency_overrides[get_current_user] = _mocked_current_user
    yield
    app.dependency_overrides.clear()

@pytest.mark.asyncio
@patch("app.services.users.get_users", new_callable=AsyncMock)
async def test_read_users_unit(mock_get_users):
    mock_get_users.return_value = [fake_user]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/users/", headers={"Authorization": "Bearer token"})

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json()[0]["email"] == "ana@example.com"

@patch("app.services.email.send_welcome_email", new_callable=AsyncMock)
@patch("app.services.users.crud_create_user", new_callable=AsyncMock)
@patch("app.services.users.get_user_by_dni", new_callable=AsyncMock)
@patch("app.services.users.crud_get_user_by_email", new_callable=AsyncMock)
async def test_create_user_unit(mock_get_email, mock_get_dni, mock_create_user, mock_send_email):
    mock_get_email.return_value = None
    mock_get_dni.return_value = None
    mock_create_user.return_value = fake_user
    mock_send_email.return_value = None  # ← este es el mock real que necesitás

    payload = {
        "nombres": "Ana",
        "apellidos": "Gómez",
        "dni": "87654321",
        "fecha_nacimiento": "1995-05-05",
        "email": "ana@example.com",
        "password": "Password123",
        "rol": "DOCENTE"
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/users/", json=payload)

    assert response.status_code == 201
    assert response.json()["email"] == fake_user.email


@pytest.mark.asyncio
@patch("app.services.users.get_user", new_callable=AsyncMock)
async def test_read_user_success_unit(mock_get_user):
    mock_get_user.return_value = fake_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/users/1", headers={"Authorization": "Bearer token"})

    assert response.status_code == 200
    assert response.json()["email"] == fake_user.email

@pytest.mark.asyncio
@patch("app.services.users.get_user", new_callable=AsyncMock)
async def test_read_user_not_found_unit(mock_get_user):
    mock_get_user.return_value = None
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/users/999", headers={"Authorization": "Bearer token"})

    assert response.status_code == 404

@pytest.mark.asyncio
@patch("app.services.users.update_user", new_callable=AsyncMock)
async def test_update_user_unit(mock_update_user):
    mock_update_user.return_value = fake_user
    payload = {"nombres": "NuevoNombre", "email": "nuevo@example.com"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put("/users/1", json=payload, headers={"Authorization": "Bearer token"})

    assert response.status_code == 200
    assert response.json()["nombres"] == "Ana"

@pytest.mark.asyncio
@patch("app.services.users.delete_user", new_callable=AsyncMock)
async def test_delete_user_unit(mock_delete_user):
    mock_delete_user.return_value = True

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete("/users/1", headers={"Authorization": "Bearer token"})

    assert response.status_code == 204

@pytest.mark.asyncio
@patch("app.routers.user.update_user_password", new_callable=AsyncMock)  # cambia esto
@patch("app.services.users.get_user", new_callable=AsyncMock)
async def test_update_password_unit(mock_get_user, mock_update_password):
    mock_get_user.return_value = fake_user
    mock_update_password.return_value = None

    payload = {"current_password": "OldPass123", "new_password": "NewPass456"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch("/users/1/password", json=payload, headers={"Authorization": "Bearer token"})

    assert response.status_code == 204
