-- Game Service Database Initialization
-- This script sets up the initial database structure for the Game Service

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For fuzzy text search
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For composite indexes

-- Create custom types
CREATE TYPE game_status AS ENUM ('active', 'inactive', 'coming_soon', 'discontinued');
CREATE TYPE game_rating AS ENUM ('E', 'E10+', 'T', 'M', 'AO', 'RP');

-- Set default configuration
ALTER DATABASE lugx_games SET timezone TO 'UTC';
ALTER DATABASE lugx_games SET statement_timeout TO '30s';
ALTER DATABASE lugx_games SET idle_in_transaction_session_timeout TO '60s';

-- Performance settings
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
CREATE SCHEMA IF NOT EXISTS game_service;

-- Set search path
ALTER DATABASE lugx_games SET search_path TO game_service, public;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA game_service TO game_service;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA game_service TO game_service;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA game_service TO game_service;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Game Service database initialized successfully at %', NOW();
END
$$;