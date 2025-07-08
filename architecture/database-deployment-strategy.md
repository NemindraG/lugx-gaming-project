# Lugx Gaming Platform - Database Deployment Strategy

## Executive Summary

This document clarifies the database deployment strategy across all environments for the Lugx Gaming platform. The strategy varies by environment to optimize for development efficiency, testing accuracy, and production reliability while maintaining data consistency and performance.

## Database Deployment Strategy Overview

### Environment-Specific Approach

| Environment | PostgreSQL | ClickHouse | Redis | Deployment Method | Rationale |
|------------|------------|------------|-------|------------------|-----------|
| **Local Dev** | Docker Compose | Docker Compose | Docker Compose | Outside Kubernetes | Fast setup, easy debugging |
| **Staging** | StatefulSet | StatefulSet | StatefulSet | Inside Kubernetes | Production mirror |
| **Production** | Managed Service | Managed Service | Managed Service | Outside Kubernetes | High availability, managed scaling |

---

## 1. Local Development Environment

### 1.1 Database Deployment (Outside Kubernetes)

#### **Why Outside Kubernetes for Local Development?**
- **Faster Startup**: No need to wait for Kubernetes StatefulSets
- **Easier Debugging**: Direct access to database logs and configuration
- **Resource Efficiency**: Less overhead than running databases in Kubernetes
- **Development Speed**: Quick database resets and schema changes
- **Simplified Networking**: Direct localhost connections

#### **Docker Compose Configuration**

```yaml
# docker-compose.databases.yml (Local Development)
version: '3.8'

services:
  # PostgreSQL for Game Service
  postgresql-game:
    image: postgres:15.4-alpine
    container_name: lugx-postgresql-game
    environment:
      POSTGRES_DB: lugx_games_dev
      POSTGRES_USER: lugx_user
      POSTGRES_PASSWORD: lugx_dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgresql_game_data:/var/lib/postgresql/data
      - ./database/init-scripts/game-service:/docker-entrypoint-initdb.d
    networks:
      - lugx-dev-network

  # PostgreSQL for Order Service
  postgresql-order:
    image: postgres:15.4-alpine
    container_name: lugx-postgresql-order
    environment:
      POSTGRES_DB: lugx_orders_dev
      POSTGRES_USER: lugx_user
      POSTGRES_PASSWORD: lugx_dev_password
    ports:
      - "5433:5432"
    volumes:
      - postgresql_order_data:/var/lib/postgresql/data
      - ./database/init-scripts/order-service:/docker-entrypoint-initdb.d
    networks:
      - lugx-dev-network

  # ClickHouse for Analytics Service (Enhanced for Web Analytics)
  clickhouse:
    image: clickhouse/clickhouse-server:23.8.4-alpine
    container_name: lugx-clickhouse
    environment:
      CLICKHOUSE_DB: lugx_analytics_dev
      CLICKHOUSE_USER: lugx_user
      CLICKHOUSE_PASSWORD: lugx_dev_password
      CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT: 1
    ports:
      - "8123:8123"  # HTTP interface for API access
      - "9000:9000"  # Native interface for high-performance queries
      - "9009:9009"  # Inter-server communication
    volumes:
      - clickhouse_data:/var/lib/clickhouse
      - ./database/init-scripts/analytics-service:/docker-entrypoint-initdb.d
      - ./config/clickhouse/config.xml:/etc/clickhouse-server/config.xml
      - ./config/clickhouse/users.xml:/etc/clickhouse-server/users.xml
      - ./config/clickhouse/web-analytics-schema.sql:/docker-entrypoint-initdb.d/01-web-analytics-schema.sql
    networks:
      - lugx-dev-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8123/ping"]
      interval: 30s
      timeout: 5s
      retries: 3
    # Performance settings for web analytics
    ulimits:
      nofile:
        soft: 65536
        hard: 65536
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G

  # Redis for Caching and Sessions
  redis:
    image: redis:7.2.1-alpine
    container_name: lugx-redis
    command: redis-server --appendonly yes --requirepass lugx_dev_password
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - lugx-dev-network

volumes:
  postgresql_game_data:
  postgresql_order_data:
  clickhouse_data:
  redis_data:

networks:
  lugx-dev-network:
    driver: bridge
```

#### **Service Connection Configuration**

