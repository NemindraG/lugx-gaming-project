# Lugx Gaming Platform - Local Development Environment Setup (Phase 1.3.1)

## Executive Summary

This document provides a comprehensive guide for setting up a local development environment that mirrors the production Lugx Gaming platform architecture. The setup includes Kubernetes cluster with Istio service mesh, databases, development tools, and local container registry for a complete development experience.

## Prerequisites

### System Requirements
- **Operating System**: macOS 10.15+, Ubuntu 20.04+, or Windows 10+ with WSL2
- **RAM**: Minimum 16GB, Recommended 32GB
- **CPU**: Minimum 4 cores, Recommended 8+ cores
- **Storage**: Minimum 50GB free space, Recommended 100GB+ SSD
- **Network**: Stable internet connection for initial setup

### Required Software
- Docker Desktop 4.15+ or Docker Engine 20.10+
- kubectl 1.28+
- Helm 3.10+
- Git 2.30+
- Python 3.11+
- Node.js 18+ (for frontend tooling)

---

## 1. Kubernetes Cluster Setup

### 1.1 Kind (Kubernetes in Docker) - Recommended

#### **Installation**

```bash
# Install Kind
# macOS
brew install kind

# Linux
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Windows (PowerShell)
choco install kind
```

#### **Cluster Configuration**

```yaml
# config/kind-cluster-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: lugx-gaming-dev
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
  - containerPort: 15021
    hostPort: 15021
    protocol: TCP
- role: worker
  labels:
    node-type: "game-service"
- role: worker
  labels:
    node-type: "order-service"
- role: worker
  labels:
    node-type: "analytics-service"
networking:
  podSubnet: "10.244.0.0/16"
  serviceSubnet: "10.96.0.0/12"
  disableDefaultCNI: false
  kubeProxyMode: "ipvs"
```

#### **Cluster Creation Script**

```bash
#!/bin/bash
# scripts/setup-kind-cluster.sh

set -e

echo "🚀 Setting up Lugx Gaming Development Cluster with Kind..."

# Create Kind cluster
echo "📦 Creating Kind cluster..."
kind create cluster --config=config/kind-cluster-config.yaml

# Wait for cluster to be ready
echo "⏳ Waiting for cluster to be ready..."
kubectl wait --for=condition=Ready nodes --all --timeout=300s

# Load local images (if any exist)
echo "📥 Loading pre-built images..."
if [ -f "images/lugx-gaming-images.tar" ]; then
    kind load image-archive images/lugx-gaming-images.tar --name lugx-gaming-dev
fi

# Install Istio
echo "🌐 Installing Istio service mesh..."
./scripts/install-istio.sh

# Create namespaces
echo "📂 Creating namespaces..."
kubectl create namespace lugx-gaming
kubectl create namespace lugx-monitoring
kubectl create namespace lugx-databases

# Label namespaces for Istio injection
kubectl label namespace lugx-gaming istio-injection=enabled
kubectl label namespace lugx-monitoring istio-injection=enabled

echo "✅ Kind cluster setup complete!"
echo "🔗 Cluster endpoint: $(kubectl cluster-info | grep 'control plane' | awk '{print $6}')"
echo "📋 To use cluster: export KUBECONFIG=\"$(kind get kubeconfig-path --name lugx-gaming-dev)\""
```

### 1.2 Istio Service Mesh Installation

#### **Istio Installation Script**

