# tests/test_routers/test_router_users.py
import pytest
from httpx import AsyncClient
from datetime import date

from app.core.security import create_access_token
from app.schemas.user import UserCreate, UserRole
from app.crud.user import create_user
from unittest.mock import AsyncMock, patch

from app.services.users import create_user_service

async def create_test_user_in_db(db, **kwargs):
    user_data = {
        "nombres": "Test",
        "apellidos": "User",
        "dni": "99999999",
        "fecha_nacimiento": date(1990, 1, 1),
        "email": "testuser@example.com",
        "password": "Password123",
        "rol": UserRole.ALUMNO
    }
    user_data.update(kwargs)
    user_in = UserCreate(**user_data)
    return await create_user(db, user_in)

def get_auth_header(email: str):
    token = create_access_token({"sub": email})
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
@patch("app.services.users.publish_email_message", new_callable=AsyncMock)
async def test_create_user_service_success(mock_publish, async_db):
    user_in = UserCreate(
        nombres="Juan",
        apellidos="Test",
        dni="30123456",
        fecha_nacimiento=date(1990, 1, 1),
        email="juan@test.com",
        password="Segura123",
        rol=UserRole.ALUMNO,
    )

    new_user = await create_user_service(async_db, user_in)

    assert new_user.email == user_in.email
    assert new_user.dni == user_in.dni
    mock_publish.assert_called_once_with(
        to=user_in.email,
        token="",
        type_="welcome_email",
    )
    
@pytest.mark.asyncio
async def test_read_users_success(async_client: AsyncClient, async_db):
    admin = await create_test_user_in_db(async_db, email="admin@example.com", dni="12345670", rol=UserRole.ADMIN)
    headers = get_auth_header(admin.email)
    response = await async_client.get("/users/", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_read_users_unauthorized(async_client: AsyncClient):
    response = await async_client.get("/users/")
    assert response.status_code == 401 or response.status_code == 403

@pytest.mark.asyncio
async def test_read_user_success(async_client: AsyncClient, async_db):
    admin = await create_test_user_in_db(async_db, email="admin@example.com", dni="12345671", rol=UserRole.ADMIN)
    user = await create_test_user_in_db(async_db, email="readme@example.com", dni="12345672")
    headers = get_auth_header(admin.email)

    response = await async_client.get(f"/users/{user.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == user.email

@pytest.mark.asyncio
async def test_read_user_not_found(async_client: AsyncClient, async_db):
    admin = await create_test_user_in_db(async_db, email="admin@example.com", dni="31234567", rol=UserRole.ADMIN)
    headers = get_auth_header(admin.email)

    response = await async_client.get("/users/99999", headers=headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_user_self_success(async_client: AsyncClient, async_db):
    user = await create_test_user_in_db(async_db, email="self@example.com", dni="41234567")
    headers = get_auth_header(user.email)
    payload = {"nombres": "NuevoNombre", "email": "nuevo@example.com"}

    response = await async_client.put(f"/users/{user.id}", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["nombres"] == "NuevoNombre"

@pytest.mark.asyncio
async def test_update_user_no_permission(async_client: AsyncClient, async_db):
    user1 = await create_test_user_in_db(async_db, email="user1@example.com", dni="51234567")
    user2 = await create_test_user_in_db(async_db, email="user2@example.com", dni="61234567")
    headers = get_auth_header(user1.email)

    response = await async_client.put(f"/users/{user2.id}", json={"nombres": "Hacker"}, headers=headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_delete_user_by_admin(async_client: AsyncClient, async_db):
    admin = await create_test_user_in_db(async_db, email="admin@example.com", dni="71234567", rol=UserRole.ADMIN)
    user = await create_test_user_in_db(async_db, email="victim@example.com", dni="81234567")
    headers = get_auth_header(admin.email)

    response = await async_client.delete(f"/users/{user.id}", headers=headers)
    assert response.status_code == 204

@pytest.mark.asyncio
async def test_admin_cannot_delete_self(async_client: AsyncClient, async_db):
    admin = await create_test_user_in_db(async_db, email="admin@example.com", dni="91234567", rol=UserRole.ADMIN)
    headers = get_auth_header(admin.email)

    response = await async_client.delete(f"/users/{admin.id}", headers=headers)
    assert response.status_code == 403
    assert "no puede eliminarse" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_user_cannot_delete_other_user(async_client: AsyncClient, async_db):
    user1 = await create_test_user_in_db(async_db, email="user1@example.com", dni="10123456")
    user2 = await create_test_user_in_db(async_db, email="user2@example.com", dni="11123456")
    headers = get_auth_header(user1.email)

    response = await async_client.delete(f"/users/{user2.id}", headers=headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_user_can_delete_self(async_client: AsyncClient, async_db):
    user = await create_test_user_in_db(async_db, email="deleteme@example.com", dni="12123456")
    headers = get_auth_header(user.email)

    response = await async_client.delete(f"/users/{user.id}", headers=headers)
    assert response.status_code == 204

@pytest.mark.asyncio
async def test_update_password_success(async_client: AsyncClient, async_db):
    user = await create_test_user_in_db(async_db, email="passuser@example.com", dni="13123456", password="OldPass123")
    headers = get_auth_header(user.email)
    payload = {"current_password": "OldPass123", "new_password": "NewPass456"}

    response = await async_client.patch(f"/users/{user.id}/password", json=payload, headers=headers)
    assert response.status_code == 204

@pytest.mark.asyncio
async def test_update_password_wrong_current(async_client: AsyncClient, async_db):
    user = await create_test_user_in_db(async_db, email="wrongpass@example.com", dni="14123456", password="OldPass123")
    headers = get_auth_header(user.email)
    payload = {"current_password": "WrongPass", "new_password": "NewPass456"}

    response = await async_client.patch(f"/users/{user.id}/password", json=payload, headers=headers)
    assert response.status_code == 403
    assert "incorrecta" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_password_not_self(async_client: AsyncClient, async_db):
    user1 = await create_test_user_in_db(async_db, email="yo@example.com", dni="15123456", password="MiPass123")
    user2 = await create_test_user_in_db(async_db, email="otro@example.com", dni="16123456")
    headers = get_auth_header(user1.email)
    payload = {"current_password": "MiPass123", "new_password": "Nuevo123"}

    response = await async_client.patch(f"/users/{user2.id}/password", json=payload, headers=headers)
    assert response.status_code == 403
