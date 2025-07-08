# Lugx Gaming Platform - Master Architecture Specification

## Purpose
This document defines the authoritative values for all technical specifications across the Lugx Gaming platform architecture. All other documents must reference these standardized values to ensure consistency.

---

## 1. ClickHouse Performance Specifications

### **Event Ingestion Targets**
- **Sustained Rate**: 100,000 events/second
- **Peak Burst Rate**: 500,000 events/second (5-minute bursts)
- **Daily Event Volume**: 8.6 billion events/day (sustained rate)

### **Query Performance Targets**
- **Real-time Analytics**: <100ms (95th percentile)
- **Dashboard Queries**: <2 seconds
- **Complex Funnel Analysis**: <5 seconds
- **User Journey Queries**: <3 seconds

### **Cluster Configuration**
- **Shards**: 6 shards (time-based partitioning)
- **Replicas**: 2 replicas per shard
- **Total Nodes**: 12 nodes (6 primary + 6 replica)
- **Storage per Node**: 1TB NVMe SSD
- **Memory per Node**: 64GB RAM
- **CPU per Node**: 16 vCPU

### **Data Retention**
- **Raw Events**: 90 days
- **Aggregated Data**: 2 years
- **Real-time Data**: 24 hours (hot storage)

---

## 2. Analytics Service Scaling Configuration

### **Horizontal Pod Autoscaling (HPA)**
```yaml
minReplicas: 3              # High availability baseline
maxReplicas: 20             # Reasonable scaling limit
targetCPUUtilization: 70%   # Scale up trigger
targetMemoryUtilization: 80% # Memory scale trigger
```

### **Custom Scaling Triggers**
- **Event Queue Depth**: >5,000 events → Scale up 5 pods
- **API Request Rate**: >10,000 req/min → Scale up 3 pods
- **ClickHouse Write Latency**: >500ms → Scale up 2 pods

### **Resource Allocation per Pod**
```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

---

## 3. Database Connection Pool Specifications

### **Game Service (PostgreSQL)**
- **Pool Size**: 20 connections
- **Max Overflow**: 10 connections
- **Pool Timeout**: 30 seconds
- **Pool Recycle**: 3600 seconds (1 hour)

### **Order Service (PostgreSQL)**
- **Pool Size**: 50 connections (transaction-heavy)
- **Max Overflow**: 20 connections
- **Pool Timeout**: 30 seconds
- **Pool Recycle**: 3600 seconds

### **Analytics Service (ClickHouse)**
- **Pool Size**: 30 connections
- **Max Overflow**: 10 connections
- **Pool Timeout**: 10 seconds (shorter for analytics)
- **Pool Recycle**: 1800 seconds (30 minutes)

### **Redis Configuration**
- **Max Connections**: 100
- **Timeout**: 5 seconds
- **Retry on Failure**: 3 attempts

---

## 4. API Endpoint Standardization

### **Analytics Service Endpoints**
```
Base Path: /api/v1/analytics

Core Endpoints:
- POST   /api/v1/analytics/events/batch
- GET    /api/v1/analytics/metrics/realtime
- GET    /api/v1/analytics/journey/{session_id}
- POST   /api/v1/analytics/session/start
- POST   /api/v1/analytics/session/end
- GET    /api/v1/analytics/funnel/{funnel_id}
- GET    /api/v1/analytics/users/active
```

### **Game Service Endpoints**
```
Base Path: /api/v1/games

Core Endpoints:
- GET    /api/v1/games/trending?limit={n}
- GET    /api/v1/games/search?q={query}
- GET    /api/v1/games/{id}
- GET    /api/v1/games/categories
```

### **Order Service Endpoints**
```
Base Path: /api/v1

Authentication:
- POST   /api/v1/auth/login
- POST   /api/v1/auth/register
- POST   /api/v1/auth/refresh

