#!/bin/bash

# Lugx Gaming Platform - Set Global Environment Variables for Development
# Source this file to set environment variables: source ./set-env.sh

echo "Setting Lugx Gaming Platform environment variables..."

# PostgreSQL - Game Service
export POSTGRES_GAME_DB=lugx_games
export POSTGRES_GAME_USER=game_service
export POSTGRES_GAME_PASSWORD=game_secure_password_2024
export POSTGRES_GAME_PORT=5432

# PostgreSQL - Order Service
export POSTGRES_ORDER_DB=lugx_orders
export POSTGRES_ORDER_USER=order_service
export POSTGRES_ORDER_PASSWORD=order_secure_password_2024
export POSTGRES_ORDER_PORT=5433

# ClickHouse - Analytics Service
export CLICKHOUSE_DB=lugx_analytics
export CLICKHOUSE_USER=analytics_service
export CLICKHOUSE_PASSWORD=analytics_secure_password_2024
export CLICKHOUSE_HTTP_PORT=8123
export CLICKHOUSE_NATIVE_PORT=9000

# Redis - Caching & Sessions
export REDIS_PASSWORD=redis_secure_password_2024
export REDIS_PORT=6379

# Database URLs for services
export GAME_SERVICE_DATABASE_URL="postgresql+asyncpg://${POSTGRES_GAME_USER}:${POSTGRES_GAME_PASSWORD}@localhost:${POSTGRES_GAME_PORT}/${POSTGRES_GAME_DB}"
export ORDER_SERVICE_DATABASE_URL="postgresql+asyncpg://${POSTGRES_ORDER_USER}:${POSTGRES_ORDER_PASSWORD}@localhost:${POSTGRES_ORDER_PORT}/${POSTGRES_ORDER_DB}"
export ANALYTICS_DATABASE_URL="clickhouse+asynch://${CLICKHOUSE_USER}:${CLICKHOUSE_PASSWORD}@localhost:${CLICKHOUSE_HTTP_PORT}/${CLICKHOUSE_DB}"

# Generic DATABASE_URL (will be overridden per service)
export DATABASE_URL="${GAME_SERVICE_DATABASE_URL}"

echo "Environment variables set successfully!"
echo ""
echo "Database URLs configured:"
echo "  Game Service: ${GAME_SERVICE_DATABASE_URL}"
echo "  Order Service: ${ORDER_SERVICE_DATABASE_URL}"
echo "  Analytics: ${ANALYTICS_DATABASE_URL}"
echo ""
echo "To persist these variables, add 'source $(pwd)/set-env.sh' to your shell profile."