```python
# Local Development Database Connections
LOCAL_DB_CONFIG = {
    "game_service": {
        "database_url": "postgresql://lugx_user:lugx_dev_password@localhost:5432/lugx_games_dev",
        "pool_size": 20,
        "max_overflow": 10
    },
    "order_service": {
        "database_url": "postgresql://lugx_user:lugx_dev_password@localhost:5433/lugx_orders_dev",
        "pool_size": 50,
        "max_overflow": 20
    },
    "analytics_service": {
        "clickhouse_url": "clickhouse://lugx_user:lugx_dev_password@localhost:9000/lugx_analytics_dev",
        "pool_size": 30,
        "max_overflow": 10,
        "batch_size": 1000
    },
    "redis": {
        "url": "redis://:lugx_dev_password@localhost:6379/0",
        "max_connections": 100
    }
}
```

---

## 2. Staging Environment

### 2.1 Database Deployment (Inside Kubernetes)

#### **Why Inside Kubernetes for Staging?**
- **Production Mirror**: Replicates production Kubernetes deployment patterns
- **Service Mesh Integration**: Full Istio observability and security
- **Resource Management**: Kubernetes resource limits and requests
- **Backup Testing**: Test backup and recovery procedures
- **Network Policies**: Test security and network isolation

#### **PostgreSQL StatefulSet Configuration**

```yaml
# infrastructure/kubernetes/base/postgresql-game.yml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql-game
  labels:
    app: postgresql-game
spec:
  serviceName: postgresql-game
  replicas: 1
  selector:
    matchLabels:
      app: postgresql-game
  template:
    metadata:
      labels:
        app: postgresql-game
    spec:
      containers:
      - name: postgresql
        image: postgres:15.4-alpine
        ports:
        - containerPort: 5432
          name: postgres
        env:
        - name: POSTGRES_DB
          value: "lugx_games_staging"
        - name: POSTGRES_USER
          value: "lugx_user"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgresql-secret
              key: password
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        volumeMounts:
        - name: postgresql-storage
          mountPath: /var/lib/postgresql/data
        - name: init-scripts
          mountPath: /docker-entrypoint-initdb.d
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - lugx_user
            - -d
            - lugx_games_staging
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - lugx_user
            - -d
            - lugx_games_staging
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: init-scripts
        configMap:
          name: postgresql-game-init
  volumeClaimTemplates:
  - metadata:
      name: postgresql-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 20Gi
      storageClassName: ssd-retain

---
apiVersion: v1
kind: Service
metadata:
  name: postgresql-game
  labels:
    app: postgresql-game
spec:
  ports:
  - port: 5432
    targetPort: 5432
    name: postgres
  selector:
    app: postgresql-game
  type: ClusterIP
```

#### **ClickHouse StatefulSet Configuration**

```yaml
# infrastructure/kubernetes/base/clickhouse.yml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: clickhouse
  labels:
    app: clickhouse
spec:
  serviceName: clickhouse
  replicas: 1
  selector:
    matchLabels:
      app: clickhouse
  template:
    metadata:
      labels:
        app: clickhouse
    spec:
      containers:
      - name: clickhouse
        image: clickhouse/clickhouse-server:23.8.4-alpine
        ports:
        - containerPort: 8123
          name: http
        - containerPort: 9000
          name: native
        env:
        - name: CLICKHOUSE_DB
          value: "lugx_analytics_staging"
        - name: CLICKHOUSE_USER
          value: "lugx_user"
        - name: CLICKHOUSE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: clickhouse-secret
              key: password
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        volumeMounts:
        - name: clickhouse-storage
          mountPath: /var/lib/clickhouse
        - name: clickhouse-config
          mountPath: /etc/clickhouse-server/config.xml
          subPath: config.xml
        livenessProbe:
          httpGet:
            path: /ping
            port: 8123
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ping
            port: 8123
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: clickhouse-config
        configMap:
          name: clickhouse-config
  volumeClaimTemplates:
  - metadata:
      name: clickhouse-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
      storageClassName: ssd-retain

---
apiVersion: v1
kind: Service
metadata:
  name: clickhouse
  labels:
    app: clickhouse
spec:
  ports:
  - port: 8123
    targetPort: 8123
    name: http
  - port: 9000
    targetPort: 9000
    name: native
  selector:
    app: clickhouse
  type: ClusterIP
```

