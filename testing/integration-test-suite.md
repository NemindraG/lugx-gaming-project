# Lugx Gaming Platform - Integration Test Suite Design

## Executive Summary

This document provides a comprehensive integration test suite design for the Lugx Gaming platform, ensuring automated validation of all microservices, database integrations, and critical user journeys both during CI/CD deployments and ongoing system reliability monitoring.

## Testing Strategy Overview

### Test Pyramid Implementation
```
┌─────────────────────────────────────────────────────────────────┐
│                    LUGX GAMING TEST PYRAMID                    │
│                                                                 │
│                        ┌─────────────┐                        │
│                        │     E2E     │                        │
│                        │   Tests     │                        │
│                        │     (5%)    │                        │
│                        └─────────────┘                        │
│                    ┌─────────────────────┐                    │
│                    │   Integration Tests │                    │
│                    │        (25%)        │                    │
│                    └─────────────────────┘                    │
│            ┌─────────────────────────────────────┐            │
│            │          Unit Tests                 │            │
│            │            (70%)                    │            │
│            └─────────────────────────────────────┘            │
│                                                                 │
│  Focus: Fast feedback, reliable CI/CD, comprehensive coverage  │
└─────────────────────────────────────────────────────────────────┘
```

### Test Categories
```yaml
Test Categories:
  1. API Integration Tests:
     - Service-to-service communication
     - Database connectivity
     - External service integration
     - Error handling and resilience
  
  2. Data Flow Tests:
     - Event processing pipelines
     - ClickHouse data ingestion
     - Real-time analytics validation
     - Cross-service data consistency
  
  3. Business Logic Tests:
     - End-to-end user journeys
     - Order processing workflows
     - Game catalog operations
     - Analytics capture and reporting
  
  4. Performance Tests:
     - Load testing under peak traffic
     - Database query performance
     - API response time validation
     - System resource utilization
  
  5. Security Tests:
     - Authentication and authorization
     - Input validation and sanitization
     - Security header validation
     - JWT token handling
```

---

## 1. API Integration Test Framework

### 1.1 Test Infrastructure Setup

```python
# testing/integration/framework/test_base.py
import pytest
import asyncio
import httpx
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import os

@dataclass
class TestConfig:
    base_url: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    timeout: int = 30
    max_retries: int = 3
    verify_ssl: bool = True

class IntegrationTestBase:
    """Base class for all integration tests"""
    
    def __init__(self):
        self.config = TestConfig()
        self.session = None
        self.auth_token = None
    
    async def setup_session(self):
        """Setup HTTP session for tests"""
        self.session = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            verify=self.config.verify_ssl
        )
    
    async def teardown_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.aclose()
    
    async def authenticate(self, username: str = "test_user", password: str = "test_pass"):
        """Authenticate and get JWT token"""
        auth_data = {
            "username": username,
            "password": password
        }
        
        response = await self.session.post("/api/v1/auth/login", json=auth_data)
        if response.status_code == 200:
            token_data = response.json()
            self.auth_token = token_data["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
            return True
        return False
    
    async def make_request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """Make HTTP request with retry logic"""
        for attempt in range(self.config.max_retries):
            try:
                response = await self.session.request(method, endpoint, **kwargs)
                return response
            except httpx.RequestError as e:
                if attempt == self.config.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    def assert_response_success(self, response: httpx.Response, expected_status: int = 200):
        """Assert response is successful"""
        assert response.status_code == expected_status, (
            f"Expected status {expected_status}, got {response.status_code}. "
            f"Response: {response.text[:500]}"
        )
    
    def assert_response_contains(self, response: httpx.Response, *keys):
        """Assert response JSON contains specific keys"""
        data = response.json()
        for key in keys:
            assert key in data, f"Response missing key: {key}. Response: {data}"
    
    def assert_response_time(self, response: httpx.Response, max_time_ms: int = 2000):
        """Assert response time is within acceptable limits"""
        response_time_ms = response.elapsed.total_seconds() * 1000
        assert response_time_ms < max_time_ms, (
            f"Response time {response_time_ms}ms exceeds limit {max_time_ms}ms"
        )

@pytest.fixture(scope="session")
async def integration_test_base():
    """Pytest fixture for integration test base"""
    test_base = IntegrationTestBase()
    await test_base.setup_session()
    yield test_base
    await test_base.teardown_session()
```

### 1.2 Service Health and Connectivity Tests

