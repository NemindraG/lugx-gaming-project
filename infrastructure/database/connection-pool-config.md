# Database Connection Pool Configuration

## Overview

These are the recommended connection pool settings for the application layer when connecting to the databases. These settings should be implemented in the FastAPI services using SQLAlchemy/AsyncPG.

## PostgreSQL Connection Pools

### Game Service Database
```python
# Connection Pool Configuration
POOL_SIZE = 20          # Normal connection pool size
MAX_OVERFLOW = 10       # Additional connections under load
POOL_TIMEOUT = 30       # Seconds to wait for connection
POOL_RECYCLE = 3600     # Recycle connections after 1 hour
POOL_PRE_PING = True    # Test connections before use

# Connection string
DATABASE_URL = "postgresql+asyncpg://game_service:password@localhost:5432/lugx_games"
```

### Order Service Database
```python
# Connection Pool Configuration
POOL_SIZE = 50          # Higher for transaction-heavy service
MAX_OVERFLOW = 20       # Additional connections under load
POOL_TIMEOUT = 30       # Seconds to wait for connection
POOL_RECYCLE = 3600     # Recycle connections after 1 hour
POOL_PRE_PING = True    # Test connections before use

# Connection string
DATABASE_URL = "postgresql+asyncpg://order_service:password@localhost:5433/lugx_orders"
```

## ClickHouse Connection Pool

### Analytics Service Database
```python
# Connection Pool Configuration
POOL_SIZE = 30          # For high-volume analytics
MAX_CONNECTIONS = 100   # Total maximum connections
CONNECTION_TIMEOUT = 10 # Seconds to wait for connection
SEND_RECEIVE_TIMEOUT = 300  # 5 minutes for large queries

# Connection configuration
CLICKHOUSE_CONFIG = {
    'host': 'localhost',
    'port': 9000,
    'database': 'lugx_analytics',
    'user': 'analytics_service',
    'password': 'analytics_secure_password_2024',
    'compression': True,
    'secure': False,
    'verify': False,
    'pool_size': 30
}
```

## Redis Connection Pool

### Shared Cache/Session Store
```python
# Connection Pool Configuration
MAX_CONNECTIONS = 100   # Total pool size
CONNECTION_TIMEOUT = 20 # Seconds
SOCKET_TIMEOUT = 5      # Seconds
RETRY_ON_TIMEOUT = True

# Connection configuration
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'password': 'redis_secure_password_2024',
    'db': 0,
    'decode_responses': True,
    'max_connections': 100,
    'socket_connect_timeout': 20,
    'socket_timeout': 5,
    'retry_on_timeout': True
}
```

## Implementation Notes

1. **Environment Variables**: All passwords should come from environment variables or secrets management
2. **Health Checks**: Implement connection health checks in the application
3. **Monitoring**: Track active connections, wait time, and pool exhaustion
4. **Circuit Breakers**: Implement circuit breakers for database failures
5. **Retry Logic**: Implement exponential backoff for transient failures

## SQLAlchemy Async Engine Example

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Create async engine with pool configuration
engine = create_async_engine(
    DATABASE_URL,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    pool_recycle=POOL_RECYCLE,
    pool_pre_ping=POOL_PRE_PING,
    echo=False  # Set to True for SQL logging in development
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)
```

## Monitoring Queries

### PostgreSQL Connection Monitoring
```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity 
WHERE datname = 'lugx_games' AND state = 'active';

-- Connection pool efficiency
SELECT state, count(*) 
FROM pg_stat_activity 
WHERE datname = 'lugx_games' 
GROUP BY state;
```

### ClickHouse Connection Monitoring
```sql
-- Active queries
SELECT count() FROM system.processes;

-- Connection count by user
SELECT user, count() 
FROM system.processes 
GROUP BY user;
```

## Performance Tuning

1. **Game Service**: Lower pool size due to read-heavy workload with caching
2. **Order Service**: Higher pool size for transaction processing
3. **Analytics Service**: Moderate pool with longer query timeouts
4. **Redis**: High connection limit for session management

These configurations align with the master architecture specification and are optimized for each service's workload characteristics.