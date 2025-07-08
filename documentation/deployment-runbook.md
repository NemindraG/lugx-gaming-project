# Lugx Gaming Platform - Deployment Runbook

## Executive Summary

This runbook provides step-by-step procedures for deploying the Lugx Gaming platform to production environments. It covers initial setup, routine deployments, rollback procedures, and troubleshooting guides to ensure reliable and consistent deployments.

## Quick Reference

### 🚀 **Emergency Contacts**
- **Platform Team Lead**: platform-lead@lugxgaming.com
- **DevOps Engineer**: devops@lugxgaming.com  
- **On-Call Engineer**: +1-XXX-XXX-XXXX
- **Slack Channel**: #devops-alerts

### 📋 **Pre-Deployment Checklist**
- [ ] All tests passing in CI/CD pipeline
- [ ] Security scans completed
- [ ] Database migrations reviewed
- [ ] Rollback plan confirmed
- [ ] Monitoring alerts configured
- [ ] Team notified of deployment window

---

## 1. Environment Overview

### 1.1 Environment Architecture

```yaml
Environments:
  Development:
    Purpose: Local development and testing
    Infrastructure: Docker Compose
    Database: PostgreSQL + ClickHouse (single node)
    Monitoring: Basic logging
    
  Staging:
    Purpose: Integration testing and pre-production validation
    Infrastructure: Kubernetes (minikube/EKS)
    Database: PostgreSQL + ClickHouse (small cluster)
    Monitoring: Full observability stack
    
  Production:
    Purpose: Live user traffic
    Infrastructure: Amazon EKS
    Database: RDS + ClickHouse cluster + ElastiCache
    Monitoring: Full observability + alerting
```

### 1.2 Infrastructure Components

```yaml
Production Infrastructure:
  Kubernetes Cluster:
    Provider: Amazon EKS
    Version: 1.28
    Node Groups: 
      - General Purpose: t3.medium (3-10 nodes)
      - Compute Optimized: c5.large (2-5 nodes)
    
  Databases:
    PostgreSQL: 
      - Game Service: RDS PostgreSQL 15
      - Order Service: RDS PostgreSQL 15
    ClickHouse: EC2 cluster (6 nodes)
    Redis: ElastiCache (3 node cluster)
    
  Load Balancers:
    External: AWS Application Load Balancer
    Internal: Istio Gateway + VirtualServices
    
  Storage:
    Container Images: Amazon ECR
    Static Assets: Amazon S3 + CloudFront
    Backups: S3 with cross-region replication
```

---

## 2. Prerequisites and Access Requirements

### 2.1 Required Tools

```bash
# Install required CLI tools
# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Helm
curl https://get.helm.sh/helm-v3.13.0-linux-amd64.tar.gz | tar xz
sudo mv linux-amd64/helm /usr/local/bin/

# Docker
sudo apt-get update && sudo apt-get install docker.io
sudo usermod -aG docker $USER

# Additional tools
sudo apt-get install jq curl git
```

### 2.2 Access Configuration

```bash
# Configure AWS credentials
aws configure
# AWS Access Key ID: [Enter your access key]
# AWS Secret Access Key: [Enter your secret key]
# Default region name: us-west-2
# Default output format: json

# Configure kubectl for EKS
aws eks update-kubeconfig --region us-west-2 --name lugx-gaming-prod

# Verify access
kubectl get nodes
kubectl get namespaces

# Configure container registry access
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-west-2.amazonaws.com
```

### 2.3 Environment Variables

```bash
# Create deployment environment file
cat > .env.deployment << EOF
# AWS Configuration
AWS_REGION=us-west-2
AWS_ACCOUNT_ID=123456789012
EKS_CLUSTER_NAME=lugx-gaming-prod

# Container Registry
ECR_REGISTRY=123456789012.dkr.ecr.us-west-2.amazonaws.com

# Kubernetes Namespaces
NAMESPACE_PROD=production
NAMESPACE_STAGING=staging

# Database Connections
GAME_DB_HOST=lugx-games-prod.cluster-xyz.us-west-2.rds.amazonaws.com
ORDER_DB_HOST=lugx-orders-prod.cluster-abc.us-west-2.rds.amazonaws.com
CLICKHOUSE_HOST=clickhouse-nlb.lugx-gaming.internal
REDIS_HOST=lugx-redis-prod.cache.amazonaws.com

# Monitoring
PROMETHEUS_URL=http://prometheus.monitoring.svc.cluster.local:9090
GRAFANA_URL=https://monitoring.lugxgaming.com
JAEGER_URL=http://jaeger.monitoring.svc.cluster.local:16686
EOF

# Source environment variables
source .env.deployment
```

---

## 3. Initial Production Setup

### 3.1 One-Time Infrastructure Setup