```python
# testing/integration/test_service_health.py
import pytest
from .framework.test_base import IntegrationTestBase

class TestServiceHealth(IntegrationTestBase):
    """Test health endpoints for all services"""
    
    @pytest.mark.critical
    async def test_all_health_endpoints(self):
        """Test all service health endpoints"""
        health_endpoints = [
            "/api/v1/games/health",
            "/api/v1/orders/health", 
            "/api/v1/analytics/health"
        ]
        
        for endpoint in health_endpoints:
            response = await self.make_request("GET", endpoint)
            self.assert_response_success(response)
            self.assert_response_time(response, max_time_ms=1000)
            
            health_data = response.json()
            assert health_data["status"] == "healthy"
            assert "timestamp" in health_data
            assert "uptime_seconds" in health_data
    
    @pytest.mark.critical
    async def test_readiness_endpoints(self):
        """Test Kubernetes readiness probes"""
        readiness_endpoints = [
            "/api/v1/games/ready",
            "/api/v1/orders/ready",
            "/api/v1/analytics/ready"
        ]
        
        for endpoint in readiness_endpoints:
            response = await self.make_request("GET", endpoint)
            self.assert_response_success(response)
            
            ready_data = response.json()
            assert ready_data["status"] == "ready"
    
    @pytest.mark.critical
    async def test_database_connectivity(self):
        """Test database connectivity through service APIs"""
        # Test Game Service database
        response = await self.make_request("GET", "/api/v1/games/categories")
        self.assert_response_success(response)
        
        # Test Order Service database (requires auth)
        await self.authenticate()
        response = await self.make_request("GET", "/api/v1/orders")
        self.assert_response_success(response)
        
        # Test Analytics Service (ClickHouse)
        response = await self.make_request("GET", "/api/v1/analytics/metrics/realtime")
        self.assert_response_success(response)
```

### 1.3 Game Service Integration Tests

```python
# testing/integration/test_game_service.py
import pytest
from .framework.test_base import IntegrationTestBase

class TestGameServiceIntegration(IntegrationTestBase):
    """Integration tests for Game Service"""
    
    @pytest.mark.critical
    async def test_game_catalog_operations(self):
        """Test core game catalog functionality"""
        # Test get trending games
        response = await self.make_request("GET", "/api/v1/games/trending?limit=5")
        self.assert_response_success(response)
        self.assert_response_time(response, max_time_ms=1000)
        
        games_data = response.json()
        assert "games" in games_data
        assert len(games_data["games"]) <= 5
        
        for game in games_data["games"]:
            assert "id" in game
            assert "name" in game
            assert "price" in game
            assert "category" in game
    
    @pytest.mark.critical
    async def test_game_search_functionality(self):
        """Test game search and filtering"""
        # Test search by name
        response = await self.make_request("GET", "/api/v1/games/search?q=action")
        self.assert_response_success(response)
        
        search_data = response.json()
        assert "games" in search_data
        assert "total" in search_data
        assert "page" in search_data
        
        # Test category filtering
        response = await self.make_request("GET", "/api/v1/games?category=RPG")
        self.assert_response_success(response)
        
        # Test price filtering
        response = await self.make_request("GET", "/api/v1/games?min_price=10&max_price=50")
        self.assert_response_success(response)
    
    async def test_game_details_and_reviews(self):
        """Test game details and review functionality"""
        # Get a game first
        response = await self.make_request("GET", "/api/v1/games/trending?limit=1")
        games = response.json()["games"]
        if not games:
            pytest.skip("No games available for testing")
        
        game_id = games[0]["id"]
        
        # Test game details
        response = await self.make_request("GET", f"/api/v1/games/{game_id}")
        self.assert_response_success(response)
        
        game_details = response.json()
        assert game_details["id"] == game_id
        assert "name" in game_details
        assert "description" in game_details
        assert "images" in game_details
        
        # Test game reviews
        response = await self.make_request("GET", f"/api/v1/games/{game_id}/reviews")
        self.assert_response_success(response)
        
        reviews_data = response.json()
        assert "reviews" in reviews_data
        assert "average_rating" in reviews_data
    
    async def test_inventory_operations(self):
        """Test inventory management operations"""
        # Get a game for inventory testing
        response = await self.make_request("GET", "/api/v1/games/trending?limit=1")
        game_id = response.json()["games"][0]["id"]
        
        # Test inventory check
        response = await self.make_request("GET", f"/api/v1/games/{game_id}/inventory")
        self.assert_response_success(response)
        
        inventory_data = response.json()
        assert "available" in inventory_data
        assert "quantity" in inventory_data
        assert "in_stock" in inventory_data
```

### 1.4 Order Service Integration Tests

