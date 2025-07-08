# Lugx Gaming Platform - Shared Development Infrastructure Setup (Phase 1.3.2)

## Executive Summary

This document defines the shared development infrastructure for the Lugx Gaming platform, including Git repository structure, container registry setup, shared development cluster configuration, and environment-specific configuration management. This infrastructure ensures consistency across development teams and provides a staging environment that mirrors production.

## Infrastructure Overview

### Shared Infrastructure Components
- **Git Repository Strategy**: Monorepo with clear module boundaries and branching policies
- **Container Registry**: Shared registry with proper tagging and lifecycle management
- **Staging Environment**: Production-like cluster for integration testing
- **Configuration Management**: Environment-specific configurations using GitOps principles
- **CI/CD Pipeline**: Automated testing, building, and deployment workflows

---

## 1. Git Repository Structure

### 1.1 Monorepo Strategy

#### **Repository Structure**

```
lugx-gaming-project/
├── README.md
├── CONTRIBUTING.md
├── LICENSE
├── .gitignore
├── .gitattributes
│
├── architecture/                    # Architecture documentation
│   ├── diagrams/
│   ├── system-overview.md
│   ├── technology-stack.md
│   ├── frontend-api-mapping.md
│   ├── integration-points.md
│   ├── data-flow-design.md
│   ├── frontend-integration-strategy.md
│   └── non-functional-requirements.md
│
├── development/                     # Development environment setup
│   ├── local-development-setup.md
│   ├── shared-development-setup.md
│   └── scripts/
│       ├── setup-dev-environment.sh
│       ├── setup-kind-cluster.sh
│       ├── setup-databases.sh
│       └── validate-setup.sh
│
├── services/                        # Microservices
│   ├── game-service/
│   │   ├── src/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── pyproject.toml
│   │   └── README.md
│   ├── order-service/
│   │   ├── src/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── pyproject.toml
│   │   └── README.md
│   └── analytics-service/
│       ├── src/
│       ├── tests/
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── pyproject.toml
│       └── README.md
│
├── frontend/                        # Frontend application
│   ├── lugx_gaming/                # Existing jQuery + Bootstrap frontend
│   ├── api/                        # API integration layer
│   ├── integration/                # Progressive enhancement modules
│   ├── pages/                      # New pages (login, register, cart)
│   └── config/
│
├── infrastructure/                  # Infrastructure as Code
│   ├── kubernetes/
│   │   ├── base/                   # Base Kubernetes manifests
│   │   ├── overlays/               # Environment-specific overlays
│   │   │   ├── development/
│   │   │   ├── staging/
│   │   │   └── production/
│   │   └── istio/                  # Istio configuration
│   ├── helm/                       # Helm charts
│   │   ├── lugx-gaming/
│   │   └── charts/
│   └── terraform/                  # Cloud infrastructure
│       ├── modules/
│       ├── environments/
│       └── scripts/
│
├── database/                       # Database schemas and migrations
│   ├── migrations/
│   │   ├── game-service/
│   │   ├── order-service/
│   │   └── analytics-service/
│   ├── init-scripts/
│   └── seeds/
│
├── monitoring/                     # Monitoring and observability
│   ├── prometheus/
│   ├── grafana/
│   │   ├── dashboards/
│   │   └── datasources/
│   ├── jaeger/
│   └── alerting/
│
├── docs/                          # Documentation
│   ├── api/                       # API documentation
│   ├── deployment/                # Deployment guides
│   ├── development/               # Development guides
│   └── user/                      # User documentation
│
├── scripts/                       # Utility scripts
│   ├── build/
│   ├── deploy/
│   ├── test/
│   └── utilities/
│
├── config/                        # Configuration files
│   ├── environments/
│   │   ├── development/
│   │   ├── staging/
│   │   └── production/
│   ├── logging/
│   └── security/
│
├── tests/                         # Integration and E2E tests
│   ├── integration/
│   ├── e2e/
│   ├── load/
│   └── security/
│
└── .github/                       # GitHub workflows and templates
    ├── workflows/
    │   ├── ci.yml
    │   ├── cd.yml
    │   ├── security.yml
    │   └── release.yml
    ├── ISSUE_TEMPLATE/
    ├── PULL_REQUEST_TEMPLATE.md
    └── dependabot.yml
```

