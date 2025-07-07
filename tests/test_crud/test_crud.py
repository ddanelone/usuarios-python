# test_crud.py
import pytest
from datetime import date
from app.crud.user import (
    get_user,
    get_user_by_email,
    get_user_by_dni,
    get_users,
    create_user,
    update_user,
    delete_user,
)
from app.schemas.user import UserCreate, UserUpdate, UserRole
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import IntegrityError

@pytest.mark.asyncio
async def test_create_and_get_user(async_db):
    user_in = UserCreate(
        nombres="Test",
        apellidos="User",
        dni="55555555",
        fecha_nacimiento=date(1985, 5, 15),
        email="TestUser@Example.Com",
        password="Secret123",
        rol=UserRole.ALUMNO,
    )
    user = await create_user(async_db, user_in)

    # Comprobar creación
    assert user.id is not None
    assert user.email == "testuser@example.com"  # debe estar normalizado
    assert user.dni == "55555555"

    # get_user
    user_by_id = await get_user(async_db, user.id)
    assert user_by_id is not None
    assert user_by_id.id == user.id

    # get_user_by_email
    user_by_email = await get_user_by_email(async_db, "TESTUSER@example.com")
    assert user_by_email is not None
    assert user_by_email.id == user.id

    # get_user_by_dni
    user_by_dni = await get_user_by_dni(async_db, "55555555")
    assert user_by_dni is not None
    assert user_by_dni.id == user.id

@pytest.mark.asyncio
async def test_get_users_with_pagination(async_db):
    # crear varios usuarios
    users_to_create = [
        UserCreate(
            nombres=f"User{i}",
            apellidos="Test",
            dni=f"1111111{i}",
            fecha_nacimiento=date(1990, 1, 1),
            email=f"user{i}@example.com",
            password="Password123",
            rol=UserRole.ALUMNO,
        )
        for i in range(5)
    ]
    for user_in in users_to_create:
        await create_user(async_db, user_in)

    users = await get_users(async_db, skip=1, limit=3)
    assert len(users) == 3
    assert all(hasattr(u, "email") for u in users)

@pytest.mark.asyncio
async def test_update_user(async_db):
    user_in = UserCreate(
        nombres="Update",
        apellidos="Test",
        dni="99999999",
        fecha_nacimiento=date(1995, 6, 30),
        email="update@example.com",
        password="Password123",
        rol=UserRole.ALUMNO,
    )
    user = await create_user(async_db, user_in)

    user_update = UserUpdate(
        nombres="Updated",
        email="updated@example.com"
    )
    updated_user = await update_user(async_db, user.id, user_update)

    assert updated_user is not None
    assert updated_user.nombres == "Updated"
    assert updated_user.email == "updated@example.com"  # Normalizado a minúsculas
    assert updated_user.dni == "99999999"  # sin cambios

@pytest.mark.asyncio
async def test_delete_user(async_db):
    user_in = UserCreate(
        nombres="Delete",
        apellidos="Test",
        dni="88888888",
        fecha_nacimiento=date(1980, 3, 3),
        email="delete@example.com",
        password="Password123",
        rol=UserRole.ALUMNO,
    )
    user = await create_user(async_db, user_in)

    deleted = await delete_user(async_db, user.id)
    assert deleted is True

    # verificar que ya no existe
    deleted_user = await get_user(async_db, user.id)
    assert deleted_user is None

# CASOS INFELICES

@pytest.mark.asyncio
async def test_create_user_duplicate_email(async_db):
    user_in = UserCreate(
        nombres="User",
        apellidos="DupEmail",
        dni="12312312",
        fecha_nacimiento=date(1990, 1, 1),
        email="dup@example.com",
        password="Password123",
        rol=UserRole.ALUMNO,
    )
    await create_user(async_db, user_in)

    user_in_dup = UserCreate(
        nombres="Other",
        apellidos="User",
        dni="12312313",  # distinto DNI
        fecha_nacimiento=date(1990, 1, 1),
        email="dup@example.com",  # mismo email
        password="Password123",
        rol=UserRole.ADMIN,
    )

    with pytest.raises(IntegrityError) as exc_info:
        await create_user(async_db, user_in_dup)
    assert "UNIQUE constraint failed" in str(exc_info.value)

@pytest.mark.asyncio
async def test_create_user_duplicate_dni(async_db):
    user_in = UserCreate(
        nombres="User",
        apellidos="DupDNI",
        dni="45645645",
        fecha_nacimiento=date(1990, 1, 1),
        email="user1@example.com",
        password="Password123",
        rol=UserRole.ALUMNO,
    )
    await create_user(async_db, user_in)

    user_in_dup = UserCreate(
        nombres="Other",
        apellidos="User",
        dni="45645645",  # mismo DNI
        fecha_nacimiento=date(1992, 2, 2),
        email="user2@example.com",  # distinto email
        password="Password123",
        rol=UserRole.ADMIN,
    )

    with pytest.raises(IntegrityError) as exc_info:
        await create_user(async_db, user_in_dup)
    assert "UNIQUE constraint failed" in str(exc_info.value)

@pytest.mark.asyncio
async def test_update_nonexistent_user(async_db):
    user_update = UserUpdate(nombres="Ghost")
    updated_user = await update_user(async_db, user_id=9999, user_in=user_update)
    assert updated_user is None

@pytest.mark.asyncio
async def test_delete_nonexistent_user(async_db):
    deleted = await delete_user(async_db, user_id=9999)
    assert deleted is False
