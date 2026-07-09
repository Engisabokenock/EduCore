"""Application lifespan events."""
import logging
from app.core.database import Base, engine

logger = logging.getLogger("educore.lifespan")

async def startup_create_tables():
    """Ensure all ORM tables exist in the database on startup."""
    async with engine.connect() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn))
    logger.info("Database tables ensured via startup_create_tables")
