# app/schemas/token.py

from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    user_role: str

class TokenData(BaseModel):
    email: str | None = None
    user_id: int | None = None
    user_role: str | None = None

class UserLogin(BaseModel):
    email: str
    password: str
