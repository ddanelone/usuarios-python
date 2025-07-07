# conftest.py
import pytest_asyncio
from datetime import date
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.db.base import Base
from app.db.models.user import User
from app.db.session import get_session
from app.schemas.user import UserCreate, UserRole
from app.crud.user import create_user

from httpx import AsyncClient, ASGITransport

DATABASE_TEST_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    DATABASE_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

@pytest_asyncio.fixture(scope="function", autouse=True)
async def prepare_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def async_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session

async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

@pytest_asyncio.fixture
async def test_user(async_db: AsyncSession) -> User:
    user_in = UserCreate(
        nombres="Juan",
        apellidos="Pérez",
        dni="12345678",
        fecha_nacimiento=date(1990, 1, 1),
        email="juan@example.com",
        password="Password123",
        rol=UserRole.ALUMNO,
    )
    user = await create_user(async_db, user_in)
    return user

@pytest_asyncio.fixture(scope="module")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
