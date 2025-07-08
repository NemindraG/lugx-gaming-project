# Lugx Gaming Platform - Testing Suite

## Overview

This directory contains all test scripts and testing frameworks for the Lugx Gaming platform. Tests are organized by component and testing type to ensure comprehensive coverage across all microservices and infrastructure.

## Directory Structure

```
testing/
├── infrastructure/          # Infrastructure and database tests
│   └── test-database-connections.py
├── unit/                   # Unit tests for individual components
│   ├── game-service/
│   ├── order-service/
│   └── analytics-service/
├── integration/            # Integration tests between services
├── e2e/                   # End-to-end user journey tests
├── performance/           # Load and stress tests
└── security/              # Security and penetration tests
```

## Infrastructure Tests

### Database Connection Test
```bash
cd infrastructure
python test-database-connections.py
```

This test verifies:
- PostgreSQL Game Service connectivity
- PostgreSQL Order Service connectivity
- ClickHouse Analytics connectivity
- Redis Cache connectivity

## Test Requirements

Install test dependencies:
```bash
pip install asyncpg redis clickhouse-driver pytest pytest-asyncio httpx
```

## Running Tests

### All Tests
```bash
pytest
```

### Specific Test Category
```bash
pytest unit/
pytest integration/
pytest e2e/
```

### With Coverage
```bash
pytest --cov=services --cov-report=html
```

## Test Standards

1. **Naming Convention**: `test_<component>_<scenario>.py`
2. **Test Structure**: Arrange-Act-Assert pattern
3. **Async Tests**: Use `pytest-asyncio` for FastAPI async operations
4. **Fixtures**: Shared test data in `conftest.py` files
5. **Mocking**: External services should be mocked in unit tests

## CI/CD Integration

Tests are automatically run in the CI/CD pipeline:
- Unit tests on every commit
- Integration tests on pull requests
- E2E tests before production deployment
- Performance tests weekly

## Future Test Implementation

As we progress through the phases:
- Week 2: Database schema validation tests
- Week 3: Kubernetes deployment tests
- Week 4: Service mesh communication tests
- Week 5: API endpoint tests
- Week 6: Full integration test suite