#!/bin/bash

# Istio Installation Script for Lugx Gaming Platform
# Installs and configures Istio service mesh

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
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

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed or not in PATH"
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    print_error "Cannot connect to Kubernetes cluster"
    exit 1
fi

# Download and install Istio if not present
ISTIO_VERSION="1.19.3"
ISTIO_DIR="istio-${ISTIO_VERSION}"

if [ ! -d "$ISTIO_DIR" ]; then
    print_status "Downloading Istio ${ISTIO_VERSION}..."
    curl -L https://istio.io/downloadIstio | ISTIO_VERSION=${ISTIO_VERSION} sh -
fi

# Add istioctl to PATH
export PATH=$PWD/$ISTIO_DIR/bin:$PATH

# Verify istioctl
if ! command -v istioctl &> /dev/null; then
    print_error "istioctl not found in PATH"
    exit 1
fi

print_status "Installing Istio control plane..."

# Install Istio with demo profile (suitable for development)
istioctl install --set values.defaultRevision=default --set values.global.meshID=lugx-mesh --set values.global.network=lugx-network -y

# Verify installation
print_status "Verifying Istio installation..."
kubectl wait --for=condition=Ready pods -l app=istiod -n istio-system --timeout=300s

# Enable automatic sidecar injection for lugx-dev namespace
print_status "Enabling sidecar injection for lugx-dev namespace..."
kubectl label namespace lugx-dev istio-injection=enabled --overwrite

# Install Istio addons (Jaeger, Kiali, Prometheus, Grafana)
print_status "Installing Istio addons..."
kubectl apply -f $ISTIO_DIR/samples/addons/

# Wait for addons to be ready
print_status "Waiting for addons to be ready..."
kubectl wait --for=condition=Ready pods -l app=jaeger -n istio-system --timeout=300s || true
kubectl wait --for=condition=Ready pods -l app=kiali -n istio-system --timeout=300s || true

print_status "Istio installation completed successfully!"

# Display access information
echo
print_status "Access Information:"
echo "  - Kiali Dashboard: kubectl port-forward -n istio-system svc/kiali 20001:20001"
echo "  - Jaeger UI: kubectl port-forward -n istio-system svc/jaeger 16686:16686"
echo "  - Grafana: kubectl port-forward -n istio-system svc/grafana 3000:3000"
echo "  - Prometheus: kubectl port-forward -n istio-system svc/prometheus 9090:9090"

print_status "Next steps:"
echo "  1. Deploy applications to lugx-dev namespace"
echo "  2. Configure Istio Gateway and VirtualServices"
echo "  3. Set up traffic policies and security rules"