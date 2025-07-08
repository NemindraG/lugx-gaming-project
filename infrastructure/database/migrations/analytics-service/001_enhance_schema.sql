-- Analytics Service Schema Enhancements
-- Version: 001
-- Description: Additional tables and views for comprehensive analytics

USE lugx_analytics;

-- User behavior aggregations table
CREATE TABLE IF NOT EXISTS user_behavior_daily
(
    date Date,
    user_id Nullable(String),
    
    -- Activity metrics
    total_events UInt32,
    unique_pages UInt16,
    total_page_views UInt32,
    total_clicks UInt32,
    total_scroll_events UInt32,
    
    -- Engagement metrics
    total_session_duration UInt32,
    avg_session_duration Float32,
    bounce_rate Float32,
    pages_per_session Float32,
    
    -- E-commerce metrics
    products_viewed UInt16,
    add_to_cart_count UInt16,
    remove_from_cart_count UInt16,
    purchases_count UInt16,
    total_revenue Decimal64(2),
    
    -- Device/Platform
    primary_device LowCardinality(String),
    primary_browser LowCardinality(String),
    
    -- Calculated fields
    engagement_score Float32
)
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, user_id)
TTL date + INTERVAL 365 DAY;

-- Product performance table
CREATE TABLE IF NOT EXISTS product_performance_hourly
(
    timestamp DateTime,
    hour DateTime,
    product_id String,
    
    -- View metrics
    view_count UInt32,
    unique_viewers UInt32,
    avg_view_duration UInt32,
    
    -- Interaction metrics
    click_count UInt32,
    add_to_cart_count UInt32,
    purchase_count UInt32,
    
    -- Conversion metrics
    view_to_cart_rate Float32,
    cart_to_purchase_rate Float32,
    overall_conversion_rate Float32,
    
    -- Revenue metrics
    total_revenue Decimal64(2),
    avg_order_value Decimal64(2)
)
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (hour, product_id)
TTL hour + INTERVAL 90 DAY;

-- Search analytics table
CREATE TABLE IF NOT EXISTS search_queries
(
    timestamp DateTime64(3),
    date Date DEFAULT toDate(timestamp),
    session_id String,
    user_id Nullable(String),
    
    -- Search data
    query_text String,
    query_normalized String, -- Lowercase, trimmed
    results_count UInt32,
    clicked_position Nullable(UInt8),
    clicked_product_id Nullable(String),
    
    -- Search metadata
    search_type LowCardinality(String), -- 'instant', 'full', 'category'
    filters_applied String DEFAULT '{}', -- JSON
    sort_order Nullable(String),
    
    -- Performance
    response_time_ms UInt32
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, timestamp)
TTL date + INTERVAL 90 DAY;

-- A/B test results table
CREATE TABLE IF NOT EXISTS ab_test_events
(
    timestamp DateTime64(3),
    date Date DEFAULT toDate(timestamp),
    test_id String,
    variant LowCardinality(String),
    user_id Nullable(String),
    session_id String,
    
    -- Event data
    event_type String,
    event_value Nullable(Float64),
    
    -- Conversion tracking
    is_conversion Boolean DEFAULT false,
    conversion_value Nullable(Decimal64(2))
)
ENGINE = MergeTree()
PARTITION BY (test_id, toYYYYMM(date))
ORDER BY (test_id, variant, timestamp);

-- Marketing campaign tracking
CREATE TABLE IF NOT EXISTS campaign_events
(
    timestamp DateTime64(3),
    date Date DEFAULT toDate(timestamp),
    session_id String,
    user_id Nullable(String),
    
    -- Campaign data
    campaign_id Nullable(String),
    campaign_source Nullable(String), -- google, facebook, email
    campaign_medium Nullable(String), -- cpc, social, email
    campaign_name Nullable(String),
    campaign_content Nullable(String),
    
    -- Attribution
    is_first_touch Boolean,
    is_last_touch Boolean,
    touch_number UInt8,
    
    -- Conversion
    converted Boolean DEFAULT false,
    conversion_value Nullable(Decimal64(2)),
    days_to_conversion Nullable(UInt16)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, campaign_source, campaign_medium)
TTL date + INTERVAL 180 DAY;

