# Lugx Gaming Platform - Observability Infrastructure Design

## Executive Summary

This document provides a comprehensive observability infrastructure design for the Lugx Gaming platform, implementing monitoring, logging, tracing, and alerting systems to ensure optimal performance, reliability, and rapid issue resolution across all microservices.

## Observability Architecture Overview

### Three Pillars of Observability
```
┌─────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY STACK                         │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │   METRICS   │    │    LOGS     │    │   TRACES    │        │
│  │             │    │             │    │             │        │
│  │ Prometheus  │    │  Fluentd    │    │   Jaeger    │        │
│  │ Grafana     │    │ Elasticsearch│    │ OpenTelemetry│       │
│  │ AlertManager│    │   Kibana    │    │             │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│         │                   │                   │              │
│         └───────────────────┼───────────────────┘              │
│                             │                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              UNIFIED OBSERVABILITY                      │   │
│  │                                                         │   │
│  │  • Real-time Monitoring & Alerting                     │   │
│  │  • Distributed Tracing & Performance Analysis          │   │
│  │  • Centralized Logging & Error Tracking                │   │
│  │  • Business Metrics & SLA Monitoring                   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack
```yaml
Observability Technology Stack:
  Metrics Collection: Prometheus + Node Exporter + Custom Exporters
  Metrics Visualization: Grafana
  Alerting: AlertManager + PagerDuty + Slack
  Logging: Fluentd + Elasticsearch + Kibana (ELK Stack)
  Distributed Tracing: Jaeger + OpenTelemetry
  APM: Jaeger + Custom instrumentation
  Uptime Monitoring: Blackbox Exporter + External monitoring
  Business Intelligence: Custom dashboards + QuickSight integration
```

---

## 1. Metrics Collection & Monitoring

### 1.1 Prometheus Configuration

```yaml
# monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'lugx-gaming-prod'
    environment: 'production'

rule_files:
  - "alert_rules/*.yml"
  - "recording_rules/*.yml"

alerting:
  alertmanagers:
  - static_configs:
    - targets:
      - alertmanager:9093

scrape_configs:
  # Kubernetes API Server
  - job_name: 'kubernetes-apiservers'
    kubernetes_sd_configs:
    - role: endpoints
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    relabel_configs:
    - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
      action: keep
      regex: default;kubernetes;https

  # Kubernetes Nodes
  - job_name: 'kubernetes-nodes'
    kubernetes_sd_configs:
    - role: node
    relabel_configs:
    - action: labelmap
      regex: __meta_kubernetes_node_label_(.+)

  # Kubernetes Pods
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
    - role: pod
    relabel_configs:
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
      action: keep
      regex: true
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
      action: replace
      target_label: __metrics_path__
      regex: (.+)

  # Lugx Gaming Services
  - job_name: 'lugx-frontend'
    kubernetes_sd_configs:
    - role: endpoints
    relabel_configs:
    - source_labels: [__meta_kubernetes_service_name]
      action: keep
      regex: frontend-service
    metrics_path: /metrics
    scrape_interval: 30s

  - job_name: 'lugx-game-service'
    kubernetes_sd_configs:
    - role: endpoints
    relabel_configs:
    - source_labels: [__meta_kubernetes_service_name]
      action: keep
      regex: game-service
    metrics_path: /api/v1/metrics
    scrape_interval: 15s

  - job_name: 'lugx-order-service'
    kubernetes_sd_configs:
    - role: endpoints
    relabel_configs:
    - source_labels: [__meta_kubernetes_service_name]
      action: keep
      regex: order-service
    metrics_path: /api/v1/metrics
    scrape_interval: 15s

  - job_name: 'lugx-analytics-service'
    kubernetes_sd_configs:
    - role: endpoints
    relabel_configs:
    - source_labels: [__meta_kubernetes_service_name]
      action: keep
      regex: analytics-service
    metrics_path: /api/v1/metrics
    scrape_interval: 10s

  # ClickHouse Database
  - job_name: 'clickhouse'
    static_configs:
    - targets: ['clickhouse-service:8123']
    metrics_path: /metrics
    scrape_interval: 30s

  # PostgreSQL Databases
  - job_name: 'postgres-exporter'
    static_configs:
    - targets: ['postgres-exporter:9187']
    scrape_interval: 30s

  # Redis
  - job_name: 'redis-exporter'
    static_configs:
    - targets: ['redis-exporter:9121']
    scrape_interval: 30s

  # Istio Service Mesh
  - job_name: 'istio-mesh'
    kubernetes_sd_configs:
    - role: endpoints
      namespaces:
        names:
        - istio-system
    relabel_configs:
    - source_labels: [__meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
      action: keep
      regex: istio-telemetry;prometheus
```

### 1.2 Custom Application Metrics

```python
# services/shared/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps

# Application-specific metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status', 'service']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'service'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

active_users_gauge = Gauge(
    'active_users_total',
    'Number of active users'
)

database_connections_gauge = Gauge(
    'database_connections_active',
    'Active database connections',
    ['service', 'database']
)

business_metrics = {
    'orders_total': Counter(
        'orders_total',
        'Total orders placed',
        ['status', 'payment_method']
    ),
    'revenue_total': Counter(
        'revenue_total_cents',
        'Total revenue in cents',
        ['currency']
    ),
    'game_views_total': Counter(
        'game_views_total',
        'Total game page views',
        ['game_id', 'category']
    ),
    'cart_operations_total': Counter(
        'cart_operations_total',
        'Cart operations',
        ['operation']  # add, remove, update, checkout
    )
}

clickhouse_metrics = {
    'events_ingested_total': Counter(
        'clickhouse_events_ingested_total',
        'Total events ingested into ClickHouse',
        ['event_type']
    ),
    'query_duration_seconds': Histogram(
        'clickhouse_query_duration_seconds',
        'ClickHouse query duration',
        ['query_type'],
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
    ),
    'query_errors_total': Counter(
        'clickhouse_query_errors_total',
        'ClickHouse query errors',
        ['error_type']
    )
}

# Decorators for automatic instrumentation
def track_requests(service_name):
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            method = request.method
            endpoint = str(request.url.path)
            
            start_time = time.time()
            try:
                response = await func(request, *args, **kwargs)
                status = str(response.status_code)
                
                # Record metrics
                http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status,
                    service=service_name
                ).inc()
                
                duration = time.time() - start_time
                http_request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint,
                    service=service_name
                ).observe(duration)
                
                return response
                
            except Exception as e:
                http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status='500',
                    service=service_name
                ).inc()
                raise
        return wrapper
    return decorator

