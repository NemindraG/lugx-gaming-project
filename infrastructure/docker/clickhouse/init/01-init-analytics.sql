-- ClickHouse Analytics Database Initialization
-- This script sets up the initial database structure for high-volume web analytics

-- Create database
CREATE DATABASE IF NOT EXISTS lugx_analytics;

USE lugx_analytics;

-- Create table for raw web events (as designed in Phase 2 plan)
CREATE TABLE IF NOT EXISTS web_events
(
    event_id UUID DEFAULT generateUUIDv4(),
    event_type LowCardinality(String),
    timestamp DateTime64(3) DEFAULT now64(3),
    date Date DEFAULT toDate(timestamp),
    session_id String,
    user_id Nullable(String),
    
    -- Page tracking
    page_url String,
    page_title Nullable(String),
    referrer Nullable(String),
    
    -- User interactions
    element_type Nullable(LowCardinality(String)),
    element_text Nullable(String),
    element_id Nullable(String),
    click_x Nullable(UInt16),
    click_y Nullable(UInt16),
    
    -- Scroll tracking
    scroll_depth Nullable(UInt8),
    max_scroll Nullable(UInt8),
    page_height Nullable(UInt16),
    
    -- E-commerce specific
    product_id Nullable(String),
    category Nullable(String),
    price Nullable(Decimal64(2)),
    quantity Nullable(UInt32),
    
    -- Device/browser context
    user_agent String,
    screen_width Nullable(UInt16),
    screen_height Nullable(UInt16),
    viewport_width Nullable(UInt16),
    viewport_height Nullable(UInt16),
    device_type LowCardinality(String) DEFAULT 'unknown',
    browser LowCardinality(String) DEFAULT 'unknown',
    os LowCardinality(String) DEFAULT 'unknown',
    
    -- Geographic data
    country_code Nullable(FixedString(2)),
    region Nullable(String),
    city Nullable(String),
    
    -- Performance metrics
    page_load_time Nullable(UInt32),
    dom_ready_time Nullable(UInt32),
    
    -- Custom event properties (JSON)
    properties String DEFAULT '{}'
) 
ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (event_type, timestamp, session_id)
TTL date + INTERVAL 90 DAY
SETTINGS index_granularity = 8192;

-- Create materialized view for hourly aggregations
CREATE MATERIALIZED VIEW IF NOT EXISTS hourly_page_views
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (hour, page_url)
AS
SELECT
    toStartOfHour(timestamp) AS hour,
    page_url,
    count() AS view_count,
    uniq(session_id) AS unique_sessions,
    uniq(user_id) AS unique_users,
    avg(page_load_time) AS avg_load_time
FROM web_events
WHERE event_type = 'page_view'
GROUP BY hour, page_url;

-- Create table for user sessions
CREATE TABLE IF NOT EXISTS user_sessions
(
    session_id String,
    user_id Nullable(String),
    session_start DateTime64(3),
    session_end DateTime64(3),
    duration_seconds UInt32,
    page_count UInt16,
    event_count UInt32,
    bounce Boolean,
    conversion Boolean,
    revenue Nullable(Decimal64(2)),
    
    -- Entry/Exit pages
    entry_page String,
    exit_page String,
    
    -- Device info (from first event)
    device_type LowCardinality(String),
    browser LowCardinality(String),
    os LowCardinality(String),
    
    -- Geographic
    country_code Nullable(FixedString(2)),
    
    date Date DEFAULT toDate(session_start)
)
ENGINE = ReplacingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, session_id);

-- Create table for conversion funnels
CREATE TABLE IF NOT EXISTS conversion_funnels
(
    funnel_id String,
    session_id String,
    user_id Nullable(String),
    step_number UInt8,
    step_name String,
    timestamp DateTime64(3),
    time_to_next_step Nullable(UInt32),
    completed Boolean,
    
    date Date DEFAULT toDate(timestamp)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (funnel_id, session_id, step_number);

-- Create table for real-time metrics
CREATE TABLE IF NOT EXISTS realtime_metrics
(
    metric_name String,
    timestamp DateTime64(3) DEFAULT now64(3),
    value Float64,
    dimensions String DEFAULT '{}'
)
ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (metric_name, timestamp)
TTL timestamp + INTERVAL 7 DAY;

-- Create user for analytics service
CREATE USER IF NOT EXISTS analytics_service 
    IDENTIFIED WITH sha256_password BY 'analytics_secure_password_2024'
    SETTINGS max_execution_time = 3600;

-- Grant permissions
GRANT ALL ON lugx_analytics.* TO analytics_service;

-- Log successful initialization
SELECT 'ClickHouse Analytics database initialized successfully' AS status, now() AS initialized_at;