```python
# testing/integration/test_order_service.py
import pytest
from .framework.test_base import IntegrationTestBase
import time

class TestOrderServiceIntegration(IntegrationTestBase):
    """Integration tests for Order Service"""
    
    async def setup_method(self):
        """Setup for each test method"""
        await self.setup_session()
        
        # Create test user
        test_user_data = {
            "email": f"test_{int(time.time())}@example.com",
            "username": f"testuser_{int(time.time())}",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = await self.make_request("POST", "/api/v1/auth/register", json=test_user_data)
        if response.status_code == 201:
            self.test_user = test_user_data
            await self.authenticate(test_user_data["username"], test_user_data["password"])
    
    @pytest.mark.critical
    async def test_user_authentication_flow(self):
        """Test complete user authentication flow"""
        # Test registration (already done in setup)
        assert self.auth_token is not None
        
        # Test profile access
        response = await self.make_request("GET", "/api/v1/auth/profile")
        self.assert_response_success(response)
        
        profile_data = response.json()
        assert profile_data["email"] == self.test_user["email"]
        assert profile_data["username"] == self.test_user["username"]
        
        # Test token refresh
        response = await self.make_request("POST", "/api/v1/auth/refresh")
        self.assert_response_success(response)
        
        refresh_data = response.json()
        assert "access_token" in refresh_data
    
    @pytest.mark.critical
    async def test_shopping_cart_operations(self):
        """Test complete shopping cart workflow"""
        # Get available game
        response = await self.make_request("GET", "/api/v1/games/trending?limit=1")
        game = response.json()["games"][0]
        game_id = game["id"]
        
        # Test add to cart
        cart_item = {
            "game_id": game_id,
            "quantity": 1
        }
        
        response = await self.make_request("POST", "/api/v1/cart/add", json=cart_item)
        self.assert_response_success(response, expected_status=201)
        
        # Test get cart
        response = await self.make_request("GET", "/api/v1/cart")
        self.assert_response_success(response)
        
        cart_data = response.json()
        assert "items" in cart_data
        assert "total_amount" in cart_data
        assert len(cart_data["items"]) == 1
        assert cart_data["items"][0]["game_id"] == game_id
        
        # Test update cart item
        update_data = {"quantity": 2}
        cart_item_id = cart_data["items"][0]["id"]
        
        response = await self.make_request(
            "PUT", 
            f"/api/v1/cart/items/{cart_item_id}", 
            json=update_data
        )
        self.assert_response_success(response)
        
        # Test remove from cart
        response = await self.make_request("DELETE", f"/api/v1/cart/items/{cart_item_id}")
        self.assert_response_success(response, expected_status=204)
        
        # Verify cart is empty
        response = await self.make_request("GET", "/api/v1/cart")
        cart_data = response.json()
        assert len(cart_data["items"]) == 0
    
    @pytest.mark.critical
    async def test_order_processing_workflow(self):
        """Test complete order processing from cart to completion"""
        # Add item to cart
        response = await self.make_request("GET", "/api/v1/games/trending?limit=1")
        game = response.json()["games"][0]
        
        cart_item = {"game_id": game["id"], "quantity": 1}
        await self.make_request("POST", "/api/v1/cart/add", json=cart_item)
        
        # Create order from cart
        order_data = {
            "payment_method": "credit_card",
            "shipping_address": {
                "first_name": "Test",
                "last_name": "User",
                "address_line_1": "123 Test St",
                "city": "Test City",
                "state": "TS",
                "postal_code": "12345",
                "country": "US"
            }
        }
        
        response = await self.make_request("POST", "/api/v1/orders", json=order_data)
        self.assert_response_success(response, expected_status=201)
        
        order_response = response.json()
        assert "order_id" in order_response
        assert "order_number" in order_response
        assert "status" in order_response
        
        order_id = order_response["order_id"]
        
        # Test get order details
        response = await self.make_request("GET", f"/api/v1/orders/{order_id}")
        self.assert_response_success(response)
        
        order_details = response.json()
        assert order_details["id"] == order_id
        assert "items" in order_details
        assert "total_amount" in order_details
        assert order_details["status"] == "pending"
        
        # Test order status updates (simulate payment processing)
        status_update = {"status": "processing"}
        response = await self.make_request(
            "PATCH", 
            f"/api/v1/orders/{order_id}/status", 
            json=status_update
        )
        self.assert_response_success(response)
```

### 1.5 Analytics Service Integration Tests