def track_database_operations(database_name):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                
                duration = time.time() - start_time
                database_query_duration.labels(
                    database=database_name,
                    operation=func.__name__
                ).observe(duration)
                
                return result
            except Exception as e:
                database_errors_total.labels(
                    database=database_name,
                    error_type=type(e).__name__
                ).inc()
                raise
        return wrapper
    return decorator

# Business metric tracking functions
class BusinessMetrics:
    @staticmethod
    def track_order(order_status: str, payment_method: str):
        business_metrics['orders_total'].labels(
            status=order_status,
            payment_method=payment_method
        ).inc()
    
    @staticmethod
    def track_revenue(amount_cents: int, currency: str = 'USD'):
        business_metrics['revenue_total'].labels(
            currency=currency
        ).inc(amount_cents)
    
    @staticmethod
    def track_game_view(game_id: str, category: str):
        business_metrics['game_views_total'].labels(
            game_id=game_id,
            category=category
        ).inc()
    
    @staticmethod
    def track_cart_operation(operation: str):
        business_metrics['cart_operations_total'].labels(
            operation=operation
        ).inc()

class ClickHouseMetrics:
    @staticmethod
    def track_event_ingestion(event_type: str, count: int = 1):
        clickhouse_metrics['events_ingested_total'].labels(
            event_type=event_type
        ).inc(count)
    
    @staticmethod
    def track_query(query_type: str, duration: float):
        clickhouse_metrics['query_duration_seconds'].labels(
            query_type=query_type
        ).observe(duration)
    
    @staticmethod
    def track_query_error(error_type: str):
        clickhouse_metrics['query_errors_total'].labels(
            error_type=error_type
        ).inc()
