# Lugx Gaming Platform - AWS QuickSight Integration Design

## Executive Summary

This document provides a comprehensive design for integrating AWS QuickSight with our ClickHouse analytics database to create real-time, interactive dashboards for visualizing web analytics data captured from the Lugx Gaming platform.

## Architecture Overview

### Integration Flow
```
Frontend Web Analytics → ClickHouse → AWS QuickSight → Interactive Dashboards
```

### Components
- **ClickHouse Database**: Source of analytics data
- **AWS QuickSight**: Business intelligence and visualization service
- **SPICE Engine**: QuickSight's in-memory calculation engine
- **Real-time Datasets**: Live data connections for dashboard updates

---

## 1. ClickHouse to QuickSight Connection Architecture

### 1.1 Connection Method
**Direct Database Connection** via ClickHouse HTTP interface

```yaml
QuickSight Connection Configuration:
  Connection Type: ClickHouse
  Host: clickhouse-nlb.lugx-gaming.internal
  Port: 8123
  Database: lugx_analytics
  Protocol: HTTP/HTTPS
  Authentication: Username/Password
  SSL: Enabled (for production)
```

### 1.2 Network Configuration

```yaml
# AWS VPC Peering for QuickSight Access
VPC Peering Setup:
  Source VPC: QuickSight VPC (AWS Managed)
  Target VPC: Lugx Gaming EKS Cluster VPC
  
  Security Groups:
    ClickHouse Security Group:
      - Allow inbound 8123 from QuickSight IP ranges
      - Allow inbound 9000 for native protocol (if needed)
    
    QuickSight Access:
      - IP Whitelist: QuickSight service IP ranges
      - Authentication: Service account credentials
```

### 1.3 ClickHouse Views for QuickSight

```sql
-- Optimized Views for QuickSight Performance
-- 1. Page Views Summary View
CREATE VIEW analytics_quicksight.page_views_summary AS
SELECT 
    toDate(timestamp) as date,
    toHour(timestamp) as hour,
    page_url,
    count() as page_views,
    uniq(session_id) as unique_sessions,
    uniq(user_id) as unique_users,
    avg(if(element_type = 'scroll', scroll_depth, NULL)) as avg_scroll_depth
FROM web_events 
WHERE event_type = 'page_view'
GROUP BY date, hour, page_url
ORDER BY date DESC, hour DESC;

-- 2. User Engagement Metrics View
CREATE VIEW analytics_quicksight.user_engagement_metrics AS
SELECT 
    toDate(timestamp) as date,
    uniq(user_id) as daily_active_users,
    count() as total_events,
    uniq(session_id) as total_sessions,
    avg(if(event_type = 'session_end', 
        toUInt32(extractFromString(properties, '"session_duration":(\\d+)')), 
        NULL)) as avg_session_duration,
    countIf(event_type = 'click') as total_clicks,
    countIf(event_type = 'scroll_depth') as scroll_events
FROM web_events 
GROUP BY date
ORDER BY date DESC;

-- 3. Game Performance Analytics View
CREATE VIEW analytics_quicksight.game_performance AS
SELECT 
    toDate(timestamp) as date,
    extractFromString(page_url, '/game/([^/\\?]+)') as game_id,
    count() as game_views,
    uniq(session_id) as unique_viewers,
    countIf(event_type = 'add_to_cart') as add_to_cart_events,
    countIf(event_type = 'purchase') as purchase_events,
    if(game_views > 0, add_to_cart_events / game_views, 0) as conversion_rate
FROM web_events 
WHERE page_url LIKE '%/game/%' OR event_type IN ('add_to_cart', 'purchase')
GROUP BY date, game_id
HAVING game_views > 0
ORDER BY date DESC, game_views DESC;

-- 4. Real-time Active Users View
CREATE VIEW analytics_quicksight.realtime_active_users AS
SELECT 
    toStartOfMinute(timestamp) as minute,
    uniq(user_id) as active_users,
    uniq(session_id) as active_sessions,
    count() as events_per_minute
FROM web_events 
WHERE timestamp >= now() - INTERVAL 2 HOUR
GROUP BY minute
ORDER BY minute DESC;

-- 5. Conversion Funnel View
CREATE VIEW analytics_quicksight.conversion_funnel AS
SELECT 
    toDate(timestamp) as date,
    countIf(event_type = 'page_view' AND page_url LIKE '%/shop%') as shop_visits,
    countIf(event_type = 'product_view') as product_views,
    countIf(event_type = 'add_to_cart') as cart_additions,
    countIf(event_type = 'checkout_start') as checkout_starts,
    countIf(event_type = 'purchase') as purchases,
    if(shop_visits > 0, product_views / shop_visits, 0) as browse_rate,
    if(product_views > 0, cart_additions / product_views, 0) as cart_rate,
    if(cart_additions > 0, purchases / cart_additions, 0) as purchase_rate
FROM web_events 
GROUP BY date
ORDER BY date DESC;
```