```bash
#!/bin/bash
# scripts/setup-production-infrastructure.sh

set -e
source .env.deployment

echo "🚀 Setting up Lugx Gaming production infrastructure..."

# Create EKS cluster (if not exists)
if ! aws eks describe-cluster --name $EKS_CLUSTER_NAME &>/dev/null; then
    echo "Creating EKS cluster..."
    eksctl create cluster --name $EKS_CLUSTER_NAME --region $AWS_REGION --version 1.28 --nodegroup-name workers --node-type t3.medium --nodes 3 --nodes-min 1 --nodes-max 10
fi

# Create namespaces
kubectl create namespace $NAMESPACE_PROD --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace istio-system --dry-run=client -o yaml | kubectl apply -f -

# Install Istio service mesh
if ! kubectl get namespace istio-system &>/dev/null; then
    echo "Installing Istio..."
    curl -L https://istio.io/downloadIstio | sh -
    cd istio-* && export PATH=$PWD/bin:$PATH
    istioctl install --set values.defaultRevision=default -y
    kubectl label namespace $NAMESPACE_PROD istio-injection=enabled
fi

# Install monitoring stack
echo "Installing monitoring stack..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
helm repo update

# Install Prometheus
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
    --namespace monitoring \
    --set prometheus.prometheusSpec.retention=30d \
    --set grafana.enabled=true \
    --set grafana.adminPassword=admin123

# Install Jaeger
helm upgrade --install jaeger jaegertracing/jaeger \
    --namespace monitoring \
    --set provisionDataStore.cassandra=false \
    --set storage.type=elasticsearch

echo "✅ Infrastructure setup complete!"
```

### 3.2 Database Initialization

```bash
#!/bin/bash
# scripts/initialize-databases.sh

set -e
source .env.deployment

echo "🗄️ Initializing production databases..."

# Initialize PostgreSQL databases
echo "Initializing PostgreSQL databases..."

# Game Service Database
PGPASSWORD=$GAME_DB_PASSWORD psql -h $GAME_DB_HOST -U lugx_admin -d lugx_games_prod << EOF
-- Create schemas and initial data
\i database/migrations/game-service/001_initial_schema.sql
\i database/migrations/game-service/002_seed_data.sql
EOF

# Order Service Database  
PGPASSWORD=$ORDER_DB_PASSWORD psql -h $ORDER_DB_HOST -U lugx_admin -d lugx_orders_prod << EOF
-- Create schemas and initial data
\i database/migrations/order-service/001_initial_schema.sql
\i database/migrations/order-service/002_seed_data.sql
EOF

# Initialize ClickHouse
echo "Initializing ClickHouse database..."
curl -X POST "${CLICKHOUSE_HOST}:8123/" \
    --user "lugx_admin:${CLICKHOUSE_PASSWORD}" \
    --data-binary @database/migrations/analytics-service/001_clickhouse_schema.sql

echo "✅ Database initialization complete!"
```

### 3.3 Secrets and ConfigMaps

```bash
#!/bin/bash
# scripts/setup-secrets.sh

set -e
source .env.deployment

echo "🔐 Setting up Kubernetes secrets and config maps..."

# Create database secrets
kubectl create secret generic game-service-secrets \
    --namespace=$NAMESPACE_PROD \
    --from-literal=database-url="postgresql://lugx_admin:${GAME_DB_PASSWORD}@${GAME_DB_HOST}:5432/lugx_games_prod" \
    --from-literal=redis-url="redis://${REDIS_HOST}:6379/0" \
    --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic order-service-secrets \
    --namespace=$NAMESPACE_PROD \
    --from-literal=database-url="postgresql://lugx_admin:${ORDER_DB_PASSWORD}@${ORDER_DB_HOST}:5432/lugx_orders_prod" \
    --from-literal=redis-url="redis://${REDIS_HOST}:6379/1" \
    --from-literal=jwt-secret="${JWT_SECRET}" \
    --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic analytics-service-secrets \
    --namespace=$NAMESPACE_PROD \
    --from-literal=clickhouse-url="http://lugx_admin:${CLICKHOUSE_PASSWORD}@${CLICKHOUSE_HOST}:8123/lugx_analytics" \
    --from-literal=redis-url="redis://${REDIS_HOST}:6379/2" \
    --dry-run=client -o yaml | kubectl apply -f -

# Create TLS certificates secret
kubectl create secret tls lugx-gaming-tls \
    --namespace=$NAMESPACE_PROD \
    --cert=certificates/lugxgaming.com.crt \
    --key=certificates/lugxgaming.com.key \
    --dry-run=client -o yaml | kubectl apply -f -

# Create application config map
kubectl create configmap app-config \
    --namespace=$NAMESPACE_PROD \
    --from-literal=environment=production \
    --from-literal=log-level=INFO \
    --from-literal=api-version=v1 \
    --dry-run=client -o yaml | kubectl apply -f -

echo "✅ Secrets and config maps created!"
```

---

## 4. Standard Deployment Procedures

### 4.1 Pre-Deployment Validation

```bash
#!/bin/bash
# scripts/pre-deployment-validation.sh

set -e
source .env.deployment

echo "🔍 Running pre-deployment validation..."

# Check CI/CD pipeline status
echo "Checking CI/CD pipeline status..."
if ! gh run list --status success --limit 1 | grep -q "success"; then
    echo "❌ Latest CI/CD run not successful. Aborting deployment."
    exit 1
fi

# Validate Docker images exist
echo "Validating container images..."
SERVICES=("frontend" "game-service" "order-service" "analytics-service")
IMAGE_TAG=${1:-latest}

for service in "${SERVICES[@]}"; do
    if ! aws ecr describe-images --repository-name lugx-$service --image-ids imageTag=$IMAGE_TAG &>/dev/null; then
        echo "❌ Image lugx-$service:$IMAGE_TAG not found in ECR"
        exit 1
    fi
done

# Check cluster health
echo "Checking cluster health..."
if ! kubectl get nodes | grep -q "Ready"; then
    echo "❌ Cluster nodes not ready"
    exit 1
fi

# Check resource availability
echo "Checking resource availability..."
AVAILABLE_CPU=$(kubectl top nodes | awk 'NR>1 {sum+=$3} END {print sum}')
AVAILABLE_MEMORY=$(kubectl top nodes | awk 'NR>1 {sum+=$5} END {print sum}')

echo "Available CPU: ${AVAILABLE_CPU}m"
echo "Available Memory: ${AVAILABLE_MEMORY}Mi"

# Check database connectivity
echo "Checking database connectivity..."
if ! kubectl run --rm -i --tty db-test --image=postgres:15 --restart=Never -- psql $GAME_DB_URL -c "SELECT 1;" &>/dev/null; then
    echo "❌ Cannot connect to Game Service database"
    exit 1
fi

# Check external dependencies
echo "Checking external dependencies..."
if ! curl -f https://api.stripe.com/v1/charges --user $STRIPE_SECRET_KEY: -X GET &>/dev/null; then
    echo "⚠️  Warning: Stripe API not accessible"
fi

echo "✅ Pre-deployment validation passed!"
```

