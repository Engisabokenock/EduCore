from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Initialize Async Engine with Production Connection Pooling Configuration
engine = create_async_engine(
    settings.DATABASE_URL,
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
