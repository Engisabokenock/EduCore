from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


def _async_database_url(url: str) -> str:
    """
    Ensure an async driver is selected regardless of the supplied scheme.

    Hosting platforms often inject a synchronous `postgresql://` or `postgres://`
    DATABASE_URL, which would make SQLAlchemy fall back to the sync `psycopg2`
    dialect (not installed). Rewrite it to the async `asyncpg` driver.
    """
    if url.startswith("postgresql+asyncpg://") or url.startswith("postgres+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://"):]
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://"):]
    return url


# Initialize Async Engine with Production Connection Pooling Configuration
DATABASE_URL = _async_database_url(settings.DATABASE_URL)
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # Mitigates database connection dropping drops
    pool_size=20,             # Production maximum persistent connections
    max_overflow=10,          # Extra burst capacity connections
    echo=False
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,   # Essential configuration preventing lifecycle errors in async operations
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency Provider for scoped Database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