```python
# testing/integration/test_analytics_service.py
import pytest
from .framework.test_base import IntegrationTestBase
import time
from datetime import datetime

class TestAnalyticsServiceIntegration(IntegrationTestBase):
    """Integration tests for Analytics Service"""
    
    @pytest.mark.critical
    async def test_event_ingestion_pipeline(self):
        """Test analytics event ingestion and storage"""
        # Test batch event submission
        events_batch = {
            "events": [
                {
                    "event_id": f"test_{int(time.time())}_1",
                    "event_type": "page_view",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "session_id": "test_session_123",
                    "page_url": "/test-page",
                    "page_title": "Test Page",
                    "user_agent": "Test Agent",
                    "viewport_width": 1920,
                    "viewport_height": 1080
                },
                {
                    "event_id": f"test_{int(time.time())}_2",
                    "event_type": "click",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "session_id": "test_session_123",
                    "page_url": "/test-page",
                    "element_type": "button",
                    "element_text": "Test Button",
                    "click_x": 100,
                    "click_y": 200
                }
            ]
        }
        
        response = await self.make_request(
            "POST", 
            "/api/v1/analytics/events/batch", 
            json=events_batch
        )
        self.assert_response_success(response, expected_status=201)
        
        batch_response = response.json()
        assert "events_processed" in batch_response
        assert batch_response["events_processed"] == 2
        assert "processing_time_ms" in batch_response
    
    async def test_real_time_analytics_queries(self):
        """Test real-time analytics data retrieval"""
        # Wait a moment for events to be processed
        await asyncio.sleep(2)
        
        # Test real-time metrics
        response = await self.make_request("GET", "/api/v1/analytics/metrics/realtime")
        self.assert_response_success(response)
        self.assert_response_time(response, max_time_ms=1000)
        
        metrics_data = response.json()
        assert "active_users" in metrics_data
        assert "page_views_per_minute" in metrics_data
        assert "events_per_minute" in metrics_data
        assert "timestamp" in metrics_data
    
    async def test_session_analytics(self):
        """Test session tracking and analytics"""
        # Start a session
        session_data = {
            "session_id": f"integration_test_{int(time.time())}",
            "user_agent": "Integration Test Agent",
            "screen_width": 1920,
            "screen_height": 1080,
            "initial_page": "/integration-test"
        }
        
        response = await self.make_request(
            "POST", 
            "/api/v1/analytics/session/start", 
            json=session_data
        )
        self.assert_response_success(response, expected_status=201)
        
        session_id = session_data["session_id"]
        
        # Submit some session events
        events = {
            "events": [
                {
                    "event_type": "page_view",
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "page_url": "/test-page-1"
                },
                {
                    "event_type": "page_view", 
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "page_url": "/test-page-2"
                }
            ]
        }
        
        await self.make_request("POST", "/api/v1/analytics/events/batch", json=events)
        
        # Wait for processing
        await asyncio.sleep(3)
        
        # Test get session journey
        response = await self.make_request(
            "GET", 
            f"/api/v1/analytics/journey/{session_id}"
        )
        self.assert_response_success(response)
        
        journey_data = response.json()
        assert "session_id" in journey_data
        assert "events" in journey_data
        assert len(journey_data["events"]) >= 2
        
        # End session
        end_session_data = {
            "session_duration": 120000,  # 2 minutes
            "total_page_views": 2,
            "total_interactions": 5
        }
        
        response = await self.make_request(
            "POST", 
            f"/api/v1/analytics/session/{session_id}/end", 
            json=end_session_data
        )
        self.assert_response_success(response)
    
    async def test_business_analytics_queries(self):
        """Test business metrics and analytics queries"""
        # Test conversion funnel data
        response = await self.make_request("GET", "/api/v1/analytics/funnel/default")
        self.assert_response_success(response)
        
        funnel_data = response.json()
        assert "steps" in funnel_data
        assert "conversion_rates" in funnel_data
        
        # Test popular content
        response = await self.make_request("GET", "/api/v1/analytics/content/popular?limit=10")
        self.assert_response_success(response)
        
        popular_data = response.json()
        assert "pages" in popular_data
        
        # Test user engagement metrics
        response = await self.make_request("GET", "/api/v1/analytics/engagement/summary")
        self.assert_response_success(response)
        
        engagement_data = response.json()
        assert "average_session_duration" in engagement_data
        assert "pages_per_session" in engagement_data
        assert "bounce_rate" in engagement_data
```

---

## 2. End-to-End User Journey Tests

### 2.1 Complete User Journey Test

