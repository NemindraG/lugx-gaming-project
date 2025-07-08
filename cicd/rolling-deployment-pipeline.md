# Lugx Gaming Platform - CI/CD Pipeline with Rolling Deployment Strategy

## Executive Summary

This document provides a comprehensive CI/CD pipeline design for the Lugx Gaming platform, implementing a **Rolling Deployment Strategy** to maintain 100% uptime during deployments while ensuring automated testing and validation at every stage.

## Pipeline Architecture Overview

### Deployment Strategy: Rolling Deployment
**Rolling Deployment** gradually replaces instances of the previous version with the new version, ensuring zero downtime and the ability to roll back if issues are detected.

```
Rolling Deployment Flow:
┌─────────────────────────────────────────────────────────────────┐
│                    ROLLING UPDATE STRATEGY                     │
│                                                                 │
│  Old Version Pods: [V1] [V1] [V1] [V1]                        │
│                     ↓                                          │
│  Step 1:           [V2] [V1] [V1] [V1]  ← Deploy 25%          │
│  Step 2:           [V2] [V2] [V1] [V1]  ← Deploy 50%          │
│  Step 3:           [V2] [V2] [V2] [V1]  ← Deploy 75%          │
│  Step 4:           [V2] [V2] [V2] [V2]  ← Deploy 100%         │
│                                                                 │
│  Benefits: Zero downtime, gradual rollout, easy rollback       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. CI/CD Pipeline Architecture

### 1.1 Technology Stack

```yaml
CI/CD Technology Stack:
  Version Control: GitHub
  CI/CD Platform: GitHub Actions
  Container Registry: Amazon ECR
  Kubernetes: Amazon EKS
  Monitoring: Prometheus + Grafana
  Testing: Jest, Pytest, K6
  Security Scanning: Trivy, SonarQube
  Deployment: Kubernetes Rolling Update
  Rollback: Automatic on health check failure
```

### 1.2 Pipeline Stages

```yaml
Pipeline Stages:
  1. Source Code Trigger
  2. Code Quality & Security Scan
  3. Unit & Integration Tests
  4. Container Build & Scan
  5. Deploy to Staging
  6. Integration Tests (Staging)
  7. Rolling Deploy to Production
  8. Post-Deployment Health Checks
  9. Integration Tests (Production)
  10. Monitoring & Alerting
```

---

## 2. GitHub Actions Workflow Configuration

### 2.1 Main CI/CD Workflow

```yaml
# .github/workflows/lugx-gaming-cicd.yml
name: Lugx Gaming CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
    paths-ignore: [ 'docs/**', '*.md' ]
  pull_request:
    branches: [ main ]

env:
  AWS_REGION: us-west-2
  EKS_CLUSTER_NAME: lugx-gaming-prod
  ECR_REGISTRY: 123456789012.dkr.ecr.us-west-2.amazonaws.com

