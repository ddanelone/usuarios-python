from fastapi import FastAPI
from app.routers import user
from app.db.base import Base
from app.db.session import engine

# 👇 IMPORTANTE: este import es lo que registra el modelo User en Base.metadata
from app.db.models import user as user_models

app = FastAPI()

app.include_router(user.router)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