#### **Redis StatefulSet Configuration**

```yaml
# infrastructure/kubernetes/base/redis.yml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
  labels:
    app: redis
spec:
  serviceName: redis
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7.2.1-alpine
        ports:
        - containerPort: 6379
          name: redis
        command:
        - redis-server
        - --appendonly
        - "yes"
        - --requirepass
        - $(REDIS_PASSWORD)
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: password
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"
        volumeMounts:
        - name: redis-storage
          mountPath: /data
        livenessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 5
          periodSeconds: 5
  volumeClaimTemplates:
  - metadata:
      name: redis-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
      storageClassName: ssd-retain

---
apiVersion: v1
kind: Service
metadata:
  name: redis
  labels:
    app: redis
spec:
  ports:
  - port: 6379
    targetPort: 6379
    name: redis
  selector:
    app: redis
  type: ClusterIP
```

---

## 3. Production Environment

### 3.1 Database Deployment (Managed Services - Outside Kubernetes)

#### **Why Managed Services for Production?**
- **High Availability**: 99.99% uptime SLA with automatic failover
- **Automated Backups**: Point-in-time recovery and automated backup scheduling
- **Managed Scaling**: Automatic scaling based on load and performance metrics
- **Security**: Managed encryption, patching, and security updates
- **Cost Efficiency**: Pay-as-you-use with optimized resource allocation
- **Expert Support**: 24/7 support from cloud provider database experts

#### **AWS Production Database Configuration**