### 1.2 Branching Strategy

#### **Git Flow Implementation**

```bash
# Branch naming conventions and policies
# .github/branch-protection-rules.yml

Branch Structure:
  main:                    # Production-ready code
    protection: true
    required_reviews: 2
    dismiss_stale_reviews: true
    require_code_owner_reviews: true
    
  develop:                 # Integration branch
    protection: true
    required_reviews: 1
    auto_merge_enabled: true
    
  feature/*:              # Feature development
    naming: feature/JIRA-123-description
    base_branch: develop
    auto_delete: true
    
  release/*:              # Release preparation
    naming: release/v1.2.3
    base_branch: develop
    protection: true
    
  hotfix/*:               # Production fixes
    naming: hotfix/JIRA-456-critical-fix
    base_branch: main
    protection: true
```

#### **Commit Message Convention**

```bash
# Conventional Commits specification
# .gitmessage template

# <type>[optional scope]: <description>
#
# [optional body]
#
# [optional footer(s)]

# Types:
# feat: A new feature
# fix: A bug fix
# docs: Documentation only changes
# style: Changes that do not affect the meaning of the code
# refactor: A code change that neither fixes a bug nor adds a feature
# perf: A code change that improves performance
# test: Adding missing tests or correcting existing tests
# chore: Changes to the build process or auxiliary tools

# Examples:
# feat(game-service): add game recommendation engine
# fix(order-service): resolve payment processing timeout
# docs(api): update authentication endpoints documentation
```

---

## 2. Container Registry Setup

### 2.1 Shared Container Registry

#### **Harbor Registry Setup**