### 4.2 Rolling Deployment Process

```bash
#!/bin/bash
# scripts/deploy-rolling-update.sh

set -e
source .env.deployment

IMAGE_TAG=${1:-latest}
NAMESPACE=${2:-$NAMESPACE_PROD}

echo "🚀 Starting rolling deployment of Lugx Gaming platform..."
echo "Image Tag: $IMAGE_TAG"
echo "Namespace: $NAMESPACE"

# Pre-deployment validation
./scripts/pre-deployment-validation.sh $IMAGE_TAG

# Function to deploy a service with rolling update
deploy_service() {
    local service_name=$1
    local image_tag=$2
    local namespace=$3
    
    echo "Deploying $service_name..."
    
    # Update deployment image
    kubectl set image deployment/${service_name}-deployment \
        $service_name=$ECR_REGISTRY/lugx-$service_name:$image_tag \
        -n $namespace
    
    # Wait for rollout to complete
    kubectl rollout status deployment/${service_name}-deployment -n $namespace --timeout=600s
    
    if [ $? -eq 0 ]; then
        echo "✅ $service_name deployment successful"
    else
        echo "❌ $service_name deployment failed"
        echo "Rolling back $service_name..."
        kubectl rollout undo deployment/${service_name}-deployment -n $namespace
        exit 1
    fi
    
    # Health check
    sleep 30
    if ! kubectl get pods -n $namespace -l app=$service_name | grep -q "Running"; then
        echo "❌ $service_name pods not running correctly"
        kubectl rollout undo deployment/${service_name}-deployment -n $namespace
        exit 1
    fi
}

# Deploy services in dependency order
echo "📦 Deploying services..."

# 1. Deploy backend services first
deploy_service "game-service" $IMAGE_TAG $NAMESPACE
deploy_service "order-service" $IMAGE_TAG $NAMESPACE  
deploy_service "analytics-service" $IMAGE_TAG $NAMESPACE

# 2. Deploy frontend last
deploy_service "frontend" $IMAGE_TAG $NAMESPACE

# Post-deployment health checks
echo "🏥 Running post-deployment health checks..."
./scripts/post-deployment-health-check.sh $NAMESPACE

# Update monitoring dashboards
echo "📊 Updating monitoring dashboards..."
curl -X POST "$PROMETHEUS_URL/api/v1/admin/tsdb/snapshot" -H "Content-Type: application/json"

# Send deployment notification
echo "📢 Sending deployment notification..."
curl -X POST $SLACK_WEBHOOK_URL -H 'Content-type: application/json' \
    --data "{\"text\":\"✅ Lugx Gaming deployment successful!\n**Version:** $IMAGE_TAG\n**Namespace:** $NAMESPACE\n**Time:** $(date)\"}"

echo "🎉 Deployment completed successfully!"
```

### 4.3 Post-Deployment Health Checks