```

---

## 2. Grafana Dashboard Configuration

### 2.1 Infrastructure Overview Dashboard

```json
{
  "dashboard": {
    "id": null,
    "title": "Lugx Gaming - Infrastructure Overview",
    "tags": ["lugx-gaming", "infrastructure"],
    "timezone": "UTC",
    "panels": [
      {
        "id": 1,
        "title": "Cluster Resource Usage",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(container_cpu_usage_seconds_total[5m])) by (instance)",
            "legendFormat": "CPU Usage"
          },
          {
            "expr": "sum(container_memory_usage_bytes) by (instance) / 1024 / 1024 / 1024",
            "legendFormat": "Memory Usage (GB)"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 70},
                {"color": "red", "value": 90}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Service Health Status",
        "type": "table",
        "targets": [
          {
            "expr": "up{job=~\"lugx-.*\"}",
            "format": "table",
            "instant": true
          }
        ],
        "transformations": [
          {
            "id": "organize",
            "options": {
              "includeByName": {
                "job": true,
                "Value": true,
                "instance": true
              },
              "renameByName": {
                "job": "Service",
                "Value": "Status",
                "instance": "Instance"
              }
            }
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "HTTP Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m])) by (service)",
            "legendFormat": "{{service}}"
          }
        ],
        "yAxes": [
          {
            "label": "Requests/sec",
            "min": 0
          }
        ],
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
      },
      {
        "id": 4,
        "title": "Response Time P95",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (service, le))",
            "legendFormat": "{{service}} P95"
          }
        ],
        "yAxes": [
          {
            "label": "Duration (seconds)",
            "min": 0
          }
        ],
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 16}
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
```

### 2.2 Business Metrics Dashboard

```json
{
  "dashboard": {
    "id": null,
    "title": "Lugx Gaming - Business Metrics",
    "tags": ["lugx-gaming", "business"],
    "panels": [
      {
        "id": 1,
        "title": "Active Users",
        "type": "stat",
        "targets": [
          {
            "expr": "active_users_total",
            "legendFormat": "Current Active Users"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "short",
            "color": {"mode": "palette-classic"}
          }
        },
        "gridPos": {"h": 6, "w": 6, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Orders per Hour",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(increase(orders_total[1h]))",
            "legendFormat": "Orders/Hour"
          }
        ],
        "gridPos": {"h": 6, "w": 6, "x": 6, "y": 0}
      },
      {
        "id": 3,
        "title": "Revenue per Hour",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(increase(revenue_total_cents[1h])) / 100",
            "legendFormat": "Revenue/Hour ($)"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "currencyUSD"
          }
        },
        "gridPos": {"h": 6, "w": 6, "x": 12, "y": 0}
      },
      {
        "id": 4,
        "title": "Game Views",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(game_views_total[5m])) * 60",
            "legendFormat": "Views/Minute"
          }
        ],
        "gridPos": {"h": 6, "w": 6, "x": 18, "y": 0}
      },
      {
        "id": 5,
        "title": "Top Games by Views",
        "type": "bargauge",
        "targets": [
          {
            "expr": "topk(10, sum(increase(game_views_total[1h])) by (game_id))",
            "legendFormat": "{{game_id}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 6}
      },
      {
        "id": 6,
        "title": "Conversion Funnel",
        "type": "table",
        "targets": [
          {
            "expr": "sum(increase(game_views_total[1h]))",
            "legendFormat": "Game Views"
          },
          {
            "expr": "sum(increase(cart_operations_total{operation=\"add\"}[1h]))",
            "legendFormat": "Cart Additions"
          },
          {
            "expr": "sum(increase(orders_total{status=\"completed\"}[1h]))",
            "legendFormat": "Completed Orders"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 6}
      }
    ],
    "time": {
      "from": "now-6h",
      "to": "now"
    },
    "refresh": "1m"
  }
}
```

### 2.3 Database Performance Dashboard

```json
{
  "dashboard": {
    "id": null,
    "title": "Lugx Gaming - Database Performance",
    "tags": ["lugx-gaming", "database"],
    "panels": [
      {
        "id": 1,
        "title": "ClickHouse Query Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(clickhouse_query_duration_seconds_bucket[5m])) by (query_type, le))",
            "legendFormat": "{{query_type}} P95"
          },
          {
            "expr": "histogram_quantile(0.50, sum(rate(clickhouse_query_duration_seconds_bucket[5m])) by (query_type, le))",
            "legendFormat": "{{query_type}} P50"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "ClickHouse Event Ingestion Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(clickhouse_events_ingested_total[5m])) by (event_type)",
            "legendFormat": "{{event_type}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "PostgreSQL Connection Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(database_connections_active) by (service, database)",
            "legendFormat": "{{service}}-{{database}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
      },
      {
        "id": 4,
        "title": "Database Error Rates",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(database_errors_total[5m])) by (database, error_type)",
            "legendFormat": "{{database}}-{{error_type}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
      }
    ]
  }
}
```

---

## 3. Alerting Configuration

### 3.1 Critical Alert Rules

```yaml
# monitoring/prometheus/alert_rules/critical_alerts.yml
groups:
- name: critical_alerts
  rules:
  # Service Availability
  - alert: ServiceDown
    expr: up{job=~"lugx-.*"} == 0
    for: 2m
    labels:
      severity: critical
      team: platform
    annotations:
      summary: "Service {{ $labels.job }} is down"
      description: "Service {{ $labels.job }} on instance {{ $labels.instance }} has been down for more than 2 minutes"
      runbook_url: "https://docs.lugxgaming.com/runbooks/service-down"

  # High Error Rate
  - alert: HighErrorRate
    expr: |
      (
        sum(rate(http_requests_total{status=~"5.."}[5m])) by (service) /
        sum(rate(http_requests_total[5m])) by (service)
      ) > 0.05
    for: 5m
    labels:
      severity: critical
      team: platform
    annotations:
      summary: "High error rate on {{ $labels.service }}"
      description: "Error rate is {{ $value | humanizePercentage }} on {{ $labels.service }}"

  # Response Time
  - alert: HighResponseTime
    expr: |
      histogram_quantile(0.95, 
        sum(rate(http_request_duration_seconds_bucket[5m])) by (service, le)
      ) > 2
    for: 5m
    labels:
      severity: warning
      team: platform
    annotations:
      summary: "High response time on {{ $labels.service }}"
      description: "95th percentile response time is {{ $value }}s on {{ $labels.service }}"

  # Database Issues
  - alert: ClickHouseQueryErrors
    expr: |
      sum(rate(clickhouse_query_errors_total[5m])) by (error_type) > 0.1
    for: 3m
    labels:
      severity: critical
      team: data
    annotations:
      summary: "ClickHouse query errors detected"
      description: "ClickHouse is experiencing {{ $value }} errors/sec of type {{ $labels.error_type }}"

  - alert: DatabaseConnectionsHigh
    expr: |
      sum(database_connections_active) by (service, database) > 80
    for: 5m
    labels:
      severity: warning
      team: platform
    annotations:
      summary: "High database connections for {{ $labels.service }}"
      description: "{{ $labels.service }} has {{ $value }} active connections to {{ $labels.database }}"

  # Resource Usage
  - alert: HighMemoryUsage
    expr: |
      (container_memory_usage_bytes / container_spec_memory_limit_bytes) > 0.9
    for: 5m
    labels:
      severity: warning
      team: platform
    annotations:
      summary: "High memory usage on {{ $labels.pod }}"
      description: "Memory usage is {{ $value | humanizePercentage }} on pod {{ $labels.pod }}"

  - alert: HighCPUUsage
    expr: |
      rate(container_cpu_usage_seconds_total[5m]) > 0.8
    for: 10m
    labels:
      severity: warning
      team: platform
    annotations:
      summary: "High CPU usage on {{ $labels.pod }}"
      description: "CPU usage is {{ $value | humanizePercentage }} on pod {{ $labels.pod }}"

  # Business Metrics
  - alert: OrderProcessingFailure
    expr: |
      sum(rate(orders_total{status="failed"}[5m])) > 0.02
    for: 2m
    labels:
      severity: critical
      team: business
    annotations:
      summary: "High order failure rate"
      description: "Order failure rate is {{ $value }}/sec"

  - alert: AnalyticsIngestionDown
    expr: |
      sum(rate(clickhouse_events_ingested_total[5m])) == 0
    for: 3m
    labels:
      severity: critical
      team: data
    annotations:
      summary: "Analytics event ingestion stopped"
      description: "No analytics events have been ingested for 3 minutes"
