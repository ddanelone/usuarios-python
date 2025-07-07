# tests/test_routers/test_router_users.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_user(async_client: AsyncClient):
    payload = {
        "nombres": "Ana",
        "apellidos": "Gómez",
        "dni": "87654321",
        "fecha_nacimiento": "1995-05-05",
        "email": "ana@example.com",
        "password": "Password123",
        "rol": "DOCENTE"
    }
    response = await async_client.post("/users/", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["email"] == "ana@example.com"
