# Lugx Gaming Platform - Integration Points Documentation

## Executive Summary

This document defines all integration points within the Lugx Gaming platform ecosystem, including microservice-to-microservice communication, external service integrations, database relationships, and third-party API connections. It provides the foundation for understanding how all components work together to deliver a cohesive gaming platform experience.

## Integration Architecture Overview

### Integration Principles
- **Loose Coupling**: Services communicate through well-defined APIs
- **High Cohesion**: Related functionality grouped within service boundaries
- **Fault Tolerance**: Graceful degradation when integrations fail
- **Observability**: Comprehensive monitoring of all integration points
- **Security**: All communications encrypted and authenticated

### Integration Patterns
- **Synchronous Integration**: REST APIs for immediate data requirements
- **Asynchronous Integration**: Event-driven communication for non-blocking operations
- **Database Integration**: Shared data access patterns and consistency models
- **External Integration**: Third-party service consumption and data exchange

---

## Istio Service Mesh Integration Layer

### Service Mesh Communication Architecture

**Purpose**: Istio service mesh provides zero-configuration observability, traffic management, and security for all service communications.

```
Service Mesh Communication Flow:
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              ISTIO GATEWAY LAYER                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                     External Traffic Entry Point                               │ │
│  │   • SSL Termination (TLS 1.3)     • Domain-based Routing                      │ │
│  │   • Rate Limiting (Per IP/User)    • JWT Validation                           │ │
│  │   • DDoS Protection               • Geographic Filtering                      │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                 HTTPS Traffic
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           ISTIO VIRTUAL SERVICES LAYER                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                        Intelligent Traffic Routing                             │ │
│  │   /api/v1/games/*     → Game Service (with retry policy)                      │ │
│  │   /api/v1/auth/*      → Order Service (with circuit breaker)                 │ │
│  │   /api/v1/cart/*      → Order Service (with timeout: 30s)                    │ │
│  │   /api/v1/orders/*    → Order Service (with retry: 3 attempts)               │ │
│  │   /api/v1/analytics/* → Analytics Service (with timeout: 10s)                │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
            │                        │                        │
    Game Requests              Order Requests           Analytics Events
            ▼                        ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          ISTIO ENVOY SIDECAR PROXIES                               │
│                                                                                     │
│  ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐           │
│  │ Game Service    │      │ Order Service   │      │Analytics Service│           │
│  │ Envoy Proxy     │◄────►│ Envoy Proxy     │      │ Envoy Proxy     │           │
│  │                 │      │                 │ ────►│                 │           │
│  │ • mTLS Auto     │      │ • Load Balance  │      │ • Traffic Mirror│           │
│  │ • Circuit Break │      │ • Health Check  │      │ • Rate Limiting │           │
│  │ • Observability │      │ • Fault Inject  │      │ • Metrics       │           │
│  └─────────────────┘      └─────────────────┘      └─────────────────┘           │
│           │                         │                         │                   │
│    PostgreSQL (Games)         PostgreSQL (Orders)      ClickHouse (Events)        │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

#### **Istio Gateway Configuration**

```yaml
# Istio Gateway - External Traffic Entry
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: lugx-gaming-gateway
  namespace: istio-system
spec:
  selector:
    istio: ingressgateway
  servers:
  # HTTP to HTTPS Redirect
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - lugxgaming.com
    - "*.lugxgaming.com"
    tls:
      httpsRedirect: true
  
  # HTTPS with TLS Termination
  - port:
      number: 443
      name: https
      protocol: HTTPS
    hosts:
    - lugxgaming.com
    - "*.lugxgaming.com"
    tls:
      mode: SIMPLE
      credentialName: lugx-gaming-tls-cert
      minProtocolVersion: TLSV1_3
      maxProtocolVersion: TLSV1_3
```

#### **VirtualService Routing Configuration**

```yaml
# Istio VirtualService - Traffic Routing Rules
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: lugx-gaming-api-routes
  namespace: production
spec:
  hosts:
  - lugxgaming.com
  gateways:
  - istio-system/lugx-gaming-gateway
  http:
  
  # Game Service Routes with Fault Tolerance
  - match:
    - uri:
        prefix: /api/v1/games
    - uri:
        prefix: /api/v1/categories
    - uri:
        prefix: /api/v1/publishers
    route:
    - destination:
        host: game-service.production.svc.cluster.local
        port:
          number: 8000
    timeout: 30s
    retries:
      attempts: 3
      perTryTimeout: 10s
      retryOn: gateway-error,connect-failure,refused-stream
    fault:
      delay:
        percentage:
          value: 0.1  # 0.1% of requests get delayed (for testing)
        fixedDelay: 5s
  
  # Order Service Routes with Circuit Breaker
  - match:
    - uri:
        prefix: /api/v1/auth
    - uri:
        prefix: /api/v1/cart
    - uri:
        prefix: /api/v1/orders
    - uri:
        prefix: /api/v1/newsletter
    route:
    - destination:
        host: order-service.production.svc.cluster.local
        port:
          number: 8000
        subset: v1
    timeout: 30s
    retries:
      attempts: 2
      perTryTimeout: 15s
      retryOn: 5xx,reset,connect-failure,refused-stream
  
  # Enhanced Analytics Service Routes for Web Analytics
  - match:
    - uri:
        prefix: /api/v1/analytics/events/batch
    route:
    - destination:
        host: analytics-service.production.svc.cluster.local
        port:
          number: 8000
    timeout: 30s  # Increased for batch processing
    retries:
      attempts: 3
      perTryTimeout: 10s
      retryOn: 5xx,reset,connect-failure
    headers:
      request:
        add:
          x-analytics-source: "istio-gateway"
          x-batch-processing: "true"
          x-high-volume: "web-analytics"
  
  # Real-time Analytics Queries
  - match:
    - uri:
        prefix: /api/v1/analytics/metrics/realtime
    route:
    - destination:
        host: analytics-service.production.svc.cluster.local
        port:
          number: 8000
    timeout: 5s  # Fast response for real-time data
    retries:
      attempts: 2
      perTryTimeout: 2s
    headers:
      request:
        add:
          x-analytics-query: "realtime"
          x-cache-priority: "high"
  
  # User Journey and Session Analytics
  - match:
    - uri:
        prefix: /api/v1/analytics/journey
    - uri:
        prefix: /api/v1/analytics/session
    route:
    - destination:
        host: analytics-service.production.svc.cluster.local
        port:
          number: 8000
    timeout: 15s
    retries:
      attempts: 2
      perTryTimeout: 7s
    headers:
      request:
        add:
          x-analytics-type: "user-behavior"
          x-query-complexity: "medium"
  
  # General Analytics Endpoints
  - match:
    - uri:
        prefix: /api/v1/analytics
    route:
    - destination:
        host: analytics-service.production.svc.cluster.local
        port:
          number: 8000
    timeout: 10s
    retries:
      attempts: 3
      perTryTimeout: 5s
    headers:
      request:
        add:
          x-analytics-source: "istio-gateway"
```

#### **Security Policies Configuration**

```yaml
# Automatic mTLS for All Services
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default-mtls
  namespace: production
spec:
  mtls:
    mode: STRICT  # Require mTLS for all service-to-service communication

---
# JWT Authentication Policy for Protected Endpoints
apiVersion: security.istio.io/v1beta1
kind: RequestAuthentication
metadata:
  name: jwt-authentication
  namespace: production
spec:
  selector:
    matchLabels:
      app: order-service
  jwtRules:
  - issuer: "lugx-gaming-order-service"
    jwksUri: "http://order-service.production.svc.cluster.local:8000/.well-known/jwks.json"
    audiences: ["lugx-gaming-api"]
    forwardOriginalToken: true

---
# Authorization Policies for API Endpoints
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: order-service-authz
  namespace: production
