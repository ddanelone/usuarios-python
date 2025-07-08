# app/core/config.py
from pydantic_settings import BaseSettings
from datetime import timedelta
from pydantic import Field

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    MAX_ATTEMPTS: int = 3
    # en segundos
    LOCKOUT_TIME: int = 900 
    
    BCRYPT_ROUNDS: int = Field(default=12)

    @property
    def lockout_duration(self) -> timedelta:
        return timedelta(seconds=self.LOCKOUT_TIME)
     
    # Inicio configuración del correo electrónico
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    # COMENTAR SI NO USO MAILTRAP
    MAIL_TLS: bool
    MAIL_SSL: bool
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True
    # Fin de la configuración del correo electrónico

    class Config:
        env_file = ".env"

settings = Settings()  # type: ignore    