```bash
#!/bin/bash
# scripts/install-istio.sh

set -e

ISTIO_VERSION="1.19.3"

echo "🌐 Installing Istio ${ISTIO_VERSION}..."

# Download Istio
if [ ! -d "istio-${ISTIO_VERSION}" ]; then
    echo "📥 Downloading Istio..."
    curl -L https://istio.io/downloadIstio | ISTIO_VERSION=${ISTIO_VERSION} sh -
fi

# Add istioctl to PATH
export PATH=$PWD/istio-${ISTIO_VERSION}/bin:$PATH

# Install Istio with development profile
echo "⚙️ Installing Istio with development profile..."
istioctl install --set values.defaultRevision=default --set values.pilot.env.EXTERNAL_ISTIOD=false -y

# Install Istio addons for development
echo "🔧 Installing Istio addons..."
kubectl apply -f istio-${ISTIO_VERSION}/samples/addons/

# Wait for deployments to be ready
echo "⏳ Waiting for Istio components to be ready..."
kubectl wait --for=condition=available --timeout=600s deployment/istiod -n istio-system
kubectl wait --for=condition=available --timeout=600s deployment/grafana -n istio-system
kubectl wait --for=condition=available --timeout=600s deployment/prometheus -n istio-system
kubectl wait --for=condition=available --timeout=600s deployment/jaeger -n istio-system
kubectl wait --for=condition=available --timeout=600s deployment/kiali -n istio-system

echo "✅ Istio installation complete!"
echo "🌐 Kiali dashboard: kubectl port-forward svc/kiali 20001:20001 -n istio-system"
echo "📊 Grafana dashboard: kubectl port-forward svc/grafana 3000:3000 -n istio-system"
echo "🔍 Jaeger tracing: kubectl port-forward svc/jaeger 16686:16686 -n istio-system"
```

---

## 2. Local Database Setup

### 2.1 Docker Compose Database Configuration

#### **Database Docker Compose**

```yaml
# docker-compose.databases.yml
version: '3.8'

services:
  # PostgreSQL for Game and Order Services
  postgresql-game:
    image: postgres:15.4-alpine
    container_name: lugx-postgresql-game
    environment:
      POSTGRES_DB: lugx_games
      POSTGRES_USER: lugx_user
      POSTGRES_PASSWORD: lugx_dev_password
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8 --lc-collate=en_US.UTF-8 --lc-ctype=en_US.UTF-8"
    ports:
      - "5432:5432"
    volumes:
      - postgresql_game_data:/var/lib/postgresql/data
      - ./database/init-scripts/game-service:/docker-entrypoint-initdb.d
    networks:
      - lugx-dev-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U lugx_user -d lugx_games"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  postgresql-order:
    image: postgres:15.4-alpine
    container_name: lugx-postgresql-order
    environment:
      POSTGRES_DB: lugx_orders
      POSTGRES_USER: lugx_user
      POSTGRES_PASSWORD: lugx_dev_password
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8 --lc-collate=en_US.UTF-8 --lc-ctype=en_US.UTF-8"
    ports:
      - "5433:5432"
    volumes:
      - postgresql_order_data:/var/lib/postgresql/data
      - ./database/init-scripts/order-service:/docker-entrypoint-initdb.d
    networks:
      - lugx-dev-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U lugx_user -d lugx_orders"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # ClickHouse for Analytics Service
  clickhouse:
    image: clickhouse/clickhouse-server:23.8.4-alpine
    container_name: lugx-clickhouse
    environment:
      CLICKHOUSE_DB: lugx_analytics
      CLICKHOUSE_USER: lugx_user
      CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT: 1
      CLICKHOUSE_PASSWORD: lugx_dev_password
    ports:
      - "8123:8123"  # HTTP interface
      - "9000:9000"  # Native interface
    volumes:
      - clickhouse_data:/var/lib/clickhouse
      - ./database/init-scripts/analytics-service:/docker-entrypoint-initdb.d
      - ./config/clickhouse/config.xml:/etc/clickhouse-server/config.xml
      - ./config/clickhouse/users.xml:/etc/clickhouse-server/users.xml
    networks:
      - lugx-dev-network
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8123/ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Redis for Caching and Sessions
  redis:
    image: redis:7.2.1-alpine
    container_name: lugx-redis
    command: redis-server --appendonly yes --requirepass lugx_dev_password
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
      - ./config/redis/redis.conf:/etc/redis/redis.conf
    networks:
      - lugx-dev-network
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # pgAdmin for PostgreSQL Management
  pgadmin:
    image: dpage/pgadmin4:7.6
    container_name: lugx-pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@lugxgaming.com
      PGADMIN_DEFAULT_PASSWORD: lugx_admin_password
      PGADMIN_CONFIG_SERVER_MODE: 'False'
    ports:
      - "5050:80"
    volumes:
      - pgadmin_data:/var/lib/pgadmin
      - ./config/pgadmin/servers.json:/pgadmin4/servers.json
    networks:
      - lugx-dev-network
    depends_on:
      - postgresql-game
      - postgresql-order
    restart: unless-stopped

  # Redis Commander for Redis Management
  redis-commander:
    image: rediscommander/redis-commander:latest
    container_name: lugx-redis-commander
    environment:
      REDIS_HOSTS: "local:redis:6379:0:lugx_dev_password"
      HTTP_USER: admin
      HTTP_PASSWORD: lugx_admin_password
    ports:
      - "8081:8081"
    networks:
      - lugx-dev-network
    depends_on:
      - redis
    restart: unless-stopped

volumes:
  postgresql_game_data:
    driver: local
  postgresql_order_data:
    driver: local
  clickhouse_data:
    driver: local
  redis_data:
    driver: local
  pgadmin_data:
    driver: local

networks:
  lugx-dev-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

#### **Database Setup Script**

```bash
#!/bin/bash
# scripts/setup-databases.sh

