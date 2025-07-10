# tests/integration/test_int_router_user.py

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from unittest.mock import patch

@pytest.mark.asyncio
async def test_create_user_success(async_client: AsyncClient):
    user_data = {
        "nombres": "Ana",
        "apellidos": "García",
        "dni": "98765432",
        "fecha_nacimiento": "1995-06-20",
        "email": "ana@example.com",
        "password": "Password123",
        "rol": "ALUMNO"
    }
    with patch("app.services.users.publish_email_message") as mock_publish:
        mock_publish.return_value = None
        response = await async_client.post("/users/", json=user_data)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["rol"] == user_data["rol"]
    assert "id" in data
    mock_publish.assert_called_once()

@pytest.mark.asyncio
async def test_get_users_requires_auth(async_client: AsyncClient):
    response = await async_client.get("/users/")
    assert response.status_code in [401, 403]

@pytest.mark.asyncio
async def test_read_user_authenticated(async_client: AsyncClient, test_user):
    login_resp = await async_client.post("/auth/login", json={
        "email": test_user.email,
        "password": "Password123"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.get(f"/users/{test_user.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == test_user.email

@pytest.mark.asyncio
async def test_update_user_unauthorized(async_client: AsyncClient, test_user):
    response = await async_client.put(f"/users/{test_user.id}", json={"nombres": "NuevoNombre"})
    assert response.status_code in [401, 403]

@pytest.mark.asyncio
async def test_change_password_success(async_client: AsyncClient, test_user):
    login_resp = await async_client.post("/auth/login", json={
        "email": test_user.email,
        "password": "Password123"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.patch(f"/users/{test_user.id}/password", headers=headers, json={
        "current_password": "Password123",
        "new_password": "NewPassword123"
    })
    assert response.status_code == 204

    login_resp = await async_client.post("/auth/login", json={
        "email": test_user.email,
        "password": "NewPassword123"
    })
    assert login_resp.status_code == 200

@pytest.mark.asyncio
async def test_create_user_duplicate_email(async_client: AsyncClient, test_user):
    user_data = {
        "nombres": "Repetido",
        "apellidos": "Email",
        "dni": "00000111",
        "fecha_nacimiento": "2000-01-01",
        "email": test_user.email,
        "password": "Password123",
        "rol": "ALUMNO"
    }
    with patch("app.services.users.publish_email_message"):
        response = await async_client.post("/users/", json=user_data)
    assert response.status_code == 400
    assert "email" in response.text.lower()

@pytest.mark.asyncio
async def test_create_user_duplicate_dni(async_client: AsyncClient, test_user):
    user_data = {
        "nombres": "Repetido",
        "apellidos": "DNI",
        "dni": test_user.dni,
        "fecha_nacimiento": "2000-01-01",
        "email": "nuevo@example.com",
        "password": "Password123",
        "rol": "ALUMNO"
    }
    with patch("app.services.users.publish_email_message"):
        response = await async_client.post("/users/", json=user_data)
    assert response.status_code == 400
    assert "dni" in response.text.lower()

@pytest.mark.asyncio
async def test_update_user_by_admin(async_client: AsyncClient, async_db: AsyncSession):
    admin_data = {
        "nombres": "Admin",
        "apellidos": "User",
        "dni": "55555555",
        "fecha_nacimiento": "1980-01-01",
        "email": "admin@example.com",
        "password": "Password123",
        "rol": "ADMIN"
    }
    with patch("app.services.users.publish_email_message"):
        await async_client.post("/users/", json=admin_data)

    login_resp = await async_client.post("/auth/login", json={
        "email": admin_data["email"],
        "password": admin_data["password"]
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    other_data = {
        "nombres": "Pedro",
        "apellidos": "Picapiedra",
        "dni": "22222333",
        "fecha_nacimiento": "1990-05-05",
        "email": "pedro@example.com",
        "password": "Password123",
        "rol": "ALUMNO"
    }
    with patch("app.services.users.publish_email_message"):
        create_resp = await async_client.post("/users/", json=other_data)

    user_id = create_resp.json()["id"]

    update_resp = await async_client.put(f"/users/{user_id}", json={"nombres": "Peter"}, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["nombres"] == "Peter"

@pytest.mark.asyncio
async def test_delete_user_self_allowed(async_client: AsyncClient):
    user_data = {
        "nombres": "Beto",
        "apellidos": "Borges",
        "dni": "11223344",
        "fecha_nacimiento": "1992-02-02",
        "email": "beto@example.com",
        "password": "Password123",
        "rol": "ALUMNO"
    }
    with patch("app.services.users.publish_email_message"):
        create = await async_client.post("/users/", json=user_data)
    user_id = create.json()["id"]

    login = await async_client.post("/auth/login", json={
        "email": user_data["email"],
        "password": user_data["password"]
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    delete = await async_client.delete(f"/users/{user_id}", headers=headers)
    assert delete.status_code == 204

@pytest.mark.asyncio
async def test_delete_user_by_admin_forbidden_self(async_client: AsyncClient):
    with patch("app.services.users.publish_email_message"):
        await async_client.post("/users/", json={
            "nombres": "Admin",
            "apellidos": "User",
            "dni": "99999999",
            "fecha_nacimiento": "1980-01-01",
            "email": "admin@example.com",
            "password": "Password123",
            "rol": "ADMIN"
        })

    login_resp = await async_client.post("/auth/login", json={
        "email": "admin@example.com",
        "password": "Password123"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    whoami = await async_client.get("/users/", headers=headers)
    admin_id = [u for u in whoami.json() if u["email"] == "admin@example.com"][0]["id"]

    response = await async_client.delete(f"/users/{admin_id}", headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Un administrador no puede eliminarse a sí mismo"

@pytest.mark.asyncio
async def test_delete_user_not_found(async_client: AsyncClient, async_db: AsyncSession):
    from app.schemas.user import UserCreate, UserRole
    from app.crud.user import create_user

    await create_user(async_db, UserCreate(
        nombres="Admin",
        apellidos="Test",
        dni="12345679",
        fecha_nacimiento=date(1990, 1, 1),
        email="admin@example.com",
        password="Password123",
        rol=UserRole.ADMIN
    ))

    login = await async_client.post("/auth/login", json={
        "email": "admin@example.com",
        "password": "Password123"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.delete("/users/9999", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

@pytest.mark.asyncio
async def test_change_password_wrong_current(async_client: AsyncClient, test_user):
    login = await async_client.post("/auth/login", json={
        "email": test_user.email,
        "password": "Password123"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.patch(f"/users/{test_user.id}/password", headers=headers, json={
        "current_password": "WrongPass123",
        "new_password": "OtraPassword123"
    })
    assert response.status_code == 403
    assert response.json()["detail"] == "Contraseña actual incorrecta"

@pytest.mark.asyncio
async def test_change_password_invalid_new(async_client: AsyncClient, test_user):
    login = await async_client.post("/auth/login", json={
        "email": test_user.email,
        "password": "Password123"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.patch(f"/users/{test_user.id}/password", headers=headers, json={
        "current_password": "Password123",
        "new_password": "123"
    })
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_update_user_not_found(async_client: AsyncClient, async_db: AsyncSession):
    from app.schemas.user import UserCreate, UserRole
    from app.crud.user import create_user

    await create_user(async_db, UserCreate(
        nombres="Admin",
        apellidos="UpdateTest",
        dni="88888888",
        fecha_nacimiento=date(1990, 1, 1),
        email="admin-updater@example.com",
        password="Password123",
        rol=UserRole.ADMIN
    ))

    login = await async_client.post("/auth/login", json={
        "email": "admin-updater@example.com",
        "password": "Password123"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.put("/users/9999", headers=headers, json={"nombres": "Nuevo"})
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

@pytest.mark.asyncio
async def test_get_user_unauthorized(async_client: AsyncClient):
    response = await async_client.get("/users/1")
    assert response.status_code in [401, 403]