---

## 2. QuickSight Dataset Configuration

### 2.1 Dataset Definitions

```yaml
# Dataset 1: Page Analytics
Page_Analytics_Dataset:
  Name: "Lugx Gaming - Page Analytics"
  Source: ClickHouse View (page_views_summary)
  Refresh Schedule: Every 15 minutes
  SPICE Capacity: 500MB
  
  Calculated Fields:
    - Bounce Rate: (Single Page Sessions / Total Sessions) * 100
    - Pages Per Session: Total Page Views / Total Sessions
    - Engagement Score: (Avg Scroll Depth * Pages Per Session) / 100

# Dataset 2: User Engagement
User_Engagement_Dataset:
  Name: "Lugx Gaming - User Engagement" 
  Source: ClickHouse View (user_engagement_metrics)
  Refresh Schedule: Every 30 minutes
  SPICE Capacity: 200MB
  
  Calculated Fields:
    - Click Through Rate: (Total Clicks / Total Page Views) * 100
    - Session Quality: Avg Session Duration / 60 (in minutes)
    - Events Per User: Total Events / Daily Active Users

# Dataset 3: Game Performance
Game_Performance_Dataset:
  Name: "Lugx Gaming - Game Performance"
  Source: ClickHouse View (game_performance)
  Refresh Schedule: Every 1 hour
  SPICE Capacity: 1GB
  
  Calculated Fields:
    - View to Cart Rate: (Add to Cart Events / Game Views) * 100
    - Purchase Conversion: (Purchase Events / Game Views) * 100
    - Revenue Impact: Purchase Events * Average Game Price

# Dataset 4: Real-time Monitoring
Realtime_Dataset:
  Name: "Lugx Gaming - Real-time"
  Source: ClickHouse View (realtime_active_users)
  Refresh Schedule: Every 5 minutes
  SPICE Capacity: 100MB
```

### 2.2 Data Source Connection String

```python
# ClickHouse Connection Configuration for QuickSight
QUICKSIGHT_CLICKHOUSE_CONFIG = {
    "host": "clickhouse-nlb.lugx-gaming.internal",
    "port": 8123,
    "database": "lugx_analytics", 
    "username": "quicksight_user",
    "password": "${QUICKSIGHT_DB_PASSWORD}",
    "ssl": True,
    "connection_timeout": 30,
    "query_timeout": 300,
    "additional_params": {
        "enable_http_compression": 1,
        "output_format_json_quote_64bit_integers": 0,
        "readonly": 1
    }
}
```

---

## 3. Dashboard Design Specifications

### 3.1 Executive Dashboard
**Purpose**: High-level KPIs for business stakeholders

```yaml
Executive_Dashboard:
  Name: "Lugx Gaming - Executive Overview"
  Refresh: Auto (every 15 minutes)
  
  Visuals:
    1. KPI Cards Row:
       - Daily Active Users (gauge)
       - Total Revenue (currency)
       - Conversion Rate (percentage)
       - Average Session Duration (time)
    
    2. Trend Charts:
       - Daily Active Users (7-day trend line)
       - Revenue Growth (monthly bar chart)
       - Top Performing Games (horizontal bar)
    
    3. Real-time Monitoring:
       - Current Active Users (number)
       - Live Page Views (streaming chart)
       - Geographic Distribution (map)
    
    4. Conversion Funnel:
       - Shop Visits → Product Views → Cart → Purchase
       - Drop-off rates at each stage
```