```yaml
# docker-compose.harbor.yml
version: '3.8'

services:
  harbor-log:
    image: goharbor/harbor-log:v2.9.1
    container_name: harbor-log
    restart: unless-stopped
    dns_search: .
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - DAC_OVERRIDE
      - SETGID
      - SETUID
    volumes:
      - ./harbor/log/:/var/log/docker/:z
      - type: bind
        source: ./config/harbor/logrotate.conf
        target: /etc/logrotate.d/docker
    ports:
      - 127.0.0.1:1514:10514
    networks:
      - harbor

  harbor-registry:
    image: goharbor/registry-photon:v2.9.1
    container_name: harbor-registry
    restart: unless-stopped
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
    volumes:
      - ./harbor/registry:/storage:z
      - ./config/harbor/registry/:/etc/registry/:z
      - type: bind
        source: ./config/harbor/root.crt
        target: /etc/registry/root.crt
      - type: bind
        source: ./config/harbor/passwd
        target: /etc/registry/passwd
    networks:
      - harbor
    dns_search: .
    depends_on:
      - harbor-log
    logging:
      driver: "syslog"
      options:
        syslog-address: "tcp://localhost:1514"
        tag: "registry"

  harbor-registryctl:
    image: goharbor/harbor-registryctl:v2.9.1
    container_name: harbor-registryctl
    env_file:
      - ./config/harbor/registryctl_env
    restart: unless-stopped
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
    volumes:
      - ./harbor/registry:/storage:z
      - ./config/harbor/registry/:/etc/registry/:z
      - type: bind
        source: ./config/harbor/registryctl_config.yml
        target: /etc/registryctl/config.yml
    networks:
      - harbor
    dns_search: .
    depends_on:
      - harbor-log
    logging:
      driver: "syslog"
      options:
        syslog-address: "tcp://localhost:1514"
        tag: "registryctl"

  harbor-postgresql:
    image: goharbor/harbor-db:v2.9.1
    container_name: harbor-db
    restart: unless-stopped
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - DAC_OVERRIDE
      - SETGID
      - SETUID
    volumes:
      - ./harbor/database:/var/lib/postgresql/data:z
    networks:
      - harbor
    dns_search: .
    env_file:
      - ./config/harbor/db_env
    depends_on:
      - harbor-log
    logging:
      driver: "syslog"
      options:
        syslog-address: "tcp://localhost:1514"
        tag: "postgresql"

  harbor-core:
    image: goharbor/harbor-core:v2.9.1
    container_name: harbor-core
    env_file:
      - ./config/harbor/core_env
    restart: unless-stopped
    cap_drop:
      - ALL
    cap_add:
      - SETGID
      - SETUID
    volumes:
      - ./harbor/ca_download/:/etc/core/ca/:z
      - ./harbor/:/data/:z
      - ./config/harbor/core/certificates/:/etc/core/certificates/:z
      - type: bind
        source: ./config/harbor/core/app.conf
        target: /etc/core/app.conf
      - type: bind
        source: ./config/harbor/secret_key
        target: /etc/core/key
    networks:
      - harbor
    dns_search: .
    depends_on:
      - harbor-log
      - harbor-registry
      - harbor-postgresql
      - harbor-redis
    logging:
      driver: "syslog"
      options:
        syslog-address: "tcp://localhost:1514"
        tag: "core"

  harbor-portal:
    image: goharbor/harbor-portal:v2.9.1
    container_name: harbor-portal
    restart: unless-stopped
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
      - NET_BIND_SERVICE
    networks:
      - harbor
    dns_search: .
    depends_on:
      - harbor-log
    logging:
      driver: "syslog"
      options:
        syslog-address: "tcp://localhost:1514"
        tag: "portal"

  harbor-jobservice:
    image: goharbor/harbor-jobservice:v2.9.1
    container_name: harbor-jobservice
    env_file:
      - ./config/harbor/jobservice_env
    restart: unless-stopped
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
    volumes:
      - ./harbor/job_logs:/var/log/jobs:z
      - type: bind
        source: ./config/harbor/jobservice_config.yml
        target: /etc/jobservice/config.yml
    networks:
      - harbor
    dns_search: .
    depends_on:
      - harbor-log
      - harbor-core
    logging:
      driver: "syslog"
      options:
        syslog-address: "tcp://localhost:1514"
        tag: "jobservice"

  harbor-redis:
    image: goharbor/redis-photon:v2.9.1
    container_name: harbor-redis
    restart: unless-stopped
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
    volumes:
      - ./harbor/redis:/var/lib/redis
    networks:
      - harbor
    dns_search: .
    depends_on:
      - harbor-log
    logging:
      driver: "syslog"
      options:
        syslog-address: "tcp://localhost:1514"
        tag: "redis"

  harbor-proxy:
    image: goharbor/nginx-photon:v2.9.1
    container_name: harbor-proxy
    restart: unless-stopped
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
      - NET_BIND_SERVICE
    volumes:
      - ./config/harbor/nginx:/etc/nginx:z
      - type: bind
        source: ./config/harbor/cert/
        target: /etc/cert/
    networks:
      - harbor
    dns_search: .
    ports:
      - 80:8080
      - 443:8443
    depends_on:
      - harbor-log
      - harbor-postgresql
      - harbor-registry
      - harbor-core
      - harbor-portal
    logging:
      driver: "syslog"
      options:
        syslog-address: "tcp://localhost:1514"
        tag: "proxy"

networks:
  harbor:
    external: false
```

#### **Registry Lifecycle Management**