spec:
  selector:
    matchLabels:
      app: order-service
  rules:
  
  # Allow unauthenticated access to public endpoints
  - to:
    - operation:
        paths: ["/api/v1/auth/login", "/api/v1/auth/register", "/health", "/api/v1/newsletter/subscribe"]
    - operation:
        methods: ["OPTIONS"]  # Allow CORS preflight
  
  # Require valid JWT for protected endpoints
  - from:
    - source:
        requestPrincipals: ["lugx-gaming-order-service/*"]
    to:
    - operation:
        paths: ["/api/v1/cart/*", "/api/v1/orders/*", "/api/v1/auth/logout"]
  
  # Service-to-service communication
  - from:
    - source:
        principals: ["cluster.local/ns/production/sa/game-service", "cluster.local/ns/production/sa/analytics-service"]
    to:
    - operation:
        paths: ["/api/v1/auth/validate", "/api/v1/users/*/profile"]

---
# Enhanced Rate Limiting for Web Analytics Endpoints
apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
metadata:
  name: analytics-rate-limiting
  namespace: production
spec:
  workloadSelector:
    labels:
      app: analytics-service
  configPatches:
  - applyTo: HTTP_FILTER
    match:
      context: SIDECAR_INBOUND
      listener:
        filterChain:
          filter:
            name: "envoy.filters.network.http_connection_manager"
    patch:
      operation: INSERT_BEFORE
      value:
        name: envoy.filters.http.local_ratelimit
        typed_config:
          "@type": type.googleapis.com/udpa.type.v1.TypedStruct
          type_url: type.googleapis.com/envoy.extensions.filters.http.local_ratelimit.v3.LocalRateLimit
          value:
            stat_prefix: analytics_rate_limiter
            token_bucket:
              max_tokens: 50000
              tokens_per_fill: 1000
              fill_interval: 1s
            filter_enabled:
              runtime_key: analytics_rate_limit_enabled
              default_value:
                numerator: 100
                denominator: HUNDRED
            filter_enforced:
              runtime_key: analytics_rate_limit_enforced
              default_value:
                numerator: 100
                denominator: HUNDRED
            response_headers_to_add:
              - append: false
                header:
                  key: x-local-rate-limit
                  value: 'true'

---
# Different Rate Limits for Different Analytics Endpoints
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: analytics-endpoint-policies
  namespace: production
spec:
  selector:
    matchLabels:
      app: analytics-service
  rules:
  # High-volume batch event processing
  - from:
    - source: {}
    to:
    - operation:
        paths: ["/api/v1/analytics/events/batch"]
    when:
    - key: source.ip
      notValues: ["10.0.0.0/8", "172.16.0.0/12"]  # Internal networks unrestricted
  
  # Real-time analytics queries (more restrictive)
  - from:
    - source: {}
    to:
    - operation:
        paths: ["/api/v1/analytics/metrics/realtime"]
    when:
    - key: request.headers[user-agent]
      notValues: ["lugx-internal-service"]
  
  # User journey and session analytics
  - from:
    - source: {}
    to:
    - operation:
        paths: ["/api/v1/analytics/journey/*", "/api/v1/analytics/session/*"]
    when:
    - key: request.headers[authorization]
      values: ["Bearer *"]  # Require authentication
```

#### **DestinationRule for Traffic Policies**

```yaml
# Game Service Traffic Policies
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: game-service-destination
  namespace: production
spec:
  host: game-service.production.svc.cluster.local
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
        connectTimeout: 30s
      http:
        http1MaxPendingRequests: 50
        http2MaxRequests: 100
        maxRequestsPerConnection: 10
        maxRetries: 3
    loadBalancer:
      simple: LEAST_CONN  # Use least connection load balancing
    circuitBreaker:
      consecutiveGatewayErrors: 5
      consecutiveErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
      minHealthPercent: 30
  subsets:
  - name: v1
    labels:
      version: v1
    trafficPolicy:
      circuitBreaker:
        consecutiveErrors: 3

---
# Order Service Traffic Policies
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: order-service-destination
  namespace: production
spec:
  host: order-service.production.svc.cluster.local
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 50
        connectTimeout: 10s
      http:
        http1MaxPendingRequests: 25
        http2MaxRequests: 50
        maxRequestsPerConnection: 5
        maxRetries: 2
    loadBalancer:
      simple: ROUND_ROBIN
    circuitBreaker:
      consecutiveGatewayErrors: 3
      consecutiveErrors: 3
      interval: 60s
      baseEjectionTime: 60s
      maxEjectionPercent: 25
  subsets:
  - name: v1
    labels:
      version: v1

---
# Analytics Service Traffic Policies
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: analytics-service-destination
  namespace: production
spec:
  host: analytics-service.production.svc.cluster.local
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 200
        connectTimeout: 5s
      http:
        http1MaxPendingRequests: 100
        http2MaxRequests: 200
        maxRequestsPerConnection: 20
        maxRetries: 1  # Don't retry analytics events aggressively
    loadBalancer:
      simple: RANDOM  # Random distribution for analytics load
    circuitBreaker:
      consecutiveGatewayErrors: 10  # More lenient for analytics
      consecutiveErrors: 10
      interval: 30s
      baseEjectionTime: 15s
      maxEjectionPercent: 30
```

#### **Service Mesh Observability Integration**

```python
# Service Integration with Istio Observability
class IstioObservabilityService:
    def __init__(self):
        # Istio automatically injects distributed tracing headers
        self.trace_headers = [
            'x-request-id',
            'x-b3-traceid',
            'x-b3-spanid',
            'x-b3-parentspanid',
            'x-b3-sampled',
            'x-b3-flags',
            'x-ot-span-context'
        ]
    
    def extract_trace_context(self, request: Request) -> Dict[str, str]:
        """Extract Istio trace context from incoming request"""
        trace_context = {}
        for header in self.trace_headers:
            value = request.headers.get(header)
            if value:
                trace_context[header] = value
        return trace_context
    
    def propagate_trace_context(self, headers: Dict[str, str], 
                               trace_context: Dict[str, str]) -> Dict[str, str]:
        """Propagate trace context to outgoing service calls"""
        propagated_headers = headers.copy()
        propagated_headers.update(trace_context)
        return propagated_headers