set -e

echo "🗄️ Setting up Lugx Gaming databases..."

# Create necessary directories
mkdir -p database/init-scripts/game-service
mkdir -p database/init-scripts/order-service
mkdir -p database/init-scripts/analytics-service
mkdir -p config/clickhouse
mkdir -p config/redis
mkdir -p config/pgadmin

# Generate database init scripts
echo "📝 Generating database initialization scripts..."
./scripts/generate-db-init-scripts.sh

# Start databases
echo "🚀 Starting database services..."
docker-compose -f docker-compose.databases.yml up -d

# Wait for databases to be ready
echo "⏳ Waiting for databases to be ready..."
./scripts/wait-for-databases.sh

# Run database migrations
echo "📊 Running database migrations..."
./scripts/run-migrations.sh

echo "✅ Database setup complete!"
echo "🌐 pgAdmin: http://localhost:5050 (admin@lugxgaming.com / lugx_admin_password)"
echo "🔧 Redis Commander: http://localhost:8081 (admin / lugx_admin_password)"
echo "📊 ClickHouse: http://localhost:8123 (lugx_user / lugx_dev_password)"
```

### 2.2 Database Configuration Files

#### **ClickHouse Configuration**

```xml
<!-- config/clickhouse/config.xml -->
<?xml version="1.0"?>
<yandex>
    <logger>
        <level>information</level>
        <console>1</console>
        <log>/var/log/clickhouse-server/clickhouse-server.log</log>
        <errorlog>/var/log/clickhouse-server/clickhouse-server.err.log</errorlog>
        <size>1000M</size>
        <count>10</count>
    </logger>
    
    <http_port>8123</http_port>
    <tcp_port>9000</tcp_port>
    <interserver_http_port>9009</interserver_http_port>
    
    <listen_host>0.0.0.0</listen_host>
    
    <max_connections>1000</max_connections>
    <keep_alive_timeout>3</keep_alive_timeout>
    <max_concurrent_queries>100</max_concurrent_queries>
    <uncompressed_cache_size>8589934592</uncompressed_cache_size>
    <mark_cache_size>5368709120</mark_cache_size>
    
    <path>/var/lib/clickhouse/</path>
    <tmp_path>/var/lib/clickhouse/tmp/</tmp_path>
    <user_files_path>/var/lib/clickhouse/user_files/</user_files_path>
    
    <users_config>users.xml</users_config>
    
    <default_profile>default</default_profile>
    <default_database>lugx_analytics</default_database>
    
    <timezone>UTC</timezone>
    
    <mlock_executable>false</mlock_executable>
    
    <macros>
        <cluster>lugx_analytics_cluster</cluster>
    </macros>
    
    <remote_servers>
        <lugx_analytics_cluster>
            <shard>
                <replica>
                    <host>localhost</host>
                    <port>9000</port>
                </replica>
            </shard>
        </lugx_analytics_cluster>
    </remote_servers>