```yaml
# infrastructure/terraform/production/databases.tf
# PostgreSQL - AWS RDS
resource "aws_db_instance" "game_service_db" {
  identifier = "lugx-games-prod"
  
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.r6g.xlarge"
  
  allocated_storage     = 100
  max_allocated_storage = 1000
  storage_type         = "gp3"
  storage_encrypted    = true
  
  db_name  = "lugx_games_prod"
  username = "lugx_admin"
  password = var.db_password
  
  # High Availability
  multi_az               = true
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  # Security
  vpc_security_group_ids = [aws_security_group.db_security_group.id]
  db_subnet_group_name   = aws_db_subnet_group.db_subnet_group.name
  
  # Monitoring
  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_enhanced_monitoring.arn
  
  # Performance Insights
  performance_insights_enabled = true
  performance_insights_retention_period = 7
  
  # Deletion protection
  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "lugx-games-prod-final-snapshot"
  
  tags = {
    Name        = "Lugx Games Production Database"
    Environment = "production"
    Service     = "game-service"
  }
}

resource "aws_db_instance" "order_service_db" {
  identifier = "lugx-orders-prod"
  
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.r6g.2xlarge"  # Larger for order processing
  
  allocated_storage     = 200
  max_allocated_storage = 2000
  storage_type         = "gp3"
  storage_encrypted    = true
  
  db_name  = "lugx_orders_prod"
  username = "lugx_admin"
  password = var.db_password
  
  # High Availability
  multi_az               = true
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  # Read Replica for scaling
  replicate_source_db = null  # Will create read replicas separately
  
  tags = {
    Name        = "Lugx Orders Production Database"
    Environment = "production"
    Service     = "order-service"
  }
}

# ClickHouse - Production Cluster for High-Volume Web Analytics
resource "aws_instance" "clickhouse_cluster" {
  count = 6  # Increased for web analytics volume
  
  ami           = "ami-0c02fb55956c7d316"  # Amazon Linux 2
  instance_type = "r6g.4xlarge"  # Upgraded for web analytics performance
  
  vpc_security_group_ids = [aws_security_group.clickhouse_security_group.id]
  subnet_id              = aws_subnet.private_subnets[count.index % 3].id
  
  # Enhanced storage for web analytics
  root_block_device {
    volume_size = 200
    volume_type = "gp3"
    iops        = 16000
    throughput  = 1000
    encrypted   = true
  }
  
  # High-performance storage for analytics data
  ebs_block_device {
    device_name = "/dev/sdf"
    volume_size = 2000  # Increased for web analytics volume
    volume_type = "gp3"
    iops        = 16000
    throughput  = 1000
    encrypted   = true
  }
  
  # Additional storage for distributed tables
  ebs_block_device {
    device_name = "/dev/sdg"
    volume_size = 1000
    volume_type = "gp3"
    iops        = 12000
    throughput  = 750
    encrypted   = true
  }
  
  user_data = templatefile("${path.module}/clickhouse-web-analytics-init.sh", {
    cluster_name = "lugx-analytics-prod"
    node_index   = count.index
    is_replica   = count.index >= 3
    shard_num    = (count.index % 3) + 1
    replica_num  = (count.index < 3) ? 1 : 2
  })
  
  # Enhanced performance settings
  instance_metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }
  
  monitoring = true
  
  tags = {
    Name        = "Lugx ClickHouse ${count.index < 3 ? "Shard" : "Replica"} ${count.index + 1}"
    Environment = "production"
    Service     = "analytics-service"
    Cluster     = "lugx-analytics-prod"
    Role        = count.index < 3 ? "primary" : "replica"
    Shard       = (count.index % 3) + 1
    Purpose     = "web-analytics"
  }
}

# ClickHouse Load Balancer for High Availability
resource "aws_lb" "clickhouse_nlb" {
  name               = "lugx-clickhouse-nlb"
  internal           = true
  load_balancer_type = "network"
  subnets            = aws_subnet.private_subnets[*].id

  enable_deletion_protection = true

  tags = {
    Name        = "Lugx ClickHouse Network Load Balancer"
    Environment = "production"
    Service     = "analytics-service"
  }
}

resource "aws_lb_target_group" "clickhouse_http" {
  name     = "lugx-clickhouse-http"
  port     = 8123
  protocol = "TCP"
  vpc_id   = aws_vpc.main.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/ping"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name = "Lugx ClickHouse HTTP Target Group"
  }
}

resource "aws_lb_target_group" "clickhouse_native" {
  name     = "lugx-clickhouse-native"
  port     = 9000
  protocol = "TCP"
  vpc_id   = aws_vpc.main.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    port                = 8123
    protocol            = "HTTP"
    path                = "/ping"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name = "Lugx ClickHouse Native Target Group"
  }
}

# ClickHouse Auto Scaling for Web Analytics Load
resource "aws_autoscaling_group" "clickhouse_asg" {
  name                = "lugx-clickhouse-asg"
  vpc_zone_identifier = aws_subnet.private_subnets[*].id
  target_group_arns   = [aws_lb_target_group.clickhouse_http.arn]
  health_check_type   = "ELB"
  health_check_grace_period = 300

  min_size         = 6
  max_size         = 12
  desired_capacity = 6

  launch_template {
    id      = aws_launch_template.clickhouse_lt.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "Lugx ClickHouse ASG"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = "production"
    propagate_at_launch = true
  }
}

# Redis - AWS ElastiCache
resource "aws_elasticache_replication_group" "redis_cluster" {
  replication_group_id       = "lugx-redis-prod"
  description                = "Lugx Gaming Redis Cluster"
  
  node_type                  = "cache.r6g.xlarge"
  port                       = 6379
  parameter_group_name       = "default.redis7"
  
  num_cache_clusters         = 3
  automatic_failover_enabled = true
  multi_az_enabled          = true
  
  subnet_group_name = aws_elasticache_subnet_group.redis_subnet_group.name
  security_group_ids = [aws_security_group.redis_security_group.id]
  
  # Encryption
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = var.redis_auth_token
  
  # Backup
  snapshot_retention_limit = 5
  snapshot_window         = "03:00-05:00"
  
  # Maintenance
  maintenance_window = "sun:05:00-sun:07:00"
  
  tags = {
    Name        = "Lugx Gaming Redis Cluster"
    Environment = "production"
  }
}
```

#### **Service Connection Configuration for Production**

```python
# Production Database Connections
PRODUCTION_DB_CONFIG = {
    "game_service": {
        "database_url": "postgresql://lugx_admin:${DB_PASSWORD}@lugx-games-prod.cluster-xyz.us-west-2.rds.amazonaws.com:5432/lugx_games_prod",
        "pool_size": 20,
        "max_overflow": 50,
        "ssl_mode": "require"
    },
    "order_service": {
        "database_url": "postgresql://lugx_admin:${DB_PASSWORD}@lugx-orders-prod.cluster-abc.us-west-2.rds.amazonaws.com:5432/lugx_orders_prod",
        "pool_size": 50,
        "max_overflow": 100,
        "ssl_mode": "require"
    },
    "analytics_service": {
        "clickhouse_url": "clickhouse://lugx_admin:${DB_PASSWORD}@clickhouse-prod-lb.lugxgaming.com:9000/lugx_analytics_prod",
        "cluster": "lugx-analytics-prod",
        "batch_size": 10000,
        "ssl": True
    },
    "redis": {
        "url": "rediss://:${REDIS_AUTH_TOKEN}@lugx-redis-prod.xyz.cache.amazonaws.com:6379/0",
        "max_connections": 100,
        "ssl": True
    }
}
```