# Enhanced Service-to-Service Communication with Tracing
class TracedServiceClient:
    def __init__(self, service_name: str, base_url: str):
        self.service_name = service_name
        self.base_url = base_url
        self.observability = IstioObservabilityService()
    
    async def make_request(self, method: str, endpoint: str, 
                         request_context: Request, **kwargs) -> Dict:
        """Make service call with distributed tracing"""
        
        # Extract trace context from incoming request
        trace_context = self.observability.extract_trace_context(request_context)
        
        # Prepare headers with trace propagation
        headers = kwargs.get('headers', {})
        headers = self.observability.propagate_trace_context(headers, trace_context)
        
        # Add service authentication
        headers['Authorization'] = f"Bearer {self.get_service_token()}"
        
        # Add request correlation ID
        correlation_id = request_context.headers.get('x-correlation-id') or str(uuid.uuid4())
        headers['x-correlation-id'] = correlation_id
        
        kwargs['headers'] = headers
        
        url = f"{self.base_url}{endpoint}"
        
        # Make request with automatic retries and circuit breaking (handled by Istio)
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, **kwargs)
            
            # Log service interaction for observability
            logger.info(
                f"Service call: {method} {url}",
                extra={
                    "service_name": self.service_name,
                    "correlation_id": correlation_id,
                    "status_code": response.status_code,
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
            )
            
            return response
```

## Microservice Integration Points

### 1. Game Service ↔ Order Service Integration

#### **Product Validation Integration**

**Purpose**: Order Service validates game information during cart and checkout operations.

```
Order Service Request Flow:
┌─────────────────────────────────────────────────────────────────┐
│                    ORDER SERVICE                                │
│                                                                 │
│  Cart/Checkout Operation                                       │
│  ├── User adds game to cart                                    │
│  ├── Validate game exists                                      │
│  ├── Get current pricing                                       │
│  ├── Check availability                                        │
│  └── Reserve inventory                                         │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                     GAME SERVICE                                │
│                                                                 │
│  GET /api/v1/games/{game_id}                                   │
│  ├── Return game details                                       │
│  ├── Current pricing information                               │
│  ├── Availability status                                       │
│  └── Inventory levels                                          │
│                                                                 │
│  POST /api/v1/games/{game_id}/inventory                       │
│  ├── Reserve specified quantity                                │
│  ├── Generate reservation ID                                   │
│  ├── Set reservation timeout                                   │
│  └── Return reservation confirmation                           │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation Details:**

```python
# Order Service - Game Validation
class GameServiceClient:
    def __init__(self, base_url: str, service_token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {service_token}"}
    
    async def validate_game(self, game_id: int) -> Dict:
        """Validate game exists and get current details"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/games/{game_id}",
                headers=self.headers,
                timeout=5.0
            )
            if response.status_code == 404:
                raise GameNotFoundError(f"Game {game_id} not found")
            response.raise_for_status()
            return response.json()
    
    async def reserve_inventory(self, game_id: int, quantity: int, 
                              reservation_id: str) -> bool:
        """Reserve game inventory for order processing"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/games/{game_id}/inventory",
                json={
                    "quantity": quantity,
                    "reservation_id": reservation_id
                },
                headers=self.headers,
                timeout=10.0
            )
            return response.status_code == 200

# Circuit Breaker Pattern for Resilience
class GameServiceCircuitBreaker:
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call_game_service(self, operation: Callable):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenError("Game Service unavailable")
        
        try:
            result = await operation()
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            raise e
```

#### **Error Handling and Fallback Strategies**

```python
# Order Service - Fallback Mechanisms
class OrderProcessingService:
    async def process_cart_item(self, game_id: int, quantity: int):
        try:
            # Primary: Get live game data
            game_data = await self.game_service.validate_game(game_id)
            
        except GameServiceUnavailableError:
            # Fallback: Use cached game data
            game_data = await self.get_cached_game_data(game_id)
            if not game_data:
                raise CartItemValidationError(
                    "Game validation unavailable"
                )
        
        except GameNotFoundError:
            # Game no longer exists
            raise CartItemValidationError(
                f"Game {game_id} is no longer available"
            )
        
        return self.create_cart_item(game_data, quantity)
    
    async def get_cached_game_data(self, game_id: int) -> Optional[Dict]:
        """Fallback to cached game data when Game Service unavailable"""
        cache_key = f"game_data:{game_id}"
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        return None
```

### 2. Analytics Service ← All Services Integration

#### **Event Collection Integration**

**Purpose**: Analytics Service receives events from all services for comprehensive business intelligence.

```
Event Flow Architecture:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Game Service   │    │  Order Service  │    │    Frontend     │
│                 │    │                 │    │                 │
│ • Game views    │    │ • Cart actions  │    │ • Page views    │
│ • Search events │    │ • Purchases     │    │ • Click events  │
│ • Popularity    │    │ • User actions  │    │ • Scroll depth  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ↓                       ↓                       ↓
┌─────────────────────────────────────────────────────────────────┐
│                   ANALYTICS SERVICE                             │
│                                                                 │
│  Event Ingestion Layer                                         │
│  ├── POST /api/v1/events/pageview                             │
│  ├── POST /api/v1/events/click                                │
│  ├── POST /api/v1/events/cart                                 │
│  ├── POST /api/v1/events/purchase                             │
│  └── POST /api/v1/events/batch                                │
│                                                                 │
│  Stream Processing                                              │
│  ├── Real-time aggregations                                    │
│  ├── User session tracking                                     │
│  ├── Conversion funnel analysis                                │
│  └── Live dashboard updates                                    │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│                     CLICKHOUSE DATABASE                        │
│                                                                 │
│  Event Storage                                                  │
│  ├── Raw events table (partitioned by date)                   │
│  ├── Aggregated metrics materialized views                     │
│  ├── User behavior analysis tables                             │
│  └── Real-time dashboard data                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation Details:**

```python
# Analytics Service - Event Processing
class EventProcessingService:
    def __init__(self):
        self.clickhouse = AsyncClickHouseClient()
        self.redis = AsyncRedisClient()
        self.event_queue = asyncio.Queue(maxsize=10000)
        
    async def ingest_event(self, event_data: Dict) -> str:
        """Ingest single event for processing"""
        # Validate event schema
        event = self.validate_event_schema(event_data)
        
        # Enrich event with additional context
        enriched_event = await self.enrich_event(event)
        
        # Add to processing queue
        await self.event_queue.put(enriched_event)
        
        # Update real-time metrics
        await self.update_realtime_metrics(enriched_event)
        
        return event["event_id"]
    
    async def batch_ingest_events(self, events: List[Dict]) -> Dict:
        """Process multiple events in batch"""
        processed = 0
        failed = 0
        errors = []
        
        for event_data in events:
            try:
                await self.ingest_event(event_data)
                processed += 1
            except Exception as e:
                failed += 1
                errors.append(str(e))
        
        return {
            "processed": processed,
            "failed": failed,
            "errors": errors
        }
    
    async def enrich_event(self, event: Dict) -> Dict:
        """Add contextual information to events"""
        enriched = event.copy()
        
        # Add geolocation data
        if "ip_address" in event:
            geo_data = await self.get_geolocation(event["ip_address"])
            enriched.update(geo_data)
        
        # Add user session context
        if "user_id" in event:
            user_context = await self.get_user_context(event["user_id"])
            enriched.update(user_context)
        
        # Add timestamp if not present
        if "timestamp" not in enriched:
            enriched["timestamp"] = datetime.utcnow().isoformat()
        
        return enriched

# Background Event Processing Worker
class EventProcessingWorker:
    async def start_processing(self):
        """Background worker for processing events"""
        while True:
            try:
                # Process events in batches for efficiency
                batch = []
                
                # Collect batch of events (max 100 or 1 second timeout)
                batch_start = time.time()
                while (len(batch) < 100 and 
                       time.time() - batch_start < 1.0):
                    try:
                        event = await asyncio.wait_for(
                            self.event_queue.get(), timeout=0.1
                        )
                        batch.append(event)
                    except asyncio.TimeoutError:
                        break
                
                if batch:
                    await self.process_event_batch(batch)
                    
            except Exception as e:
                logger.error(f"Event processing error: {e}")
                await asyncio.sleep(1)
    
    async def process_event_batch(self, events: List[Dict]):
        """Process batch of events to ClickHouse"""
        try:
            # Insert into ClickHouse
            await self.clickhouse.insert_events(events)
            
            # Update aggregation tables
            await self.update_aggregations(events)
            
            # Trigger any real-time alerts
            await self.check_alert_conditions(events)
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            # Re-queue events for retry
            for event in events:
                await self.event_queue.put(event)
```

#### **Service-to-Service Event Reporting**

```python
# Game Service - Analytics Integration
class GameAnalyticsReporter:
    def __init__(self, analytics_service_url: str, service_token: str):
        self.analytics_url = analytics_service_url
        self.headers = {"Authorization": f"Bearer {service_token}"}
    
    async def report_game_view(self, game_id: int, user_id: Optional[int], 
                              session_id: str, context: Dict):
        """Report game view event to analytics"""
        event_data = {
            "event_type": "game_view",
            "game_id": game_id,
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            **context
        }
        
        await self.send_event_async(event_data)
    
    async def report_search_event(self, query: str, results_count: int,
                                 filters: Dict, user_context: Dict):
        """Report search event to analytics"""
        event_data = {
            "event_type": "search",
            "search_query": query,
            "results_count": results_count,
            "search_filters": filters,
            **user_context
        }
        
        await self.send_event_async(event_data)
    
    async def send_event_async(self, event_data: Dict):
        """Non-blocking event sending"""
        asyncio.create_task(self._send_event(event_data))
    
    async def _send_event(self, event_data: Dict):
        """Actually send event to analytics service"""
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.analytics_url}/api/v1/events/batch",
                    json={"events": [event_data]},
                    headers=self.headers,
                    timeout=5.0
                )
        except Exception as e:
            # Log error but don't block main operation
            logger.warning(f"Failed to send analytics event: {e}")