```bash
#!/bin/bash
# scripts/post-deployment-health-check.sh

set -e
source .env.deployment

NAMESPACE=${1:-$NAMESPACE_PROD}
BASE_URL="https://lugxgaming.com"

echo "🏥 Running comprehensive post-deployment health checks..."

# Function to check endpoint with retry
check_endpoint() {
    local url=$1
    local expected_status=${2:-200}
    local max_attempts=5
    local wait_time=10
    
    for attempt in $(seq 1 $max_attempts); do
        echo "Checking $url (attempt $attempt/$max_attempts)..."
        
        status_code=$(curl -s -o /dev/null -w "%{http_code}" $url || echo "000")
        
        if [ "$status_code" -eq "$expected_status" ]; then
            echo "✅ $url returned $status_code"
            return 0
        else
            echo "⚠️  $url returned $status_code, expected $expected_status"
            if [ $attempt -lt $max_attempts ]; then
                echo "Retrying in $wait_time seconds..."
                sleep $wait_time
            fi
        fi
    done
    
    echo "❌ $url health check failed after $max_attempts attempts"
    return 1
}

# Check Kubernetes deployments
echo "Checking Kubernetes deployments..."
SERVICES=("frontend" "game-service" "order-service" "analytics-service")

for service in "${SERVICES[@]}"; do
    if ! kubectl rollout status deployment/${service}-deployment -n $NAMESPACE --timeout=60s; then
        echo "❌ $service deployment not ready"
        exit 1
    fi
done

# Check service endpoints
echo "Checking service endpoints..."
check_endpoint "$BASE_URL/health" 200
check_endpoint "$BASE_URL/api/v1/games/health" 200
check_endpoint "$BASE_URL/api/v1/orders/health" 200
check_endpoint "$BASE_URL/api/v1/analytics/health" 200

# Check database connectivity
echo "Checking database connectivity..."
kubectl run --rm -i --tty --restart=Never db-connectivity-test \
    --image=postgres:15 \
    --namespace=$NAMESPACE \
    -- psql "$GAME_DB_URL" -c "SELECT 1 as game_db_test;" || {
    echo "❌ Game database connectivity failed"
    exit 1
}

kubectl run --rm -i --tty --restart=Never db-connectivity-test-2 \
    --image=postgres:15 \
    --namespace=$NAMESPACE \
    -- psql "$ORDER_DB_URL" -c "SELECT 1 as order_db_test;" || {
    echo "❌ Order database connectivity failed"
    exit 1
}

# Check ClickHouse connectivity
if ! curl -f "${CLICKHOUSE_HOST}:8123/ping" --user "lugx_admin:${CLICKHOUSE_PASSWORD}"; then
    echo "❌ ClickHouse connectivity failed"
    exit 1
fi

# Performance validation
echo "Running performance validation..."
response_time=$(curl -o /dev/null -s -w '%{time_total}' $BASE_URL)
if (( $(echo "$response_time > 3.0" | bc -l) )); then
    echo "⚠️  Warning: Homepage response time is ${response_time}s (should be < 3s)"
else
    echo "✅ Homepage response time: ${response_time}s"
fi

# Check critical user flows
echo "Testing critical user flows..."
# Test game catalog loading
if ! curl -f "$BASE_URL/api/v1/games/trending?limit=5" >/dev/null 2>&1; then
    echo "❌ Game catalog endpoint failed"
    exit 1
fi

# Test analytics event submission
curl -X POST "$BASE_URL/api/v1/analytics/events/batch" \
    -H "Content-Type: application/json" \
    -d '{
        "events": [{
            "event_type": "health_check",
            "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
            "session_id": "health_check_session"
        }]
    }' || {
    echo "❌ Analytics event submission failed"
    exit 1
}

# Check monitoring systems
echo "Checking monitoring systems..."
if ! curl -f "$PROMETHEUS_URL/api/v1/query?query=up" >/dev/null 2>&1; then
    echo "⚠️  Warning: Prometheus not accessible"
fi

if ! curl -f "$GRAFANA_URL/api/health" >/dev/null 2>&1; then
    echo "⚠️  Warning: Grafana not accessible"
fi

echo "✅ All post-deployment health checks passed!"
```

---

## 5. Rollback Procedures

### 5.1 Emergency Rollback

```bash
#!/bin/bash
# scripts/emergency-rollback.sh

set -e
source .env.deployment

NAMESPACE=${1:-$NAMESPACE_PROD}
REASON=${2:-"Emergency rollback"}

echo "🚨 EMERGENCY ROLLBACK INITIATED"
echo "Namespace: $NAMESPACE"
echo "Reason: $REASON"
echo "Time: $(date)"

# Confirm rollback
read -p "Are you sure you want to perform emergency rollback? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Rollback cancelled"
    exit 0
fi

# Rollback all services
SERVICES=("frontend" "game-service" "order-service" "analytics-service")

echo "Rolling back all services..."
for service in "${SERVICES[@]}"; do
    echo "Rolling back $service..."
    kubectl rollout undo deployment/${service}-deployment -n $NAMESPACE
    
    # Wait for rollback to complete
    kubectl rollout status deployment/${service}-deployment -n $NAMESPACE --timeout=300s
    
    if [ $? -eq 0 ]; then
        echo "✅ $service rollback successful"
    else
        echo "❌ $service rollback failed"
        # Continue with other services but note the failure
    fi
done

# Health check after rollback
echo "Running post-rollback health checks..."
sleep 60  # Wait for services to stabilize

./scripts/post-deployment-health-check.sh $NAMESPACE || {
    echo "❌ Post-rollback health checks failed"
    echo "🚨 CRITICAL: Manual intervention required"
    exit 1
}

# Notify team
curl -X POST $SLACK_WEBHOOK_URL -H 'Content-type: application/json' \
    --data "{
        \"text\": \"🚨 **EMERGENCY ROLLBACK COMPLETED**\",
        \"attachments\": [{
            \"color\": \"danger\",
            \"fields\": [
                {\"title\": \"Namespace\", \"value\": \"$NAMESPACE\", \"short\": true},
                {\"title\": \"Reason\", \"value\": \"$REASON\", \"short\": true},
                {\"title\": \"Time\", \"value\": \"$(date)\", \"short\": true},
                {\"title\": \"Status\", \"value\": \"Completed\", \"short\": true}
            ]
        }]
    }"

echo "✅ Emergency rollback completed successfully"
echo "Please investigate the root cause and prepare a fix"
```

### 5.2 Targeted Service Rollback