```bash
#!/bin/bash
# scripts/setup-shared-registry.sh

set -e

echo "🐳 Setting up shared Harbor container registry..."

# Create Harbor configuration
mkdir -p config/harbor/{nginx,core,registry,jobservice,cert}

# Generate Harbor configuration
cat > config/harbor/harbor.yml << 'EOF'
hostname: harbor.lugxgaming.dev

http:
  port: 80

https:
  port: 443
  certificate: /etc/cert/harbor.crt
  private_key: /etc/cert/harbor.key

harbor_admin_password: LugxGaming2023!

database:
  password: LugxDbPassword
  max_idle_conns: 100
  max_open_conns: 900

data_volume: ./harbor

trivy:
  ignore_unfixed: false
  skip_update: false
  insecure: false

jobservice:
  max_job_workers: 10

notification:
  webhook_job_max_retry: 10

chart:
  absolute_url: disabled

log:
  level: info
  local:
    rotate_count: 50
    rotate_size: 200M
    location: ./harbor/log

_version: 2.9.0

proxy:
  http_proxy:
  https_proxy:
  no_proxy: 127.0.0.1,localhost,.local,.internal,log,db,redis,nginx,core,portal,registry,registryctl,trivy-adapter,chartmuseum,jobservice,notary-server,notary-signer

metric:
  enabled: false
  port: 9090
  path: /metrics
EOF

# Generate SSL certificates
./scripts/generate-harbor-certs.sh

# Install Harbor
echo "📦 Installing Harbor..."
docker-compose -f docker-compose.harbor.yml up -d

# Wait for Harbor to be ready
echo "⏳ Waiting for Harbor to be ready..."
sleep 60

# Create lugx-gaming project
./scripts/configure-harbor-projects.sh

echo "✅ Harbor registry setup complete!"
echo "🌐 Harbor UI: https://harbor.lugxgaming.dev"
echo "👤 Admin login: admin / LugxGaming2023!"
```

### 2.2 Image Tagging Strategy

#### **Container Image Tagging Convention**

```bash
# Image tagging strategy
# scripts/tag-images.sh

#!/bin/bash
set -e

SERVICE_NAME=$1
BUILD_NUMBER=$2
GIT_COMMIT=$3
BRANCH_NAME=$4

REGISTRY="harbor.lugxgaming.dev/lugx-gaming"

# Base image name
BASE_IMAGE="${REGISTRY}/${SERVICE_NAME}"

# Tag variations
COMMIT_TAG="${BASE_IMAGE}:${GIT_COMMIT:0:8}"
BUILD_TAG="${BASE_IMAGE}:build-${BUILD_NUMBER}"
BRANCH_TAG="${BASE_IMAGE}:${BRANCH_NAME//\//-}"

# Environment-specific tags
if [ "$BRANCH_NAME" = "main" ]; then
    STABLE_TAG="${BASE_IMAGE}:stable"
    LATEST_TAG="${BASE_IMAGE}:latest"
elif [ "$BRANCH_NAME" = "develop" ]; then
    DEV_TAG="${BASE_IMAGE}:dev"
fi

# Tag images
echo "🏷️ Tagging images for ${SERVICE_NAME}..."
docker tag "${SERVICE_NAME}:local" "$COMMIT_TAG"
docker tag "${SERVICE_NAME}:local" "$BUILD_TAG"
docker tag "${SERVICE_NAME}:local" "$BRANCH_TAG"

if [ "$BRANCH_NAME" = "main" ]; then
    docker tag "${SERVICE_NAME}:local" "$STABLE_TAG"
    docker tag "${SERVICE_NAME}:local" "$LATEST_TAG"
elif [ "$BRANCH_NAME" = "develop" ]; then
    docker tag "${SERVICE_NAME}:local" "$DEV_TAG"
fi

# Push images
echo "📤 Pushing images to registry..."
docker push "$COMMIT_TAG"
docker push "$BUILD_TAG"
docker push "$BRANCH_TAG"

if [ "$BRANCH_NAME" = "main" ]; then
    docker push "$STABLE_TAG"
    docker push "$LATEST_TAG"
elif [ "$BRANCH_NAME" = "develop" ]; then
    docker push "$DEV_TAG"
fi

echo "✅ Image tagging and push complete!"
```

---

## 3. Shared Development Cluster

### 3.1 Staging Environment Setup

#### **Staging Cluster Configuration**