Cart & Orders:
- GET    /api/v1/cart
- POST   /api/v1/cart/add
- POST   /api/v1/orders
- GET    /api/v1/orders/{id}
```

---

## 5. Rate Limiting Specifications

### **Analytics Service Rate Limits**
- **Batch Events**: 1,000 requests/minute per IP
- **Real-time Queries**: 100 requests/minute per authenticated user
- **General Analytics**: 500 requests/minute per IP
- **Internal Services**: Unlimited (10.0.0.0/8 networks)

### **Game Service Rate Limits**
- **Public APIs**: 1,000 requests/minute per IP
- **Search APIs**: 100 requests/minute per IP
- **Authenticated APIs**: 2,000 requests/minute per user

### **Order Service Rate Limits**
- **Authentication**: 10 attempts/minute per IP
- **Cart Operations**: 500 requests/minute per user
- **Order Creation**: 10 orders/minute per user

---

## 6. Service Naming Conventions

### **Kubernetes Resources** (kebab-case)
- Service Names: `game-service`, `order-service`, `analytics-service`
- Deployment Names: `game-service-deployment`
- ConfigMap Names: `game-service-config`

### **Code Classes** (PascalCase)
- Service Classes: `GameService`, `OrderService`, `AnalyticsService`
- Model Classes: `Game`, `Order`, `User`, `WebEvent`

### **Database Names** (snake_case)
- Databases: `lugx_games`, `lugx_orders`, `lugx_analytics`
- Tables: `web_events`, `user_sessions`, `game_catalog`

### **Environment Variables** (UPPER_SNAKE_CASE)
- `DATABASE_URL`, `REDIS_URL`, `CLICKHOUSE_URL`
- `MAX_CONNECTIONS`, `POOL_SIZE`

---

## 7. Performance and Monitoring Targets

### **API Response Times**
- **Authentication**: <100ms (95th percentile)
- **Game Catalog**: <200ms (95th percentile)
- **Real-time Analytics**: <100ms (95th percentile)
- **Complex Queries**: <2 seconds (95th percentile)

### **Throughput Targets**
- **Page Views**: 50,000 requests/second
- **API Calls**: 10,000 requests/second
- **Database Writes**: 5,000 transactions/second

### **Availability Targets**
- **Core Services**: 99.9% uptime
- **Analytics Service**: 99.5% uptime (can be briefly unavailable)
- **Database Systems**: 99.99% uptime

---

## 8. Security Specifications

### **Authentication**
- **JWT Token Expiry**: 24 hours
- **Refresh Token Expiry**: 30 days
- **Session Timeout**: 2 hours of inactivity

### **Authorization**
- **Rate Limiting**: Per specifications above
- **IP Allowlisting**: Internal networks (10.0.0.0/8, 172.16.0.0/12)
- **API Key Rotation**: Every 90 days

---

## 9. Data Storage Specifications

### **PostgreSQL Configuration**
- **Game Service DB**: 500GB storage, 8GB shared_buffers
- **Order Service DB**: 1TB storage, 16GB shared_buffers
- **Connection Limit**: 100 per database

### **ClickHouse Configuration**
- **Per Node Storage**: 1TB NVMe SSD
- **Compression**: LZ4 (3:1 ratio expected)
- **Partitioning**: Daily partitions, monthly for historical

### **Redis Configuration**
- **Memory**: 16GB per instance
- **Persistence**: RDB + AOF
- **Cluster**: 6 nodes (3 masters, 3 replicas)

---

## Implementation Notes

1. **All architecture documents must reference these values**
2. **Any deviation requires updating this master specification first**
3. **Values are based on realistic gaming platform requirements**
4. **Performance targets include 20% headroom for growth**
5. **Scaling limits allow for 10x traffic growth**

---

## Version Control

- **Version**: 1.0.0
- **Last Updated**: 2024-01-15
- **Next Review**: 2024-04-15
- **Owner**: Architecture Team

*This specification is the single source of truth for all technical values across the Lugx Gaming platform architecture.*