```python
# testing/integration/test_user_journeys.py
import pytest
from .framework.test_base import IntegrationTestBase
import asyncio
import time

class TestCompleteUserJourneys(IntegrationTestBase):
    """Test complete user journeys from registration to purchase"""
    
    @pytest.mark.e2e
    async def test_complete_purchase_journey(self):
        """Test complete user journey: Register → Browse → Add to Cart → Purchase"""
        
        # Step 1: User Registration
        timestamp = int(time.time())
        user_data = {
            "email": f"journey_test_{timestamp}@example.com",
            "username": f"journey_user_{timestamp}",
            "password": "securepass123",
            "first_name": "Journey",
            "last_name": "Tester"
        }
        
        response = await self.make_request("POST", "/api/v1/auth/register", json=user_data)
        self.assert_response_success(response, expected_status=201)
        
        # Authenticate
        await self.authenticate(user_data["username"], user_data["password"])
        
        # Step 2: Browse Game Catalog
        response = await self.make_request("GET", "/api/v1/games/trending?limit=10")
        self.assert_response_success(response)
        
        games = response.json()["games"]
        assert len(games) > 0, "No games available for testing"
        
        selected_game = games[0]
        game_id = selected_game["id"]
        
        # View game details
        response = await self.make_request("GET", f"/api/v1/games/{game_id}")
        self.assert_response_success(response)
        
        # Step 3: Add Game to Cart
        cart_item = {
            "game_id": game_id,
            "quantity": 1
        }
        
        response = await self.make_request("POST", "/api/v1/cart/add", json=cart_item)
        self.assert_response_success(response, expected_status=201)
        
        # Verify cart contents
        response = await self.make_request("GET", "/api/v1/cart")
        cart_data = response.json()
        assert len(cart_data["items"]) == 1
        assert cart_data["items"][0]["game_id"] == game_id
        
        # Step 4: Complete Purchase
        order_data = {
            "payment_method": "credit_card",
            "shipping_address": {
                "first_name": "Journey",
                "last_name": "Tester",
                "address_line_1": "123 Integration Test St",
                "city": "Test City",
                "state": "TC",
                "postal_code": "12345",
                "country": "US"
            }
        }
        
        response = await self.make_request("POST", "/api/v1/orders", json=order_data)
        self.assert_response_success(response, expected_status=201)
        
        order = response.json()
        order_id = order["order_id"]
        
        # Step 5: Verify Order Details
        response = await self.make_request("GET", f"/api/v1/orders/{order_id}")
        self.assert_response_success(response)
        
        order_details = response.json()
        assert order_details["id"] == order_id
        assert len(order_details["items"]) == 1
        assert order_details["items"][0]["game_id"] == game_id
        assert order_details["status"] == "pending"
        
        # Step 6: Verify Cart is Cleared
        response = await self.make_request("GET", "/api/v1/cart")
        cart_data = response.json()
        assert len(cart_data["items"]) == 0
        
        # Step 7: Verify Analytics Events (optional, may need delay)
        await asyncio.sleep(2)  # Allow time for async event processing
        
        # This would verify that analytics events were captured
        # In a real scenario, you might check specific analytics endpoints
        
        return {
            "user_id": user_data["username"],
            "game_id": game_id,
            "order_id": order_id,
            "journey_status": "completed"
        }
    
    @pytest.mark.e2e
    async def test_guest_to_registered_user_journey(self):
        """Test guest user browsing then registering before purchase"""
        
        # Step 1: Browse as Guest
        response = await self.make_request("GET", "/api/v1/games/categories")
        self.assert_response_success(response)
        
        categories = response.json()["categories"]
        if categories:
            category_slug = categories[0]["slug"]
            
            # Browse category
            response = await self.make_request(
                "GET", 
                f"/api/v1/games?category={category_slug}&limit=5"
            )
            self.assert_response_success(response)
        
        # Step 2: Try to add to cart (should fail without auth)
        cart_item = {"game_id": 1, "quantity": 1}
        response = await self.make_request("POST", "/api/v1/cart/add", json=cart_item)
        assert response.status_code == 401, "Guest should not be able to add to cart"
        
        # Step 3: Register
        timestamp = int(time.time())
        user_data = {
            "email": f"guest_to_reg_{timestamp}@example.com",
            "username": f"guest_reg_{timestamp}",
            "password": "guestpass123"
        }
        
        response = await self.make_request("POST", "/api/v1/auth/register", json=user_data)
        self.assert_response_success(response, expected_status=201)
        
        # Step 4: Login and continue shopping
        await self.authenticate(user_data["username"], user_data["password"])
        
        # Now cart operations should work
        response = await self.make_request("POST", "/api/v1/cart/add", json=cart_item)
        self.assert_response_success(response, expected_status=201)
```

---

## 3. Performance and Load Testing

### 3.1 Load Testing with K6