</yandex>
```

#### **Redis Configuration**

```conf
# config/redis/redis.conf
# Network
bind 0.0.0.0
port 6379
protected-mode no

# General
daemonize no
supervised no
pidfile /var/run/redis_6379.pid
loglevel notice
logfile ""
databases 16

# Snapshotting
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir ./

# Replication
replica-serve-stale-data yes
replica-read-only yes
repl-diskless-sync no
repl-diskless-sync-delay 5

# Security
requirepass lugx_dev_password

# Memory Management
maxmemory 256mb
maxmemory-policy allkeys-lru

# Append Only File
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# Slow Log
slowlog-log-slower-than 10000
slowlog-max-len 128

# Latency Monitoring
latency-monitor-threshold 100
```

---

## 3. Development Tools Configuration

### 3.1 kubectl Configuration

#### **kubectl Setup Script**

```bash
#!/bin/bash
# scripts/setup-kubectl.sh

set -e

echo "⚙️ Setting up kubectl for Lugx Gaming development..."

# Create kubectl config for development
mkdir -p ~/.kube/configs/lugx-gaming

# Set up kubectl context
kubectl config set-context lugx-gaming-dev \
    --cluster=kind-lugx-gaming-dev \
    --namespace=lugx-gaming \
    --user=kind-lugx-gaming-dev

# Use the development context
kubectl config use-context lugx-gaming-dev

# Create helpful aliases
cat >> ~/.bashrc << 'EOF'
# Lugx Gaming kubectl aliases
alias k='kubectl'
alias kns='kubectl config set-context --current --namespace'
alias kgp='kubectl get pods'
alias kgs='kubectl get services'
alias kgd='kubectl get deployments'
alias kdp='kubectl describe pod'
alias kds='kubectl describe service'
alias kdd='kubectl describe deployment'
alias klf='kubectl logs -f'

# Lugx Gaming specific aliases
alias lugx-pods='kubectl get pods -n lugx-gaming'
alias lugx-logs='kubectl logs -f -n lugx-gaming'
alias lugx-services='kubectl get services -n lugx-gaming'
alias lugx-kiali='kubectl port-forward svc/kiali 20001:20001 -n istio-system'
alias lugx-grafana='kubectl port-forward svc/grafana 3000:3000 -n istio-system'
alias lugx-jaeger='kubectl port-forward svc/jaeger 16686:16686 -n istio-system'
EOF

echo "✅ kubectl configuration complete!"
echo "🔄 Please run: source ~/.bashrc"
```

### 3.2 Helm Configuration

#### **Helm Setup and Charts**

```bash
#!/bin/bash
# scripts/setup-helm.sh

set -e

echo "📦 Setting up Helm for Lugx Gaming..."

# Add required Helm repositories
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add jetstack https://charts.jetstack.io
helm repo update

# Create Helm chart structure for Lugx Gaming services
mkdir -p helm/lugx-gaming/{templates,charts}

# Generate base Helm chart
cat > helm/lugx-gaming/Chart.yaml << 'EOF'
apiVersion: v2
name: lugx-gaming
description: A Helm chart for Lugx Gaming Platform
version: 0.1.0
appVersion: "1.0.0"
dependencies:
  - name: postgresql
    version: "12.1.9"
    repository: "https://charts.bitnami.com/bitnami"
    condition: postgresql.enabled
  - name: redis
    version: "17.3.7"
    repository: "https://charts.bitnami.com/bitnami"
    condition: redis.enabled
  - name: prometheus
    version: "15.16.1"
    repository: "https://prometheus-community.github.io/helm-charts"
    condition: prometheus.enabled
