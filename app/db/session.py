# db/models/session.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Cargar variables desde .env
load_dotenv()

# Validar que DATABASE_URL exista
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("Falta la variable DATABASE_URL en el entorno")

# Crear el motor asíncrono
engine = create_async_engine(DATABASE_URL, echo=True)

# Crear el sessionmaker con AsyncSession
async_session = async_sessionmaker(
    bind=engine,
    expire_on_commit=False
)


# Dependency para inyectar la sesión en endpoints
async def get_session() -> AsyncSession: # type: ignore
    async with async_session() as session: # type: ignore
        yield session #type: ignore
