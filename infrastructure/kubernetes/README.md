# Lugx Gaming Platform - Kubernetes Infrastructure

## Overview

This directory contains the complete Kubernetes infrastructure for the Lugx Gaming platform, implementing Phase 2.2 of our development plan. The infrastructure provides production-ready container orchestration with service mesh capabilities.

## Architecture Components

### Core Infrastructure
- **Namespaces**: Environment isolation (dev, staging, prod, monitoring)
- **RBAC**: Role-based access control with service accounts
- **Network Policies**: Zero-trust networking with traffic segmentation
- **Storage Classes**: Tiered storage for different workload requirements
- **Resource Quotas**: CPU, memory, and storage limits per environment

### Service Mesh (Istio)
- **Gateway**: External traffic entry point with TLS termination
- **VirtualServices**: Intelligent traffic routing and load balancing
- **DestinationRules**: Connection pooling and circuit breaker policies
- **Security Policies**: mTLS, JWT authentication, and authorization

## Quick Start

### Prerequisites
- Kubernetes cluster (Kind, Minikube, or cloud provider)
- kubectl configured and connected
- kustomize installed
- Istio 1.19+ (will be installed automatically)

### Deployment

1. **Deploy Base Infrastructure**
   ```bash
   ./manage-k8s.sh deploy
   ```

2. **Install Istio and Deploy Service Mesh**
   ```bash
   cd istio
   ./install-istio.sh
   cd ..
   ./manage-k8s.sh deploy istio
   ```

3. **Validate Deployment**
   ```bash
   ./manage-k8s.sh validate
   ```

### Management Commands

```bash
# Show current status
./manage-k8s.sh status

# Deploy everything including Istio
./manage-k8s.sh deploy all

# Access Istio dashboards
./manage-k8s.sh port-forward kiali    # Service mesh visualization
./manage-k8s.sh port-forward jaeger   # Distributed tracing
./manage-k8s.sh port-forward grafana  # Metrics and monitoring

# Cleanup (WARNING: Destructive)
./manage-k8s.sh cleanup
```

## Infrastructure Details

### Namespace Strategy
```
lugx-dev        → Development environment (3 replicas, moderate resources)
lugx-staging    → Pre-production testing (5 replicas, production-like)
lugx-prod       → Production workloads (auto-scaling, high resources)
lugx-monitoring → Centralized observability (Prometheus, Grafana)
istio-system    → Service mesh control plane
```

### Security Implementation
- **mTLS**: Automatic encryption between all services
- **JWT Validation**: External API authentication
- **RBAC**: Service accounts with minimal required permissions
- **Network Policies**: Zero-trust micro-segmentation
- **Rate Limiting**: Protection against abuse
- **Security Headers**: XSS, CSRF, and content security policies

### Traffic Management
```
External Traffic → Istio Gateway → VirtualService → DestinationRule → Service → Pods
                      ↓               ↓              ↓            ↓        ↓
                 TLS Termination   Routing      Load Balancing  K8s LB   Envoy
                 Authentication    Rules        Circuit Breaker         Sidecar
```

### Load Balancing Strategies
- **Game Service**: Least Connection (even distribution)
- **Order Service**: Consistent Hash (session affinity)
- **Analytics Service**: Round Robin (high throughput)
- **Frontend**: Round Robin (stateless)

### Circuit Breaker Configuration
- **Game Service**: 5 errors → 30s ejection
- **Order Service**: 3 errors → 60s ejection (stricter)
- **Analytics Service**: 10 errors → 30s ejection (relaxed)

## Storage Configuration

### Storage Classes
```
fast-ssd     → 3000 IOPS, encrypted (databases)
standard     → General purpose, encrypted (default)
slow-backup  → Throughput optimized (archives)
local-storage → Development only (Kind/Minikube)
nfs-shared   → Shared read access (assets)
```

### Resource Quotas
```
Environment | CPU Req | Memory Req | Storage | Pods
dev         | 10      | 20Gi       | 100Gi   | 50
staging     | 20      | 40Gi       | 200Gi   | 100
prod        | 100     | 200Gi      | 1Ti     | 500
```

## Service Discovery

Services communicate using Kubernetes DNS:
```
game-service.lugx-dev.svc.cluster.local:8001
order-service.lugx-dev.svc.cluster.local:8002
analytics-service.lugx-dev.svc.cluster.local:8003
frontend.lugx-dev.svc.cluster.local:80
```

## Monitoring and Observability

### Istio Addons
- **Kiali**: Service mesh visualization and configuration
- **Jaeger**: Distributed tracing across microservices
- **Grafana**: Metrics dashboards and alerting
- **Prometheus**: Metrics collection and storage

### Access Dashboards
```bash
# Kiali - Service mesh topology
kubectl port-forward -n istio-system svc/kiali 20001:20001
# Visit: http://localhost:20001

# Jaeger - Distributed tracing
kubectl port-forward -n istio-system svc/jaeger 16686:16686  
# Visit: http://localhost:16686

# Grafana - Metrics dashboards
kubectl port-forward -n istio-system svc/grafana 3000:3000
# Visit: http://localhost:3000
```

## Troubleshooting

### Common Issues

1. **Pods stuck in Pending**
   ```bash
   kubectl describe pod <pod-name> -n lugx-dev
   # Check resource quotas and storage availability
   ```

2. **Service communication failures**
   ```bash
   # Check network policies
   kubectl get networkpolicies -n lugx-dev
   
   # Check Istio configuration
   istioctl proxy-config cluster <pod-name> -n lugx-dev
   ```

3. **Certificate issues**
   ```bash
   # Check Istio certificates
   istioctl proxy-config secret <pod-name> -n lugx-dev
   ```

### Debugging Commands
```bash
# Check Istio injection
kubectl get pods -n lugx-dev -o wide

# Validate Istio configuration
istioctl analyze -n lugx-dev

# Check proxy configuration
istioctl proxy-config listener <pod-name> -n lugx-dev
```

## Security Considerations

1. **Network Security**: All inter-service communication encrypted with mTLS
2. **Access Control**: Each service has minimal required permissions
3. **Data Protection**: Persistent volumes encrypted at rest
4. **Compliance**: Audit logs for all API access
5. **Secrets Management**: Kubernetes secrets with rotation capability

## Next Steps

After Kubernetes infrastructure is ready:
1. **Phase 3**: Deploy FastAPI microservices to this infrastructure
2. **Phase 4**: Configure frontend integration with service mesh
3. **Phase 5**: Add monitoring and alerting
4. **Phase 8**: Implement CI/CD pipelines for automated deployments

## Educational Notes

This infrastructure demonstrates:
- **Production-grade Kubernetes**: RBAC, network policies, resource management
- **Service mesh benefits**: Traffic management, security, observability
- **Zero-trust networking**: Every connection authenticated and encrypted
- **Operational excellence**: Health checks, circuit breakers, graceful degradation
- **Scalability patterns**: Auto-scaling, load balancing, resource optimization