```

### 3.2 AlertManager Configuration

```yaml
# monitoring/alertmanager/alertmanager.yml
global:
  smtp_smarthost: 'smtp.lugxgaming.com:587'
  smtp_from: 'alerts@lugxgaming.com'
  smtp_auth_username: 'alerts@lugxgaming.com'
  smtp_auth_password: '${SMTP_PASSWORD}'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'default'
  routes:
  - match:
      severity: critical
    receiver: 'critical-alerts'
    group_wait: 5s
    repeat_interval: 5m
  - match:
      team: business
    receiver: 'business-alerts'
  - match:
      team: data
    receiver: 'data-alerts'

receivers:
- name: 'default'
  slack_configs:
  - api_url: '${SLACK_WEBHOOK_URL}'
    channel: '#general-alerts'
    title: 'Lugx Gaming Alert'
    text: |
      {{ range .Alerts }}
      {{ .Annotations.summary }}
      {{ .Annotations.description }}
      {{ end }}

- name: 'critical-alerts'
  pagerduty_configs:
  - routing_key: '${PAGERDUTY_ROUTING_KEY}'
    description: '{{ .GroupLabels.alertname }}: {{ .CommonAnnotations.summary }}'
    details:
      alert_count: '{{ len .Alerts }}'
      alerts: |
        {{ range .Alerts }}
        - {{ .Annotations.summary }}
        {{ end }}
  slack_configs:
  - api_url: '${SLACK_WEBHOOK_URL}'
    channel: '#critical-alerts'
    title: '🚨 CRITICAL ALERT'
    color: 'danger'
    text: |
      {{ range .Alerts }}
      *{{ .Annotations.summary }}*
      {{ .Annotations.description }}
      Runbook: {{ .Annotations.runbook_url }}
      {{ end }}

- name: 'business-alerts'
  email_configs:
  - to: 'business-team@lugxgaming.com'
    subject: 'Business Alert: {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      Severity: {{ .Labels.severity }}
      {{ end }}

- name: 'data-alerts'
  slack_configs:
  - api_url: '${SLACK_WEBHOOK_URL}'
    channel: '#data-alerts'
    title: 'Data Platform Alert'
    text: |
      {{ range .Alerts }}
      {{ .Annotations.summary }}
      {{ .Annotations.description }}
      {{ end }}