-- Create materialized view for real-time user count
CREATE MATERIALIZED VIEW IF NOT EXISTS realtime_active_users
ENGINE = Memory
AS
SELECT
    toStartOfMinute(timestamp) AS minute,
    uniq(session_id) AS active_sessions,
    uniq(user_id) AS active_users,
    count() AS total_events
FROM web_events
WHERE timestamp >= now() - INTERVAL 5 MINUTE
GROUP BY minute;

-- Create materialized view for trending products
CREATE MATERIALIZED VIEW IF NOT EXISTS trending_products_15min
ENGINE = SummingMergeTree()
ORDER BY (window_start, score DESC)
AS
SELECT
    toStartOfFifteenMinutes(timestamp) AS window_start,
    product_id,
    count() AS view_count,
    uniq(session_id) AS unique_viewers,
    sum(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) AS cart_adds,
    sum(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS purchases,
    (view_count * 1 + cart_adds * 10 + purchases * 50) AS score
FROM web_events
WHERE 
    product_id IS NOT NULL 
    AND timestamp >= now() - INTERVAL 1 HOUR
GROUP BY window_start, product_id;

-- Create view for funnel analysis
CREATE VIEW IF NOT EXISTS conversion_funnel_view AS
WITH funnel_events AS (
    SELECT
        session_id,
        user_id,
        toDate(timestamp) AS date,
        groupArray(event_type) AS event_sequence,
        groupArray(timestamp) AS event_times,
        groupArray(product_id) AS product_sequence
    FROM web_events
    WHERE timestamp >= today() - 7
    GROUP BY session_id, user_id, date
)
SELECT
    date,
    countIf(has(event_sequence, 'page_view')) AS step_1_views,
    countIf(has(event_sequence, 'product_view')) AS step_2_product_views,
    countIf(has(event_sequence, 'add_to_cart')) AS step_3_add_to_cart,
    countIf(has(event_sequence, 'checkout_start')) AS step_4_checkout_start,
    countIf(has(event_sequence, 'purchase')) AS step_5_purchase,
    
    -- Conversion rates
    step_2_product_views / step_1_views AS view_to_product_rate,
    step_3_add_to_cart / step_2_product_views AS product_to_cart_rate,
    step_4_checkout_start / step_3_add_to_cart AS cart_to_checkout_rate,
    step_5_purchase / step_4_checkout_start AS checkout_to_purchase_rate,
    step_5_purchase / step_1_views AS overall_conversion_rate
FROM funnel_events
GROUP BY date
ORDER BY date DESC;

-- Create table for storing aggregated metrics
CREATE TABLE IF NOT EXISTS business_metrics_daily
(
    date Date,
    metric_name LowCardinality(String),
    metric_value Float64,
    
    -- Dimensions
    dimension_1_name LowCardinality(String) DEFAULT '',
    dimension_1_value String DEFAULT '',
    dimension_2_name LowCardinality(String) DEFAULT '',
    dimension_2_value String DEFAULT '',
    
    -- Metadata
    calculation_time DateTime DEFAULT now(),
    data_quality_score Float32 DEFAULT 1.0
)
ENGINE = ReplacingMergeTree(calculation_time)
PARTITION BY toYYYYMM(date)
ORDER BY (date, metric_name, dimension_1_name, dimension_1_value, dimension_2_name, dimension_2_value);

-- Create indexes for better query performance
ALTER TABLE web_events ADD INDEX idx_user_id user_id TYPE bloom_filter GRANULARITY 1;
ALTER TABLE web_events ADD INDEX idx_product_id product_id TYPE bloom_filter GRANULARITY 1;
ALTER TABLE web_events ADD INDEX idx_event_type event_type TYPE minmax GRANULARITY 1;

-- Create dictionary for user segments
CREATE DICTIONARY IF NOT EXISTS user_segments
(
    user_id String,
    segment_name String,
    segment_value String,
    updated_at DateTime
)
PRIMARY KEY user_id
SOURCE(CLICKHOUSE(
    HOST 'localhost'
    PORT 9000
    USER 'analytics_service'
    PASSWORD 'analytics_secure_password_2024'
    DB 'lugx_analytics'
    TABLE 'user_segments_source'
))
LIFETIME(MIN 300 MAX 3600)
LAYOUT(FLAT());

-- Log successful enhancement
SELECT 'ClickHouse Analytics enhancements completed successfully' AS status, now() AS completed_at;