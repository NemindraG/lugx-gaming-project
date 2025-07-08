# Configuration Files Directory

This directory will contain ConfigMaps and Secrets for the Lugx Gaming platform microservices.

## What will be added in Phase 3:

### ConfigMaps (Non-sensitive configuration)
- `game-service-config.yaml` - Database URLs, API endpoints, feature flags
- `order-service-config.yaml` - Payment processor URLs, shipping settings
- `analytics-service-config.yaml` - ClickHouse connection settings, batch sizes
- `frontend-config.yaml` - API base URLs, environment settings

### Secrets (Sensitive configuration)
- `database-secrets.yaml` - PostgreSQL passwords, connection strings
- `clickhouse-secrets.yaml` - ClickHouse credentials
- `redis-secrets.yaml` - Redis authentication
- `api-secrets.yaml` - JWT signing keys, external API keys

## Why this is empty now:
The configs directory is empty because we're following the proper development sequence:
1. **Phase 2** (Current): Infrastructure foundation (nodes, pods, networking)
2. **Phase 3** (Next): Microservices implementation with their specific configs
3. **Phase 4**: Frontend integration

Each microservice will define its own configuration requirements when we build them in Phase 3.

## Example of what will be added:

```yaml
# game-service-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: game-service-config
  namespace: lugx-dev
data:
  DATABASE_URL: "postgresql://game-service-db:5432/gamedb"
  CACHE_URL: "redis://redis:6379/0"
  LOG_LEVEL: "INFO"
  ENABLE_SEARCH: "true"
```

```yaml
# database-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: database-secrets
  namespace: lugx-dev
type: Opaque
data:
  postgres-password: <base64-encoded-password>
  redis-password: <base64-encoded-password>
```