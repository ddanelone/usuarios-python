from app.models.user import User
from app.schemas.user import UserCreate
from app.db.session import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

async def create_user(db: AsyncSession, user_in: UserCreate):
    hashed_password = pwd_context.hash(user_in.password)  # si manejas passwords
    db_user = User(**user_in.dict(), hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