```bash
#!/bin/bash
# scripts/rollback-service.sh

set -e
source .env.deployment

SERVICE_NAME=$1
NAMESPACE=${2:-$NAMESPACE_PROD}
TARGET_REVISION=${3:-}

if [ -z "$SERVICE_NAME" ]; then
    echo "Usage: $0 <service-name> [namespace] [target-revision]"
    echo "Services: frontend, game-service, order-service, analytics-service"
    exit 1
fi

echo "🔄 Rolling back $SERVICE_NAME in $NAMESPACE"

# Show current rollout history
echo "Current rollout history:"
kubectl rollout history deployment/${SERVICE_NAME}-deployment -n $NAMESPACE

# Perform rollback
if [ -n "$TARGET_REVISION" ]; then
    echo "Rolling back to revision $TARGET_REVISION..."
    kubectl rollout undo deployment/${SERVICE_NAME}-deployment -n $NAMESPACE --to-revision=$TARGET_REVISION
else
    echo "Rolling back to previous revision..."
    kubectl rollout undo deployment/${SERVICE_NAME}-deployment -n $NAMESPACE
fi

# Wait for rollback completion
kubectl rollout status deployment/${SERVICE_NAME}-deployment -n $NAMESPACE --timeout=300s

# Health check
echo "Performing health check..."
sleep 30

case $SERVICE_NAME in
    "frontend")
        check_endpoint "https://lugxgaming.com/health"
        ;;
    "game-service")
        check_endpoint "https://api.lugxgaming.com/api/v1/games/health"
        ;;
    "order-service")
        check_endpoint "https://api.lugxgaming.com/api/v1/orders/health"
        ;;
    "analytics-service")
        check_endpoint "https://api.lugxgaming.com/api/v1/analytics/health"
        ;;
esac

echo "✅ $SERVICE_NAME rollback completed successfully"
```

---

## 6. Database Operations

### 6.1 Database Migration

```bash
#!/bin/bash
# scripts/run-database-migration.sh

set -e
source .env.deployment

ENVIRONMENT=${1:-production}
SERVICE=${2:-all}

echo "🗄️ Running database migrations for $SERVICE in $ENVIRONMENT"

run_postgres_migration() {
    local service=$1
    local db_host_var="${service^^}_DB_HOST"
    local db_password_var="${service^^}_DB_PASSWORD"
    local db_name_var="${service^^}_DB_NAME"
    
    local db_host=${!db_host_var}
    local db_password=${!db_password_var}
    local db_name=${!db_name_var}
    
    echo "Running PostgreSQL migration for $service..."
    
    # Run Alembic migration
    cd services/$service
    SQLALCHEMY_DATABASE_URL="postgresql://lugx_admin:$db_password@$db_host:5432/$db_name" \
        alembic upgrade head
    cd ../..
    
    echo "✅ $service PostgreSQL migration completed"
}

run_clickhouse_migration() {
    echo "Running ClickHouse migration..."
    
    # Run ClickHouse schema updates
    for migration_file in database/migrations/analytics-service/*.sql; do
        echo "Applying $migration_file..."
        curl -X POST "${CLICKHOUSE_HOST}:8123/" \
            --user "lugx_admin:${CLICKHOUSE_PASSWORD}" \
            --data-binary @"$migration_file"
    done
    
    echo "✅ ClickHouse migration completed"
}

# Backup databases before migration
echo "Creating database backups..."
./scripts/backup-databases.sh

# Run migrations based on service
case $SERVICE in
    "game-service")
        run_postgres_migration "game-service"
        ;;
    "order-service")
        run_postgres_migration "order-service"
        ;;
    "analytics-service")
        run_clickhouse_migration
        ;;
    "all")
        run_postgres_migration "game-service"
        run_postgres_migration "order-service"
        run_clickhouse_migration
        ;;
    *)
        echo "Invalid service: $SERVICE"
        echo "Valid services: game-service, order-service, analytics-service, all"
        exit 1
        ;;
esac

echo "✅ All database migrations completed successfully"
```

### 6.2 Database Backup

```bash
#!/bin/bash
# scripts/backup-databases.sh

set -e
source .env.deployment

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_BUCKET="lugx-gaming-db-backups"

echo "💾 Creating database backups for $BACKUP_DATE"

# Create backup directory
mkdir -p backups/$BACKUP_DATE

# Backup PostgreSQL databases
echo "Backing up PostgreSQL databases..."

# Game Service Database
pg_dump "postgresql://lugx_admin:${GAME_DB_PASSWORD}@${GAME_DB_HOST}:5432/lugx_games_prod" \
    --verbose --format=custom \
    > backups/$BACKUP_DATE/game_service_backup.dump

# Order Service Database
pg_dump "postgresql://lugx_admin:${ORDER_DB_PASSWORD}@${ORDER_DB_HOST}:5432/lugx_orders_prod" \
    --verbose --format=custom \
    > backups/$BACKUP_DATE/order_service_backup.dump

# Backup ClickHouse database
echo "Backing up ClickHouse database..."
curl -X POST "${CLICKHOUSE_HOST}:8123/" \
    --user "lugx_admin:${CLICKHOUSE_PASSWORD}" \
    --data "BACKUP DATABASE lugx_analytics TO S3('s3://$BACKUP_BUCKET/clickhouse/$BACKUP_DATE/', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY')"

# Upload PostgreSQL backups to S3
echo "Uploading backups to S3..."
aws s3 cp backups/$BACKUP_DATE/ s3://$BACKUP_BUCKET/postgresql/$BACKUP_DATE/ --recursive

# Create backup metadata
cat > backups/$BACKUP_DATE/backup_metadata.json << EOF
{
    "backup_date": "$BACKUP_DATE",
    "databases": {
        "game_service": {
            "type": "postgresql",
            "size": "$(du -h backups/$BACKUP_DATE/game_service_backup.dump | cut -f1)",
            "location": "s3://$BACKUP_BUCKET/postgresql/$BACKUP_DATE/game_service_backup.dump"
        },
        "order_service": {
            "type": "postgresql", 
            "size": "$(du -h backups/$BACKUP_DATE/order_service_backup.dump | cut -f1)",
            "location": "s3://$BACKUP_BUCKET/postgresql/$BACKUP_DATE/order_service_backup.dump"
        },
        "analytics_service": {
            "type": "clickhouse",
            "location": "s3://$BACKUP_BUCKET/clickhouse/$BACKUP_DATE/"
        }
    },
    "environment": "production",
    "created_by": "$USER",
    "kubernetes_version": "$(kubectl version --short | grep Server)"
}
EOF

# Upload metadata
aws s3 cp backups/$BACKUP_DATE/backup_metadata.json s3://$BACKUP_BUCKET/metadata/$BACKUP_DATE.json

# Clean up local backups older than 7 days
find backups/ -type d -mtime +7 -exec rm -rf {} \;

echo "✅ Database backup completed: $BACKUP_DATE"
echo "Backup location: s3://$BACKUP_BUCKET/"
```