# Order Service - Purchase Analytics
class OrderAnalyticsReporter:
    async def report_purchase_event(self, order: Order):
        """Report successful purchase to analytics"""
        event_data = {
            "event_type": "purchase",
            "order_id": order.id,
            "user_id": order.user_id,
            "total_amount": float(order.total_amount),
            "payment_method": order.payment_method,
            "items": [
                {
                    "game_id": item.game_id,
                    "quantity": item.quantity,
                    "price": float(item.price)
                }
                for item in order.items
            ],
            "timestamp": order.created_at.isoformat()
        }
        
        await self.analytics_reporter.send_event_async(event_data)
    
    async def report_cart_event(self, user_id: int, event_type: str,
                               game_id: int, quantity: int = None):
        """Report cart modification events"""
        event_data = {
            "event_type": "cart_action",
            "cart_event_type": event_type,  # add, remove, update
            "user_id": user_id,
            "game_id": game_id,
            "quantity": quantity,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.analytics_reporter.send_event_async(event_data)
```

---

## Database Integration Points

### 1. PostgreSQL Database Relationships

#### **Cross-Service Data Relationships**

```sql
-- Game Service Database Schema
CREATE SCHEMA game_service;

-- Games table (primary entity)
CREATE TABLE game_service.games (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    discount_price DECIMAL(10,2),
    category_id INTEGER REFERENCES game_service.categories(id),
    publisher_id INTEGER REFERENCES game_service.publishers(id),
    release_date DATE,
    image_url VARCHAR(500),
    rating DECIMAL(3,2) DEFAULT 0,
    in_stock BOOLEAN DEFAULT TRUE,
    inventory_quantity INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Categories table
CREATE TABLE game_service.categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    game_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Publishers table
CREATE TABLE game_service.publishers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    website VARCHAR(255),
    logo_url VARCHAR(500),
    game_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Game images table
CREATE TABLE game_service.game_images (
    id SERIAL PRIMARY KEY,
    game_id INTEGER NOT NULL REFERENCES game_service.games(id) ON DELETE CASCADE,
    image_url VARCHAR(500) NOT NULL,
    image_type VARCHAR(50) NOT NULL, -- cover, screenshot, thumbnail
    alt_text VARCHAR(255),
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Game reviews table
CREATE TABLE game_service.game_reviews (
    id SERIAL PRIMARY KEY,
    game_id INTEGER NOT NULL REFERENCES game_service.games(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL, -- Reference to Order Service user
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(game_id, user_id) -- One review per user per game
);

-- Inventory tracking table
CREATE TABLE game_service.inventory_transactions (
    id SERIAL PRIMARY KEY,
    game_id INTEGER NOT NULL REFERENCES game_service.games(id),
    transaction_type VARCHAR(50) NOT NULL, -- reserve, release, purchase, restock
    quantity INTEGER NOT NULL,
    reservation_id VARCHAR(100), -- For temporary reservations
    order_id INTEGER, -- Reference to Order Service order
    expires_at TIMESTAMP, -- For reservations
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

```sql
-- Order Service Database Schema
CREATE SCHEMA order_service;

-- Users table
CREATE TABLE order_service.users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    date_of_birth DATE,
    role VARCHAR(50) DEFAULT 'user', -- user, admin
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User addresses table
CREATE TABLE order_service.user_addresses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES order_service.users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- home, work, other
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    company VARCHAR(100),
    address_line_1 VARCHAR(255) NOT NULL,
    address_line_2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    country VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Shopping carts table
CREATE TABLE order_service.shopping_carts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES order_service.users(id) ON DELETE CASCADE,
    session_id VARCHAR(100), -- For guest carts
    total_items INTEGER DEFAULT 0,
    total_price DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id) -- One cart per user
);

-- Cart items table
CREATE TABLE order_service.cart_items (
    id SERIAL PRIMARY KEY,
    cart_id INTEGER NOT NULL REFERENCES order_service.shopping_carts(id) ON DELETE CASCADE,
    game_id INTEGER NOT NULL, -- Reference to Game Service
    game_name VARCHAR(255) NOT NULL, -- Denormalized for performance
    game_price DECIMAL(10,2) NOT NULL,
    game_discount_price DECIMAL(10,2),
    quantity INTEGER NOT NULL DEFAULT 1,
    subtotal DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cart_id, game_id) -- One entry per game per cart
);

-- Orders table
CREATE TABLE order_service.orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES order_service.users(id),
    order_number VARCHAR(100) NOT NULL UNIQUE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, processing, shipped, delivered, cancelled
    total_amount DECIMAL(10,2) NOT NULL,
    shipping_address_id INTEGER REFERENCES order_service.user_addresses(id),
    payment_method VARCHAR(50) NOT NULL,
    payment_status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, completed, failed, refunded
    payment_transaction_id VARCHAR(255),
    tracking_number VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order items table
CREATE TABLE order_service.order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES order_service.orders(id) ON DELETE CASCADE,
    game_id INTEGER NOT NULL, -- Reference to Game Service
    game_name VARCHAR(255) NOT NULL,
    game_price DECIMAL(10,2) NOT NULL,
    discount_price DECIMAL(10,2),
    quantity INTEGER NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Newsletter subscriptions table
CREATE TABLE order_service.newsletter_subscriptions (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),
    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    unsubscribed_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

#### **Database Consistency Strategies**

```python
# Cross-Service Data Consistency Manager
class CrossServiceDataManager:
    def __init__(self, game_db: AsyncSession, order_db: AsyncSession):
        self.game_db = game_db
        self.order_db = order_db
    
    async def sync_game_data_to_order_service(self, game_id: int):
        """Sync game data changes to order service denormalized tables"""
        async with self.game_db() as session:
            game = await session.get(Game, game_id)
            if not game:
                return
        
        # Update cart items with new game data
        async with self.order_db() as session:
            await session.execute(
                update(CartItem)
                .where(CartItem.game_id == game_id)
                .values(
                    game_name=game.name,
                    game_price=game.price,
                    game_discount_price=game.discount_price
                )
            )
            await session.commit()
    
    async def validate_cart_items_inventory(self, cart_id: int) -> List[Dict]:
        """Validate all cart items against current inventory"""
        validation_results = []
        
        async with self.order_db() as session:
            cart_items = await session.execute(
                select(CartItem).where(CartItem.cart_id == cart_id)
            )
            cart_items = cart_items.scalars().all()
        
        for item in cart_items:
            # Check current inventory in Game Service
            async with self.game_db() as session:
                game = await session.get(Game, item.game_id)
                if not game:
                    validation_results.append({
                        "item_id": item.id,
                        "game_id": item.game_id,
                        "status": "not_found",
                        "message": "Game no longer available"
                    })
                elif game.inventory_quantity < item.quantity:
                    validation_results.append({
                        "item_id": item.id,
                        "game_id": item.game_id,
                        "status": "insufficient_inventory",
                        "available": game.inventory_quantity,
                        "requested": item.quantity
                    })
                else:
                    validation_results.append({
                        "item_id": item.id,
                        "game_id": item.game_id,
                        "status": "valid"
                    })
        
        return validation_results
```

### 2. ClickHouse Analytics Database Integration

#### **Analytics Data Schema**

```sql
-- Analytics Service ClickHouse Schema

-- Raw events table (partitioned by date)
CREATE TABLE analytics.events (
    event_id String,
    event_type LowCardinality(String),
    session_id String,
    user_id Nullable(UInt32),
    timestamp DateTime,
    page_url String,
    user_agent String,
    ip_address IPv4,
    country LowCardinality(String),
    city String,
    
    -- Game-specific fields
    game_id Nullable(UInt32),
    game_name Nullable(String),
    game_category Nullable(String),
    
    -- E-commerce fields
    order_id Nullable(UInt32),
    product_price Nullable(Decimal64(2)),
    quantity Nullable(UInt16),
    
    -- Search fields
    search_query Nullable(String),
    search_filters String, -- JSON string
    results_count Nullable(UInt32),
    
    -- Interaction fields
    element_selector Nullable(String),
    click_x Nullable(UInt16),
    click_y Nullable(UInt16),
    scroll_depth Nullable(UInt8),
    
    -- Additional context (JSON)
    event_data String
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (event_type, timestamp, session_id)
TTL timestamp + INTERVAL 2 YEAR; -- Retain data for 2 years

-- Materialized view for real-time active users
CREATE MATERIALIZED VIEW analytics.active_users_mv
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (timestamp_minute)
AS SELECT
    toStartOfMinute(timestamp) as timestamp_minute,
    uniqState(session_id) as active_sessions,
    uniqState(user_id) as active_users
FROM analytics.events
WHERE event_type = 'pageview'
GROUP BY timestamp_minute;

-- Materialized view for page view aggregations
CREATE MATERIALIZED VIEW analytics.pageviews_mv
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (page_url, toYYYYMMDD(timestamp), toHour(timestamp))
AS SELECT
    page_url,
    toYYYYMMDD(timestamp) as date,
    toHour(timestamp) as hour,
    count() as view_count,
    uniq(session_id) as unique_sessions,
    uniq(user_id) as unique_users
FROM analytics.events
WHERE event_type = 'pageview'
GROUP BY page_url, date, hour;

-- Materialized view for game analytics
CREATE MATERIALIZED VIEW analytics.game_analytics_mv
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (game_id, toYYYYMMDD(timestamp))
AS SELECT
    game_id,
    toYYYYMMDD(timestamp) as date,
    countIf(event_type = 'game_view') as view_count,
    countIf(event_type = 'cart_add') as cart_add_count,
    countIf(event_type = 'purchase') as purchase_count,
    sumIf(product_price * quantity, event_type = 'purchase') as revenue
FROM analytics.events
WHERE game_id IS NOT NULL
GROUP BY game_id, date;

-- Conversion funnel analysis view
CREATE MATERIALIZED VIEW analytics.conversion_funnel_mv
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toYYYYMMDD(timestamp))
AS SELECT
    toYYYYMMDD(timestamp) as date,
    uniqState(session_id) as total_sessions,
    uniqStateIf(session_id, event_type = 'pageview') as page_views,
    uniqStateIf(session_id, event_type = 'game_view') as game_views,
    uniqStateIf(session_id, event_type = 'cart_add') as cart_additions,
    uniqStateIf(session_id, event_type = 'purchase') as purchases
FROM analytics.events
GROUP BY date;
```

#### **ClickHouse Integration Implementation**

```python
# Analytics Service - ClickHouse Integration
class ClickHouseAnalyticsRepository:
    def __init__(self, connection_string: str):
        self.client = AsyncClient.from_url(connection_string)
    
    async def insert_events(self, events: List[Dict]):
        """Batch insert events into ClickHouse"""
        # Transform events to match ClickHouse schema
        ch_events = []
        for event in events:
            ch_event = {
                'event_id': event.get('event_id', str(uuid.uuid4())),
                'event_type': event['event_type'],
                'session_id': event['session_id'],
                'user_id': event.get('user_id'),
                'timestamp': event['timestamp'],
                'page_url': event.get('page_url', ''),
                'user_agent': event.get('user_agent', ''),
                'ip_address': event.get('ip_address', '0.0.0.0'),
                'country': event.get('country', ''),
                'city': event.get('city', ''),
                'game_id': event.get('game_id'),
                'game_name': event.get('game_name'),
                'game_category': event.get('game_category'),
                'order_id': event.get('order_id'),
                'product_price': event.get('product_price'),
                'quantity': event.get('quantity'),
                'search_query': event.get('search_query'),
                'search_filters': json.dumps(event.get('search_filters', {})),
                'results_count': event.get('results_count'),
                'element_selector': event.get('element_selector'),
                'click_x': event.get('click_x'),
                'click_y': event.get('click_y'),
                'scroll_depth': event.get('scroll_depth'),
                'event_data': json.dumps(event.get('event_data', {}))
            }
            ch_events.append(ch_event)
        
        # Batch insert
        await self.client.insert(
            'analytics.events',
            ch_events,
            column_names=list(ch_events[0].keys())
        )
    
    async def get_real_time_active_users(self) -> int:
        """Get current active users count"""
        query = """
        SELECT uniq(session_id) as active_users
        FROM analytics.events
        WHERE timestamp >= now() - INTERVAL 15 MINUTE
        AND event_type = 'pageview'
        """
        
        result = await self.client.fetch_one(query)
        return result['active_users']
    
    async def get_popular_games(self, period: str = 'week', 
                               limit: int = 10) -> List[Dict]:
        """Get popular games analytics"""
        interval_map = {
            'day': '1 DAY',
            'week': '7 DAY',
            'month': '30 DAY',
            'year': '365 DAY'
        }
        
        interval = interval_map.get(period, '7 DAY')
        
        query = f"""
        SELECT 
            game_id,
            game_name,
            sum(view_count) as total_views,
            sum(cart_add_count) as total_cart_adds,
            sum(purchase_count) as total_purchases,
            sum(revenue) as total_revenue,
            if(sum(view_count) > 0, 
               sum(purchase_count) / sum(view_count), 0) as conversion_rate
        FROM analytics.game_analytics_mv
        WHERE date >= today() - INTERVAL {interval}
        AND game_id IS NOT NULL
        GROUP BY game_id, game_name
        ORDER BY total_views DESC
        LIMIT {limit}
        """
        
        results = await self.client.fetch_all(query)
        return [dict(row) for row in results]
    
    async def get_conversion_funnel(self, period: str = 'week') -> Dict:
        """Get conversion funnel analytics"""
        interval_map = {
            'day': '1 DAY',
            'week': '7 DAY',
            'month': '30 DAY'
        }
        
        interval = interval_map.get(period, '7 DAY')
        
        query = f"""
        SELECT 
            uniqMerge(total_sessions) as total_sessions,
            uniqMerge(page_views) as page_views,
            uniqMerge(game_views) as game_views,
            uniqMerge(cart_additions) as cart_additions,
            uniqMerge(purchases) as purchases
        FROM analytics.conversion_funnel_mv
        WHERE date >= today() - INTERVAL {interval}
        """
        
        result = await self.client.fetch_one(query)
        
        # Calculate conversion rates
        total_sessions = result['total_sessions']
        return {
            'total_sessions': total_sessions,
            'page_views': result['page_views'],
            'game_views': result['game_views'],
            'cart_additions': result['cart_additions'],
            'purchases': result['purchases'],
            'page_view_rate': result['page_views'] / total_sessions if total_sessions > 0 else 0,
            'game_view_rate': result['game_views'] / total_sessions if total_sessions > 0 else 0,
            'cart_rate': result['cart_additions'] / total_sessions if total_sessions > 0 else 0,
            'purchase_rate': result['purchases'] / total_sessions if total_sessions > 0 else 0
        }
```

---

## External Service Integration Points

### 1. AWS QuickSight Integration

#### **Data Source Configuration**

**Purpose**: Provide business intelligence dashboards using ClickHouse analytics data.

```python
# Analytics Service - QuickSight Data API
class QuickSightDataProvider:
    def __init__(self, clickhouse_repo: ClickHouseAnalyticsRepository):
        self.clickhouse = clickhouse_repo
    
    async def get_dashboard_kpis(self, period: str = 'day') -> Dict:
        """Provide KPI data for QuickSight dashboard"""
        interval_map = {
            'day': '1 DAY',
            'week': '7 DAY',
            'month': '30 DAY'
        }
        
        interval = interval_map.get(period, '1 DAY')
        
        # Get current period metrics
        current_query = f"""
        SELECT 
            uniq(session_id) as active_users,
            count() as page_views,
            countIf(event_type = 'purchase') as purchases,
            sumIf(product_price * quantity, event_type = 'purchase') as revenue,
            avg(scroll_depth) as avg_engagement
        FROM analytics.events
        WHERE timestamp >= now() - INTERVAL {interval}
        """
        
        current_metrics = await self.clickhouse.client.fetch_one(current_query)
        
        # Get previous period for comparison
        previous_query = f"""
        SELECT 
            uniq(session_id) as active_users,
            count() as page_views,
            countIf(event_type = 'purchase') as purchases,
            sumIf(product_price * quantity, event_type = 'purchase') as revenue,
            avg(scroll_depth) as avg_engagement
        FROM analytics.events
        WHERE timestamp >= now() - INTERVAL {interval} * 2
        AND timestamp < now() - INTERVAL {interval}
        """
        
        previous_metrics = await self.clickhouse.client.fetch_one(previous_query)
        
        # Calculate growth rates
        def growth_rate(current, previous):
            if previous == 0:
                return 0
            return ((current - previous) / previous) * 100
        
        return {
            'period': period,
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': {
                'active_users': {
                    'value': current_metrics['active_users'],
                    'growth_rate': growth_rate(
                        current_metrics['active_users'],
                        previous_metrics['active_users']
                    )
                },
                'page_views': {
                    'value': current_metrics['page_views'],
                    'growth_rate': growth_rate(
                        current_metrics['page_views'],
                        previous_metrics['page_views']
                    )
                },
                'purchases': {
                    'value': current_metrics['purchases'],
                    'growth_rate': growth_rate(
                        current_metrics['purchases'],
                        previous_metrics['purchases']
                    )
                },
                'revenue': {
                    'value': float(current_metrics['revenue'] or 0),
                    'growth_rate': growth_rate(
                        float(current_metrics['revenue'] or 0),
                        float(previous_metrics['revenue'] or 0)
                    )
                },
                'avg_engagement': {
                    'value': float(current_metrics['avg_engagement'] or 0),
                    'growth_rate': growth_rate(
                        float(current_metrics['avg_engagement'] or 0),
                        float(previous_metrics['avg_engagement'] or 0)
                    )
                }
            }
        }
    
    async def export_analytics_data(self, data_type: str, 
                                   start_date: str, end_date: str,
                                   format: str = 'csv') -> str:
        """Export analytics data for QuickSight import"""
        
        if data_type == 'game_performance':
            query = f"""
            SELECT 
                game_id,
                game_name,
                game_category,
                sum(view_count) as total_views,
                sum(cart_add_count) as total_cart_adds,
                sum(purchase_count) as total_purchases,
                sum(revenue) as total_revenue,
                if(sum(view_count) > 0, 
                   sum(purchase_count) / sum(view_count), 0) as conversion_rate
            FROM analytics.game_analytics_mv
            WHERE date >= '{start_date}' AND date <= '{end_date}'
            GROUP BY game_id, game_name, game_category
            ORDER BY total_revenue DESC
            """
        
        elif data_type == 'user_behavior':
            query = f"""
            SELECT 
                toYYYYMMDD(timestamp) as date,
                uniq(session_id) as daily_active_users,
                count() as total_events,
                countIf(event_type = 'pageview') as page_views,
                countIf(event_type = 'purchase') as purchases,
                avg(scroll_depth) as avg_scroll_depth
            FROM analytics.events
            WHERE timestamp >= '{start_date}' AND timestamp <= '{end_date}'
            GROUP BY date
            ORDER BY date
            """
        
        else:
            raise ValueError(f"Unsupported data type: {data_type}")
        
        # Execute query and format results
        results = await self.clickhouse.client.fetch_all(query)
        
        if format == 'csv':
            return self.format_as_csv(results)
        elif format == 'json':
            return json.dumps([dict(row) for row in results])
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def format_as_csv(self, results: List) -> str:
        """Format query results as CSV"""
        if not results:
            return ""
        
        # Get column names from first row
        columns = list(results[0].keys())
        
        # Create CSV content
        csv_content = []
        csv_content.append(','.join(columns))
        
        for row in results:
            csv_row = []
            for col in columns:
                value = row[col]
                if value is None:
                    csv_row.append('')
                else:
                    csv_row.append(str(value))
            csv_content.append(','.join(csv_row))
        
        return '\n'.join(csv_content)
```

### 2. Email Service Integration

#### **Notification System Integration**

```python
# Order Service - Email Integration
class EmailNotificationService:
    def __init__(self, smtp_host: str, smtp_port: int, 
                 smtp_user: str, smtp_password: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
    
    async def send_order_confirmation(self, order: Order):
        """Send order confirmation email"""
        template_data = {
            'order_number': order.order_number,
            'customer_name': f"{order.user.first_name} {order.user.last_name}",
            'order_total': f"${order.total_amount}",
            'order_items': [
                {
                    'name': item.game_name,
                    'quantity': item.quantity,
                    'price': f"${item.subtotal}"
                }
                for item in order.items
            ],
            'shipping_address': self.format_address(order.shipping_address)
        }
        
        html_content = await self.render_template(
            'order_confirmation.html', 
            template_data
        )
        
        await self.send_email(
            to_email=order.user.email,
            subject=f"Order Confirmation - {order.order_number}",
            html_content=html_content
        )
    
    async def send_newsletter_confirmation(self, email: str, name: str):
        """Send newsletter subscription confirmation"""
        template_data = {
            'subscriber_name': name or 'Gaming Enthusiast',
            'unsubscribe_link': f"https://lugxgaming.com/unsubscribe?email={email}"
        }
        
        html_content = await self.render_template(
            'newsletter_confirmation.html',
            template_data
        )
        
        await self.send_email(
            to_email=email,
            subject="Welcome to Lugx Gaming Newsletter!",
            html_content=html_content
        )
    
    async def send_email(self, to_email: str, subject: str, 
                        html_content: str):
        """Send email using SMTP"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.smtp_user
        msg['To'] = to_email
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        try:
            async with aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=True
            ) as server:
                await server.login(self.smtp_user, self.smtp_password)
                await server.send_message(msg)
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            raise EmailDeliveryError(f"Email delivery failed: {e}")
```

### 3. Payment Gateway Integration (Simulation)

#### **Payment Processing Integration**

```python
# Order Service - Payment Gateway Integration
class PaymentGatewayService:
    def __init__(self):
        self.supported_methods = ['credit_card', 'paypal', 'stripe']
    
    async def process_payment(self, payment_request: PaymentRequest) -> PaymentResponse:
        """Process payment through appropriate gateway"""
        
        if payment_request.payment_method == 'credit_card':
            return await self.process_credit_card(payment_request)
        elif payment_request.payment_method == 'paypal':
            return await self.process_paypal(payment_request)
        elif payment_request.payment_method == 'stripe':
            return await self.process_stripe(payment_request)
        else:
            raise UnsupportedPaymentMethodError(
                f"Payment method {payment_request.payment_method} not supported"
            )
    
    async def process_credit_card(self, payment_request: PaymentRequest) -> PaymentResponse:
        """Simulate credit card processing"""
        # Simulate processing delay
        await asyncio.sleep(random.uniform(1, 3))
        
        # Simulate success/failure (90% success rate)
        success = random.random() < 0.9
        
        if success:
            return PaymentResponse(
                payment_id=str(uuid.uuid4()),
                status='success',
                transaction_id=f"CC_{int(time.time())}_{random.randint(1000, 9999)}",
                amount=payment_request.amount,
                currency='USD',
                message='Payment processed successfully',
                processed_at=datetime.utcnow()
            )
        else:
            return PaymentResponse(
                payment_id=str(uuid.uuid4()),
                status='failed',
                transaction_id=None,
                amount=payment_request.amount,
                currency='USD',
                message='Payment declined by bank',
                processed_at=datetime.utcnow()
            )
    
    async def process_paypal(self, payment_request: PaymentRequest) -> PaymentResponse:
        """Simulate PayPal processing"""
        await asyncio.sleep(random.uniform(2, 4))
        
        # Simulate success/failure (95% success rate for PayPal)
        success = random.random() < 0.95
        
        if success:
            return PaymentResponse(
                payment_id=str(uuid.uuid4()),
                status='success',
                transaction_id=f"PP_{int(time.time())}_{random.randint(1000, 9999)}",
                amount=payment_request.amount,
                currency='USD',
                message='PayPal payment completed',
                processed_at=datetime.utcnow()
            )
        else:
            return PaymentResponse(
                payment_id=str(uuid.uuid4()),
                status='failed',
                transaction_id=None,
                amount=payment_request.amount,
                currency='USD',
                message='PayPal payment cancelled by user',
                processed_at=datetime.utcnow()
            )
    
    async def process_stripe(self, payment_request: PaymentRequest) -> PaymentResponse:
        """Simulate Stripe processing"""
        await asyncio.sleep(random.uniform(0.5, 2))
        
        # Simulate success/failure (92% success rate for Stripe)
        success = random.random() < 0.92
        
        if success:
            return PaymentResponse(
                payment_id=str(uuid.uuid4()),
                status='success',
                transaction_id=f"STRIPE_{int(time.time())}_{random.randint(1000, 9999)}",
                amount=payment_request.amount,
                currency='USD',
                message='Stripe payment successful',
                processed_at=datetime.utcnow()
            )
        else:
            return PaymentResponse(
                payment_id=str(uuid.uuid4()),
                status='failed',
                transaction_id=None,
                amount=payment_request.amount,
                currency='USD',
                message='Insufficient funds',
                processed_at=datetime.utcnow()
            )
```

---

## Security Integration Points

### 1. Authentication and Authorization Integration

#### **JWT Token Management Across Services**

```python
# Shared Authentication Service
class JWTAuthenticationService:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_expiry = timedelta(hours=24)
    
    def create_access_token(self, user_data: Dict) -> str:
        """Create JWT access token"""
        payload = {
            "user_id": user_data["id"],
            "email": user_data["email"],
            "role": user_data["role"],
            "exp": datetime.utcnow() + self.token_expiry,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token, self.secret_key, algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError:
            raise InvalidTokenError("Invalid token")
    
    async def get_current_user(self, token: str) -> Dict:
        """Get current user from token"""
        payload = self.verify_token(token)
        
        # Fetch fresh user data from database
        # This ensures user hasn't been deactivated
        user = await self.user_repository.get_by_id(payload["user_id"])
        if not user or not user.is_active:
            raise UserNotFoundError("User not found or inactive")
        
        return {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "first_name": user.first_name,
            "last_name": user.last_name
        }

# FastAPI Dependency for Authentication
async def get_current_user(
    token: str = Depends(HTTPBearer()),
    auth_service: JWTAuthenticationService = Depends()
) -> Dict:
    """FastAPI dependency to get current authenticated user"""
    return await auth_service.get_current_user(token.credentials)

# Service-to-Service Authentication
class ServiceAuthenticationMiddleware:
    def __init__(self, service_tokens: Dict[str, str]):
        self.service_tokens = service_tokens
        self.auth_service = JWTAuthenticationService()
    
    async def authenticate_service(self, request: Request) -> Optional[str]:
        """Authenticate service-to-service requests"""
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        try:
            payload = self.auth_service.verify_token(token)
            if payload.get("type") == "service":
                return payload.get("service_name")
        except (TokenExpiredError, InvalidTokenError):
            pass
        
        return None
```

### 2. Data Encryption Integration

#### **Encryption for Sensitive Data**

```python
# Shared Encryption Service
class DataEncryptionService:
    def __init__(self, encryption_key: bytes):
        self.fernet = Fernet(encryption_key)
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data like payment info"""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()
    
    def hash_password(self, password: str) -> str:
        """Hash password for storage"""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode(), hashed.encode())

# Database Field Encryption
class EncryptedField:
    def __init__(self, encryption_service: DataEncryptionService):
        self.encryption_service = encryption_service
    
    def __set_name__(self, owner, name):
        self.name = name
        self.private_name = f'_{name}'
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        encrypted_value = getattr(obj, self.private_name, None)
        if encrypted_value:
            return self.encryption_service.decrypt_sensitive_data(encrypted_value)
        return None
    
    def __set__(self, obj, value):
        if value:
            encrypted_value = self.encryption_service.encrypt_sensitive_data(value)
            setattr(obj, self.private_name, encrypted_value)
        else:
            setattr(obj, self.private_name, None)

### 3. Istio Service Mesh Security Integration

#### **mTLS Certificate Management**

```python
# Istio mTLS Integration Service
class IstioSecurityService:
    def __init__(self):
        self.ca_cert_path = "/etc/ssl/certs/istio-ca-root-cert.pem"
        self.cert_path = "/etc/ssl/certs/cert-chain.pem"
        self.key_path = "/etc/ssl/private/key.pem"
    
    def verify_mtls_connection(self, request: Request) -> bool:
        """Verify mTLS connection from Istio sidecar"""
        # Check for Istio-injected mTLS headers
        mtls_headers = [
            'x-forwarded-client-cert',
            'x-istio-mtls',
            'x-forwarded-proto'
        ]
        
        for header in mtls_headers:
            if header in request.headers:
                logger.debug(f"mTLS header found: {header}")
                return True
        
        return False
    
    def get_peer_certificate_info(self, request: Request) -> Optional[Dict]:
        """Extract peer certificate information from Istio headers"""
        client_cert_header = request.headers.get('x-forwarded-client-cert')
        if not client_cert_header:
            return None
        
        # Parse certificate information injected by Istio
        try:
            cert_info = self.parse_certificate_header(client_cert_header)
            return {
                'subject': cert_info.get('subject'),
                'serial_number': cert_info.get('serial'),
                'issuer': cert_info.get('issuer'),
                'valid_from': cert_info.get('not_before'),
                'valid_to': cert_info.get('not_after')
            }
        except Exception as e:
            logger.warning(f"Failed to parse client certificate: {e}")
            return None

# Service Authentication with Istio Service Accounts
class IstioServiceAuthentication:
    def __init__(self):
        self.allowed_service_accounts = {
            'game-service': 'cluster.local/ns/production/sa/game-service',
            'order-service': 'cluster.local/ns/production/sa/order-service',
            'analytics-service': 'cluster.local/ns/production/sa/analytics-service'
        }
    
    def authenticate_service_request(self, request: Request) -> Optional[str]:
        """Authenticate service-to-service request using Istio service identity"""
        # Istio injects service account information in headers
        service_account = request.headers.get('x-forwarded-for-service-account')
        source_workload = request.headers.get('x-envoy-internal')
        
        if service_account in self.allowed_service_accounts.values():
            # Extract service name from service account
            for service_name, sa in self.allowed_service_accounts.items():
                if sa == service_account:
                    logger.info(f"Authenticated service request from: {service_name}")
                    return service_name
        
        return None

# Rate Limiting Integration with Istio
class IstioRateLimitingService:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.rate_limits = {
            'analytics_events': {'requests': 1000, 'window': 60},  # 1000 requests per minute
            'api_calls': {'requests': 100, 'window': 60},          # 100 requests per minute
            'auth_attempts': {'requests': 5, 'window': 300}        # 5 attempts per 5 minutes
        }
    
    async def check_rate_limit(self, request: Request, limit_type: str) -> Tuple[bool, Dict]:
        """Check rate limit using Redis and Istio headers"""
        # Get client identifier from Istio headers
        client_ip = request.headers.get('x-forwarded-for', request.client.host)
        user_id = request.headers.get('x-user-id')  # From JWT processing
        
        # Create rate limit key
        identifier = user_id if user_id else client_ip
        rate_limit_key = f"rate_limit:{limit_type}:{identifier}"
        
        limit_config = self.rate_limits.get(limit_type)
        if not limit_config:
            return True, {}
        
        # Use Redis sliding window rate limiting
        current_time = int(time.time())
        window_start = current_time - limit_config['window']
        
        # Remove old entries
        await self.redis.zremrangebyscore(rate_limit_key, 0, window_start)
        
        # Count current requests
        current_count = await self.redis.zcard(rate_limit_key)
        
        if current_count >= limit_config['requests']:
            # Rate limit exceeded
            ttl = await self.redis.ttl(rate_limit_key)
            return False, {
                'limit': limit_config['requests'],
                'window': limit_config['window'],
                'current': current_count,
                'reset_in': ttl
            }
        
        # Add current request
        await self.redis.zadd(rate_limit_key, {str(uuid.uuid4()): current_time})
        await self.redis.expire(rate_limit_key, limit_config['window'])
        
        return True, {
            'limit': limit_config['requests'],
            'window': limit_config['window'],
            'current': current_count + 1,
            'remaining': limit_config['requests'] - current_count - 1
        }

# FastAPI Middleware for Istio Integration
class IstioIntegrationMiddleware:
    def __init__(self, app: FastAPI):
        self.app = app
        self.security_service = IstioSecurityService()
        self.auth_service = IstioServiceAuthentication()
        self.rate_limit_service = IstioRateLimitingService(redis_client)
    
    async def __call__(self, request: Request, call_next):
        # Extract Istio observability context
        request.state.trace_context = self.extract_trace_context(request)
        request.state.correlation_id = request.headers.get('x-correlation-id', str(uuid.uuid4()))
        
        # Verify mTLS if configured
        if not self.security_service.verify_mtls_connection(request):
            logger.warning(f"Non-mTLS request detected: {request.url}")
        
        # Check rate limits for API endpoints
        if request.url.path.startswith('/api/'):
            allowed, rate_info = await self.rate_limit_service.check_rate_limit(
                request, 'api_calls'
            )
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "details": rate_info
                    },
                    headers={
                        "X-RateLimit-Limit": str(rate_info['limit']),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(rate_info['reset_in'])
                    }
                )
        
        # Process request
        response = await call_next(request)
        
        # Add Istio-compatible response headers
        response.headers["X-Correlation-ID"] = request.state.correlation_id
        response.headers["X-Service-Name"] = "lugx-gaming-service"
        
        return response
```

#### **Istio Fault Injection for Testing**

```yaml
# Fault Injection for Chaos Engineering
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: game-service-fault-injection
  namespace: production
spec:
  hosts:
  - game-service.production.svc.cluster.local
  http:
  - match:
    - headers:
        x-chaos-test:
          exact: "true"
    fault:
      delay:
        percentage:
          value: 50.0  # 50% of requests delayed
        fixedDelay: 10s
      abort:
        percentage:
          value: 10.0  # 10% of requests aborted
        httpStatus: 503
    route:
    - destination:
        host: game-service.production.svc.cluster.local
  - route:
    - destination:
        host: game-service.production.svc.cluster.local
```

This comprehensive Istio service mesh integration provides automatic security, observability, and traffic management for all service communications, ensuring enterprise-grade reliability and security without requiring code changes in individual services.
```

This comprehensive integration points documentation ensures that all components of the Lugx Gaming platform work together seamlessly, providing clear guidance for implementing secure, scalable, and maintainable integrations between services, databases, and external systems.

## Istio Service Mesh Deployment Integration

### Kubernetes and Istio Deployment Configuration

#### **Service Mesh Installation Configuration**

```yaml
# Istio Installation Configuration
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
  name: lugx-gaming-istio
  namespace: istio-system
spec:
  values:
    global:
      meshID: lugx-gaming-mesh
      multiCluster:
        clusterName: lugx-gaming-cluster
      network: network1
    pilot:
      env:
        EXTERNAL_ISTIOD: false
        PILOT_TRACE_SAMPLING: 1.0  # 100% sampling for development
  components:
    pilot:
      k8s:
        resources:
          requests:
            cpu: 200m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
    ingressGateways:
    - name: istio-ingressgateway
      enabled: true
      k8s:
        service:
          type: LoadBalancer
          ports:
          - port: 80
            targetPort: 8080
            name: http2
          - port: 443
            targetPort: 8443
            name: https
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 2000m
            memory: 1024Mi
    egressGateways:
    - name: istio-egressgateway
      enabled: true
      k8s:
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 256Mi
```

#### **Service Deployment with Istio Injection**

```yaml
# Game Service Deployment with Istio Sidecar
apiVersion: apps/v1
kind: Deployment
metadata:
  name: game-service
  namespace: production
  labels:
    app: game-service
    version: v1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: game-service
      version: v1
  template:
    metadata:
      labels:
        app: game-service
        version: v1
      annotations:
        sidecar.istio.io/inject: "true"
        sidecar.istio.io/proxyCPU: "100m"
        sidecar.istio.io/proxyMemory: "128Mi"
    spec:
      serviceAccountName: game-service
      containers:
      - name: game-service
        image: lugxgaming/game-service:latest
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: game-service-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: game-service-secrets
              key: redis-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# Service Account for Istio mTLS
apiVersion: v1
kind: ServiceAccount
metadata:
  name: game-service
  namespace: production
  labels:
    app: game-service

---
# Kubernetes Service
apiVersion: v1
kind: Service
metadata:
  name: game-service
  namespace: production
  labels:
    app: game-service
spec:
  ports:
  - port: 8000
    targetPort: 8000
    protocol: TCP
    name: http
  selector:
    app: game-service
```

#### **Istio Observability Stack Integration**

```yaml
# Telemetry Configuration for Custom Metrics
apiVersion: telemetry.istio.io/v1alpha1
kind: Telemetry
metadata:
  name: lugx-gaming-metrics
  namespace: production
spec:
  metrics:
  - providers:
    - name: prometheus
  - overrides:
    - match:
        metric: ALL_METRICS
      tagOverrides:
        request_protocol:
          value: "%{REQUEST_PROTOCOL}"
        response_code:
          value: "%{RESPONSE_CODE}"
        source_app:
          value: "%{SOURCE_APP}"
        destination_service_name:
          value: "%{DESTINATION_SERVICE_NAME}"
        game_id:
          value: "%{REQUEST_HEADERS['x-game-id']}"
        user_id:
          value: "%{REQUEST_HEADERS['x-user-id']}"

---
# Access Logging Configuration
apiVersion: telemetry.istio.io/v1alpha1
kind: Telemetry
metadata:
  name: lugx-gaming-access-logs
  namespace: production
spec:
  accessLogging:
  - providers:
    - name: otel
```

This comprehensive integration points documentation now includes complete Istio service mesh configuration, providing automatic security, observability, and traffic management for the entire Lugx Gaming platform microservices ecosystem.

**Regarding AWS deployment**: The current plan focuses on Kubernetes orchestration which can be deployed on AWS EKS (Elastic Kubernetes Service). The plan could be adapted to use native AWS services like:
- **EKS** for managed Kubernetes with Istio
- **RDS** for PostgreSQL databases
- **ElastiCache** for Redis
- **CloudWatch** for monitoring integration
- **ALB** for load balancing with Istio Gateway

Would you like me to create an AWS-specific deployment architecture document?