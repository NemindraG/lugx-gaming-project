#!/bin/bash

# Kubernetes Management Script for Lugx Gaming Platform
# Provides easy deployment and management commands

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

print_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Check dependencies
check_dependencies() {
    local deps=("kubectl" "kustomize")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            print_error "$dep is required but not installed"
            exit 1
        fi
    done
}

# Check cluster connectivity
check_cluster() {
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        print_info "Make sure your kubeconfig is configured correctly"
        exit 1
    fi
    
    local context=$(kubectl config current-context)
    print_info "Connected to cluster: $context"
}

# Deploy base infrastructure
deploy_base() {
    print_status "Deploying base Kubernetes infrastructure..."
    
    # Apply base resources using kustomize
    kubectl apply -k base/
    
    # Wait for namespaces to be ready
    print_status "Waiting for namespaces to be ready..."
    kubectl wait --for=condition=Active namespace/lugx-dev --timeout=60s
    kubectl wait --for=condition=Active namespace/lugx-staging --timeout=60s
    kubectl wait --for=condition=Active namespace/lugx-prod --timeout=60s
    
    print_status "Base infrastructure deployed successfully!"
}

# Deploy Istio components
deploy_istio() {
    print_status "Deploying Istio service mesh components..."
    
    # Apply Istio configurations
    kubectl apply -f istio/gateway.yaml
    kubectl apply -f istio/destination-rules.yaml
    kubectl apply -f istio/security-policies.yaml
    
    print_status "Istio components deployed successfully!"
}

# Validate deployment
validate_deployment() {
    print_status "Validating deployment..."
    
    # Check namespaces
    print_info "Checking namespaces:"
    kubectl get namespaces -l app.kubernetes.io/name=lugx-gaming
    
    # Check RBAC
    print_info "Checking service accounts:"
    kubectl get serviceaccounts -n lugx-dev
    
    # Check network policies
    print_info "Checking network policies:"
    kubectl get networkpolicies -n lugx-dev
    
    # Check storage classes
    print_info "Checking storage classes:"
    kubectl get storageclasses -l app.kubernetes.io/name=lugx-gaming
    
    # Check Istio components
    if kubectl get namespace istio-system &> /dev/null; then
        print_info "Checking Istio components:"
        kubectl get pods -n istio-system
        kubectl get gateways -n lugx-dev
        kubectl get virtualservices -n lugx-dev
        kubectl get destinationrules -n lugx-dev
    fi
    
    print_status "Validation completed!"
}

# Show status
show_status() {
    print_status "Lugx Gaming Platform - Kubernetes Status"
    echo
    
    # Cluster info
    print_info "Cluster Information:"
    kubectl cluster-info --context=$(kubectl config current-context) | head -1
    echo
    
    # Namespaces
    print_info "Namespaces:"
    kubectl get namespaces -l app.kubernetes.io/name=lugx-gaming -o wide
    echo
    
    # Resource quotas
    print_info "Resource Quotas:"
    kubectl get resourcequotas -A --no-headers 2>/dev/null | grep lugx || echo "No resource quotas found"
    echo
    
    # Istio status
    if kubectl get namespace istio-system &> /dev/null; then
        print_info "Istio Status:"
        kubectl get pods -n istio-system --no-headers | grep -E "(istiod|istio-proxy)" | head -5
        echo
    fi
    
    # Storage
    print_info "Storage Classes:"
    kubectl get storageclasses -l app.kubernetes.io/name=lugx-gaming --no-headers
    echo
}

# Cleanup resources
cleanup() {
    print_warning "This will delete all Lugx Gaming Kubernetes resources!"
    read -p "Are you sure? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        print_info "Cleanup cancelled"
        return
    fi
    
    print_status "Cleaning up resources..."
    
    # Delete Istio components
    kubectl delete -f istio/ --ignore-not-found=true
    
    # Delete base resources
    kubectl delete -k base/ --ignore-not-found=true
    
    # Delete namespaces (this will delete everything in them)
    kubectl delete namespace lugx-dev lugx-staging lugx-prod lugx-monitoring --ignore-not-found=true
    
    print_status "Cleanup completed!"
}

# Port forward for services
port_forward() {
    local service=$1
    
    case $service in
        "kiali")
            print_info "Port forwarding Kiali dashboard..."
            kubectl port-forward -n istio-system svc/kiali 20001:20001
            ;;
        "jaeger")
            print_info "Port forwarding Jaeger UI..."
            kubectl port-forward -n istio-system svc/jaeger 16686:16686
            ;;
        "grafana")
            print_info "Port forwarding Grafana..."
            kubectl port-forward -n istio-system svc/grafana 3000:3000
            ;;
        "prometheus")
            print_info "Port forwarding Prometheus..."
            kubectl port-forward -n istio-system svc/prometheus 9090:9090
            ;;
        *)
            print_error "Unknown service: $service"
            print_info "Available services: kiali, jaeger, grafana, prometheus"
            exit 1
            ;;
    esac
}

# Main script logic
main() {
    check_dependencies
    
    case "${1:-}" in
        "deploy")
            check_cluster
            deploy_base
            if [[ "${2:-}" == "istio" ]] || [[ "${2:-}" == "all" ]]; then
                deploy_istio
            fi
            validate_deployment
            ;;
        "istio")
            check_cluster
            deploy_istio
            ;;
        "status")
            check_cluster
            show_status
            ;;
        "validate")
            check_cluster
            validate_deployment
            ;;
        "cleanup")
            check_cluster
            cleanup
            ;;
        "port-forward")
            check_cluster
            port_forward "${2:-}"
            ;;
        "help"|"-h"|"--help")
            echo "Lugx Gaming Platform - Kubernetes Management"
            echo ""
            echo "Usage: $0 <command> [options]"
            echo ""
            echo "Commands:"
            echo "  deploy [all|istio]  Deploy infrastructure (optionally with Istio)"
            echo "  istio              Deploy only Istio components"
            echo "  status             Show current status"
            echo "  validate           Validate deployment"
            echo "  cleanup            Remove all resources"
            echo "  port-forward <svc> Port forward to service (kiali|jaeger|grafana|prometheus)"
            echo "  help               Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 deploy all      # Deploy everything including Istio"
            echo "  $0 status          # Show current status"
            echo "  $0 port-forward kiali  # Access Kiali dashboard"
            ;;
        *)
            print_error "Unknown command: ${1:-}"
            print_info "Run '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"