---

## 7. Monitoring and Troubleshooting

### 7.1 Health Check Commands

```bash
#!/bin/bash
# scripts/health-check.sh

source .env.deployment

echo "🏥 Running comprehensive health checks..."

# Kubernetes cluster health
echo "=== Kubernetes Cluster Health ==="
kubectl get nodes
kubectl get pods --all-namespaces | grep -v Running | grep -v Completed || echo "All pods running"

# Service health
echo "=== Service Health ==="
kubectl get pods -n $NAMESPACE_PROD
kubectl get services -n $NAMESPACE_PROD

# Database connectivity
echo "=== Database Connectivity ==="
# PostgreSQL
kubectl run --rm -i --tty --restart=Never pg-test --image=postgres:15 \
    -- psql "$GAME_DB_URL" -c "SELECT 'Game DB: Connected' as status;"

kubectl run --rm -i --tty --restart=Never pg-test-2 --image=postgres:15 \
    -- psql "$ORDER_DB_URL" -c "SELECT 'Order DB: Connected' as status;"

# ClickHouse
curl -s "${CLICKHOUSE_HOST}:8123/ping" --user "lugx_admin:${CLICKHOUSE_PASSWORD}" && echo "ClickHouse: Connected"

# Redis
kubectl run --rm -i --tty --restart=Never redis-test --image=redis:7 \
    -- redis-cli -h $REDIS_HOST ping

# External endpoints
echo "=== External Endpoint Health ==="
curl -I https://lugxgaming.com/health 2>/dev/null | head -n 1
curl -I https://api.lugxgaming.com/api/v1/games/health 2>/dev/null | head -n 1

# Resource usage
echo "=== Resource Usage ==="
kubectl top nodes
kubectl top pods -n $NAMESPACE_PROD

# Recent events
echo "=== Recent Events ==="
kubectl get events -n $NAMESPACE_PROD --sort-by='.lastTimestamp' | tail -10
```

### 7.2 Log Analysis

```bash
#!/bin/bash
# scripts/analyze-logs.sh

SERVICE=${1:-all}
NAMESPACE=${2:-$NAMESPACE_PROD}
LINES=${3:-100}

echo "📋 Analyzing logs for $SERVICE (last $LINES lines)..."

analyze_service_logs() {
    local service=$1
    local namespace=$2
    local lines=$3
    
    echo "=== $service Logs ==="
    kubectl logs -l app=$service -n $namespace --tail=$lines --since=1h
    
    echo "=== $service Error Count ==="
    kubectl logs -l app=$service -n $namespace --since=1h | grep -i error | wc -l
    
    echo "=== $service Recent Errors ==="
    kubectl logs -l app=$service -n $namespace --since=1h | grep -i error | tail -5
}

case $SERVICE in
    "frontend"|"game-service"|"order-service"|"analytics-service")
        analyze_service_logs $SERVICE $NAMESPACE $LINES
        ;;
    "all")
        for svc in frontend game-service order-service analytics-service; do
            analyze_service_logs $svc $NAMESPACE $LINES
            echo ""
        done
        ;;
    *)
        echo "Invalid service. Use: frontend, game-service, order-service, analytics-service, or all"
        exit 1
        ;;
esac
```

### 7.3 Performance Diagnostics

```bash
#!/bin/bash
# scripts/performance-diagnostics.sh

source .env.deployment

echo "⚡ Running performance diagnostics..."

# API response times
echo "=== API Response Times ==="
endpoints=(
    "https://lugxgaming.com/"
    "https://api.lugxgaming.com/api/v1/games/trending"
    "https://api.lugxgaming.com/api/v1/games/categories"
    "https://api.lugxgaming.com/api/v1/analytics/metrics/realtime"
)

for endpoint in "${endpoints[@]}"; do
    echo "Testing $endpoint..."
    curl -o /dev/null -s -w "Response time: %{time_total}s | Status: %{http_code}\n" "$endpoint"
done

# Database query performance
echo "=== Database Query Performance ==="
# Test common queries
kubectl run --rm -i --tty --restart=Never perf-test --image=postgres:15 \
    -- psql "$GAME_DB_URL" -c "
        EXPLAIN ANALYZE 
        SELECT * FROM games 
        WHERE category_id IN (SELECT id FROM categories WHERE name = 'Action') 
        LIMIT 10;
    "

# ClickHouse query performance
curl -X POST "${CLICKHOUSE_HOST}:8123/" \
    --user "lugx_admin:${CLICKHOUSE_PASSWORD}" \
    --data "SELECT count() FROM web_events WHERE timestamp >= now() - INTERVAL 1 HOUR" \
    -w "ClickHouse query time: %{time_total}s\n"

# Resource utilization
echo "=== Resource Utilization ==="
kubectl top nodes
kubectl top pods -n $NAMESPACE_PROD --sort-by=cpu
kubectl top pods -n $NAMESPACE_PROD --sort-by=memory

# Horizontal Pod Autoscaler status
echo "=== HPA Status ==="
kubectl get hpa -n $NAMESPACE_PROD
```

