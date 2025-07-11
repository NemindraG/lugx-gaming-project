-- ClickHouse Database Initialization Script
-- Creates lugx_analytics database with proper tables and compatibility layer

-- Create the main database
CREATE DATABASE IF NOT EXISTS lugx_analytics;

-- Use the database
USE lugx_analytics;

-- Create the main events table (new schema)
CREATE TABLE IF NOT EXISTS events (
    id UInt64,
    event_type String,
    user_id Nullable(String),
    session_id String,
    timestamp DateTime64(3),
    page_url Nullable(String),
    referrer Nullable(String),
    user_agent Nullable(String),
    ip_address Nullable(String),
    properties Map(String, String),
    created_at DateTime64(3) DEFAULT now64()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, event_type, session_id)
SETTINGS index_granularity = 8192;

-- Create the web_events table (legacy compatibility)
CREATE TABLE IF NOT EXISTS web_events (
    id UInt64,
    event_type String,
    user_id Nullable(String),
    session_id String,
    timestamp DateTime64(3),
    page_url Nullable(String),
    referrer Nullable(String),
    user_agent Nullable(String),
    ip_address Nullable(String),
    properties Map(String, String),
    created_at DateTime64(3) DEFAULT now64()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, event_type, session_id)
SETTINGS index_granularity = 8192;

-- Create materialized view to sync data between tables
CREATE MATERIALIZED VIEW IF NOT EXISTS events_to_web_events_mv TO web_events AS
SELECT * FROM events;

CREATE MATERIALIZED VIEW IF NOT EXISTS web_events_to_events_mv TO events AS
SELECT * FROM web_events;

-- Create page views aggregation table
CREATE TABLE IF NOT EXISTS page_views_daily (
    date Date,
    page_url String,
    views UInt64,
    unique_visitors UInt64
) ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, page_url);

-- Create user sessions aggregation table
CREATE TABLE IF NOT EXISTS user_sessions (
    date Date,
    session_id String,
    user_id Nullable(String),
    first_seen DateTime64(3),
    last_seen DateTime64(3),
    page_views UInt32,
    duration UInt32
) ENGINE = ReplacingMergeTree(last_seen)
PARTITION BY toYYYYMM(date)
ORDER BY (date, session_id);

-- Create some useful materialized views for analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS page_views_daily_mv TO page_views_daily AS
SELECT
    toDate(timestamp) as date,
    page_url,
    count() as views,
    uniq(session_id) as unique_visitors
FROM events
WHERE event_type = 'page_view' AND page_url IS NOT NULL
GROUP BY date, page_url;

-- Insert some sample data for testing
INSERT INTO events VALUES
    (1, 'page_view', null, 'sess_001', now64(), '/', null, 'Mozilla/5.0', '127.0.0.1', {}, now64()),
    (2, 'page_view', 'user_001', 'sess_002', now64(), '/shop', '/', 'Mozilla/5.0', '127.0.0.1', {}, now64()),
    (3, 'click', 'user_001', 'sess_002', now64(), '/shop', null, 'Mozilla/5.0', '127.0.0.1', {'element': 'buy-button'}, now64());

-- Create admin user for analytics service
CREATE USER IF NOT EXISTS analytics_user IDENTIFIED WITH plaintext_password BY 'analytics_password';
GRANT SELECT, INSERT, CREATE, DROP ON lugx_analytics.* TO analytics_user;

-- Grant permissions for the default user as well
GRANT SELECT, INSERT, CREATE, DROP ON lugx_analytics.* TO default;