### 3.2 Marketing Analytics Dashboard
**Purpose**: Campaign performance and user acquisition insights

```yaml
Marketing_Dashboard:
  Name: "Lugx Gaming - Marketing Analytics"
  Refresh: Auto (every 30 minutes)
  
  Visuals:
    1. Traffic Sources:
       - Referrer Analysis (pie chart)
       - Direct vs Organic vs Paid (stacked bar)
       - UTM Campaign Performance (table)
    
    2. User Behavior:
       - Page Flow Analysis (sankey diagram)
       - Scroll Depth Distribution (histogram)
       - Click Heatmap Data (table for export)
    
    3. Content Performance:
       - Most Viewed Pages (bar chart)
       - Time on Page Analysis (scatter plot)
       - Exit Page Analysis (table)
    
    4. Device & Browser:
       - Mobile vs Desktop (donut chart)
       - Browser Performance (table)
       - Screen Resolution Impact (bar chart)
```

### 3.3 Gaming Analytics Dashboard  
**Purpose**: Game-specific performance metrics

```yaml
Gaming_Dashboard:
  Name: "Lugx Gaming - Game Performance"
  Refresh: Auto (every 1 hour)
  
  Visuals:
    1. Game Performance Matrix:
       - Views vs Conversion Rate (scatter plot)
       - Top Games by Revenue (bar chart)
       - New vs Returning Game Viewers (stacked area)
    
    2. Category Analysis:
       - Performance by Game Category (grouped bar)
       - Category Popularity Trends (line chart)
       - Seasonal Game Preferences (heatmap)
    
    3. User Journey:
       - Game Discovery Paths (sankey)
       - Cross-selling Opportunities (network diagram)
       - Purchase Timing Analysis (time series)
    
    4. Inventory Impact:
       - Stock Level vs Demand (dual axis chart)
       - Out-of-Stock Impact on Behavior (table)
```

### 3.4 Real-time Operations Dashboard
**Purpose**: Live monitoring for technical teams

```yaml
Operations_Dashboard:
  Name: "Lugx Gaming - Real-time Operations"
  Refresh: Auto (every 5 minutes)
  
  Visuals:
    1. Live Traffic:
       - Current Users Online (big number)
       - Page Views per Minute (streaming line)
       - Error Rate Monitoring (gauge)
    
    2. Performance Metrics:
       - Average Page Load Time (line chart)
       - API Response Times (multi-line chart)
       - Database Query Performance (table)
    
    3. Geographic Insights:
       - Users by Region (map)
       - Regional Performance Differences (table)
       - Time Zone Activity Patterns (heatmap)
    
    4. Alert Thresholds:
       - Traffic Spikes (threshold line)
       - Unusual Drop-offs (anomaly detection)
       - System Health Status (traffic light)
```

---

## 4. Implementation Specifications

### 4.1 QuickSight Account Setup

```yaml
AWS QuickSight Configuration:
  Edition: Enterprise
  Region: us-west-2 (match EKS cluster)
  
  User Management:
    - Admin Users: 2 (technical leads)
    - Author Users: 5 (marketing, product teams)
    - Reader Users: 20 (stakeholders, analysts)
  
  Permissions:
    - VPC Access: Enabled
    - S3 Access: Enabled (for exports)
    - RDS Access: Enabled
    - Custom Database Access: Enabled (ClickHouse)
```

### 4.2 Security Configuration

```yaml
Security Settings:
  Network:
    - VPC Peering: Lugx Gaming VPC ↔ QuickSight VPC
    - Security Groups: Restrict ClickHouse access to QuickSight IPs
    - Encryption: TLS 1.2+ for data in transit
  
  Authentication:
    - IAM Integration: Single Sign-On
    - Row-Level Security: User-based data filtering
    - Column-Level Security: Sensitive data masking
  
  Data Governance:
    - Data Lineage: Track source to dashboard
    - Audit Logging: All access and changes logged
    - Compliance: GDPR-ready data handling
```

