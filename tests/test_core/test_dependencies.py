# test_core/test_dependencies.py
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from unittest.mock import AsyncMock
from app.core import dependencies
from app.schemas.user import UserRead
from datetime import date
from types import SimpleNamespace

@pytest.mark.asyncio
async def test_get_current_user_valid_token(monkeypatch, async_db):
    monkeypatch.setattr(dependencies, "decode_access_token", lambda token: {"sub": "user@example.com"})

    dummy_user = SimpleNamespace(
        id=1,
        nombres="Juan",
        apellidos="Pérez",
        dni="12345678",
        fecha_nacimiento=date(1990, 1, 1),
        email="user@example.com",
        rol="ALUMNO",
    )
    monkeypatch.setattr(dependencies, "get_user_by_email", AsyncMock(return_value=dummy_user))

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="fake_token")

    user = await dependencies.get_current_user(creds, async_db)
    assert isinstance(user, UserRead)
    
@pytest.mark.asyncio
async def test_get_current_user_invalid_token(monkeypatch, async_db):
    monkeypatch.setattr(dependencies, "decode_access_token", lambda token: None)

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad_token")

    with pytest.raises(HTTPException) as excinfo:
        await dependencies.get_current_user(creds, async_db)
    assert excinfo.value.status_code == 401

@pytest.mark.asyncio
async def test_get_current_user_no_email(monkeypatch, async_db):
    monkeypatch.setattr(dependencies, "decode_access_token", lambda token: {})

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")

    with pytest.raises(HTTPException) as excinfo:
        await dependencies.get_current_user(creds, async_db)
    assert excinfo.value.status_code == 401

@pytest.mark.asyncio
async def test_get_current_user_user_not_found(monkeypatch, async_db):
    monkeypatch.setattr(dependencies, "decode_access_token", lambda token: {"sub": "missing@example.com"})
    monkeypatch.setattr(dependencies, "get_user_by_email", AsyncMock(return_value=None))

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")

    with pytest.raises(HTTPException) as excinfo:
        await dependencies.get_current_user(creds, async_db)
    assert excinfo.value.status_code == 401
