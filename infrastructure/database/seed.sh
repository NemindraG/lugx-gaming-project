#!/bin/bash

# Database Seed Data Script
# Loads test data into all databases

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Base directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SEED_DIR="${SCRIPT_DIR}/seeds"

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

# Function to load PostgreSQL seed data
load_postgres_seeds() {
    local service=$1
    local port=$2
    local database=$3
    local user=$4
    local password=$5
    local seed_file="${SEED_DIR}/${service}-seed.sql"
    
    print_status "Loading seed data for ${service}..."
    
    if [ ! -f "$seed_file" ]; then
        print_warning "Seed file not found: $seed_file (skipping)"
        return 0
    fi
    
    PGPASSWORD=$password psql -h localhost -p $port -U $user -d $database -f $seed_file
    
    if [ $? -eq 0 ]; then
        print_status "✓ Seed data loaded for ${service}"
    else
        print_error "Failed to load seed data for ${service}"
        return 1
    fi
    
    return 0
}

# Main seed process
main() {
    print_status "Starting database seed data loading..."
    
    # Check if databases are running
    ../manage.sh health > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        print_error "Databases are not healthy. Please start them first."
        exit 1
    fi
    
    # Prompt for confirmation
    print_warning "This will load test data into your databases. Continue? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_status "Operation cancelled."
        exit 0
    fi
    
    # Load Game Service seeds
    if load_postgres_seeds "game-service" "5432" "lugx_games" "game_service" "game_secure_password_2024"; then
        print_status "✓ Game Service data loaded"
    else
        print_error "Failed to load Game Service data"
    fi
    
    echo
    
    # Load Order Service seeds
    if load_postgres_seeds "order-service" "5433" "lugx_orders" "order_service" "order_secure_password_2024"; then
        print_status "✓ Order Service data loaded"
    else
        print_error "Failed to load Order Service data"
    fi
    
    echo
    print_status "Seed data loading completed!"
    
    # Show summary
    echo
    print_status "Data Summary:"
    echo "  - Game Service: 5 publishers, 8 categories, 9 games with inventory"
    echo "  - Order Service: 4 users, 3 shopping carts, 2 completed orders"
    echo "  - Test credentials: All users have password 'password123'"
}

# Run main function
main "$@"