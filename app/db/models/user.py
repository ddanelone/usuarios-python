from sqlalchemy import Enum as PgEnum
from app.schemas.user import UserRole
from app.db.base import Base
from sqlalchemy import Column, Integer, String, Date, DateTime
from datetime import datetime


rol = Column(PgEnum(UserRole, name="rolusuario", create_type=True), nullable=False)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nombres = Column(String, nullable=False)
    apellidos = Column(String, nullable=False)
    dni = Column(String, unique=True, nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    rol = Column(PgEnum(UserRole, name="rolusuario", create_type=True), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