EOF

# Generate values file
cat > helm/lugx-gaming/values.yaml << 'EOF'
# Lugx Gaming Platform Helm Values
global:
  environment: development
  namespace: lugx-gaming
  imageRegistry: localhost:5000
  imagePullPolicy: IfNotPresent

gameService:
  enabled: true
  replicaCount: 2
  image:
    repository: lugx-gaming/game-service
    tag: latest
  service:
    type: ClusterIP
    port: 8000
  resources:
    requests:
      memory: "256Mi"
      cpu: "200m"
    limits:
      memory: "512Mi"
      cpu: "500m"

orderService:
  enabled: true
  replicaCount: 3
  image:
    repository: lugx-gaming/order-service
    tag: latest
  service:
    type: ClusterIP
    port: 8001
  resources:
    requests:
      memory: "512Mi"
      cpu: "300m"
    limits:
      memory: "1Gi"
      cpu: "800m"

analyticsService:
  enabled: true
  replicaCount: 2
  image:
    repository: lugx-gaming/analytics-service
    tag: latest
  service:
    type: ClusterIP
    port: 8002
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "1000m"

# Database configurations
postgresql:
  enabled: false  # Using external Docker Compose

redis:
  enabled: false  # Using external Docker Compose

# Monitoring
prometheus:
  enabled: true
  server:
    persistentVolume:
      enabled: false
EOF

echo "✅ Helm configuration complete!"
```

### 3.3 Local Container Registry

#### **Local Registry Setup**

```bash
#!/bin/bash
# scripts/setup-local-registry.sh

set -e

echo "🐳 Setting up local container registry..."

# Create registry container
docker run -d \
    --name lugx-registry \
    --restart=unless-stopped \
    -p 5000:5000 \
    -v lugx-registry-data:/var/lib/registry \
    registry:2

# Wait for registry to be ready
echo "⏳ Waiting for registry to be ready..."
sleep 10

# Test registry connection
curl -X GET http://localhost:5000/v2/_catalog

# Connect registry to Kind cluster
echo "🔗 Connecting registry to Kind cluster..."
docker network connect "kind" lugx-registry

# Configure Kind to use local registry
cat << 'EOF' > /tmp/kind-registry-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: local-registry-hosting
  namespace: kube-public
data:
  localRegistryHosting.v1: |
    host: "localhost:5000"
    help: "https://kind.sigs.k8s.io/docs/user/local-registry/"
EOF

kubectl apply -f /tmp/kind-registry-config.yaml

echo "✅ Local registry setup complete!"
echo "🌐 Registry endpoint: http://localhost:5000"
echo "🔍 Registry catalog: curl http://localhost:5000/v2/_catalog"
```

---

## 4. IDE and Development Tools Configuration

### 4.1 VS Code Configuration

#### **VS Code Settings and Extensions**

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "python.sortImports.args": ["--profile", "black"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".mypy_cache": true,
    ".pytest_cache": true
  },
  "yaml.schemas": {
    "https://json.schemastore.org/kustomization": "kustomization.yaml",
    "https://raw.githubusercontent.com/instrumenta/kubernetes-json-schema/master/v1.18.0-standalone-strict/all.json": [
      "k8s/**/*.yaml",
      "kubernetes/**/*.yaml"
    ]
  },
  "kubernetes.defaultNamespace": "lugx-gaming",
  "istio.defaultNamespace": "lugx-gaming"
}
```

```json
// .vscode/extensions.json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.mypy-type-checker",
    "ms-kubernetes-tools.vscode-kubernetes-tools",
    "ms-vscode.vscode-yaml",
    "redhat.vscode-xml",
    "ms-vscode.docker",
    "ms-azuretools.vscode-docker",
    "hashicorp.terraform",
    "ms-vscode.vscode-json",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "formulahendry.auto-rename-tag",
    "christian-kohler.path-intellisense"
  ]
}
```

