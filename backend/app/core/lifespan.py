"""Application lifespan events."""
from app.core.database import Base, engine

async def startup_create_tables():
    async with engine.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)
