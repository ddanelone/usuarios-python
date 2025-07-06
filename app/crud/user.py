from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from passlib.context import CryptContext
from app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def get_user(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[User]:
    result = await db.execute(select(User).offset(skip).limit(limit))
    return list(result.scalars().all())

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    # Obtener dict de datos, excluyendo password
    data = user_in.model_dump(exclude={"password"})

    # Convertir rol enum a string
    # data["rol"] = data["rol"].value

    # Generar hash de la contraseña
    hashed_password = pwd_context.hash(user_in.password)

    # Añadir el hash a los datos
    data["password_hash"] = hashed_password

    # Crear el objeto User con los datos correctos
    user = User(**data)

    # Agregar, commit y refresh
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def update_user(db: AsyncSession, user_id: int, user_in: UserUpdate) -> User | None:
    values = user_in.model_dump(exclude_unset=True)
   # if "rol" in values and values["rol"] is not None:
   #     values["rol"] = values["rol"].value  # Convertir enum a string si está presente

    stmt = (
        update(User)
        .where(User.id == user_id)
        .values(**values)
        .execution_options(synchronize_session="fetch")
    )
    await db.execute(stmt)
    await db.commit()
    return await get_user(db, user_id)

async def delete_user(db: AsyncSession, user_id: int) -> bool:
    stmt = delete(User).where(User.id == user_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0