---

## 8. Security Procedures

### 8.1 Certificate Management

```bash
#!/bin/bash
# scripts/update-certificates.sh

source .env.deployment

echo "🔒 Updating SSL certificates..."

# Check current certificate expiry
echo "Current certificate status:"
kubectl get secrets lugx-gaming-tls -n $NAMESPACE_PROD -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -noout -dates

# Backup current certificate
kubectl get secret lugx-gaming-tls -n $NAMESPACE_PROD -o yaml > backups/tls-backup-$(date +%Y%m%d).yaml

# Update certificate (assuming new certificate files are available)
kubectl create secret tls lugx-gaming-tls-new \
    --cert=certificates/lugxgaming.com.crt \
    --key=certificates/lugxgaming.com.key \
    --namespace=$NAMESPACE_PROD \
    --dry-run=client -o yaml | kubectl apply -f -

# Replace old certificate
kubectl delete secret lugx-gaming-tls -n $NAMESPACE_PROD
kubectl patch secret lugx-gaming-tls-new -n $NAMESPACE_PROD -p '{"metadata":{"name":"lugx-gaming-tls"}}'

# Restart ingress controller to pick up new certificate
kubectl rollout restart deployment/istio-ingressgateway -n istio-system

echo "✅ SSL certificates updated successfully"
```

### 8.2 Secret Rotation

```bash
#!/bin/bash
# scripts/rotate-secrets.sh

source .env.deployment

echo "🔄 Rotating application secrets..."

# Generate new JWT secret
NEW_JWT_SECRET=$(openssl rand -base64 32)

# Generate new database passwords (in production, coordinate with RDS)
echo "Warning: Database password rotation requires coordination with AWS RDS"

# Update JWT secret
kubectl patch secret order-service-secrets -n $NAMESPACE_PROD \
    -p '{"data":{"jwt-secret":"'$(echo -n $NEW_JWT_SECRET | base64 -w 0)'"}}'

# Restart services that use JWT secret
kubectl rollout restart deployment/order-service-deployment -n $NAMESPACE_PROD

# Update monitoring secrets
kubectl patch secret monitoring-secrets -n monitoring \
    -p '{"data":{"admin-password":"'$(echo -n $(openssl rand -base64 16) | base64 -w 0)'"}}'

echo "✅ Secrets rotated successfully"
echo "Please update external systems with new credentials"
```

---

## 9. Disaster Recovery

### 9.1 Full System Recovery

```bash
#!/bin/bash
# scripts/disaster-recovery.sh

source .env.deployment

BACKUP_DATE=${1:-$(date +%Y%m%d_%H%M%S)}

echo "🆘 Starting disaster recovery procedure..."
echo "Using backup from: $BACKUP_DATE"

# Confirm disaster recovery
read -p "⚠️  This will restore the entire system. Are you sure? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Recovery cancelled"
    exit 0
fi

# 1. Restore infrastructure
echo "Step 1: Restoring infrastructure..."
./scripts/setup-production-infrastructure.sh

# 2. Restore databases
echo "Step 2: Restoring databases..."

# Download backups from S3
aws s3 cp s3://lugx-gaming-db-backups/postgresql/$BACKUP_DATE/ backups/restore/ --recursive

# Restore PostgreSQL databases
pg_restore --verbose --clean --no-acl --no-owner \
    -h $GAME_DB_HOST -U lugx_admin -d lugx_games_prod \
    backups/restore/game_service_backup.dump

pg_restore --verbose --clean --no-acl --no-owner \
    -h $ORDER_DB_HOST -U lugx_admin -d lugx_orders_prod \
    backups/restore/order_service_backup.dump

# Restore ClickHouse
curl -X POST "${CLICKHOUSE_HOST}:8123/" \
    --user "lugx_admin:${CLICKHOUSE_PASSWORD}" \
    --data "RESTORE DATABASE lugx_analytics FROM S3('s3://lugx-gaming-db-backups/clickhouse/$BACKUP_DATE/', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY')"

# 3. Deploy application
echo "Step 3: Deploying application..."
./scripts/deploy-rolling-update.sh latest

# 4. Verify recovery
echo "Step 4: Verifying recovery..."
./scripts/post-deployment-health-check.sh

echo "✅ Disaster recovery completed"
echo "Please verify all systems are functioning correctly"
```

---

## 10. Maintenance Procedures

### 10.1 Scheduled Maintenance

