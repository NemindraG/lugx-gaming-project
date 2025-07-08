-- Order Service Database Initialization
-- This script sets up the initial database structure for the Order Service

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto"; -- For password hashing
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"; -- For query performance monitoring

-- Create custom types
CREATE TYPE order_status AS ENUM ('pending', 'processing', 'paid', 'shipped', 'delivered', 'cancelled', 'refunded');
CREATE TYPE payment_status AS ENUM ('pending', 'authorized', 'captured', 'failed', 'refunded');
CREATE TYPE payment_method AS ENUM ('credit_card', 'debit_card', 'paypal', 'stripe', 'crypto');
CREATE TYPE user_role AS ENUM ('customer', 'admin', 'support', 'manager');

-- Set default configuration
ALTER DATABASE lugx_orders SET timezone TO 'UTC';
ALTER DATABASE lugx_orders SET statement_timeout TO '30s';
ALTER DATABASE lugx_orders SET idle_in_transaction_session_timeout TO '60s';

-- Performance settings for transactional workload
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET min_wal_size = '1GB';
ALTER SYSTEM SET max_wal_size = '4GB';

-- Create schema
CREATE SCHEMA IF NOT EXISTS order_service;

-- Set search path
ALTER DATABASE lugx_orders SET search_path TO order_service, public;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA order_service TO order_service;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA order_service TO order_service;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA order_service TO order_service;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Order Service database initialized successfully at %', NOW();
END
$$;