# Lugx Gaming Platform - Database Infrastructure

## Overview

This directory contains the complete infrastructure for the Lugx Gaming platform, implementing Phase 2 of our development plan. The infrastructure includes:

- **Frontend** - Nginx serving the static HTML/CSS/JS gaming website
- **PostgreSQL** (2 instances) - For Game Service and Order Service transactional data
- **ClickHouse** - For high-volume analytics and web event tracking
- **Redis** - For caching and session management
- **pgAdmin** - For PostgreSQL database management (development only)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Docker Network: lugx-network              │
│                                                             │
│  ┌─────────────────┐                                       │
│  │    Frontend     │  ←── Nginx serving static website     │
│  │   Port: 3000    │      with API proxy configuration     │
│  └─────────────────┘                                       │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                 │
│  │ PostgreSQL Game  │  │ PostgreSQL Order │                 │
│  │   Port: 5432     │  │   Port: 5433     │                 │
│  │   DB: lugx_games │  │   DB: lugx_orders│                 │
│  └─────────────────┘  └─────────────────┘                 │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                 │
│  │   ClickHouse    │  │      Redis       │                 │
│  │  Port: 8123/9000│  │   Port: 6379     │                 │
│  │ DB: lugx_analytics│ │  Password Auth   │                 │
│  └─────────────────┘  └─────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

1. **Setup Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with secure passwords
   ```

2. **Start Infrastructure**
   ```bash
   ./manage.sh start
   ```

3. **Check Health**
   ```bash
   ./manage.sh health
   ```

## Management Commands

- `./manage.sh start` - Start all database services
- `./manage.sh stop` - Stop all database services
- `./manage.sh restart` - Restart all services
- `./manage.sh logs [service]` - View logs
- `./manage.sh health` - Check service health
- `./manage.sh backup` - Create database backups
- `./manage.sh clean` - Remove all data (WARNING: destructive)

## Service Access

### Frontend
- URL: http://localhost:3000
- Static files served from: `frontend/` directory
- API proxy configured for development

### Database Connections

### PostgreSQL - Game Service
- Host: localhost
- Port: 5432
- Database: lugx_games
- User: game_service
- Password: (set in .env)

### PostgreSQL - Order Service
- Host: localhost
- Port: 5433
- Database: lugx_orders
- User: order_service
- Password: (set in .env)

### ClickHouse - Analytics
- HTTP: http://localhost:8123
- Native: localhost:9000
- Database: lugx_analytics
- User: analytics_service
- Password: (set in .env)

### Redis - Cache
- Host: localhost
- Port: 6379
- Password: (set in .env)

### pgAdmin (Development)
- URL: http://localhost:5050
- Email: admin@lugxgaming.com
- Password: (set in .env)

## Database Features

### PostgreSQL Configuration
- UTF-8 encoding with en_US locale
- Optimized for transactional workloads
- Extensions: uuid-ossp, pg_trgm, pgcrypto
- Connection pooling ready
- Custom types for enums

### ClickHouse Configuration
- Optimized for analytics workloads
- Time-based partitioning
- Automatic data retention (90 days)
- Materialized views for real-time metrics
- Compression with LZ4

### Redis Configuration
- Persistence with RDB and AOF
- Memory limit: 512MB with LRU eviction
- Password authentication
- Dangerous commands disabled

## Volume Persistence

All data is persisted in Docker volumes:
- `postgres-game-data` - Game Service database
- `postgres-order-data` - Order Service database
- `clickhouse-data` - Analytics database
- `redis-data` - Cache data

## Security Considerations

1. **Change default passwords** in .env before production use
2. **Network isolation** - Services only accessible within Docker network
3. **Encrypted connections** supported for all databases
4. **Access control** - Each service has its own user with limited permissions
5. **Backup regularly** using `./manage.sh backup`

## Troubleshooting

### Service Won't Start
```bash
# Check logs
./manage.sh logs [service-name]

# Verify port availability
lsof -i :5432  # PostgreSQL Game
lsof -i :5433  # PostgreSQL Order
lsof -i :8123  # ClickHouse
lsof -i :6379  # Redis
```

### Connection Issues
- Ensure services are healthy: `./manage.sh health`
- Check Docker network: `docker network ls`
- Verify credentials in .env file

### Performance Issues
- Monitor resource usage: `docker stats`
- Check ClickHouse queries: http://localhost:8123/play
- PostgreSQL slow queries: Check pg_stat_statements

## Testing

To test database connections:
```bash
cd ../testing/infrastructure
python test-database-connections.py
```

This will verify all database connections and report their health status.

## Next Steps

After database infrastructure is running:
1. Week 2: Implement database schemas
2. Week 3: Set up Kubernetes infrastructure
3. Week 4: Configure service mesh and networking

## Educational Notes

This infrastructure demonstrates:
- **Microservices data isolation** - Each service has its own database
- **Polyglot persistence** - Different databases for different needs
- **High availability patterns** - Health checks and persistence
- **Security best practices** - Authentication, network isolation
- **Operational excellence** - Monitoring, backups, management scripts