from pydantic import BaseModel, EmailStr, Field
from datetime import date
from enum import Enum

class UserRole(str, Enum):
    ADMINISTRADOR = "ADMINISTRADOR"
    DOCENTE = "DOCENTE"
    ALUMNO = "ALUMNO"
    INVITADO = "INVITADO"


class UserBase(BaseModel):
    nombres: str = Field(..., min_length=1)
    apellidos: str = Field(..., min_length=1)
    dni: str = Field(..., min_length=7, max_length=10)  # Ajusta según formato
    fecha_nacimiento: date
    email: EmailStr
    rol: UserRole

class UserCreate(UserBase):
    pass  # Igual que UserBase, pero se puede ampliar luego

class UserRead(UserBase):
    id: int

    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    nombres: str | None = None
    apellidos: str | None = None
    dni: str | None = None
    fecha_nacimiento: date | None = None
    email: EmailStr | None = None
    rol: UserRole | None = None