inhibit_rules:
- source_match:
    severity: 'critical'
  target_match:
    severity: 'warning'
  equal: ['alertname', 'service']
```

---

## 4. Distributed Tracing with Jaeger

### 4.1 Jaeger Deployment

```yaml
# monitoring/jaeger/jaeger-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jaeger
  namespace: monitoring
  labels:
    app: jaeger
spec:
  replicas: 2
  selector:
    matchLabels:
      app: jaeger
  template:
    metadata:
      labels:
        app: jaeger
    spec:
      containers:
      - name: jaeger
        image: jaegertracing/all-in-one:1.48
        ports:
        - containerPort: 16686
          name: ui
        - containerPort: 14268
          name: collector
        - containerPort: 14250
          name: grpc
        env:
        - name: COLLECTOR_ZIPKIN_HOST_PORT
          value: ":9411"
        - name: SPAN_STORAGE_TYPE
          value: elasticsearch
        - name: ES_SERVER_URLS
          value: "http://elasticsearch:9200"
        - name: ES_USERNAME
          value: "jaeger"
        - name: ES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: jaeger-secrets
              key: elasticsearch-password
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /
            port: 16686
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 16686
          initialDelaySeconds: 10
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: jaeger-service
  namespace: monitoring
spec:
  selector:
    app: jaeger
  ports:
  - name: ui
    port: 16686
    targetPort: 16686
  - name: collector
    port: 14268
    targetPort: 14268
  - name: grpc
    port: 14250
    targetPort: 14250
  type: ClusterIP
```

### 4.2 OpenTelemetry Instrumentation

```python
# services/shared/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
import os

def setup_tracing(service_name: str):
    """Setup distributed tracing for the service"""
    
    # Configure tracer provider
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer_provider()
    
    # Configure Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=os.getenv("JAEGER_AGENT_HOST", "jaeger-service"),
        agent_port=int(os.getenv("JAEGER_AGENT_PORT", "14268")),
        collector_endpoint=f"http://jaeger-service:14268/api/traces",
    )
    
    # Add span processor
    span_processor = BatchSpanProcessor(jaeger_exporter)
    tracer.add_span_processor(span_processor)
    
    # Auto-instrument frameworks
    FastAPIInstrumentor.instrument()
    HTTPXClientInstrumentor.instrument()
    AsyncPGInstrumentor.instrument()
    RedisInstrumentor.instrument()
    
    return trace.get_tracer(service_name)