```javascript
// testing/performance/load_test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics
let apiErrors = new Counter('api_errors');
let apiResponseTrend = new Trend('api_response_time');
let successRate = new Rate('success_rate');

export let options = {
  stages: [
    { duration: '2m', target: 50 },   // Ramp up to 50 users
    { duration: '5m', target: 100 }, // Stay at 100 users
    { duration: '3m', target: 200 }, // Ramp up to 200 users
    { duration: '5m', target: 200 }, // Stay at 200 users
    { duration: '2m', target: 0 },   // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<2000'], // 95% under 2s
    'success_rate': ['rate>0.95'],       // 95% success rate
    'api_errors': ['count<100'],         // Less than 100 errors
  },
};

const BASE_URL = __ENV.BASE_URL || 'https://api.lugxgaming.com';

export function setup() {
  // Setup phase - create test data if needed
  console.log('Starting load test setup...');
  return { timestamp: Date.now() };
}

export default function(data) {
  // Test scenarios based on user behavior patterns
  let scenario = Math.random();
  
  if (scenario < 0.4) {
    // 40% - Browse games
    testGameBrowsing();
  } else if (scenario < 0.7) {
    // 30% - Search functionality
    testGameSearch();
  } else if (scenario < 0.9) {
    // 20% - User interactions (requires auth)
    testUserInteractions();
  } else {
    // 10% - Analytics events
    testAnalyticsEvents();
  }
  
  sleep(Math.random() * 3 + 1); // Random sleep 1-4 seconds
}

function testGameBrowsing() {
  let response = http.get(`${BASE_URL}/api/v1/games/trending?limit=10`);
  
  check(response, {
    'trending games status is 200': (r) => r.status === 200,
    'trending games response time < 1s': (r) => r.timings.duration < 1000,
  });
  
  successRate.add(response.status === 200);
  apiResponseTrend.add(response.timings.duration);
  
  if (response.status !== 200) {
    apiErrors.add(1);
  }
  
  // Browse categories
  response = http.get(`${BASE_URL}/api/v1/games/categories`);
  check(response, {
    'categories status is 200': (r) => r.status === 200,
  });
  
  // View random game details
  if (response.status === 200) {
    let gameId = Math.floor(Math.random() * 100) + 1;
    response = http.get(`${BASE_URL}/api/v1/games/${gameId}`);
    
    check(response, {
      'game details response time < 1.5s': (r) => r.timings.duration < 1500,
    });
  }
}

function testGameSearch() {
  let searchTerms = ['action', 'rpg', 'strategy', 'adventure', 'simulation'];
  let term = searchTerms[Math.floor(Math.random() * searchTerms.length)];
  
  let response = http.get(`${BASE_URL}/api/v1/games/search?q=${term}&limit=20`);
  
  check(response, {
    'search status is 200': (r) => r.status === 200,
    'search response time < 2s': (r) => r.timings.duration < 2000,
  });
  
  successRate.add(response.status === 200);
  apiResponseTrend.add(response.timings.duration);
  
  if (response.status !== 200) {
    apiErrors.add(1);
  }
}

function testUserInteractions() {
  // Simulate user registration/login
  let timestamp = Date.now();
  let userData = {
    email: `loadtest_${timestamp}_${__VU}@example.com`,
    username: `loaduser_${timestamp}_${__VU}`,
    password: 'loadtest123'
  };
  
  // Register
  let response = http.post(`${BASE_URL}/api/v1/auth/register`, JSON.stringify(userData), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  if (response.status === 201) {
    // Login
    let loginData = {
      username: userData.username,
      password: userData.password
    };
    
    response = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify(loginData), {
      headers: { 'Content-Type': 'application/json' },
    });
    
    if (response.status === 200) {
      let token = response.json('access_token');
      let authHeaders = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };
      
      // Test cart operations
      let cartItem = { game_id: Math.floor(Math.random() * 50) + 1, quantity: 1 };
      response = http.post(`${BASE_URL}/api/v1/cart/add`, JSON.stringify(cartItem), {
        headers: authHeaders,
      });
      
      check(response, {
        'cart add operation successful': (r) => r.status === 201,
      });
      
      // Get cart
      response = http.get(`${BASE_URL}/api/v1/cart`, { headers: authHeaders });
      
      check(response, {
        'cart get operation successful': (r) => r.status === 200,
      });
    }
  }
}

function testAnalyticsEvents() {
  let events = {
    events: [
      {
        event_type: 'page_view',
        timestamp: new Date().toISOString(),
        session_id: `load_test_${__VU}_${Date.now()}`,
        page_url: '/load-test-page',
        user_agent: 'K6 Load Tester'
      }
    ]
  };
  
  let response = http.post(`${BASE_URL}/api/v1/analytics/events/batch`, JSON.stringify(events), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  check(response, {
    'analytics events status is 201': (r) => r.status === 201,
    'analytics events response time < 500ms': (r) => r.timings.duration < 500,
  });
  
  successRate.add(response.status === 201);
  apiResponseTrend.add(response.timings.duration);
  
  if (response.status !== 201) {
    apiErrors.add(1);
  }
}

export function teardown(data) {
  console.log('Load test completed');
  console.log(`Test duration: ${(Date.now() - data.timestamp) / 1000}s`);
}
```

