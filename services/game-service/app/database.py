"""
Database configuration and connection management for Game Service.
Implements async PostgreSQL connections with connection pooling.
"""

import os
from typing import AsyncGenerator, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from app.models.game import Base


class DatabaseConfig:
    """Database configuration settings."""

    def __init__(self):
        # Primary database URL (from environment or compose individual settings)
        self.DATABASE_URL = os.getenv("DATABASE_URL")
        
        # Fallback to individual settings if DATABASE_URL not provided
        if not self.DATABASE_URL:
            self.DB_HOST = os.getenv("DB_HOST", "postgres-game")
            self.DB_PORT = os.getenv("DB_PORT", "5432") 
            self.DB_NAME = os.getenv("DB_NAME", "lugx_games")
            self.DB_USER = os.getenv("DB_USER", "game_service")
            self.DB_PASSWORD = os.getenv("DB_PASSWORD", "game_secure_password_2024")
        else:
            # Parse DATABASE_URL to extract components
            import urllib.parse
            parsed = urllib.parse.urlparse(self.DATABASE_URL)
            self.DB_HOST = parsed.hostname
            self.DB_PORT = str(parsed.port or 5432)
            self.DB_NAME = parsed.path.lstrip('/')
            self.DB_USER = parsed.username
            self.DB_PASSWORD = parsed.password

        # Connection pool settings
        self.DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
        self.DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        self.DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))

        # Environment settings
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
        self.DEBUG = os.getenv("DEBUG", "true").lower() == "true"

    @property
    def database_url(self) -> str:
        """Get the async database URL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def database_url_sync(self) -> str:
        """Get the sync database URL for migrations."""
        if self.DATABASE_URL:
            return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


# Global database configuration
db_config = DatabaseConfig()

# Create async engine with connection pooling
engine = create_async_engine(
    db_config.database_url,
    pool_size=db_config.DB_POOL_SIZE,
    max_overflow=db_config.DB_MAX_OVERFLOW,
    pool_timeout=db_config.DB_POOL_TIMEOUT,
    pool_recycle=db_config.DB_POOL_RECYCLE,
    pool_pre_ping=True,  # Validate connections before use
    echo=db_config.DEBUG,  # Log SQL queries in debug mode
    future=True,
    # Use NullPool for testing to avoid connection issues
    poolclass=NullPool if db_config.ENVIRONMENT == "test" else None,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False,
)


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.

    Yields:
        AsyncSession: Database session for use in FastAPI endpoints

    Example:
        @app.get("/games/")
        async def get_games(db: AsyncSession = Depends(get_database_session)):
            # Use db session here
            pass
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """
    Create all database tables.
    Used for testing or initial setup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """
    Drop all database tables.
    Used for testing cleanup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def check_database_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        bool: True if connection is successful, False otherwise
    """
    import asyncio
    
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            print(f"Database connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                print(f"Failed to connect to database after {max_retries} attempts")
                return False
    
    return False


# Health check query
async def get_database_health() -> Dict[str, Any]:
    """
    Get database health information.

    Returns:
        dict: Database health status and metrics
    """
    try:
        async with AsyncSessionLocal() as session:
            # Check connection
            result = await session.execute(text("SELECT version()"))
            db_version = result.scalar()

            # Get pool status
            pool = engine.pool
            pool_status: Dict[str, Any] = {
                "size": getattr(pool, 'size', lambda: 0)(),
                "checked_in": getattr(pool, 'checkedin', lambda: 0)(),
                "checked_out": getattr(pool, 'checkedout', lambda: 0)(),
                "overflow": getattr(pool, 'overflow', lambda: 0)(),
                "invalid": getattr(pool, 'invalid', lambda: 0)(),
            }

            return {
                "status": "healthy",
                "database_version": db_version,
                "pool_status": pool_status,
                "connection_url": f"{db_config.DB_HOST}:{db_config.DB_PORT}/{db_config.DB_NAME}",
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "connection_url": f"{db_config.DB_HOST}:{db_config.DB_PORT}/{db_config.DB_NAME}",
        }


# Export commonly used items
__all__ = [
    "engine",
    "AsyncSessionLocal",
    "get_database_session",
    "create_tables",
    "drop_tables",
    "check_database_connection",
    "get_database_health",
    "db_config",
]
