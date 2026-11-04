from enum import Enum as PyEnum
from typing import AsyncGenerator, Type

from sqlalchemy import Enum as SQLEnum
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
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


def pg_enum(enum_cls: Type[PyEnum], **kwargs) -> SQLEnum:
    """
    Build a PostgreSQL ENUM column type that persists enum *values*, not member names.

    SQLAlchemy's default is to store the Python member name (``MANAGE_USERS``), while
    the database enum types are declared with the lowercase values (``manage_users``).
    Without ``values_callable`` every insert/select on an enum column fails with
    ``invalid input value for enum``. Every enum column in the codebase must use this.
    """
    return SQLEnum(
        enum_cls,
        name=kwargs.pop("name", enum_cls.__name__.lower()),
        values_callable=lambda members: [str(m.value) for m in members],
        validate_strings=True,
        **kwargs,
    )


DATABASE_URL = _async_database_url(settings.DATABASE_URL)
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,                    # Recycle connections dropped by the server / pooler
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_recycle=1800,                     # Avoid stale connections behind PgBouncer / Supabase pooler
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,   # Essential configuration preventing lifecycle errors in async operations
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Request-scoped database session.

    The unit of work is committed once the endpoint returns successfully and rolled
    back on any exception, so endpoints never need to call ``commit()`` themselves.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