### 3.2 Database Performance Testing

```python
# testing/performance/test_database_performance.py
import pytest
import asyncio
import time
from typing import List
from .framework.test_base import IntegrationTestBase

class TestDatabasePerformance(IntegrationTestBase):
    """Test database performance under load"""
    
    @pytest.mark.performance
    async def test_clickhouse_event_ingestion_performance(self):
        """Test ClickHouse can handle high-volume event ingestion"""
        
        # Generate batch of 1000 events
        events_batch = {
            "events": [
                {
                    "event_id": f"perf_test_{i}_{int(time.time())}",
                    "event_type": "page_view",
                    "timestamp": "2024-01-01T12:00:00.000Z",
                    "session_id": f"perf_session_{i % 100}",
                    "page_url": f"/perf-test-page-{i % 50}",
                    "user_agent": "Performance Test Agent"
                }
                for i in range(1000)
            ]
        }
        
        # Measure ingestion time
        start_time = time.time()
        response = await self.make_request(
            "POST", 
            "/api/v1/analytics/events/batch", 
            json=events_batch
        )
        end_time = time.time()
        
        self.assert_response_success(response, expected_status=201)
        
        processing_time = end_time - start_time
        events_per_second = 1000 / processing_time
        
        # Assert performance targets
        assert processing_time < 5.0, f"Batch processing took {processing_time:.2f}s, should be < 5s"
        assert events_per_second > 200, f"Processed {events_per_second:.2f} events/sec, should be > 200/sec"
        
        batch_response = response.json()
        assert batch_response["events_processed"] == 1000
    
    @pytest.mark.performance
    async def test_concurrent_api_requests(self):
        """Test API performance under concurrent load"""
        
        async def make_concurrent_request(endpoint: str, request_id: int):
            """Make a single request and measure performance"""
            start_time = time.time()
            try:
                response = await self.make_request("GET", endpoint)
                end_time = time.time()
                
                return {
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": response.status_code == 200
                }
            except Exception as e:
                return {
                    "request_id": request_id,
                    "status_code": 0,
                    "response_time": time.time() - start_time,
                    "success": False,
                    "error": str(e)
                }
        
        # Test endpoints
        endpoints = [
            "/api/v1/games/trending?limit=10",
            "/api/v1/games/categories",
            "/api/v1/analytics/metrics/realtime"
        ]
        
        # Create 50 concurrent requests for each endpoint
        tasks = []
        for endpoint in endpoints:
            for i in range(50):
                tasks.append(make_concurrent_request(endpoint, i))
        
        # Execute all requests concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Analyze results
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        success_rate = len(successful_requests) / len(results)
        avg_response_time = sum(r["response_time"] for r in successful_requests) / len(successful_requests)
        max_response_time = max(r["response_time"] for r in successful_requests)
        
        # Performance assertions
        assert success_rate >= 0.95, f"Success rate {success_rate:.2%} should be >= 95%"
        assert avg_response_time < 2.0, f"Average response time {avg_response_time:.2f}s should be < 2s"
        assert max_response_time < 5.0, f"Max response time {max_response_time:.2f}s should be < 5s"
        assert total_time < 10.0, f"Total test time {total_time:.2f}s should be < 10s"
        
        print(f"Concurrent test results:")
        print(f"  Total requests: {len(results)}")
        print(f"  Success rate: {success_rate:.2%}")
        print(f"  Failed requests: {len(failed_requests)}")
        print(f"  Average response time: {avg_response_time:.3f}s")
        print(f"  Max response time: {max_response_time:.3f}s")
        print(f"  Total test duration: {total_time:.2f}s")
```

---

## 4. Test Automation and CI/CD Integration

### 4.1 GitHub Actions Test Workflow

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 */4 * * *'  # Run every 4 hours

