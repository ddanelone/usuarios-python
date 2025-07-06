from pydantic_settings import BaseSettings
from datetime import timedelta
from pydantic import Field

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    MAX_ATTEMPTS: int = 3
    LOCKOUT_TIME: int = 900  # en segundos
    
    BCRYPT_ROUNDS: int = Field(default=12)

    @property
    def lockout_duration(self) -> timedelta:
        return timedelta(seconds=self.LOCKOUT_TIME)

    class Config:
        env_file = ".env"

settings = Settings()  # type: ignore
