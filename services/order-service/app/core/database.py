"""
Database configuration and management for Order Service.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, Any

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import StaticPool
import structlog

from app.core.config import settings

# Configure logger
logger = structlog.get_logger()

# Database Base
Base = declarative_base()

# Create async engine with proper configuration
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=50,  # Higher for order service (transaction-heavy)
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "server_settings": {
            "application_name": "order-service",
            "jit": "off",
        }
    },
)

# Create async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session.
    Used by FastAPI dependency injection.
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error("Database session error", error=str(e))
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for getting async database session.
    Used for manual session management.
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error("Database session error", error=str(e))
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_database_health() -> Dict[str, Any]:
    """
    Check database connectivity and performance.
    Returns health status information.
    """
    try:
        async with get_session() as session:
            # Test basic connectivity
            start_time = asyncio.get_event_loop().time()
            result = await session.execute(text("SELECT 1"))
            query_time = asyncio.get_event_loop().time() - start_time
            
            # Get connection pool status
            pool = engine.pool
            pool_status: Dict[str, Any] = {
                "size": getattr(pool, 'size', lambda: 0)(),
                "checked_in": getattr(pool, 'checkedin', lambda: 0)(),
                "checked_out": getattr(pool, 'checkedout', lambda: 0)(),
                "overflow": getattr(pool, 'overflow', lambda: 0)(),
                "invalid": getattr(pool, 'invalid', lambda: 0)(),
            }
            
            # Test a simple query performance
            start_time = asyncio.get_event_loop().time()
            await session.execute(text("SELECT COUNT(*) FROM information_schema.tables"))
            tables_query_time = asyncio.get_event_loop().time() - start_time
            
            return {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "database": "postgresql",
                "connection_pool": pool_status,
                "performance": {
                    "basic_query_time": f"{query_time:.3f}s",
                    "tables_query_time": f"{tables_query_time:.3f}s",
                },
                "details": {
                    "engine": str(engine.url).split("@")[1] if "@" in str(engine.url) else "masked",
                    "pool_size": engine.pool.size(),
                    "max_overflow": engine.pool.overflow(),
                },
            }
            
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "database": "postgresql",
        }


async def create_tables():
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")


async def drop_tables():
    """Drop all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("Database tables dropped successfully")


async def close_database():
    """Close database connection."""
    await engine.dispose()
    logger.info("Database connection closed")


# Database initialization
async def init_database():
    """Initialize database connection and tables."""
    try:
        # Test connection
        health = await get_database_health()
        if health["status"] != "healthy":
            raise RuntimeError(f"Database health check failed: {health}")
        
        logger.info("Database initialized successfully", health=health)
        
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        raise