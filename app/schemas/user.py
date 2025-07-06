## app/schemas/user.py

from pydantic import BaseModel, EmailStr, Field, validator
from datetime import date
from enum import Enum
import re

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    DOCENTE = "DOCENTE"
    ALUMNO = "ALUMNO"
    INVITADO = "INVITADO"

class UserBase(BaseModel):
    nombres: str = Field(..., min_length=1)
    apellidos: str = Field(..., min_length=1)
    dni: str = Field(..., min_length=7, max_length=10)
    fecha_nacimiento: date
    email: EmailStr
    rol: UserRole

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=16)

    @validator("password")
    def validate_password(cls, v):
        if not re.search(r"[A-Z]", v):
            raise ValueError("La contraseña debe contener al menos una letra mayúscula.")
        if not re.search(r"[a-z]", v):
            raise ValueError("La contraseña debe contener al menos una letra minúscula.")
        if not re.search(r"\d", v):
            raise ValueError("La contraseña debe contener al menos un número.")
        return v

class UserRead(UserBase):
    id: int

    class Config:
        from_attributes = True  # Cambiado para Pydantic v2

class UserUpdate(BaseModel):
    nombres: str | None = None
    apellidos: str | None = None
    dni: str | None = None
    fecha_nacimiento: date | None = None
    email: EmailStr | None = None
    rol: UserRole | None = None

class UserUpdatePassword(BaseModel):
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8, max_length=16)

    @validator("new_password")
    def validate_new_password(cls, v):
        if not re.search(r"[A-Z]", v):
            raise ValueError("Debe tener al menos una mayúscula")
        if not re.search(r"[a-z]", v):
            raise ValueError("Debe tener al menos una minúscula")
        if not re.search(r"\d", v):
            raise ValueError("Debe tener al menos un número")
        return v