```yaml
# infrastructure/kubernetes/overlays/staging/kustomization.yml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: lugx-gaming-staging

resources:
- ../../base

images:
- name: harbor.lugxgaming.dev/lugx-gaming/game-service
  newTag: dev
- name: harbor.lugxgaming.dev/lugx-gaming/order-service
  newTag: dev
- name: harbor.lugxgaming.dev/lugx-gaming/analytics-service
  newTag: dev

patchesStrategicMerge:
- staging-resources.yml
- staging-config.yml

configMapGenerator:
- name: staging-config
  files:
  - config/staging.env
  options:
    disableNameSuffixHash: true

secretGenerator:
- name: staging-secrets
  files:
  - secrets/staging-db-password
  - secrets/staging-jwt-secret
  options:
    disableNameSuffixHash: true
```

#### **Staging Environment Resources**

```yaml
# infrastructure/kubernetes/overlays/staging/staging-resources.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: game-service
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: game-service
        resources:
          requests:
            memory: "512Mi"
            cpu: "300m"
          limits:
            memory: "1Gi"
            cpu: "800m"
        env:
        - name: ENVIRONMENT
          value: "staging"
        - name: DATABASE_URL
          value: "postgresql://lugx_user:$(DB_PASSWORD)@postgresql-staging:5432/lugx_games_staging"
        - name: REDIS_URL
          value: "redis://redis-staging:6379/0"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: order-service
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        env:
        - name: ENVIRONMENT
          value: "staging"
        - name: DATABASE_URL
          value: "postgresql://lugx_user:$(DB_PASSWORD)@postgresql-staging:5432/lugx_orders_staging"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: analytics-service
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: analytics-service
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "3Gi"
            cpu: "1500m"
        env:
        - name: ENVIRONMENT
          value: "staging"
        - name: CLICKHOUSE_URL
          value: "clickhouse://lugx_user:$(DB_PASSWORD)@clickhouse-staging:9000/lugx_analytics_staging"
```

### 3.2 Istio Configuration for Staging

#### **Staging Istio Setup**

```yaml
# infrastructure/kubernetes/istio/staging-gateway.yml
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: lugx-gaming-staging-gateway
  namespace: lugx-gaming-staging
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - staging.lugxgaming.dev
    tls:
      httpsRedirect: true
  - port:
      number: 443
      name: https
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: staging-tls-cert
    hosts:
    - staging.lugxgaming.dev

---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: lugx-gaming-staging-vs
  namespace: lugx-gaming-staging
spec:
  hosts:
  - staging.lugxgaming.dev
  gateways:
  - lugx-gaming-staging-gateway
  http:
  - match:
    - uri:
        prefix: /api/v1/games
    route:
    - destination:
        host: game-service.lugx-gaming-staging.svc.cluster.local
        port:
          number: 8000
    retries:
      attempts: 3
      perTryTimeout: 10s
    timeout: 30s
  - match:
    - uri:
        prefix: /api/v1/auth
    - uri:
        prefix: /api/v1/cart
    - uri:
        prefix: /api/v1/orders
    route:
    - destination:
        host: order-service.lugx-gaming-staging.svc.cluster.local
        port:
          number: 8001
    retries:
      attempts: 3
      perTryTimeout: 15s
    timeout: 45s
  - match:
    - uri:
        prefix: /api/v1/analytics
    route:
    - destination:
        host: analytics-service.lugx-gaming-staging.svc.cluster.local
        port:
          number: 8002
    retries:
      attempts: 2
      perTryTimeout: 5s
    timeout: 10s
```

---

## 4. Configuration Management

### 4.1 Environment-Specific Configuration

#### **Configuration Structure**

```bash
config/
├── environments/
│   ├── development/
│   │   ├── database.yml
│   │   ├── services.yml
│   │   ├── istio.yml
│   │   └── monitoring.yml
│   ├── staging/
│   │   ├── database.yml
│   │   ├── services.yml
│   │   ├── istio.yml
│   │   └── monitoring.yml
│   └── production/
│       ├── database.yml
│       ├── services.yml
│       ├── istio.yml
│       └── monitoring.yml
├── secrets/
│   ├── development/
│   ├── staging/
│   └── production/
└── common/
    ├── logging.yml
    ├── security.yml
    └── networking.yml
```

#### **Environment Configuration Management**

