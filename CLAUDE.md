# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Lugx Gaming Platform is a cloud-native microservices e-commerce platform built with FastAPI, PostgreSQL, ClickHouse, and deployed on Kubernetes with Istio service mesh. This is an enterprise-grade gaming platform designed for high availability, scalability, and real-time analytics.

## Architecture

### Microservices Structure
- **Game Service** (Port 8001): Product catalog, inventory, reviews, search
- **Order Service** (Port 8002): Users, authentication, shopping cart, orders, payments
- **Analytics Service** (Port 8003): Real-time analytics, business intelligence
- **Frontend**: jQuery/Bootstrap single-page application

### Database Architecture
- **PostgreSQL**: Game Service (Port 5432), Order Service (Port 5433)
- **ClickHouse**: Analytics Service (Port 8123) for time-series data
- **Redis**: Shared cache and session storage (Port 6379)

### Technology Stack
- **Backend**: FastAPI with async/await, SQLAlchemy 2.0, Alembic migrations
- **Deployment**: Kubernetes with Istio service mesh, automatic scaling
- **Database**: PostgreSQL for ACID transactions, ClickHouse for analytics
- **Caching**: Redis for high-performance data access
- **Testing**: pytest, integration tests, K6 for load testing

## Essential Commands

### Local Development Environment

```bash
# Start all database services
./infrastructure/manage.sh start

# Check health of all services
./infrastructure/manage.sh health

# View logs
./infrastructure/manage.sh logs [service-name]

# Create database backups
./infrastructure/manage.sh backup

# Stop all services
./infrastructure/manage.sh stop

# Clean up (removes all data)
./infrastructure/manage.sh clean
```

### Database Operations

```bash
# Test database connections
python testing/infrastructure/test-database-connections.py

# Run Alembic migrations for Game Service
cd services/game-service
alembic upgrade head

# Run Alembic migrations for Order Service  
cd services/order-service
alembic upgrade head

# Create new migration
cd services/game-service
alembic revision --autogenerate -m "description"
```

### Kubernetes Deployment

```bash
# Deploy complete infrastructure
./infrastructure/kubernetes/manage-k8s.sh deploy all

# Deploy only base infrastructure
./infrastructure/kubernetes/manage-k8s.sh deploy

# Deploy Istio components
./infrastructure/kubernetes/manage-k8s.sh istio

# Check deployment status
./infrastructure/kubernetes/manage-k8s.sh status

# Validate deployment
./infrastructure/kubernetes/manage-k8s.sh validate

# Clean up all resources
./infrastructure/kubernetes/manage-k8s.sh cleanup
```

### Testing Commands

```bash
# Test Kubernetes migration integration
python testing/infrastructure/test-k8s-migration-integration.py

# Run comprehensive database tests
python testing/infrastructure/test-database-connections.py
```

## Development Rules

**CRITICAL: Follow the Education-Before-Implementation approach defined in `claude-code-rules.md`**

### Required Approach for Every Task:
1. **Solution Architecture Explanation** - Explain what, why, and how
2. **Technical Design Breakdown** - Data flow, components, patterns
3. **Impact Analysis** - System, performance, security implications
4. **Implementation Strategy** - Step-by-step approach with validation

### Forbidden Behaviors:
- Never start with code without context/explanation
- Never create unnecessary files without explicit request
- Never create README or documentation files unless requested
- Never skip reading plan documents before starting new phases

## Key Architectural Patterns

### Database Integration
- **Repository Pattern**: Data access abstraction with async SQLAlchemy
- **Connection Pooling**: AsyncPG with proper connection management
- **Migration Strategy**: Alembic with environment variable configuration
- **Init Containers**: Automatic migrations in Kubernetes deployments

### Service Communication
- **Async FastAPI**: High-concurrency async/await patterns
- **Service Mesh**: Istio for mTLS, traffic management, observability
- **Health Checks**: Kubernetes readiness/liveness probes
- **Error Handling**: Structured exception management with proper HTTP responses

### Security Implementation
- **JWT Authentication**: Token-based auth with proper validation
- **Kubernetes Secrets**: Encrypted credential management
- **mTLS**: Service-to-service encryption via Istio
- **RBAC**: Role-based access control in Kubernetes

### Performance Optimization
- **Redis Caching**: Strategic caching for frequent data access
- **Connection Pooling**: Optimized database connections
- **Async Processing**: Non-blocking I/O for high throughput
- **Horizontal Scaling**: Kubernetes auto-scaling based on metrics

## Configuration Management

### Environment Variables (via Kubernetes Secrets)
- `DATABASE_URL`: PostgreSQL connection string with substitution
- `REDIS_HOST/PORT/PASSWORD`: Cache configuration
- `CLICKHOUSE_HOST/PORT/USER/PASSWORD`: Analytics database
- Service-specific database credentials with base64 encoding

### Docker Compose (Local Development)
- External database services for development
- Shared network (`lugx-network`) for service communication
- Volume persistence for data retention
- Health checks and automatic restarts

### Kubernetes Deployment
- Multi-environment support (dev/staging/prod)
- Resource quotas and limits per namespace
- Storage classes for different performance tiers
- Network policies for security isolation

## Testing Strategy

### Test Pyramid Structure
- **70% Unit Tests**: Component-level validation with pytest
- **25% Integration Tests**: Service interaction testing
- **5% End-to-End Tests**: Complete user journey validation

### Performance Testing
- **Load Testing**: K6 scripts for realistic traffic simulation
- **Database Testing**: Connection validation and migration testing
- **Kubernetes Testing**: Integration testing for cloud deployment

## Deployment Environments

### Development (`lugx-dev`)
- 2 replicas per service for availability testing
- Resource limits: 512Mi memory, 500m CPU per service
- Direct database access for debugging

### Staging (`lugx-staging`)  
- Production-like configuration for pre-deployment testing
- Separate database instances with staging data
- Full Istio service mesh configuration

### Production (`lugx-prod`)
- High availability with auto-scaling
- Enhanced resource limits and monitoring
- Production-grade security and backup policies

## Service Dependencies

### Game Service Dependencies
- PostgreSQL (required for all operations)
- Redis (optional for caching)
- ClickHouse (for analytics events)

### Order Service Dependencies
- PostgreSQL (required for transactions)
- Redis (required for sessions)
- Game Service (for product validation)

### Analytics Service Dependencies
- ClickHouse (required for data storage)
- Redis (for real-time data streaming)

## Monitoring and Observability

### Istio Integration
- Automatic sidecar injection for traffic management
- mTLS for service-to-service communication
- Traffic routing and load balancing
- Circuit breakers and retries

### Health Monitoring
- Kubernetes readiness/liveness probes
- Database connection health checks
- Service mesh metrics collection
- Application-level health endpoints

## Common Troubleshooting

### Database Connection Issues
1. Check service health: `./infrastructure/manage.sh health`
2. Verify environment variables in Kubernetes secrets
3. Test connections: `python testing/infrastructure/test-database-connections.py`

### Kubernetes Deployment Issues
1. Validate manifests: `./infrastructure/kubernetes/manage-k8s.sh validate`
2. Check pod logs: `kubectl logs -f deployment/game-service -n lugx-dev`
3. Verify secrets: `kubectl get secrets -n lugx-dev`

### Migration Problems
1. Check Alembic configuration in `alembic.ini`
2. Verify DATABASE_URL environment variable
3. Run migrations manually: `alembic upgrade head`

Remember: This platform represents enterprise-grade architecture requiring careful consideration of security, performance, and maintainability in all implementations.