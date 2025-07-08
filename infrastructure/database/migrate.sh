#!/bin/bash

# Database Migration Script
# Applies schema migrations to all databases

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Base directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MIGRATION_DIR="${SCRIPT_DIR}/migrations"

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

# Function to run PostgreSQL migrations
run_postgres_migration() {
    local service=$1
    local port=$2
    local database=$3
    local user=$4
    local password=$5
    local migration_path="${MIGRATION_DIR}/${service}"
    
    print_status "Running migrations for ${service}..."
    
    if [ ! -d "$migration_path" ]; then
        print_error "Migration directory not found: $migration_path"
        return 1
    fi
    
    # Apply migrations in order
    for migration in $(ls $migration_path/*.sql | sort); do
        migration_name=$(basename $migration)
        print_status "  Applying: $migration_name"
        
        PGPASSWORD=$password psql -h localhost -p $port -U $user -d $database -f $migration
        
        if [ $? -eq 0 ]; then
            print_status "  ✓ $migration_name applied successfully"
        else
            print_error "  ✗ Failed to apply $migration_name"
            return 1
        fi
    done
    
    return 0
}

# Function to run ClickHouse migrations
run_clickhouse_migration() {
    local migration_path="${MIGRATION_DIR}/analytics-service"
    
    print_status "Running ClickHouse migrations..."
    
    if [ ! -d "$migration_path" ]; then
        print_error "Migration directory not found: $migration_path"
        return 1
    fi
    
    # Apply migrations in order
    for migration in $(ls $migration_path/*.sql | sort); do
        migration_name=$(basename $migration)
        print_status "  Applying: $migration_name"
        
        docker exec -i analytics-service-db clickhouse-client \
            --user analytics_service \
            --password analytics_secure_password_2024 \
            --multiquery < $migration
        
        if [ $? -eq 0 ]; then
            print_status "  ✓ $migration_name applied successfully"
        else
            print_error "  ✗ Failed to apply $migration_name"
            return 1
        fi
    done
    
    return 0
}

# Main migration process
main() {
    print_status "Starting database migrations..."
    
    # Check if databases are running
    ../manage.sh health > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        print_error "Databases are not healthy. Please start them first."
        exit 1
    fi
    
    # Run Game Service migrations
    if run_postgres_migration "game-service" "5432" "lugx_games" "game_service" "game_secure_password_2024"; then
        print_status "✓ Game Service migrations completed"
    else
        print_error "Game Service migrations failed"
        exit 1
    fi
    
    echo
    
    # Run Order Service migrations
    if run_postgres_migration "order-service" "5433" "lugx_orders" "order_service" "order_secure_password_2024"; then
        print_status "✓ Order Service migrations completed"
    else
        print_error "Order Service migrations failed"
        exit 1
    fi
    
    echo
    
    # Run Analytics Service migrations
    if run_clickhouse_migration; then
        print_status "✓ Analytics Service migrations completed"
    else
        print_error "Analytics Service migrations failed"
        exit 1
    fi
    
    echo
    print_status "All migrations completed successfully!"
    
    # Show summary
    echo
    print_status "Migration Summary:"
    echo "  - Game Service: Publishers, Categories, Games, Inventory, Reviews"
    echo "  - Order Service: Users, Carts, Orders, Payments"
    echo "  - Analytics Service: Enhanced with behavior tracking, A/B testing, campaigns"
}

# Run main function
main "$@"