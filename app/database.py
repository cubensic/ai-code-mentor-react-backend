from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

# Convert postgresql:// to postgresql+asyncpg:// if needed
def get_async_database_url(url: str) -> str:
    """Convert standard postgresql:// URL to asyncpg format if needed"""
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url

# Create async engine - this is the connection pool to PostgreSQL
engine = create_async_engine(
    get_async_database_url(settings.DATABASE_URL),
    echo=True,  # Logs SQL queries (helpful for debugging)
    future=True
)

# Create session factory - this creates database sessions
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for all database models
Base = declarative_base()

# Dependency to get database session in FastAPI routes
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()