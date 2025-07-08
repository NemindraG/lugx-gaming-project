#!/bin/bash

# Lugx Gaming Platform - Database Infrastructure Management Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from .env.example..."
    cp .env.example .env
    print_status "Created .env file. Please update it with secure passwords!"
    exit 1
fi

# Main script logic
case "$1" in
    start)
        print_status "Starting database infrastructure..."
        docker-compose up -d
        print_status "Waiting for databases to be ready..."
        sleep 10
        ./manage.sh health
        ;;
    
    stop)
        print_status "Stopping database infrastructure..."
        docker-compose down
        ;;
    
    restart)
        print_status "Restarting database infrastructure..."
        docker-compose restart
        ;;
    
    logs)
        service=${2:-all}
        if [ "$service" = "all" ]; then
            docker-compose logs -f
        else
            docker-compose logs -f $service
        fi
        ;;
    
    health)
        print_status "Checking service health..."
        
        # Check Frontend
        if curl -f -s http://localhost:3000/health > /dev/null 2>&1; then
            print_status "Frontend (Nginx): HEALTHY"
        else
            print_error "Frontend (Nginx): UNHEALTHY"
        fi
        
        # Check PostgreSQL Game Service
        if docker exec game-service-db pg_isready -U game_service -d lugx_games > /dev/null 2>&1; then
            print_status "PostgreSQL Game Service: HEALTHY"
        else
            print_error "PostgreSQL Game Service: UNHEALTHY"
        fi
        
        # Check PostgreSQL Order Service
        if docker exec order-service-db pg_isready -U order_service -d lugx_orders > /dev/null 2>&1; then
            print_status "PostgreSQL Order Service: HEALTHY"
        else
            print_error "PostgreSQL Order Service: UNHEALTHY"
        fi
        
        # Check ClickHouse
        if docker exec analytics-service-db clickhouse-client --query "SELECT 1" > /dev/null 2>&1; then
            print_status "ClickHouse Analytics: HEALTHY"
        else
            print_error "ClickHouse Analytics: UNHEALTHY"
        fi
        
        # Check Redis
        if docker exec shared-redis-cache redis-cli ping > /dev/null 2>&1; then
            print_status "Redis Cache: HEALTHY"
        else
            print_error "Redis Cache: UNHEALTHY"
        fi
        ;;
    
    backup)
        print_status "Creating database backups..."
        mkdir -p backups/$(date +%Y%m%d)
        
        # Backup PostgreSQL databases
        docker exec game-service-db pg_dump -U game_service lugx_games > backups/$(date +%Y%m%d)/game_service_$(date +%H%M%S).sql
        docker exec order-service-db pg_dump -U order_service lugx_orders > backups/$(date +%Y%m%d)/order_service_$(date +%H%M%S).sql
        
        # Backup Redis
        docker exec shared-redis-cache redis-cli SAVE
        docker cp shared-redis-cache:/data/dump.rdb backups/$(date +%Y%m%d)/redis_$(date +%H%M%S).rdb
        
        print_status "Backups created in backups/$(date +%Y%m%d)/"
        ;;
    
    clean)
        print_warning "This will remove all containers and volumes. Are you sure? (y/N)"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            docker-compose down -v
            print_status "All containers and volumes removed."
        else
            print_status "Operation cancelled."
        fi
        ;;
    
    *)
        echo "Usage: $0 {start|stop|restart|logs|health|backup|clean}"
        echo "  start   - Start all database services"
        echo "  stop    - Stop all database services"
        echo "  restart - Restart all database services"
        echo "  logs    - View logs (optional: service name)"
        echo "  health  - Check health of all services"
        echo "  backup  - Create backups of all databases"
        echo "  clean   - Remove all containers and volumes"
        exit 1
        ;;
esac