env:
  API_BASE_URL: http://localhost:8000
  CLICKHOUSE_URL: http://localhost:8123
  POSTGRES_URL: postgresql://test:test@localhost:5432/test_db

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_USER: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
      
      clickhouse:
        image: clickhouse/clickhouse-server:23.8
        ports:
          - 8123:8123
          - 9000:9000
        env:
          CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT: 1
    
    steps:
    - name: Checkout Code
      uses: actions/checkout@v4
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install Dependencies
      run: |
        pip install -r requirements.txt
        pip install -r testing/requirements.txt
    
    - name: Setup Test Databases
      run: |
        # Initialize PostgreSQL test data
        PGPASSWORD=test psql -h localhost -U test -d test_db -f testing/fixtures/test_schema.sql
        
        # Initialize ClickHouse test data
        curl -X POST 'http://localhost:8123/' --data-binary @testing/fixtures/clickhouse_schema.sql
    
    - name: Start Services in Background
      run: |
        # Start all microservices in background
        cd services/game-service && python -m uvicorn app.main:app --port 8001 &
        cd services/order-service && python -m uvicorn app.main:app --port 8002 &
        cd services/analytics-service && python -m uvicorn app.main:app --port 8003 &
        
        # Start API Gateway
        cd infrastructure/api-gateway && python -m uvicorn main:app --port 8000 &
        
        # Wait for services to start
        sleep 30
    
    - name: Health Check Services
      run: |
        curl -f http://localhost:8000/health || exit 1
        curl -f http://localhost:8001/api/v1/games/health || exit 1
        curl -f http://localhost:8002/api/v1/orders/health || exit 1
        curl -f http://localhost:8003/api/v1/analytics/health || exit 1
    
    - name: Run Critical Path Tests
      run: |
        cd testing/integration
        pytest test_service_health.py -v --tb=short -m critical
    
    - name: Run Service Integration Tests
      run: |
        cd testing/integration
        pytest test_game_service.py test_order_service.py test_analytics_service.py -v --tb=short
    
    - name: Run End-to-End Tests
      run: |
        cd testing/integration
        pytest test_user_journeys.py -v --tb=short -m e2e
    
    - name: Run Performance Tests
      run: |
        cd testing/integration
        pytest test_database_performance.py -v --tb=short -m performance
    
    - name: Generate Test Report
      if: always()
      run: |
        cd testing/integration
        pytest --html=../../reports/integration-test-report.html --self-contained-html
    
    - name: Upload Test Results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: integration-test-results
        path: |
          reports/integration-test-report.html
          testing/integration/test-results.xml

  load-testing:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Checkout Code
      uses: actions/checkout@v4
    
    - name: Setup K6
      run: |
        sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
        echo "deb https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
        sudo apt-get update
        sudo apt-get install k6
    
    - name: Run Load Tests
      env:
        BASE_URL: ${{ secrets.STAGING_URL }}
      run: |
        cd testing/performance
        k6 run --out json=load-test-results.json load_test.js
    
    - name: Upload Load Test Results
      uses: actions/upload-artifact@v3
      with:
        name: load-test-results
        path: testing/performance/load-test-results.json
```

### 4.2 Test Configuration and Fixtures

```python
# testing/conftest.py
import pytest
import asyncio
import os
from typing import AsyncGenerator
from httpx import AsyncClient

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def api_client() -> AsyncGenerator[AsyncClient, None]:
    """Create HTTP client for API testing"""
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    async with AsyncClient(
        base_url=base_url,
        timeout=30.0,
        verify=False
    ) as client:
        yield client

@pytest.fixture
async def authenticated_client(api_client: AsyncClient) -> AsyncClient:
    """Create authenticated HTTP client"""
    # Create test user
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass123"
    }
    
    # Register user (ignore if already exists)
    await api_client.post("/api/v1/auth/register", json=user_data)
    
    # Login
    response = await api_client.post("/api/v1/auth/login", json={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        api_client.headers.update({"Authorization": f"Bearer {token}"})
    
    return api_client

@pytest.fixture
def sample_game_data():
    """Sample game data for testing"""
    return {
        "name": "Test Game",
        "description": "A test game for integration testing",
        "price": 29.99,
        "category": "Action",
        "publisher": "Test Publisher",
        "release_date": "2024-01-01",
        "in_stock": True,
        "inventory_quantity": 100
    }

@pytest.fixture
def sample_analytics_events():
    """Sample analytics events for testing"""
    return {
        "events": [
            {
                "event_type": "page_view",
                "timestamp": "2024-01-01T12:00:00.000Z",
                "session_id": "test_session_123",
                "page_url": "/test-page",
                "page_title": "Test Page",
                "user_agent": "Test Agent"
            },
            {
                "event_type": "click",
                "timestamp": "2024-01-01T12:00:01.000Z",
                "session_id": "test_session_123",
                "page_url": "/test-page",
                "element_type": "button",
                "element_text": "Test Button",
                "click_x": 100,
                "click_y": 200
            }
        ]
    }

# Test markers
pytest.mark.critical = pytest.mark.create_marks("critical", "Critical path tests that must pass")
pytest.mark.e2e = pytest.mark.create_marks("e2e", "End-to-end user journey tests")
pytest.mark.performance = pytest.mark.create_marks("performance", "Performance and load tests")
pytest.mark.security = pytest.mark.create_marks("security", "Security validation tests")
```

This comprehensive integration test suite ensures thorough validation of all system components, user journeys, and performance characteristics, providing confidence in deployments and ongoing system reliability.