---

## 4. Database Migration Strategy

### 4.1 Environment-Specific Migration Approach

#### **Migration Pipeline**

```bash
#!/bin/bash
# scripts/migrate-databases.sh

ENVIRONMENT=$1

case $ENVIRONMENT in
  "local")
    echo "🔄 Running local database migrations..."
    
    # Game Service
    cd services/game-service
    alembic upgrade head
    cd ../../
    
    # Order Service  
    cd services/order-service
    alembic upgrade head
    cd ../../
    
    # Analytics Service
    cd services/analytics-service
    python scripts/migrate_clickhouse.py --env=local
    cd ../../
    ;;
    
  "staging")
    echo "🔄 Running staging database migrations..."
    
    # Connect to staging cluster
    kubectl config use-context staging-cluster
    
    # Run migrations via Kubernetes jobs
    kubectl apply -f infrastructure/kubernetes/jobs/migration-game-service.yml
    kubectl apply -f infrastructure/kubernetes/jobs/migration-order-service.yml
    kubectl apply -f infrastructure/kubernetes/jobs/migration-analytics-service.yml
    
    # Wait for completion
    kubectl wait --for=condition=complete --timeout=600s job/game-service-migration
    kubectl wait --for=condition=complete --timeout=600s job/order-service-migration
    kubectl wait --for=condition=complete --timeout=600s job/analytics-service-migration
    ;;
    
  "production")
    echo "🔄 Running production database migrations..."
    
    # Requires manual approval for production
    read -p "Are you sure you want to run production migrations? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
      echo "Migration cancelled"
      exit 1
    fi
    
    # Run migrations against managed services
    PGPASSWORD=$PROD_DB_PASSWORD psql -h lugx-games-prod.cluster-xyz.us-west-2.rds.amazonaws.com -U lugx_admin -d lugx_games_prod -f migrations/game-service/latest.sql
    PGPASSWORD=$PROD_DB_PASSWORD psql -h lugx-orders-prod.cluster-abc.us-west-2.rds.amazonaws.com -U lugx_admin -d lugx_orders_prod -f migrations/order-service/latest.sql
    
    # ClickHouse migrations
    python scripts/migrate_clickhouse_prod.py
    ;;
    
  *)
    echo "Usage: $0 {local|staging|production}"
    exit 1
    ;;
esac
```

---

## 5. Backup and Recovery Strategy

### 5.1 Environment-Specific Backup Policies

| Environment | PostgreSQL | ClickHouse | Redis | Retention |
|------------|------------|------------|-------|-----------|
| **Local** | Manual snapshots | Manual exports | Not required | As needed |
| **Staging** | Daily backups | Daily exports | Daily snapshots | 7 days |
| **Production** | Continuous + Daily | Continuous + Daily | Daily snapshots | 30 days |

### 5.2 Production Backup Configuration

```yaml
# Production Backup Jobs
apiVersion: batch/v1
kind: CronJob
metadata:
  name: database-backup-job
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: lugx-gaming/backup-tool:latest
            env:
            - name: BACKUP_TYPE
              value: "full"
            - name: S3_BUCKET
              value: "lugx-gaming-backups"
            - name: RETENTION_DAYS
              value: "30"
            command:
            - /scripts/backup-all-databases.sh
          restartPolicy: OnFailure
```

## Summary

This database deployment strategy ensures:

- **🚀 Fast Development**: Docker Compose for local development
- **🧪 Accurate Testing**: Kubernetes StatefulSets in staging
- **🛡️ Production Reliability**: Managed cloud services for production
- **📊 Consistent Schema**: Same database structure across all environments
- **🔄 Smooth Migrations**: Environment-appropriate migration strategies
- **💾 Reliable Backups**: Comprehensive backup and recovery procedures

The hybrid approach balances development speed, testing accuracy, and production reliability while maintaining consistent data models across all environments.