### 4.3 Performance Optimization

```yaml
Performance Configuration:
  SPICE Settings:
    - Total Capacity: 2GB allocated
    - Auto-refresh: Enabled for real-time datasets
    - Incremental Refresh: Enabled for large datasets
  
  Query Optimization:
    - Materialized Views: Pre-computed for complex queries
    - Indexing: Optimized for time-based queries
    - Caching: 15-minute cache for dashboard tiles
  
  Monitoring:
    - Query Performance: CloudWatch metrics
    - Usage Analytics: QuickSight usage tracking
    - Cost Optimization: SPICE usage monitoring
```

---

## 5. Deployment Strategy

### 5.1 Phase 1: Foundation (Week 1)
1. **Day 1-2**: Set up QuickSight account and VPC peering
2. **Day 3**: Create ClickHouse service account and security groups
3. **Day 4**: Implement optimized views in ClickHouse
4. **Day 5**: Test connection and basic data import

### 5.2 Phase 2: Core Dashboards (Week 2)
1. **Day 1-2**: Build Executive Dashboard
2. **Day 3-4**: Implement Marketing Analytics Dashboard
3. **Day 5**: Create Real-time Operations Dashboard

### 5.3 Phase 3: Advanced Features (Week 3)
1. **Day 1-2**: Build Gaming Analytics Dashboard
2. **Day 3**: Implement alerts and automated reports
3. **Day 4**: Set up user permissions and row-level security
4. **Day 5**: Performance optimization and testing

---

## 6. Monitoring and Maintenance

### 6.1 Health Checks
```python
# QuickSight Health Monitoring
class QuickSightHealthCheck:
    def check_data_freshness(self):
        # Verify data refresh within SLA
        max_age = datetime.now() - timedelta(minutes=20)
        return self.last_refresh_time > max_age
    
    def check_query_performance(self):
        # Monitor query execution times
        return self.avg_query_time < 10  # seconds
    
    def check_spice_capacity(self):
        # Monitor SPICE usage
        return self.spice_usage_percent < 80
```

### 6.2 Alerting Configuration
```yaml
CloudWatch Alarms:
  Data Freshness Alert:
    Metric: Time since last successful refresh
    Threshold: > 30 minutes
    Action: SNS notification to ops team
  
  Query Performance Alert:
    Metric: Average query execution time
    Threshold: > 15 seconds
    Action: Email notification to data team
  
  SPICE Capacity Alert:
    Metric: SPICE usage percentage
    Threshold: > 85%
    Action: Auto-scaling recommendation
```

---

## 7. Cost Optimization

### 7.1 Pricing Model
```yaml
QuickSight Costs:
  Monthly Subscription:
    - Admin Users: $24/user/month × 2 = $48
    - Author Users: $12/user/month × 5 = $60
    - Reader Users: $5/user/month × 20 = $100
    - Total User Costs: $208/month
  
  SPICE Capacity:
    - Base: 1GB included
    - Additional: $0.25/GB/month × 1GB = $0.25
    - Total SPICE Costs: $0.25/month
  
  Total Monthly Cost: ~$210
```

### 7.2 Cost Control Measures
- **Automated SPICE Management**: Remove unused datasets
- **User Access Reviews**: Monthly access audits
- **Query Optimization**: Efficient ClickHouse views
- **Regional Deployment**: Co-locate with data sources

---

## 8. Success Metrics

### 8.1 Technical KPIs
- **Data Freshness**: < 15 minutes lag
- **Query Performance**: < 10 seconds average
- **Uptime**: 99.9% availability
- **User Adoption**: 80% monthly active users

### 8.2 Business Value
- **Decision Speed**: 50% faster insight generation
- **Data-Driven Decisions**: 90% of decisions backed by analytics
- **Revenue Impact**: Measurable conversion rate improvements
- **Cost Efficiency**: ROI > 300% within 6 months

This AWS QuickSight integration design provides a comprehensive, scalable solution for visualizing Lugx Gaming's web analytics data with real-time insights and business intelligence capabilities.