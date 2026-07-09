"""Application lifespan events."""
import logging
from app.core.database import Base, engine

logger = logging.getLogger("educore.lifespan")

async def startup_create_tables():
    """
    Ensure all ORM tables exist in the database on startup.

    Uses engine.begin() so the DDL transaction is committed to PostgreSQL.
    Explicitly imports all model modules so Base.metadata is fully populated
    before create_all runs. This avoids 'relation does not exist' errors on
    fresh Railway deployments where no alembic migrations are present.
    """
    from app.models import (
        base,
        analytics,
        cbc,
        download,
        grade,
        notification,
        payment,
        resource,
        review,
        school,
        subject,
        subscription,
        topic,
        tracking,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured via startup_create_tables")
