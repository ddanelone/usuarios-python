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

def validar_password(password: str) -> str:
    if len(password) < 8 or len(password) > 16:
        raise ValueError("La contraseña debe tener entre 8 y 16 caracteres.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Debe contener al menos una letra mayúscula.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Debe contener al menos una letra minúscula.")
    if not re.search(r"\d", password):
        raise ValueError("Debe contener al menos un número.")
    return password
 
class UserBase(BaseModel):
    nombres: str = Field(..., min_length=1)
    apellidos: str = Field(..., min_length=1)
    dni: str = Field(..., min_length=7, max_length=10)
    fecha_nacimiento: date
    email: EmailStr
    rol: UserRole

class UserCreate(UserBase):
    password: str

    @validator("password")
    def check_password(cls, v):
        return validar_password(v)

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
    new_password: str

    @validator("new_password")
    def check_new_password(cls, v):
        return validar_password(v)