jobs:
  # ========================================
  # STAGE 1: CODE QUALITY & SECURITY
  # ========================================
  code-quality:
    name: Code Quality & Security Scan
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout Code
      uses: actions/checkout@v4
      with:
        fetch-depth: 0  # Full history for SonarQube
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install Dependencies
      run: |
        # Frontend dependencies
        cd lugx_gaming && npm ci
        
        # Backend dependencies
        cd ../services/game-service && pip install -r requirements.txt
        cd ../order-service && pip install -r requirements.txt
        cd ../analytics-service && pip install -r requirements.txt
    
    - name: Lint Code
      run: |
        # Frontend linting
        cd lugx_gaming && npm run lint
        
        # Backend linting
        cd ../services/game-service && flake8 .
        cd ../order-service && flake8 .
        cd ../analytics-service && flake8 .
    
    - name: Security Vulnerability Scan
      uses: github/super-linter@v5
      env:
        DEFAULT_BRANCH: main
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        VALIDATE_PYTHON_PYLINT: false
        VALIDATE_PYTHON_FLAKE8: true
        VALIDATE_JAVASCRIPT_ES: true
    
    - name: SonarQube Code Analysis
      uses: sonarqube-quality-gate-action@master
      env:
        SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}

  # ========================================
  # STAGE 2: UNIT & INTEGRATION TESTS
  # ========================================
  unit-tests:
    name: Unit & Integration Tests
    runs-on: ubuntu-latest
    needs: code-quality
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - name: Checkout Code
      uses: actions/checkout@v4
    
    - name: Setup Test Environment
      run: |
        # Setup test databases
        export DATABASE_URL="postgresql://postgres:test_password@localhost:5432/test_db"
        export REDIS_URL="redis://localhost:6379/0"
    
    - name: Run Frontend Tests
      run: |
        cd lugx_gaming
        npm ci
        npm run test:coverage
    
    - name: Run Backend Tests
      run: |
        # Game Service Tests
        cd services/game-service
        pytest tests/ --cov=app --cov-report=xml
        
        # Order Service Tests
        cd ../order-service
        pytest tests/ --cov=app --cov-report=xml
        
        # Analytics Service Tests
        cd ../analytics-service
        pytest tests/ --cov=app --cov-report=xml
    
    - name: Upload Test Coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./services/*/coverage.xml
        fail_ci_if_error: true

  # ========================================
  # STAGE 3: CONTAINER BUILD & SCAN
  # ========================================
  build-and-scan:
    name: Build & Scan Container Images
    runs-on: ubuntu-latest
    needs: unit-tests
    
    strategy:
      matrix:
        service: [frontend, game-service, order-service, analytics-service]
    
    steps:
    - name: Checkout Code
      uses: actions/checkout@v4
    
    - name: Configure AWS Credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}
    
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v2
    
    - name: Build Container Image
      id: build-image
      run: |
        # Dynamic service path selection
        case "${{ matrix.service }}" in
          "frontend")
            SERVICE_PATH="lugx_gaming"
            DOCKERFILE_PATH="Dockerfile"
            ;;
          *)
            SERVICE_PATH="services/${{ matrix.service }}"
            DOCKERFILE_PATH="Dockerfile"
            ;;
        esac
        
        # Build and tag image
        IMAGE_TAG="${{ github.sha }}"
        IMAGE_URI="${{ env.ECR_REGISTRY }}/lugx-${{ matrix.service }}:${IMAGE_TAG}"
        
        docker build -t ${IMAGE_URI} -f ${SERVICE_PATH}/${DOCKERFILE_PATH} ${SERVICE_PATH}
        docker tag ${IMAGE_URI} ${{ env.ECR_REGISTRY }}/lugx-${{ matrix.service }}:latest
        
        echo "image-uri=${IMAGE_URI}" >> $GITHUB_OUTPUT
    
    - name: Container Security Scan
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: ${{ steps.build-image.outputs.image-uri }}
        format: 'sarif'
        output: 'trivy-results-${{ matrix.service }}.sarif'
    
    - name: Upload Trivy Scan Results
      uses: github/codeql-action/upload-sarif@v3
      with:
        sarif_file: 'trivy-results-${{ matrix.service }}.sarif'
    
    - name: Push to ECR
      if: github.ref == 'refs/heads/main'
      run: |
        docker push ${{ steps.build-image.outputs.image-uri }}
        docker push ${{ env.ECR_REGISTRY }}/lugx-${{ matrix.service }}:latest

  # ========================================
  # STAGE 4: STAGING DEPLOYMENT
  # ========================================
  deploy-staging:
    name: Deploy to Staging Environment
    runs-on: ubuntu-latest
    needs: build-and-scan
    if: github.ref == 'refs/heads/main'
    
    environment:
      name: staging
      url: https://staging.lugxgaming.com
    
    steps:
    - name: Checkout Code
      uses: actions/checkout@v4
    
    - name: Configure AWS & Kubernetes
      run: |
        aws eks update-kubeconfig --region ${{ env.AWS_REGION }} --name ${{ env.EKS_CLUSTER_NAME }}
        kubectl config use-context arn:aws:eks:${{ env.AWS_REGION }}:123456789012:cluster/${{ env.EKS_CLUSTER_NAME }}
    
    - name: Deploy to Staging
      run: |
        # Update image tags in staging manifests
        cd infrastructure/kubernetes/staging
        
        # Update image tags
        IMAGE_TAG="${{ github.sha }}"
        sed -i "s|image: .*lugx-frontend:.*|image: ${{ env.ECR_REGISTRY }}/lugx-frontend:${IMAGE_TAG}|" frontend/deployment.yaml
        sed -i "s|image: .*lugx-game-service:.*|image: ${{ env.ECR_REGISTRY }}/lugx-game-service:${IMAGE_TAG}|" game-service/deployment.yaml
        sed -i "s|image: .*lugx-order-service:.*|image: ${{ env.ECR_REGISTRY }}/lugx-order-service:${IMAGE_TAG}|" order-service/deployment.yaml
        sed -i "s|image: .*lugx-analytics-service:.*|image: ${{ env.ECR_REGISTRY }}/lugx-analytics-service:${IMAGE_TAG}|" analytics-service/deployment.yaml
        
        # Apply staging deployment
        kubectl apply -f . --recursive
    
    - name: Wait for Staging Deployment
      run: |
        kubectl rollout status deployment/frontend-deployment -n staging --timeout=600s
        kubectl rollout status deployment/game-service-deployment -n staging --timeout=600s
        kubectl rollout status deployment/order-service-deployment -n staging --timeout=600s
        kubectl rollout status deployment/analytics-service-deployment -n staging --timeout=600s

  # ========================================
  # STAGE 5: STAGING INTEGRATION TESTS
  # ========================================
  staging-tests:
    name: Integration Tests (Staging)
    runs-on: ubuntu-latest
    needs: deploy-staging
    
    steps:
    - name: Checkout Code
      uses: actions/checkout@v4
    
    - name: Setup Test Environment
      run: |
        npm ci -prefix testing/integration
        pip install -r testing/integration/requirements.txt
    
    - name: Run Integration Tests
      env:
        STAGING_URL: https://staging.lugxgaming.com
        API_BASE_URL: https://api.staging.lugxgaming.com
      run: |
        cd testing/integration
        
        # API Integration Tests
        pytest test_api_integration.py --base-url=$API_BASE_URL
        
        # Frontend Integration Tests
        npm run test:e2e -- --base-url=$STAGING_URL
        
        # Performance Tests
        k6 run performance_tests.js
    
    - name: Health Check Validation
      run: |
        # Validate all services are healthy
        curl -f $STAGING_URL/health || exit 1
        curl -f $API_BASE_URL/api/v1/games/health || exit 1
        curl -f $API_BASE_URL/api/v1/orders/health || exit 1
        curl -f $API_BASE_URL/api/v1/analytics/health || exit 1

  # ========================================
  # STAGE 6: PRODUCTION ROLLING DEPLOYMENT
  # ========================================
  deploy-production:
    name: Rolling Deploy to Production
    runs-on: ubuntu-latest
    needs: staging-tests
    if: github.ref == 'refs/heads/main'
    
    environment:
      name: production
      url: https://lugxgaming.com
    
    steps:
    - name: Checkout Code
      uses: actions/checkout@v4
    
    - name: Configure Production Access
      run: |
        aws eks update-kubeconfig --region ${{ env.AWS_REGION }} --name ${{ env.EKS_CLUSTER_NAME }}
        kubectl config use-context arn:aws:eks:${{ env.AWS_REGION }}:123456789012:cluster/${{ env.EKS_CLUSTER_NAME }}
    
    - name: Rolling Update Configuration
      run: |
        # Configure rolling update strategy
        cd infrastructure/kubernetes/production
        
        # Ensure rolling update settings
        kubectl patch deployment frontend-deployment -n production -p '{
          "spec": {
            "strategy": {
              "type": "RollingUpdate",
              "rollingUpdate": {
                "maxUnavailable": "25%",
                "maxSurge": "25%"
              }
            }
          }
        }'
    
    - name: Deploy Frontend (Rolling)
      run: |
        IMAGE_TAG="${{ github.sha }}"
        kubectl set image deployment/frontend-deployment \
          frontend=${{ env.ECR_REGISTRY }}/lugx-frontend:${IMAGE_TAG} \
          -n production
        
        # Wait for rolling update to complete
        kubectl rollout status deployment/frontend-deployment -n production --timeout=600s
    
    - name: Deploy Game Service (Rolling)
      run: |
        IMAGE_TAG="${{ github.sha }}"
        kubectl set image deployment/game-service-deployment \
          game-service=${{ env.ECR_REGISTRY }}/lugx-game-service:${IMAGE_TAG} \
          -n production
        
        kubectl rollout status deployment/game-service-deployment -n production --timeout=600s
    
    - name: Deploy Order Service (Rolling)
      run: |
        IMAGE_TAG="${{ github.sha }}"
        kubectl set image deployment/order-service-deployment \
          order-service=${{ env.ECR_REGISTRY }}/lugx-order-service:${IMAGE_TAG} \
          -n production
        
        kubectl rollout status deployment/order-service-deployment -n production --timeout=600s
    
    - name: Deploy Analytics Service (Rolling)
      run: |
        IMAGE_TAG="${{ github.sha }}"
        kubectl set image deployment/analytics-service-deployment \
          analytics-service=${{ env.ECR_REGISTRY }}/lugx-analytics-service:${IMAGE_TAG} \
          -n production
        
        kubectl rollout status deployment/analytics-service-deployment -n production --timeout=600s

  # ========================================
  # STAGE 7: POST-DEPLOYMENT VALIDATION
  # ========================================
  production-validation:
    name: Production Health Check & Integration Tests
    runs-on: ubuntu-latest
    needs: deploy-production
    
    steps:
    - name: Checkout Code
      uses: actions/checkout@v4
    
    - name: Production Health Checks
      env:
        PROD_URL: https://lugxgaming.com
        API_URL: https://api.lugxgaming.com
      run: |
        # Wait for services to be ready
        sleep 60
        
        # Comprehensive health checks
        echo "Checking frontend health..."
        curl -f $PROD_URL/health || exit 1
        
        echo "Checking API health..."
        curl -f $API_URL/api/v1/games/health || exit 1
        curl -f $API_URL/api/v1/orders/health || exit 1
        curl -f $API_URL/api/v1/analytics/health || exit 1
        
        # Check response times
        RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' $PROD_URL)
        if (( $(echo "$RESPONSE_TIME > 2.0" | bc -l) )); then
          echo "Frontend response time too slow: ${RESPONSE_TIME}s"
          exit 1
        fi
    
    - name: Run Production Integration Tests
      env:
        PROD_URL: https://lugxgaming.com
        API_URL: https://api.lugxgaming.com
      run: |
        cd testing/integration
        
        # Run critical path tests only
        pytest test_critical_paths.py --base-url=$API_URL
        
        # Run smoke tests
        npm run test:smoke -- --base-url=$PROD_URL
    
    - name: Database Connectivity Test
      run: |
        # Test database connections (non-destructive)
        kubectl exec -n production deployment/game-service-deployment -- \
          python -c "from app.database import engine; engine.execute('SELECT 1')"
        
        kubectl exec -n production deployment/order-service-deployment -- \
          python -c "from app.database import engine; engine.execute('SELECT 1')"

  # ========================================
  # STAGE 8: AUTOMATIC ROLLBACK ON FAILURE
  # ========================================
  rollback-on-failure:
    name: Automatic Rollback on Failure
    runs-on: ubuntu-latest
    needs: production-validation
    if: failure()
    
    steps:
    - name: Rollback Production Deployment
      run: |
        echo "Rolling back production deployment due to validation failure..."
        
        # Rollback all services to previous version
        kubectl rollout undo deployment/frontend-deployment -n production
        kubectl rollout undo deployment/game-service-deployment -n production
        kubectl rollout undo deployment/order-service-deployment -n production
        kubectl rollout undo deployment/analytics-service-deployment -n production
        
        # Wait for rollback to complete
        kubectl rollout status deployment/frontend-deployment -n production
        kubectl rollout status deployment/game-service-deployment -n production
        kubectl rollout status deployment/order-service-deployment -n production
        kubectl rollout status deployment/analytics-service-deployment -n production
    
    - name: Notify Teams of Rollback
      uses: 8398a7/action-slack@v3
      with:
        status: failure
        channel: '#devops-alerts'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
        message: |
          🚨 **PRODUCTION ROLLBACK EXECUTED**
          
          **Repository**: ${{ github.repository }}
          **Commit**: ${{ github.sha }}
          **Branch**: ${{ github.ref }}
          **Reason**: Post-deployment validation failed
          
          All services have been rolled back to the previous stable version.
          Please investigate the failed deployment immediately.

  # ========================================
  # STAGE 9: MONITORING & NOTIFICATIONS
  # ========================================
  post-deployment-monitoring:
    name: Setup Post-Deployment Monitoring
    runs-on: ubuntu-latest
    needs: production-validation
    if: success()
    
    steps:
    - name: Update Monitoring Dashboards
      run: |
        # Update deployment tracking in monitoring
        curl -X POST "https://monitoring.lugxgaming.com/api/deployments" \
          -H "Authorization: Bearer ${{ secrets.MONITORING_TOKEN }}" \
          -d "{
            \"version\": \"${{ github.sha }}\",
            \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
            \"services\": [\"frontend\", \"game-service\", \"order-service\", \"analytics-service\"],
            \"environment\": \"production\"
          }"
    
    - name: Notify Success
      uses: 8398a7/action-slack@v3
      with:
        status: success
        channel: '#deployments'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
        message: |
          ✅ **PRODUCTION DEPLOYMENT SUCCESSFUL**
          
          **Repository**: ${{ github.repository }}
          **Commit**: ${{ github.sha }}
          **Branch**: ${{ github.ref }}
          **Services**: Frontend, Game Service, Order Service, Analytics Service
          
          All health checks passed. Deployment completed successfully.
          Monitor: https://monitoring.lugxgaming.com
```

---

## 3. Kubernetes Rolling Update Configuration

### 3.1 Deployment Strategy Settings

```yaml
# infrastructure/kubernetes/production/frontend/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-deployment
  namespace: production
spec:
  replicas: 6
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 25%  # At most 1-2 pods unavailable
      maxSurge: 25%        # At most 1-2 extra pods during update
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
        version: "{{ .Values.image.tag }}"
    spec:
      containers:
      - name: frontend
        image: 123456789012.dkr.ecr.us-west-2.amazonaws.com/lugx-frontend:latest
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        env:
        - name: API_BASE_URL
          value: "https://api.lugxgaming.com"
        - name: ENVIRONMENT
          value: "production"

---
# Service configuration remains stable during rolling updates
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: production
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
    protocol: TCP
  type: ClusterIP
```

### 3.2 Backend Services Rolling Update

```yaml
# infrastructure/kubernetes/production/game-service/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: game-service-deployment
  namespace: production
spec:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1     # Keep 3/4 pods running
      maxSurge: 1          # Maximum 5 pods during update
  selector:
    matchLabels:
      app: game-service
  template:
    metadata:
      labels:
        app: game-service
        version: "{{ .Values.image.tag }}"
    spec:
      containers:
      - name: game-service
        image: 123456789012.dkr.ecr.us-west-2.amazonaws.com/lugx-game-service:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/v1/games/health
            port: 8000
          initialDelaySeconds: 45
          periodSeconds: 15
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /api/v1/games/ready
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 2
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: game-service-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: game-service-secrets
              key: redis-url
```

---

## 4. Integration Test Suite

### 4.1 Critical Path Tests

```python
# testing/integration/test_critical_paths.py
import pytest
import requests
import time
from datetime import datetime

class TestCriticalPaths:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
    
    @pytest.mark.critical
    def test_homepage_load(self):
        """Test homepage loads successfully"""
        response = self.session.get(f"{self.base_url}/")
        assert response.status_code == 200
        assert "Lugx Gaming" in response.text
        assert response.elapsed.total_seconds() < 2.0
    
    @pytest.mark.critical  
    def test_api_health_endpoints(self):
        """Test all API health endpoints"""
        health_endpoints = [
            "/api/v1/games/health",
            "/api/v1/orders/health", 
            "/api/v1/analytics/health"
        ]
        
        for endpoint in health_endpoints:
            response = self.session.get(f"{self.base_url}{endpoint}")
            assert response.status_code == 200
            
            health_data = response.json()
            assert health_data["status"] == "healthy"
            assert health_data["timestamp"] is not None
    
    @pytest.mark.critical
    def test_game_catalog_api(self):
        """Test game catalog functionality"""
        # Test trending games
        response = self.session.get(f"{self.base_url}/api/v1/games/trending")
        assert response.status_code == 200
        
        games = response.json()
        assert len(games["games"]) > 0
        assert all(game["id"] for game in games["games"])
        assert all(game["name"] for game in games["games"])
    
    @pytest.mark.critical
    def test_analytics_event_capture(self):
        """Test analytics event submission"""
        event_data = {
            "events": [{
                "event_type": "page_view",
                "page_url": "/test",
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": "test_session"
            }]
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/analytics/events/batch",
            json=event_data
        )
        assert response.status_code in [200, 201]
    
    @pytest.mark.critical
    def test_database_connectivity(self):
        """Test database connectivity via API"""
        # Test Game Service DB
        response = self.session.get(f"{self.base_url}/api/v1/games?limit=1")
        assert response.status_code == 200
        
        # Test Order Service DB (create test user)
        test_user = {
            "email": f"test_{int(time.time())}@test.com",
            "username": f"testuser_{int(time.time())}",
            "password": "testpass123"
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/register",
            json=test_user
        )
        assert response.status_code in [200, 201, 409]  # 409 if user exists
```

### 4.2 Performance Tests

```javascript
// testing/integration/performance_tests.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics
let apiErrors = new Counter('api_errors');
let apiResponseTrend = new Trend('api_response_time');
let successRate = new Rate('success_rate');

export let options = {
  stages: [
    { duration: '2m', target: 10 },  // Ramp up
    { duration: '5m', target: 50 },  // Stay at 50 users
    { duration: '2m', target: 0 },   // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<2000'], // 95% of requests under 2s
    'success_rate': ['rate>0.95'],       // 95% success rate
    'api_errors': ['count<50'],          // Less than 50 API errors
  },
};

const BASE_URL = __ENV.BASE_URL || 'https://api.lugxgaming.com';

export default function() {
  // Test homepage
  let homeResponse = http.get(`${BASE_URL}/`);
  check(homeResponse, {
    'homepage status is 200': (r) => r.status === 200,
    'homepage response time < 2s': (r) => r.timings.duration < 2000,
  });
  
  // Test API endpoints
  let gamesResponse = http.get(`${BASE_URL}/api/v1/games/trending`);
  check(gamesResponse, {
    'games API status is 200': (r) => r.status === 200,
    'games API response time < 1s': (r) => r.timings.duration < 1000,
  });
  
  // Record metrics
  successRate.add(homeResponse.status === 200);
  apiResponseTrend.add(gamesResponse.timings.duration);
  
  if (gamesResponse.status !== 200) {
    apiErrors.add(1);
  }
  
  sleep(1);
}
```

---

## 5. Monitoring and Alerting Integration

### 5.1 Deployment Monitoring

```yaml
# monitoring/prometheus/deployment-alerts.yml
groups:
- name: deployment.rules
  rules:
  - alert: RollingUpdateStuck
    expr: |
      (
        kube_deployment_status_replicas != kube_deployment_status_updated_replicas
      ) and (
        changes(kube_deployment_status_observed_generation[10m]) == 0
      )
    for: 10m
    labels:
      severity: critical
    annotations:
      summary: "Rolling update stuck for deployment {{ $labels.deployment }}"
      description: "Deployment {{ $labels.deployment }} has been stuck in rolling update for more than 10 minutes"

  - alert: DeploymentReplicasMismatch
    expr: |
      kube_deployment_spec_replicas != kube_deployment_status_replicas
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Deployment replicas mismatch"
      description: "Deployment {{ $labels.deployment }} has {{ $value }} replicas available, expected {{ $labels.spec_replicas }}"

  - alert: PodCrashLooping
    expr: |
      rate(kube_pod_container_status_restarts_total[15m]) > 0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Pod {{ $labels.pod }} is crash looping"
      description: "Pod {{ $labels.pod }} has restarted {{ $value }} times in the last 15 minutes"
```

### 5.2 Health Check Monitoring

```python
# monitoring/health_check_monitor.py
import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import List, Dict

class HealthCheckMonitor:
    def __init__(self):
        self.endpoints = [
            "https://lugxgaming.com/health",
            "https://api.lugxgaming.com/api/v1/games/health",
            "https://api.lugxgaming.com/api/v1/orders/health",
            "https://api.lugxgaming.com/api/v1/analytics/health"
        ]
        self.alert_threshold = 3  # Alert after 3 consecutive failures
        self.failure_counts = {endpoint: 0 for endpoint in self.endpoints}
    
    async def check_endpoint(self, session: aiohttp.ClientSession, endpoint: str) -> Dict:
        try:
            async with session.get(endpoint, timeout=10) as response:
                if response.status == 200:
                    self.failure_counts[endpoint] = 0
                    return {
                        "endpoint": endpoint,
                        "status": "healthy",
                        "response_time": response.headers.get('X-Response-Time', 'N/A'),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    self.failure_counts[endpoint] += 1
                    return {
                        "endpoint": endpoint,
                        "status": "unhealthy",
                        "status_code": response.status,
                        "failure_count": self.failure_counts[endpoint],
                        "timestamp": datetime.utcnow().isoformat()
                    }
        except Exception as e:
            self.failure_counts[endpoint] += 1
            return {
                "endpoint": endpoint,
                "status": "error",
                "error": str(e),
                "failure_count": self.failure_counts[endpoint],
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def monitor_all_endpoints(self) -> List[Dict]:
        async with aiohttp.ClientSession() as session:
            tasks = [self.check_endpoint(session, endpoint) for endpoint in self.endpoints]
            results = await asyncio.gather(*tasks)
            
            # Check for alert conditions
            for result in results:
                if (result.get("failure_count", 0) >= self.alert_threshold):
                    await self.send_alert(result)
            
            return results
    
    async def send_alert(self, result: Dict):
        # Send alert to monitoring system
        alert_data = {
            "alert": "endpoint_failure",
            "endpoint": result["endpoint"],
            "failure_count": result["failure_count"],
            "timestamp": result["timestamp"],
            "severity": "critical"
        }
        
        # Send to Slack, PagerDuty, etc.
        logging.error(f"ALERT: {alert_data}")

# Run continuous monitoring
async def main():
    monitor = HealthCheckMonitor()
    while True:
        results = await monitor.monitor_all_endpoints()
        logging.info(f"Health check completed: {len(results)} endpoints checked")
        await asyncio.sleep(60)  # Check every minute

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 6. Rollback Strategy

### 6.1 Automatic Rollback Triggers

```yaml
# Rollback trigger conditions
Automatic Rollback Triggers:
  1. Health Check Failure:
     - Any service health endpoint returns 5xx for 3 consecutive checks
     - Response time > 5 seconds for 5 consecutive checks
  
  2. Error Rate Spike:
     - Application error rate > 5% for 2 minutes
     - Database connection errors > 10 in 1 minute
  
  3. Resource Exhaustion:
     - Memory usage > 90% for 5 minutes
     - CPU usage > 95% for 3 minutes
  
  4. Integration Test Failure:
     - Critical path tests fail
     - Performance tests exceed thresholds
```

### 6.2 Manual Rollback Procedure

```bash
#!/bin/bash
# scripts/manual_rollback.sh

set -e

NAMESPACE="production"
SERVICES=("frontend" "game-service" "order-service" "analytics-service")

echo "🚨 Initiating manual rollback for Lugx Gaming Platform..."

# Confirm rollback
read -p "Are you sure you want to rollback all services? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Rollback cancelled"
    exit 0
fi

# Rollback each service
for service in "${SERVICES[@]}"; do
    echo "Rolling back ${service}..."
    kubectl rollout undo deployment/${service}-deployment -n ${NAMESPACE}
    
    echo "Waiting for ${service} rollback to complete..."
    kubectl rollout status deployment/${service}-deployment -n ${NAMESPACE} --timeout=300s
    
    if [ $? -eq 0 ]; then
        echo "✅ ${service} rollback successful"
    else
        echo "❌ ${service} rollback failed"
        exit 1
    fi
done

echo "🎉 All services successfully rolled back to previous version"

# Run post-rollback health checks
echo "Running post-rollback health checks..."
./scripts/health_check.sh

echo "Rollback completed successfully!"
```

---

## 7. Security Considerations

### 7.1 CI/CD Security Measures

```yaml
Security Measures:
  1. Secret Management:
     - All secrets stored in GitHub Secrets
     - Kubernetes secrets for runtime configuration
     - No hardcoded credentials in code or configs
  
  2. Container Security:
     - Base images scanned with Trivy
     - Non-root container execution
     - Minimal base images (distroless/alpine)
     - Regular security updates
  
  3. Network Security:
     - Private container registry (ECR)
     - VPC networking for EKS
     - Network policies for pod-to-pod communication
     - TLS/mTLS for all service communication
  
  4. Access Control:
     - RBAC for Kubernetes access
     - IAM roles for AWS resource access
     - Branch protection rules
     - Required reviews for production changes
```

### 7.2 Deployment Security Validation

```python
# security/deployment_security_check.py
def validate_deployment_security():
    """Validate security configurations during deployment"""
    
    checks = [
        check_secrets_not_exposed(),
        check_container_security_context(),
        check_network_policies(),
        check_resource_limits(),
        check_service_account_permissions()
    ]
    
    failed_checks = [check for check in checks if not check["passed"]]
    
    if failed_checks:
        raise SecurityValidationError(f"Security validation failed: {failed_checks}")
    
    return True

def check_secrets_not_exposed():
    """Ensure no secrets are exposed in environment variables"""
    # Implementation here
    pass

def check_container_security_context():
    """Validate container security context"""
    # Implementation here
    pass
```

This comprehensive CI/CD pipeline design ensures zero-downtime rolling deployments while maintaining high security standards and automated quality gates throughout the deployment process.