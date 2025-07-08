# Database Schemas Documentation

## Overview

This directory contains all database schemas, migrations, and seed data for the Lugx Gaming platform. The schemas follow Domain-Driven Design principles with complete data isolation between services.

## Schema Architecture

### Game Service (PostgreSQL)
**Purpose**: Product catalog and inventory management

**Tables**:
- `publishers` - Game development studios
- `categories` - Game genres with hierarchical support
- `games` - Main product catalog with pricing and metadata
- `game_categories` - Many-to-many relationship
- `inventory` - Stock management (digital/physical)
- `reviews` - Customer ratings and feedback

**Key Features**:
- Full-text search on game titles and descriptions
- Hierarchical category support
- Enum types for game status and ratings
- Automatic search vector updates
- UUID primary keys for distributed systems

### Order Service (PostgreSQL)
**Purpose**: User management and transaction processing

**Tables**:
- `users` - Authentication and profiles
- `user_addresses` - Shipping/billing addresses
- `shopping_carts` - Session-based cart management
- `cart_items` - Items in shopping carts
- `orders` - Completed purchases
- `order_items` - Line items with denormalized data
- `payments` - Payment transactions
- `password_resets` - Password recovery tokens
- `user_sessions` - Active authentication sessions

**Key Features**:
- BCrypt password hashing
- Session-based and user-based carts
- Order number generation
- Payment gateway abstraction
- Soft deletes for data retention

### Analytics Service (ClickHouse)
**Purpose**: High-volume event tracking and analytics

**Tables**:
- `web_events` - All user interactions
- `user_sessions` - Session aggregations
- `conversion_funnels` - Multi-step user journeys
- `user_behavior_daily` - Daily user metrics
- `product_performance_hourly` - Product analytics
- `search_queries` - Search behavior tracking
- `ab_test_events` - A/B testing data
- `campaign_events` - Marketing attribution

**Key Features**:
- Time-based partitioning
- Materialized views for real-time metrics
- 90-day data retention
- Compression with LZ4
- Bloom filter indexes

## Migration Management

### Running Migrations
```bash
cd infrastructure/database
./migrate.sh
```

This will apply all migrations in order to each database.

### Migration Files
- Located in `migrations/<service-name>/`
- Named with version numbers: `001_initial_schema.sql`
- Applied in alphabetical order

### Creating New Migrations
1. Create new file: `migrations/<service>/002_description.sql`
2. Include schema changes only (no data)
3. Make migrations idempotent where possible
4. Run `./migrate.sh` to apply

## Seed Data

### Loading Test Data
```bash
cd infrastructure/database
./seed.sh
```

### Test Data Includes
- **Game Service**: 
  - 5 publishers
  - 8 categories
  - 9 games (3 featured)
  - Sample reviews
  
- **Order Service**:
  - 4 test users (password: `password123`)
  - Sample addresses
  - Active shopping carts
  - Completed orders with payments

## Database Connections

### Development Credentials
See `infrastructure/.env` for connection details.

### Connection Pooling
- Game Service: 20 connections
- Order Service: 50 connections (higher for transactions)
- Analytics Service: 30 connections

## Performance Optimizations

### PostgreSQL
- B-tree indexes on foreign keys
- GIN indexes for full-text search
- Partial indexes for filtered queries
- Updated trigger for timestamp management

### ClickHouse
- MergeTree engine for analytics
- Time-based partitioning
- Materialized views for aggregations
- Bloom filters for user/product lookups

## Security Considerations

1. **Access Control**: Each service has its own database user
2. **Password Security**: BCrypt with cost factor 12
3. **SQL Injection**: Parameterized queries only
4. **Data Privacy**: PII handling in compliance tables
5. **Audit Trail**: All modifications tracked with timestamps

## Backup Strategy

- PostgreSQL: Daily pg_dump with WAL archiving
- ClickHouse: Replicated tables with backup to S3
- Redis: RDB + AOF for persistence

## Next Steps

After schemas are created:
1. Week 3: Kubernetes infrastructure setup
2. Week 4: Service mesh configuration
3. Week 5: SQLAlchemy models and data access layer
4. Week 6: Integration testing