```yaml
# config/environments/staging/services.yml
gameService:
  replicas: 2
  image: harbor.lugxgaming.dev/lugx-gaming/game-service:dev
  resources:
    requests:
      memory: "512Mi"
      cpu: "300m"
    limits:
      memory: "1Gi"
      cpu: "800m"
  config:
    LOG_LEVEL: "INFO"
    MAX_WORKERS: 4
    DATABASE_POOL_SIZE: 20
    CACHE_TTL: 900  # 15 minutes
    
orderService:
  replicas: 3
  image: harbor.lugxgaming.dev/lugx-gaming/order-service:dev
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "1000m"
  config:
    LOG_LEVEL: "INFO"
    MAX_WORKERS: 8
    DATABASE_POOL_SIZE: 50
    SESSION_TIMEOUT: 3600  # 1 hour
    
analyticsService:
  replicas: 2
  image: harbor.lugxgaming.dev/lugx-gaming/analytics-service:dev
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "3Gi"
      cpu: "1500m"
  config:
    LOG_LEVEL: "INFO"
    BATCH_SIZE: 1000
    FLUSH_INTERVAL: 5
    RETENTION_DAYS: 90
```

### 4.2 GitOps Configuration

#### **ArgoCD Application Setup**

```yaml
# infrastructure/gitops/lugx-gaming-staging.yml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: lugx-gaming-staging
  namespace: argocd
spec:
  project: lugx-gaming
  source:
    repoURL: https://github.com/lugx-gaming/lugx-gaming-project
    targetRevision: develop
    path: infrastructure/kubernetes/overlays/staging
  destination:
    server: https://kubernetes.default.svc
    namespace: lugx-gaming-staging
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
  revisionHistoryLimit: 10
```

---

## 5. CI/CD Pipeline Integration

### 5.1 GitHub Actions Workflows

#### **Continuous Integration Workflow**

```yaml
# .github/workflows/ci.yml
name: Continuous Integration

on:
  push:
    branches: [ develop, main ]
  pull_request:
    branches: [ develop, main ]

env:
  REGISTRY: harbor.lugxgaming.dev/lugx-gaming

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [game-service, order-service, analytics-service]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('services/${{ matrix.service }}/requirements.txt') }}
    
    - name: Install dependencies
      run: |
        cd services/${{ matrix.service }}
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run linting
      run: |
        cd services/${{ matrix.service }}
        flake8 src/ tests/
        black --check src/ tests/
        isort --check src/ tests/
        mypy src/
    
    - name: Run tests
      run: |
        cd services/${{ matrix.service }}
        pytest tests/ --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: services/${{ matrix.service }}/coverage.xml
        flags: ${{ matrix.service }}

  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Run security scan
      uses: securecodewarrior/github-action-add-sarif@v1
      with:
        sarif-file: security-scan-results.sarif

  build:
    runs-on: ubuntu-latest
    needs: [test, security]
    if: github.event_name == 'push'
    strategy:
      matrix:
        service: [game-service, order-service, analytics-service]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Login to Harbor
      uses: docker/login-action@v3
      with:
        registry: harbor.lugxgaming.dev
        username: ${{ secrets.HARBOR_USERNAME }}
        password: ${{ secrets.HARBOR_PASSWORD }}
    
    - name: Build and push
      uses: docker/build-push-action@v5
      with:
        context: services/${{ matrix.service }}
        push: true
        tags: |
          ${{ env.REGISTRY }}/${{ matrix.service }}:${{ github.sha }}
          ${{ env.REGISTRY }}/${{ matrix.service }}:${{ github.ref_name }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
```

#### **Continuous Deployment Workflow**

