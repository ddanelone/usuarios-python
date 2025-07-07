# app/main.py
from fastapi import FastAPI
from app.core.login_config import configure_logging
from app.routers import user, auth
from app.db.base import Base
from app.db.session import engine

# Importar modelos para crear tablas
from app.db.models import user as user_models

configure_logging()

app = FastAPI()

app.include_router(user.router)
app.include_router(auth.router)  # <--- acá incluimos el auth

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