### 4.2 Python Development Environment

#### **Python Environment Setup**

```bash
#!/bin/bash
# scripts/setup-python-env.sh

set -e

echo "🐍 Setting up Python development environment..."

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Set up Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "✅ Python environment setup complete!"
echo "🔄 To activate: source venv/bin/activate"
```

```txt
# requirements-dev.txt
# FastAPI and dependencies
fastapi[all]==0.104.1
uvicorn[standard]==0.24.0
gunicorn==21.2.0

# Database drivers
asyncpg==0.29.0
asyncio-mqtt==0.16.1
redis[hiredis]==5.0.1
clickhouse-driver==0.2.6

# ORM and migrations
sqlalchemy[asyncio]==2.0.23
alembic==1.12.1

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2
pytest-mock==3.12.0

# Development tools
black==23.11.0
isort==5.12.0
mypy==1.7.1
flake8==6.1.0
pre-commit==3.5.0

# Documentation
mkdocs==1.5.3
mkdocs-material==9.4.8

# Monitoring
prometheus-client==0.19.0
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0

# Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
```

### 4.3 Git Configuration

#### **Git Hooks and Configuration**

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: check-json
      - id: pretty-format-json
        args: ['--autofix']

  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: https://github.com/adrienverge/yamllint
    rev: v1.33.0
    hooks:
      - id: yamllint
        args: [-c=.yamllint.yaml]

  - repo: https://github.com/Lucas-C/pre-commit-hooks-safety
    rev: v1.3.2
    hooks:
      - id: python-safety-dependencies-check
```

---

## 5. Complete Development Setup Script

### 5.1 Master Setup Script

```bash
#!/bin/bash
# setup-dev-environment.sh

set -e

echo "🚀 Lugx Gaming Platform - Development Environment Setup"
echo "======================================================="

# Check prerequisites
echo "📋 Checking prerequisites..."
./scripts/check-prerequisites.sh

# Set up Kind cluster with Istio
echo "🌐 Setting up Kubernetes cluster..."
./scripts/setup-kind-cluster.sh

# Set up databases
echo "🗄️ Setting up databases..."
./scripts/setup-databases.sh

# Set up local registry
echo "🐳 Setting up local container registry..."
./scripts/setup-local-registry.sh

# Set up development tools
echo "⚙️ Setting up development tools..."
./scripts/setup-kubectl.sh
./scripts/setup-helm.sh
./scripts/setup-python-env.sh

# Build and deploy initial services
echo "🔨 Building and deploying services..."
./scripts/build-and-deploy.sh

# Run health checks
echo "🔍 Running health checks..."
./scripts/health-check.sh

echo "✅ Development environment setup complete!"
echo ""
echo "🌐 Available Services:"
echo "   - Kiali (Service Mesh): http://localhost:20001"
echo "   - Grafana (Monitoring): http://localhost:3000"
echo "   - Jaeger (Tracing): http://localhost:16686"
echo "   - pgAdmin (Database): http://localhost:5050"
echo "   - Redis Commander: http://localhost:8081"
echo "   - Container Registry: http://localhost:5000"
echo ""
echo "🔧 Quick Commands:"
echo "   - kubectl get pods -n lugx-gaming"
echo "   - helm list -n lugx-gaming"
echo "   - docker-compose -f docker-compose.databases.yml ps"
echo ""
echo "📖 Next Steps:"
echo "   1. Review the setup with: ./scripts/validate-setup.sh"
echo "   2. Start developing services"
echo "   3. Use: ./scripts/dev-workflow.sh for daily development"
```

This comprehensive local development setup provides a complete environment that mirrors production, enabling efficient development of the Lugx Gaming platform with all necessary tools and infrastructure components.