```yaml
# .github/workflows/cd.yml
name: Continuous Deployment

on:
  push:
    branches: [ develop ]
  workflow_run:
    workflows: ["Continuous Integration"]
    types:
      - completed

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop' && github.event.workflow_run.conclusion == 'success'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup kubectl
      uses: azure/setup-kubectl@v3
      with:
        version: '1.28.0'
    
    - name: Setup Kustomize
      uses: imranismail/setup-kustomize@v2
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-west-2
    
    - name: Update kubeconfig
      run: |
        aws eks update-kubeconfig --name lugx-gaming-staging --region us-west-2
    
    - name: Deploy to staging
      run: |
        cd infrastructure/kubernetes/overlays/staging
        kustomize edit set image harbor.lugxgaming.dev/lugx-gaming/game-service:${{ github.sha }}
        kustomize edit set image harbor.lugxgaming.dev/lugx-gaming/order-service:${{ github.sha }}
        kustomize edit set image harbor.lugxgaming.dev/lugx-gaming/analytics-service:${{ github.sha }}
        kubectl apply -k .
    
    - name: Wait for deployment
      run: |
        kubectl rollout status deployment/game-service -n lugx-gaming-staging --timeout=600s
        kubectl rollout status deployment/order-service -n lugx-gaming-staging --timeout=600s
        kubectl rollout status deployment/analytics-service -n lugx-gaming-staging --timeout=600s
    
    - name: Run integration tests
      run: |
        ./scripts/run-integration-tests.sh staging
    
    - name: Notify deployment status
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        channel: '#deployments'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## 6. Team Collaboration Tools

### 6.1 Development Workflow Scripts

#### **Daily Development Workflow**

```bash
#!/bin/bash
# scripts/dev-workflow.sh

set -e

ACTION=$1

case $ACTION in
  "start")
    echo "🚀 Starting daily development workflow..."
    
    # Update from remote
    git fetch origin
    git pull origin develop
    
    # Start local services
    docker-compose -f docker-compose.databases.yml up -d
    
    # Check cluster status
    kubectl cluster-info
    kubectl get pods -n lugx-gaming
    
    # Start port forwards for development
    kubectl port-forward svc/kiali 20001:20001 -n istio-system &
    kubectl port-forward svc/grafana 3000:3000 -n istio-system &
    kubectl port-forward svc/jaeger 16686:16686 -n istio-system &
    
    echo "✅ Development environment ready!"
    ;;
    
  "test")
    echo "🧪 Running comprehensive tests..."
    
    # Run unit tests for all services
    for service in game-service order-service analytics-service; do
      echo "Testing $service..."
      cd services/$service
      pytest tests/ --cov=src
      cd ../../
    done
    
    # Run integration tests
    ./scripts/run-integration-tests.sh local
    
    echo "✅ All tests completed!"
    ;;
    
  "build")
    echo "🔨 Building all services..."
    
    # Build Docker images
    for service in game-service order-service analytics-service; do
      echo "Building $service..."
      docker build -t $service:local services/$service/
    done
    
    # Load images to Kind cluster
    for service in game-service order-service analytics-service; do
      kind load docker-image $service:local --name lugx-gaming-dev
    done
    
    echo "✅ All services built and loaded!"
    ;;
    
  "deploy")
    echo "🚀 Deploying to local cluster..."
    
    # Deploy using Helm
    helm upgrade --install lugx-gaming helm/lugx-gaming/ \
      --namespace lugx-gaming \
      --create-namespace \
      --values helm/lugx-gaming/values.yaml \
      --values helm/lugx-gaming/values-dev.yaml
    
    echo "✅ Deployment complete!"
    ;;
    
  "stop")
    echo "🛑 Stopping development environment..."
    
    # Stop port forwards
    pkill -f "kubectl port-forward" || true
    
    # Stop databases
    docker-compose -f docker-compose.databases.yml down
    
    echo "✅ Development environment stopped!"
    ;;
    
  *)
    echo "Usage: $0 {start|test|build|deploy|stop}"
    echo ""
    echo "Commands:"
    echo "  start  - Start development environment"
    echo "  test   - Run all tests"
    echo "  build  - Build and load all services"
    echo "  deploy - Deploy to local cluster"
    echo "  stop   - Stop development environment"
    ;;
esac
```

This comprehensive shared development infrastructure setup provides a robust foundation for team collaboration, ensuring consistency across development environments and enabling efficient CI/CD workflows for the Lugx Gaming platform.