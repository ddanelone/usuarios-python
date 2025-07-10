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

app.include_router(user.router, prefix="/api")
app.include_router(auth.router, prefix="/api")  
#app.include_router(tp1_inciso_1.router, prefix="/api/tp1")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