# Custom tracing decorators
def trace_function(operation_name: str = None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            span_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(span_name) as span:
                # Add function attributes
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("function.result", "success")
                    return result
                except Exception as e:
                    span.set_attribute("function.result", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    raise
        return wrapper
    return decorator

class TracedDatabaseClient:
    def __init__(self, database_url: str, service_name: str):
        self.database_url = database_url
        self.service_name = service_name
        self.tracer = trace.get_tracer(f"{service_name}.database")
    
    async def execute_query(self, query: str, params: dict = None):
        with self.tracer.start_as_current_span("database.query") as span:
            span.set_attribute("db.statement", query)
            span.set_attribute("db.operation", query.split()[0].upper())
            span.set_attribute("service.name", self.service_name)
            
            if params:
                span.set_attribute("db.params.count", len(params))
            
            try:
                # Execute actual database query
                result = await self._execute_query(query, params)
                span.set_attribute("db.rows_affected", len(result) if result else 0)
                return result
            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.type", type(e).__name__)
                raise

class TracedHTTPClient:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.tracer = trace.get_tracer(f"{service_name}.http_client")
    
    async def make_request(self, method: str, url: str, **kwargs):
        with self.tracer.start_as_current_span("http.client.request") as span:
            span.set_attribute("http.method", method)
            span.set_attribute("http.url", url)
            span.set_attribute("service.name", self.service_name)
            
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.request(method, url, **kwargs)
                    
                    span.set_attribute("http.status_code", response.status_code)
                    span.set_attribute("http.response_size", len(response.content))
                    
                    return response
            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.type", type(e).__name__)
                raise
```

---

## 5. Centralized Logging with ELK Stack

### 5.1 Fluentd Configuration

```yaml
# monitoring/logging/fluentd-configmap.yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
  namespace: monitoring
data:
  fluent.conf: |
    <source>
      @type tail
      @id input_tail_container_logs
      path /var/log/containers/*.log
      pos_file /var/log/fluentd-containers.log.pos
      tag kubernetes.*
      read_from_head true
      <parse>
        @type kubernetes
        time_format %Y-%m-%dT%H:%M:%S.%NZ
      </parse>
    </source>

    <filter kubernetes.**>
      @type kubernetes_metadata
      @id filter_kube_metadata
      kubernetes_url "#{ENV['KUBERNETES_SERVICE_HOST']}:#{ENV['KUBERNETES_SERVICE_PORT_HTTPS']}"
      verify_ssl "#{ENV['KUBERNETES_VERIFY_SSL'] || true}"
      ca_file "#{ENV['KUBERNETES_CA_FILE']}"
      skip_labels false
      skip_container_metadata false
      skip_master_url false
      skip_namespace_metadata false
    </filter>

    # Lugx Gaming specific log parsing
    <filter kubernetes.var.log.containers.frontend-**>
      @type parser
      key_name log
      reserve_data true
      remove_key_name_field true
      <parse>
        @type json
        time_key timestamp
        time_format %Y-%m-%dT%H:%M:%S.%3NZ
      </parse>
    </filter>

    <filter kubernetes.var.log.containers.**-service-**>
      @type parser
      key_name log
      reserve_data true
      remove_key_name_field true
      <parse>
        @type json
        time_key timestamp
        time_format %Y-%m-%dT%H:%M:%S.%3NZ
      </parse>
    </filter>

    # Add environment and service labels
    <filter kubernetes.**>
      @type record_transformer
      <record>
        environment "#{ENV['ENVIRONMENT'] || 'production'}"
        cluster "#{ENV['CLUSTER_NAME'] || 'lugx-gaming-prod'}"
        service_name ${record["kubernetes"]["labels"]["app"] || "unknown"}
      </record>
    </filter>

    # Route logs to different indices
    <match kubernetes.var.log.containers.frontend-**>
      @type elasticsearch
      @id out_es_frontend
      host elasticsearch.monitoring.svc.cluster.local
      port 9200
      logstash_format true
      logstash_prefix lugx-frontend
      index_name lugx-frontend
      type_name _doc
      include_tag_key true
      tag_key @log_name
      <buffer>
        @type file
        path /var/log/fluentd-buffers/frontend.buffer
        flush_mode interval
        retry_type exponential_backoff
        flush_thread_count 2
        flush_interval 5s
        retry_forever
        retry_max_interval 30
        chunk_limit_size 2M
        queue_limit_length 8
        overflow_action block
      </buffer>
    </match>

    <match kubernetes.var.log.containers.**-service-**>
      @type elasticsearch
      @id out_es_services
      host elasticsearch.monitoring.svc.cluster.local
      port 9200
      logstash_format true
      logstash_prefix lugx-services
      index_name lugx-services
      type_name _doc
      include_tag_key true
      tag_key @log_name
      <buffer>
        @type file
        path /var/log/fluentd-buffers/services.buffer
        flush_mode interval
        retry_type exponential_backoff
        flush_thread_count 2
        flush_interval 5s
        retry_forever
        retry_max_interval 30
        chunk_limit_size 2M
        queue_limit_length 8
        overflow_action block
      </buffer>
    </match>

    <match kubernetes.**>
      @type elasticsearch
      @id out_es_kubernetes
      host elasticsearch.monitoring.svc.cluster.local
      port 9200
      logstash_format true
      logstash_prefix lugx-kubernetes
      index_name lugx-kubernetes
      type_name _doc
      include_tag_key true
      tag_key @log_name
      <buffer>
        @type file
        path /var/log/fluentd-buffers/kubernetes.buffer
        flush_mode interval
        retry_type exponential_backoff
        flush_thread_count 2
        flush_interval 5s
        retry_forever
        retry_max_interval 30
        chunk_limit_size 2M
        queue_limit_length 8
        overflow_action block
      </buffer>
    </match>
```

### 5.2 Structured Logging Implementation

```python
# services/shared/logging.py
import logging
import json
import traceback
from datetime import datetime
from typing import Any, Dict
from contextvars import ContextVar
from opentelemetry import trace

# Context variables for request correlation
request_id_context: ContextVar[str] = ContextVar('request_id', default='')
user_id_context: ContextVar[str] = ContextVar('user_id', default='')

class StructuredLogger:
    def __init__(self, service_name: str, level: str = "INFO"):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Configure structured logging handler
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)
    
    def _get_base_fields(self) -> Dict[str, Any]:
        """Get base fields for all log entries"""
        span = trace.get_current_span()
        span_context = span.get_span_context()
        
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": self.service_name,
            "environment": os.getenv("ENVIRONMENT", "production"),
            "request_id": request_id_context.get(),
            "user_id": user_id_context.get(),
            "trace_id": format(span_context.trace_id, "032x") if span_context.is_valid else None,
            "span_id": format(span_context.span_id, "016x") if span_context.is_valid else None,
        }
    
    def info(self, message: str, **kwargs):
        """Log info level message"""
        self._log("INFO", message, **kwargs)
    
    def error(self, message: str, error: Exception = None, **kwargs):
        """Log error level message"""
        extra_fields = kwargs
        if error:
            extra_fields.update({
                "error_type": type(error).__name__,
                "error_message": str(error),
                "error_traceback": traceback.format_exc()
            })
        self._log("ERROR", message, **extra_fields)
    
    def warning(self, message: str, **kwargs):
        """Log warning level message"""
        self._log("WARNING", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug level message"""
        self._log("DEBUG", message, **kwargs)
    
    def _log(self, level: str, message: str, **kwargs):
        """Internal logging method"""
        log_entry = self._get_base_fields()
        log_entry.update({
            "level": level,
            "message": message,
            **kwargs
        })
        
        # Use appropriate logging level
        if level == "INFO":
            self.logger.info(json.dumps(log_entry))
        elif level == "ERROR":
            self.logger.error(json.dumps(log_entry))
        elif level == "WARNING":
            self.logger.warning(json.dumps(log_entry))
        elif level == "DEBUG":
            self.logger.debug(json.dumps(log_entry))

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging"""
    
    def format(self, record):
        # Return the message as-is (already JSON formatted)
        return record.getMessage()

# Usage examples for different services
class GameServiceLogger(StructuredLogger):
    def log_game_view(self, game_id: str, user_id: str, category: str):
        self.info(
            "Game viewed",
            event_type="game_view",
            game_id=game_id,
            user_id=user_id,
            category=category
        )
    
    def log_search_query(self, query: str, results_count: int, duration_ms: float):
        self.info(
            "Search performed",
            event_type="search",
            search_query=query,
            results_count=results_count,
            duration_ms=duration_ms
        )

class OrderServiceLogger(StructuredLogger):
    def log_order_created(self, order_id: str, user_id: str, total_amount: float):
        self.info(
            "Order created",
            event_type="order_created",
            order_id=order_id,
            user_id=user_id,
            total_amount=total_amount
        )
    
    def log_payment_processed(self, order_id: str, payment_method: str, status: str):
        self.info(
            "Payment processed",
            event_type="payment_processed",
            order_id=order_id,
            payment_method=payment_method,
            payment_status=status
        )

class AnalyticsServiceLogger(StructuredLogger):
    def log_events_batch_processed(self, event_count: int, processing_time: float):
        self.info(
            "Events batch processed",
            event_type="batch_processed",
            event_count=event_count,
            processing_time_ms=processing_time * 1000
        )
    
    def log_clickhouse_query(self, query_type: str, duration: float, rows_returned: int):
        self.info(
            "ClickHouse query executed",
            event_type="clickhouse_query",
            query_type=query_type,
            duration_ms=duration * 1000,
            rows_returned=rows_returned
        )
```

---

## 6. Health Check and Uptime Monitoring

### 6.1 Health Check Endpoints

```python
# services/shared/health.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import asyncio
import time
from datetime import datetime

router = APIRouter()

class HealthChecker:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.start_time = datetime.utcnow()
        self.checks = {}
    
    def add_check(self, name: str, check_func):
        """Add a health check function"""
        self.checks[name] = check_func
    
    async def run_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}
        overall_healthy = True
        
        for name, check_func in self.checks.items():
            try:
                start_time = time.time()
                result = await check_func()
                duration = (time.time() - start_time) * 1000
                
                results[name] = {
                    "status": "healthy" if result else "unhealthy",
                    "duration_ms": round(duration, 2),
                    "details": result if isinstance(result, dict) else {}
                }
                
                if not result:
                    overall_healthy = False
                    
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "error": str(e),
                    "duration_ms": 0
                }
                overall_healthy = False
        
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            "service": self.service_name,
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "uptime_seconds": round(uptime, 2),
            "checks": results
        }

# Health check implementations for each service
class DatabaseHealthCheck:
    def __init__(self, db_engine):
        self.db_engine = db_engine
    
    async def __call__(self) -> bool:
        try:
            await self.db_engine.execute("SELECT 1")
            return True
        except Exception:
            return False

class RedisHealthCheck:
    def __init__(self, redis_client):
        self.redis_client = redis_client
    
    async def __call__(self) -> bool:
        try:
            await self.redis_client.ping()
            return True
        except Exception:
            return False

class ClickHouseHealthCheck:
    def __init__(self, clickhouse_client):
        self.clickhouse_client = clickhouse_client
    
    async def __call__(self) -> Dict[str, Any]:
        try:
            result = await self.clickhouse_client.execute("SELECT version()")
            return {
                "status": True,
                "version": result[0][0] if result else "unknown"
            }
        except Exception as e:
            return {
                "status": False,
                "error": str(e)
            }

# FastAPI health endpoints
@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    health_checker = HealthChecker("lugx-service")
    
    # Add service-specific checks
    health_checker.add_check("database", DatabaseHealthCheck(db_engine))
    health_checker.add_check("redis", RedisHealthCheck(redis_client))
    
    health_result = await health_checker.run_checks()
    
    if health_result["status"] == "healthy":
        return health_result
    else:
        raise HTTPException(status_code=503, detail=health_result)

@router.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe endpoint"""
    # More stringent checks for readiness
    checks = [
        check_database_ready(),
        check_cache_ready(),
        check_dependencies_ready()
    ]
    
    results = await asyncio.gather(*checks, return_exceptions=True)
    
    if all(result is True for result in results):
        return {"status": "ready"}
    else:
        raise HTTPException(status_code=503, detail={"status": "not_ready", "checks": results})

@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe endpoint"""
    # Basic liveness check
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
```

### 6.2 External Uptime Monitoring

```python
# monitoring/uptime/external_monitor.py
import asyncio
import aiohttp
import time
from typing import List, Dict
from dataclasses import dataclass
from datetime import datetime

@dataclass
class MonitorEndpoint:
    name: str
    url: str
    method: str = "GET"
    timeout: int = 10
    expected_status: int = 200
    check_interval: int = 60

class UptimeMonitor:
    def __init__(self):
        self.endpoints = [
            MonitorEndpoint(
                name="Frontend Homepage",
                url="https://lugxgaming.com",
                check_interval=30
            ),
            MonitorEndpoint(
                name="Game Service API",
                url="https://api.lugxgaming.com/api/v1/games/health",
                check_interval=30
            ),
            MonitorEndpoint(
                name="Order Service API", 
                url="https://api.lugxgaming.com/api/v1/orders/health",
                check_interval=30
            ),
            MonitorEndpoint(
                name="Analytics Service API",
                url="https://api.lugxgaming.com/api/v1/analytics/health",
                check_interval=30
            )
        ]
        
        self.results = {}
    
    async def check_endpoint(self, endpoint: MonitorEndpoint) -> Dict:
        """Check a single endpoint"""
        start_time = time.time()
        
        try:
            timeout = aiohttp.ClientTimeout(total=endpoint.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.request(endpoint.method, endpoint.url) as response:
                    duration = (time.time() - start_time) * 1000
                    
                    result = {
                        "name": endpoint.name,
                        "url": endpoint.url,
                        "status": "up" if response.status == endpoint.expected_status else "down",
                        "status_code": response.status,
                        "response_time_ms": round(duration, 2),
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                    
                    if response.status == endpoint.expected_status:
                        result["details"] = await response.json() if response.content_type == 'application/json' else None
                    
                    return result
                    
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return {
                "name": endpoint.name,
                "url": endpoint.url,
                "status": "down",
                "error": str(e),
                "response_time_ms": round(duration, 2),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def monitor_all_endpoints(self):
        """Monitor all endpoints continuously"""
        while True:
            tasks = [self.check_endpoint(endpoint) for endpoint in self.endpoints]
            results = await asyncio.gather(*tasks)
            
            # Store results and send alerts if needed
            for result in results:
                endpoint_name = result["name"]
                
                # Check if status changed
                previous_status = self.results.get(endpoint_name, {}).get("status")
                current_status = result["status"]
                
                if previous_status and previous_status != current_status:
                    await self.send_status_change_alert(result, previous_status)
                
                self.results[endpoint_name] = result
            
            # Wait for the shortest check interval
            min_interval = min(endpoint.check_interval for endpoint in self.endpoints)
            await asyncio.sleep(min_interval)
    
    async def send_status_change_alert(self, result: Dict, previous_status: str):
        """Send alert when endpoint status changes"""
        if result["status"] == "down" and previous_status == "up":
            # Endpoint went down
            alert_data = {
                "alert_type": "endpoint_down",
                "endpoint": result["name"],
                "url": result["url"],
                "error": result.get("error", "HTTP error"),
                "timestamp": result["timestamp"]
            }
            await self.send_alert(alert_data)
            
        elif result["status"] == "up" and previous_status == "down":
            # Endpoint recovered
            alert_data = {
                "alert_type": "endpoint_recovered",
                "endpoint": result["name"],
                "url": result["url"],
                "timestamp": result["timestamp"]
            }
            await self.send_alert(alert_data)
    
    async def send_alert(self, alert_data: Dict):
        """Send alert to monitoring systems"""
        # Implement actual alerting (Slack, PagerDuty, etc.)
        print(f"ALERT: {alert_data}")

# Run the uptime monitor
async def main():
    monitor = UptimeMonitor()
    await monitor.monitor_all_endpoints()

if __name__ == "__main__":
    asyncio.run(main())
```

This comprehensive observability infrastructure provides complete visibility into the Lugx Gaming platform's performance, health, and business metrics, ensuring rapid issue detection and resolution while maintaining optimal user experience.