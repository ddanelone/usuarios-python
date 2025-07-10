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
    
    RABBITMQ_URI: str = "amqp://guest:guest@localhost/"  # valor por defecto

    @property
    def lockout_duration(self) -> timedelta:
        return timedelta(seconds=self.LOCKOUT_TIME)
        
    class Config:
        env_file = ".env"

settings = Settings()  # type: ignore    