```bash
#!/bin/bash
# scripts/scheduled-maintenance.sh

source .env.deployment

echo "🔧 Starting scheduled maintenance..."

# Put maintenance page up
kubectl apply -f manifests/maintenance-page.yaml

# Scale down non-essential services
kubectl scale deployment/analytics-service-deployment --replicas=1 -n $NAMESPACE_PROD

# Update system components
helm upgrade prometheus prometheus-community/kube-prometheus-stack -n monitoring
helm upgrade jaeger jaegertracing/jaeger -n monitoring

# Run database maintenance
./scripts/database-maintenance.sh

# Update container images (security patches)
./scripts/update-base-images.sh

# Scale services back up
kubectl scale deployment/analytics-service-deployment --replicas=3 -n $NAMESPACE_PROD

# Remove maintenance page
kubectl delete -f manifests/maintenance-page.yaml

# Health check
./scripts/post-deployment-health-check.sh

echo "✅ Scheduled maintenance completed"
```

### 10.2 Database Maintenance

```bash
#!/bin/bash
# scripts/database-maintenance.sh

source .env.deployment

echo "🗄️ Running database maintenance..."

# PostgreSQL maintenance
echo "Running PostgreSQL maintenance..."
kubectl run --rm -i --tty --restart=Never db-maintenance --image=postgres:15 \
    -- psql "$GAME_DB_URL" -c "
        VACUUM ANALYZE;
        REINDEX DATABASE lugx_games_prod;
    "

kubectl run --rm -i --tty --restart=Never db-maintenance-2 --image=postgres:15 \
    -- psql "$ORDER_DB_URL" -c "
        VACUUM ANALYZE;
        REINDEX DATABASE lugx_orders_prod;
    "

# ClickHouse maintenance
echo "Running ClickHouse maintenance..."
curl -X POST "${CLICKHOUSE_HOST}:8123/" \
    --user "lugx_admin:${CLICKHOUSE_PASSWORD}" \
    --data "OPTIMIZE TABLE web_events"

curl -X POST "${CLICKHOUSE_HOST}:8123/" \
    --user "lugx_admin:${CLICKHOUSE_PASSWORD}" \
    --data "SYSTEM DROP DNS CACHE"

echo "✅ Database maintenance completed"
```

---

## 11. Emergency Contacts and Escalation

### 11.1 Contact Information

```yaml
Emergency Contacts:
  Primary On-Call: +1-XXX-XXX-XXXX
  Platform Team Lead: platform-lead@lugxgaming.com
  DevOps Engineer: devops@lugxgaming.com
  Database Administrator: dba@lugxgaming.com
  Security Team: security@lugxgaming.com

Escalation Matrix:
  Level 1 (5 minutes): On-Call Engineer
  Level 2 (15 minutes): Platform Team Lead + DevOps Engineer
  Level 3 (30 minutes): Engineering Manager + CTO
  Level 4 (60 minutes): CEO + All Stakeholders

Communication Channels:
  Primary: Slack #devops-alerts
  Secondary: Phone/SMS
  Updates: Slack #general
  Status Page: https://status.lugxgaming.com
```

### 11.2 Incident Response Checklist

```yaml
Incident Response Checklist:
  
  1. Detection (0-2 minutes):
     - [ ] Incident detected via monitoring/alerts
     - [ ] Initial impact assessment
     - [ ] Notify on-call engineer
  
  2. Response (2-5 minutes):
     - [ ] Join incident response channel
     - [ ] Declare incident severity level
     - [ ] Begin investigation
     - [ ] Update status page if customer-facing
  
  3. Investigation (5-15 minutes):
     - [ ] Check service health endpoints
     - [ ] Review recent deployments
     - [ ] Check monitoring dashboards
     - [ ] Analyze error logs
  
  4. Mitigation (15-30 minutes):
     - [ ] Implement immediate fix OR
     - [ ] Perform rollback if needed
     - [ ] Verify mitigation effectiveness
     - [ ] Monitor for stability
  
  5. Resolution (30+ minutes):
     - [ ] Confirm complete resolution
     - [ ] Update status page
     - [ ] Notify stakeholders
     - [ ] Schedule post-incident review
  
  6. Post-Incident (24-48 hours):
     - [ ] Conduct post-incident review
     - [ ] Document lessons learned
     - [ ] Implement preventive measures
     - [ ] Update runbooks if needed
```

---

## 12. Appendix

### 12.1 Common Commands Reference

```bash
# Quick status check
kubectl get pods -n production -o wide

# View service logs
kubectl logs -f deployment/game-service-deployment -n production

# Check resource usage
kubectl top pods -n production

# Scale service
kubectl scale deployment/frontend-deployment --replicas=5 -n production

# Port forward for debugging
kubectl port-forward svc/prometheus-server 9090:80 -n monitoring

# Execute command in pod
kubectl exec -it deployment/game-service-deployment -n production -- /bin/bash

# View ConfigMaps and Secrets
kubectl get configmaps -n production
kubectl get secrets -n production

# Check Horizontal Pod Autoscaler
kubectl get hpa -n production

# View recent events
kubectl get events -n production --sort-by=.metadata.creationTimestamp
```

### 12.2 Useful Monitoring Queries

```promql
# High CPU usage
rate(container_cpu_usage_seconds_total[5m]) > 0.8

# High memory usage
container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9

# High error rate
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05

# Slow response times
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 2

# Database connection issues
mysql_global_status_threads_connected / mysql_global_variables_max_connections > 0.8

# Pod restart frequency
increase(kube_pod_container_status_restarts_total[1h]) > 0
```

This comprehensive deployment runbook provides all necessary procedures for safely and reliably deploying and maintaining the Lugx Gaming platform in production environments.