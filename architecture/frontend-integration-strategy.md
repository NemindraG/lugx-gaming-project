# Lugx Gaming Platform - Frontend Integration Strategy

## Executive Summary

This document outlines the comprehensive strategy for integrating the existing jQuery + Bootstrap frontend with the FastAPI backend services through Istio Gateway. The approach emphasizes progressive enhancement, preserving existing functionality while adding dynamic capabilities, ensuring zero disruption to current user experience.

## Integration Philosophy

### Core Principles
- **Preserve Existing Investment**: Maintain all current HTML, CSS, and JavaScript files without modification
- **Progressive Enhancement**: Add dynamic functionality on top of existing static content
- **Graceful Degradation**: Ensure static content remains functional when APIs fail
- **Performance First**: Minimize impact on page load times and user experience
- **Zero Breaking Changes**: No modifications to existing frontend codebase

### Technology Alignment
- **Frontend**: jQuery 3.6+ with Bootstrap 5 responsive design
- **API Layer**: Modern JavaScript ES6+ with Fetch API
- **Gateway**: Istio Gateway for centralized API access
- **Authentication**: JWT token management with localStorage
- **Analytics**: Event-driven tracking with batched API calls

---

## Architecture Overview

### Frontend Integration Architecture

```
Existing Frontend (Preserved)
├── index.html              # Homepage (no changes)
├── shop.html              # Game catalog (no changes)  
├── product-details.html   # Game details (no changes)
├── contact.html           # Contact page (no changes)
├── assets/
│   ├── css/               # Existing styles (unchanged)
│   ├── js/                # Existing functionality (unchanged)
│   └── images/            # Existing assets (unchanged)
└── ...

New Integration Layer (Added)
├── api/                   # NEW - API integration layer
│   ├── apiService.js      # Centralized HTTP client
│   ├── authService.js     # JWT authentication handling
│   └── analyticsService.js # Event tracking
├── integration/           # NEW - Progressive enhancement
│   ├── gameIntegration.js # Dynamic game data loading
│   ├── cartIntegration.js # Shopping cart functionality
│   └── userIntegration.js # User authentication flows
├── pages/                 # NEW - Missing pages
│   ├── login.html         # User login
│   ├── register.html      # User registration
│   └── cart.html          # Shopping cart
└── config/                # NEW - Configuration
    └── config.js          # API endpoints and settings
```

### Integration Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND BROWSER LAYER                                   │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                    Existing jQuery + Bootstrap Frontend                         │ │
│  │    index.html │ shop.html │ product-details.html │ contact.html               │ │
│  │                                                                                 │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐ │ │
│  │  │                    NEW: Additional Frontend Pages                           │ │ │
│  │  │    login.html │ register.html │ cart.html                                  │ │ │
│  │  └─────────────────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                                 │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐ │ │
│  │  │                  NEW: JavaScript API Integration Layer                      │ │ │
│  │  │   • Progressive Enhancement Modules                                         │ │ │
│  │  │   • Dynamic Content Loading                                                 │ │ │
│  │  │   • Event Tracking & Analytics                                              │ │ │
│  │  │   • Error Handling & Fallback                                               │ │ │
│  │  └─────────────────────────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                    HTTPS REST API Calls
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              ISTIO GATEWAY LAYER                                   │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                           Istio Gateway (Envoy)                                 │ │
│  │    SSL Termination │ Rate Limiting │ JWT Validation │ Request Routing           │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                           │                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                         Istio VirtualServices                                   │ │
│  │   /api/v1/games/* → Game Service │ /api/v1/auth/* → Order Service               │ │
│  │   /api/v1/cart/*  → Order Service │ /api/v1/analytics/* → Analytics Service     │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
                    ┌──────────────────────┼──────────────────────┐
                    │                      │                      │
                    ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            FASTAPI BACKEND SERVICES                                │
│                                                                                     │
│  ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐           │
│  │   Game Service  │      │  Order Service  │      │Analytics Service│           │
│  │    (FastAPI)    │      │    (FastAPI)    │      │    (FastAPI)    │           │
│  │                 │      │                 │      │                 │           │
│  │ • Game Catalog  │◄────►│ • User Auth     │      │ • Event Capture │           │
│  │ • Search/Filter │      │ • Shopping Cart │ ────►│ • Real-time     │           │
│  │ • Inventory     │      │ • Order Process │      │   Analytics     │           │
│  │ • Reviews       │      │ • Payment Sim   │      │ • BI Reports    │           │
│  └─────────────────┘      └─────────────────┘      └─────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Progressive Enhancement Strategy

### Phase 1: Foundation Layer Implementation

#### **API Service Infrastructure**

```javascript
// File: api/apiService.js
class APIService {
    constructor() {
        this.baseURL = 'https://lugxgaming.com/api/v1';
        this.timeout = 30000; // 30 seconds
        this.retryAttempts = 3;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        const config = {
            method: options.method || 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...this.getAuthHeaders(),
                ...options.headers
            },
            ...options
        };

        if (options.body && typeof options.body === 'object') {
            config.body = JSON.stringify(options.body);
        }

        // Implement retry logic with exponential backoff
        for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), this.timeout);
                
                config.signal = controller.signal;
                
                const response = await fetch(url, config);
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    throw new APIError(response.status, await this.extractErrorMessage(response));
                }
                
                return await response.json();
                
            } catch (error) {
                if (attempt === this.retryAttempts) {
                    console.error(`API request failed after ${this.retryAttempts} attempts:`, error);
                    throw error;
                }
                
                // Exponential backoff delay
                const delay = Math.pow(2, attempt - 1) * 1000;
                await this.delay(delay);
            }
        }
    }

    getAuthHeaders() {
        const token = authService.getToken();
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    }

    async extractErrorMessage(response) {
        try {
            const errorData = await response.json();
            return errorData.message || `HTTP ${response.status}`;
        } catch {
            return `HTTP ${response.status}`;
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Convenience methods
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url);
    }

    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: data
        });
    }

    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: data
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }
}

// Custom error class for API errors
class APIError extends Error {
    constructor(status, message) {
        super(message);
        this.name = 'APIError';
        this.status = status;
    }
}

// Global API service instance
const apiService = new APIService();
```

#### **Authentication Service**

```javascript
// File: api/authService.js
class AuthService {
    constructor() {
        this.tokenKey = 'lugx_auth_token';
        this.userKey = 'lugx_user_data';
        this.refreshKey = 'lugx_refresh_token';
    }

    setToken(token, refreshToken = null) {
        localStorage.setItem(this.tokenKey, token);
        if (refreshToken) {
            localStorage.setItem(this.refreshKey, refreshToken);
        }
    }

    getToken() {
        return localStorage.getItem(this.tokenKey);
    }

    getRefreshToken() {
        return localStorage.getItem(this.refreshKey);
    }

    removeTokens() {
        localStorage.removeItem(this.tokenKey);
        localStorage.removeItem(this.refreshKey);
        localStorage.removeItem(this.userKey);
    }

    setUser(userData) {
        localStorage.setItem(this.userKey, JSON.stringify(userData));
    }

    getUser() {
        const userData = localStorage.getItem(this.userKey);
        return userData ? JSON.parse(userData) : null;
    }

    isAuthenticated() {
        const token = this.getToken();
        if (!token) return false;
        
        try {
            // Decode JWT payload to check expiration
            const payload = JSON.parse(atob(token.split('.')[1]));
            const currentTime = Math.floor(Date.now() / 1000);
            
            // Check if token is expired (with 5 minute buffer)
            if (payload.exp && payload.exp < currentTime + 300) {
                return this.attemptTokenRefresh();
            }
            
            return true;
        } catch (error) {
            console.warn('Invalid token format:', error);
            this.removeTokens();
            return false;
        }
    }

    async attemptTokenRefresh() {
        const refreshToken = this.getRefreshToken();
        if (!refreshToken) {
            this.removeTokens();
            return false;
        }

        try {
            const response = await fetch(`${apiService.baseURL}/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${refreshToken}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.setToken(data.access_token, data.refresh_token);
                return true;
            } else {
                this.removeTokens();
                return false;
            }
        } catch (error) {
            console.warn('Token refresh failed:', error);
            this.removeTokens();
            return false;
        }
    }

    async logout() {
        try {
            // Attempt to invalidate token on server
            const token = this.getToken();
            if (token) {
                await apiService.post('/auth/logout');
            }
        } catch (error) {
            console.warn('Logout API call failed:', error);
        } finally {
            this.removeTokens();
            
            // Redirect to homepage or login page
            if (window.location.pathname !== '/index.html' && window.location.pathname !== '/') {
                window.location.href = 'index.html';
            } else {
                // Reload current page to reset UI state
                window.location.reload();
            }
        }
    }

    async login(email, password) {
        try {
            const response = await apiService.post('/auth/login', {
                email: email,
                password: password
            });

            this.setToken(response.access_token, response.refresh_token);
            this.setUser(response.user);

            return {
                success: true,
                user: response.user
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    async register(userData) {
        try {
            const response = await apiService.post('/auth/register', userData);

            this.setToken(response.access_token, response.refresh_token);
            this.setUser(response.user);

            return {
                success: true,
                user: response.user
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    requireAuth() {
        if (!this.isAuthenticated()) {
            const currentUrl = encodeURIComponent(window.location.href);
            window.location.href = `login.html?redirect=${currentUrl}`;
            return false;
        }
        return true;
    }
}

// Global auth service instance
const authService = new AuthService();
```

#### **Analytics Service**

```javascript
// File: api/analyticsService.js
class AnalyticsService {
    constructor() {
        this.eventQueue = [];
        this.batchSize = 50;
        this.flushInterval = 5000; // 5 seconds
        this.maxRetries = 3;
        this.retryDelay = 1000; // 1 second
        
        this.startBatchProcessor();
        this.setupPageUnloadHandler();
    }

    track(event, properties = {}) {
        const eventData = {
            event: event,
            properties: {
                ...properties,
                timestamp: new Date().toISOString(),
                page_url: window.location.href,
                page_title: document.title,
                referrer: document.referrer,
                user_agent: navigator.userAgent,
                viewport: {
                    width: window.innerWidth,
                    height: window.innerHeight
                },
                session_id: this.getSessionId()
            }
        };
        
        // Add user context if available
        const user = authService.getUser();
        if (user) {
            eventData.user_id = user.id;
            eventData.user_email = user.email;
        }
        
        // Add custom tracking attributes from URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has('utm_source')) {
            eventData.properties.utm_source = urlParams.get('utm_source');
        }
        if (urlParams.has('utm_campaign')) {
            eventData.properties.utm_campaign = urlParams.get('utm_campaign');
        }
        
        this.eventQueue.push(eventData);
        
        // Flush immediately for critical events
        if (this.isCriticalEvent(event)) {
            this.flush();
        }
    }

    async flush() {
        if (this.eventQueue.length === 0) return;
        
        const events = this.eventQueue.splice(0, this.batchSize);
        
        try {
            await apiService.post('/events/batch', { events });
            console.debug(`Successfully sent ${events.length} analytics events`);
        } catch (error) {
            console.warn('Analytics tracking failed:', error);
            
            // Re-queue events for retry (at the beginning)
            this.eventQueue.unshift(...events);
            
            // Implement exponential backoff for retries
            setTimeout(() => {
                if (this.eventQueue.length > 0) {
                    this.flush();
                }
            }, this.retryDelay);
        }
    }

    startBatchProcessor() {
        setInterval(() => {
            this.flush();
        }, this.flushInterval);
    }

    setupPageUnloadHandler() {
        // Flush events when user leaves the page
        window.addEventListener('beforeunload', () => {
            if (this.eventQueue.length > 0) {
                // Use sendBeacon for more reliable event sending on page unload
                const events = this.eventQueue.splice(0);
                navigator.sendBeacon(
                    `${apiService.baseURL}/events/batch`,
                    JSON.stringify({ events })
                );
            }
        });

        // Also flush on visibility change (when tab becomes hidden)
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'hidden' && this.eventQueue.length > 0) {
                this.flush();
            }
        });
    }

    isCriticalEvent(event) {
        const criticalEvents = [
            'add_to_cart', 
            'remove_from_cart', 
            'checkout_initiated', 
            'purchase_completed',
            'user_registration',
            'user_login'
        ];
        return criticalEvents.includes(event);
    }

    getSessionId() {
        let sessionId = sessionStorage.getItem('lugx_session_id');
        if (!sessionId) {
            sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            sessionStorage.setItem('lugx_session_id', sessionId);
        }
        return sessionId;
    }

    // Convenience methods for common events
    trackPageView() {
        this.track('pageview', {
            page_path: window.location.pathname,
            page_search: window.location.search,
            page_hash: window.location.hash
        });
    }

    trackClick(element, context = {}) {
        this.track('click', {
            element_type: element.tagName.toLowerCase(),
            element_text: element.textContent.trim().substring(0, 100),
            element_href: element.href || null,
            element_id: element.id || null,
            element_class: element.className || null,
            ...context
        });
    }

    trackError(error, context = {}) {
        this.track('error', {
            error_message: error.message,
            error_type: error.name,
            error_stack: error.stack ? error.stack.substring(0, 1000) : null,
            ...context
        });
    }

    trackPerformance() {
        // Track page load performance
        window.addEventListener('load', () => {
            setTimeout(() => {
                const perfData = performance.timing;
                this.track('performance', {
                    page_load_time: perfData.loadEventEnd - perfData.navigationStart,
                    dom_ready_time: perfData.domContentLoadedEventEnd - perfData.navigationStart,
                    first_byte_time: perfData.responseStart - perfData.navigationStart,
                    dns_lookup_time: perfData.domainLookupEnd - perfData.domainLookupStart,
                    connect_time: perfData.connectEnd - perfData.connectStart
                });
            }, 100);
        });
    }
}

// Global analytics service instance
const analyticsService = new AnalyticsService();

// Initialize performance tracking
analyticsService.trackPerformance();
```

### Phase 2: Page Enhancement Implementation

#### **Homepage Enhancement (index.html)**

```javascript
// File: integration/gameIntegration.js
class HomepageEnhancer {
    constructor() {
        this.isEnhanced = false;
        this.initializeEnhancements();
    }

    async initializeEnhancements() {
        // Only run on homepage
        if (!this.isHomepage()) return;

        try {
            // Track initial page view
            analyticsService.trackPageView();

            // Enhance different sections in parallel
            await Promise.allSettled([
                this.enhanceTrendingGamesSection(),
                this.enhanceMostPlayedSection(),
                this.enhanceNewsletterForm(),
                this.setupInteractionTracking()
            ]);

            this.isEnhanced = true;
            console.log('Homepage enhancement completed successfully');

        } catch (error) {
            console.warn('Homepage enhancement failed:', error);
            analyticsService.trackError(error, { context: 'homepage_enhancement' });
        }
    }

    isHomepage() {
        return window.location.pathname === '/' || 
               window.location.pathname === '/index.html' ||
               window.location.pathname.endsWith('/index.html');
    }

    async enhanceTrendingGamesSection() {
        const trendingContainer = document.querySelector('.trending-box .row');
        if (!trendingContainer) {
            console.warn('Trending games container not found');
            return;
        }

        try {
            // Show loading indicator
            this.showSectionLoading(trendingContainer, 'loading trending games...');

            // Fetch trending games from API
            const response = await apiService.get('/games/trending', { limit: 8 });

            // Replace static content with dynamic data
            await this.renderTrendingGames(response.games, trendingContainer);

            // Track successful enhancement
            analyticsService.track('section_enhanced', {
                section: 'trending_games',
                games_count: response.games.length
            });

        } catch (error) {
            console.warn('Failed to load trending games, keeping static content:', error);
            // Keep existing static content as fallback
            analyticsService.trackError(error, { context: 'trending_games_load' });
        } finally {
            this.hideSectionLoading(trendingContainer);
        }
    }

    async renderTrendingGames(games, container) {
        // Preserve existing Bootstrap classes and structure
        const gamesHTML = games.map(game => `
            <div class="col-lg-3 col-md-6 trending-item ${game.category.toLowerCase()}" data-game-id="${game.id}">
                <div class="item">
                    <div class="thumb">
                        <a href="product-details.html?id=${game.id}" data-track-click="game-card">
                            <img src="${game.image_url}" alt="${game.name}" loading="lazy">
                        </a>
                        <span class="price">
                            ${game.discount_price ? 
                                `<em>$${game.price}</em>$${game.discount_price}` : 
                                `$${game.price}`
                            }
                        </span>
                    </div>
                    <div class="down-content">
                        <span class="category">${game.category}</span>
                        <h4>${game.name}</h4>
                        <a href="product-details.html?id=${game.id}" data-track-click="explore-button">
                            <i class="fa fa-shopping-bag"></i>
                        </a>
                    </div>
                </div>
            </div>
        `).join('');

        // Smooth content transition
        container.style.opacity = '0.6';
        
        await new Promise(resolve => {
            setTimeout(() => {
                container.innerHTML = gamesHTML;
                container.style.opacity = '1';
                
                // Reinitialize existing Isotope filtering if present
                if (window.Isotope && document.querySelector('.trending-filter')) {
                    const iso = new Isotope(container, {
                        itemSelector: '.trending-item',
                        layoutMode: 'masonry'
                    });
                    
                    // Update filter functionality to work with new content
                    this.updateFilterButtons(iso);
                }
                
                resolve();
            }, 300);
        });
    }

    async enhanceMostPlayedSection() {
        const mostPlayedContainer = document.querySelector('.most-popular .row');
        if (!mostPlayedContainer) return;

        try {
            this.showSectionLoading(mostPlayedContainer, 'loading popular games...');

            const response = await apiService.get('/games/most-played', { limit: 6 });
            await this.renderMostPlayedGames(response.games, mostPlayedContainer);

            analyticsService.track('section_enhanced', {
                section: 'most_played_games',
                games_count: response.games.length
            });

        } catch (error) {
            console.warn('Failed to load most played games:', error);
            analyticsService.trackError(error, { context: 'most_played_load' });
        } finally {
            this.hideSectionLoading(mostPlayedContainer);
        }
    }

    async renderMostPlayedGames(games, container) {
        const gamesHTML = games.map(game => `
            <div class="col-lg-4 col-md-6 align-self-center mb-30" data-game-id="${game.id}">
                <div class="item">
                    <div class="thumb">
                        <a href="product-details.html?id=${game.id}" data-track-click="popular-game">
                            <img src="${game.image_url}" alt="${game.name}" loading="lazy">
                        </a>
                        <span class="price">
                            ${game.discount_price ? 
                                `<em>$${game.price}</em>$${game.discount_price}` : 
                                `$${game.price}`
                            }
                        </span>
                    </div>
                    <div class="down-content">
                        <span class="category">${game.category}</span>
                        <h4>${game.name}</h4>
                        <div class="rating">
                            ${'★'.repeat(Math.floor(game.rating))}${'☆'.repeat(5 - Math.floor(game.rating))}
                            <span class="rating-number">(${game.rating})</span>
                        </div>
                        <div class="main-button">
                            <a href="product-details.html?id=${game.id}">Explore</a>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        container.style.opacity = '0.6';
        setTimeout(() => {
            container.innerHTML = gamesHTML;
            container.style.opacity = '1';
        }, 300);
    }

    enhanceNewsletterForm() {
        const newsletterForm = document.querySelector('#newsletter-form, .newsletter form');
        if (!newsletterForm) return;

        newsletterForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const email = newsletterForm.querySelector('input[type="email"]').value;
            const name = newsletterForm.querySelector('input[name="name"]')?.value || '';

            try {
                this.showFormLoading(newsletterForm);

                await apiService.post('/newsletter/subscribe', {
                    email: email,
                    name: name
                });

                this.showSuccessMessage(newsletterForm, 'Successfully subscribed to newsletter!');
                newsletterForm.reset();

                analyticsService.track('newsletter_signup', { 
                    email_domain: email.split('@')[1] 
                });

            } catch (error) {
                let message = 'Subscription failed. Please try again.';
                
                if (error.status === 409) {
                    message = 'Email already subscribed to newsletter.';
                } else if (error.status === 400) {
                    message = 'Please enter a valid email address.';
                }

                this.showErrorMessage(newsletterForm, message);
                
                analyticsService.trackError(error, { 
                    context: 'newsletter_signup',
                    email_domain: email.split('@')[1]
                });
            } finally {
                this.hideFormLoading(newsletterForm);
            }
        });
    }

    setupInteractionTracking() {
        // Track game card clicks
        document.addEventListener('click', (e) => {
            const trackableElement = e.target.closest('[data-track-click]');
            if (trackableElement) {
                const trackType = trackableElement.dataset.trackClick;
                const gameCard = e.target.closest('[data-game-id]');
                const gameId = gameCard?.dataset.gameId;

                analyticsService.track('click', {
                    element_type: trackType,
                    game_id: gameId,
                    section: this.getElementSection(trackableElement)
                });
            }
        });

        // Track scroll depth
        this.setupScrollTracking();
    }

    setupScrollTracking() {
        let maxScrollDepth = 0;
        let scrollDepthMarkers = [25, 50, 75, 100];

        window.addEventListener('scroll', () => {
            const scrollPercent = Math.round(
                (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100
            );

            if (scrollPercent > maxScrollDepth) {
                maxScrollDepth = scrollPercent;

                // Track milestone scroll depths
                const milestone = scrollDepthMarkers.find(marker => 
                    scrollPercent >= marker && maxScrollDepth < marker + 1
                );

                if (milestone) {
                    analyticsService.track('scroll_depth', {
                        page: 'homepage',
                        depth_percent: milestone
                    });
                }
            }
        });
    }

    getElementSection(element) {
        if (element.closest('.trending-box')) return 'trending';
        if (element.closest('.most-popular')) return 'most_popular';
        if (element.closest('.newsletter')) return 'newsletter';
        return 'unknown';
    }

    showSectionLoading(container, message) {
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'loading-overlay';
        loadingOverlay.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner-border text-primary" role="status">
                    <span class="sr-only">Loading...</span>
                </div>
                <div class="loading-text mt-2">${message}</div>
            </div>
        `;
        loadingOverlay.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 255, 255, 0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            border-radius: 8px;
        `;

        container.style.position = 'relative';
        container.appendChild(loadingOverlay);
    }

    hideSectionLoading(container) {
        const loadingOverlay = container.querySelector('.loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.remove();
        }
    }

    showFormLoading(form) {
        const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.dataset.originalText = submitButton.textContent;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Subscribing...';
        }
    }

    hideFormLoading(form) {
        const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.textContent = submitButton.dataset.originalText || 'Subscribe';
        }
    }

    showSuccessMessage(form, message) {
        this.showMessage(form, message, 'alert-success');
    }

    showErrorMessage(form, message) {
        this.showMessage(form, message, 'alert-danger');
    }

    showMessage(form, message, alertClass) {
        // Remove existing messages
        const existingAlert = form.querySelector('.alert');
        if (existingAlert) {
            existingAlert.remove();
        }

        const alertDiv = document.createElement('div');
        alertDiv.className = `alert ${alertClass} mt-3`;
        alertDiv.textContent = message;

        form.appendChild(alertDiv);

        // Auto-remove success messages after 5 seconds
        if (alertClass === 'alert-success') {
            setTimeout(() => {
                alertDiv.remove();
            }, 5000);
        }
    }

    updateFilterButtons(isotopeInstance) {
        const filterButtons = document.querySelectorAll('.trending-filter a');
        
        filterButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                
                const filterValue = button.dataset.filter;
                isotopeInstance.arrange({ filter: filterValue });
                
                // Update active state
                document.querySelector('.trending-filter .is_active').classList.remove('is_active');
                button.classList.add('is_active');
                
                // Track filter usage
                analyticsService.track('filter_applied', {
                    filter_type: 'category',
                    filter_value: filterValue,
                    page: 'homepage'
                });
            });
        });
    }
}

// Initialize homepage enhancement when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new HomepageEnhancer();
});
```

### Phase 3: E-commerce Functionality

#### **Shopping Cart Integration**

```javascript
// File: integration/cartIntegration.js
class CartIntegration {
    constructor() {
        this.cartState = {
            items: [],
            total: 0,
            count: 0
        };
        
        this.initializeCart();
    }

    async initializeCart() {
        try {
            // Load cart state if user is authenticated
            if (authService.isAuthenticated()) {
                await this.loadCartFromServer();
            } else {
                // Load cart from localStorage for guest users
                this.loadCartFromLocalStorage();
            }

            this.setupCartUI();
            this.setupEventListeners();
            this.updateCartDisplay();

        } catch (error) {
            console.warn('Cart initialization failed:', error);
            analyticsService.trackError(error, { context: 'cart_initialization' });
        }
    }

    async loadCartFromServer() {
        try {
            const response = await apiService.get('/cart');
            this.cartState = {
                items: response.items || [],
                total: response.total || 0,
                count: response.total_items || 0
            };
        } catch (error) {
            if (error.status === 401) {
                // User session expired, clear local auth and reload
                authService.removeTokens();
                this.loadCartFromLocalStorage();
            } else {
                throw error;
            }
        }
    }

    loadCartFromLocalStorage() {
        const savedCart = localStorage.getItem('lugx_guest_cart');
        if (savedCart) {
            try {
                this.cartState = JSON.parse(savedCart);
            } catch (error) {
                console.warn('Invalid cart data in localStorage:', error);
                this.cartState = { items: [], total: 0, count: 0 };
            }
        }
    }

    saveCartToLocalStorage() {
        localStorage.setItem('lugx_guest_cart', JSON.stringify(this.cartState));
    }

    setupCartUI() {
        // Add cart badge to navigation if it doesn't exist
        const nav = document.querySelector('.navbar, .header-area nav');
        if (nav && !document.querySelector('.cart-badge')) {
            const cartHTML = `
                <div class="cart-widget">
                    <a href="cart.html" class="cart-link" data-track-click="cart-icon">
                        <i class="fa fa-shopping-cart"></i>
                        <span class="cart-badge">0</span>
                    </a>
                </div>
            `;
            
            // Insert cart widget into navigation
            const navList = nav.querySelector('ul');
            if (navList) {
                const cartLi = document.createElement('li');
                cartLi.innerHTML = cartHTML;
                navList.appendChild(cartLi);
            }
        }
    }

    setupEventListeners() {
        // Listen for add to cart button clicks
        document.addEventListener('click', async (e) => {
            if (e.target.matches('.add-to-cart, [data-action="add-to-cart"]')) {
                e.preventDefault();
                await this.handleAddToCart(e.target);
            }
        });

        // Listen for cart removal actions
        document.addEventListener('click', async (e) => {
            if (e.target.matches('.remove-from-cart, [data-action="remove-from-cart"]')) {
                e.preventDefault();
                await this.handleRemoveFromCart(e.target);
            }
        });

        // Sync cart when user logs in
        document.addEventListener('userLoggedIn', async () => {
            await this.syncGuestCartToServer();
        });
    }

    async handleAddToCart(button) {
        const gameId = this.extractGameId(button);
        const quantity = parseInt(button.dataset.quantity) || 1;

        if (!gameId) {
            console.warn('No game ID found for add to cart action');
            return;
        }

        try {
            this.showButtonLoading(button);

            if (authService.isAuthenticated()) {
                await this.addToServerCart(gameId, quantity);
            } else {
                await this.addToGuestCart(gameId, quantity);
            }

            this.showAddToCartSuccess(button);
            this.updateCartDisplay();

            analyticsService.track('add_to_cart', {
                game_id: gameId,
                quantity: quantity,
                cart_total: this.cartState.total,
                user_type: authService.isAuthenticated() ? 'authenticated' : 'guest'
            });

        } catch (error) {
            this.showAddToCartError(button, error);
            analyticsService.trackError(error, { 
                context: 'add_to_cart',
                game_id: gameId
            });
        } finally {
            this.hideButtonLoading(button);
        }
    }

    async addToServerCart(gameId, quantity) {
        const response = await apiService.post('/cart/items', {
            game_id: gameId,
            quantity: quantity
        });

        // Update local cart state
        await this.loadCartFromServer();
        return response;
    }

    async addToGuestCart(gameId, quantity) {
        // For guest users, we need to get game details first
        const gameDetails = await apiService.get(`/games/${gameId}`);
        
        // Check if item already exists in cart
        const existingItem = this.cartState.items.find(item => item.game_id === gameId);
        
        if (existingItem) {
            existingItem.quantity += quantity;
            existingItem.subtotal = existingItem.quantity * existingItem.price;
        } else {
            const newItem = {
                id: `guest_${Date.now()}_${gameId}`,
                game_id: gameId,
                game_name: gameDetails.name,
                price: gameDetails.discount_price || gameDetails.price,
                quantity: quantity,
                subtotal: (gameDetails.discount_price || gameDetails.price) * quantity,
                image_url: gameDetails.image_url
            };
            this.cartState.items.push(newItem);
        }

        // Recalculate totals
        this.recalculateCartTotals();
        this.saveCartToLocalStorage();
    }

    async handleRemoveFromCart(button) {
        const itemId = button.dataset.itemId;
        
        if (!itemId) {
            console.warn('No item ID found for remove action');
            return;
        }

        try {
            if (authService.isAuthenticated()) {
                await apiService.delete(`/cart/items/${itemId}`);
                await this.loadCartFromServer();
            } else {
                this.cartState.items = this.cartState.items.filter(item => item.id !== itemId);
                this.recalculateCartTotals();
                this.saveCartToLocalStorage();
            }

            this.updateCartDisplay();

            analyticsService.track('remove_from_cart', {
                item_id: itemId,
                cart_total: this.cartState.total
            });

        } catch (error) {
            console.error('Failed to remove item from cart:', error);
            analyticsService.trackError(error, { 
                context: 'remove_from_cart',
                item_id: itemId
            });
        }
    }

    async syncGuestCartToServer() {
        if (this.cartState.items.length === 0) return;

        try {
            // Add guest cart items to server cart
            for (const item of this.cartState.items) {
                await apiService.post('/cart/items', {
                    game_id: item.game_id,
                    quantity: item.quantity
                });
            }

            // Clear guest cart
            this.cartState = { items: [], total: 0, count: 0 };
            localStorage.removeItem('lugx_guest_cart');

            // Load synchronized cart from server
            await this.loadCartFromServer();
            this.updateCartDisplay();

            analyticsService.track('cart_synced', {
                synced_items: this.cartState.items.length
            });

        } catch (error) {
            console.warn('Failed to sync guest cart to server:', error);
            analyticsService.trackError(error, { context: 'cart_sync' });
        }
    }

    recalculateCartTotals() {
        this.cartState.total = this.cartState.items.reduce((total, item) => total + item.subtotal, 0);
        this.cartState.count = this.cartState.items.reduce((count, item) => count + item.quantity, 0);
    }

    updateCartDisplay() {
        const cartBadge = document.querySelector('.cart-badge');
        if (cartBadge) {
            cartBadge.textContent = this.cartState.count;
            cartBadge.style.display = this.cartState.count > 0 ? 'inline-block' : 'none';
        }

        // Update mini cart if it exists
        const miniCart = document.querySelector('.mini-cart');
        if (miniCart) {
            this.renderMiniCart(miniCart);
        }
    }

    renderMiniCart(container) {
        if (this.cartState.items.length === 0) {
            container.innerHTML = '<p class="empty-cart">Your cart is empty</p>';
            return;
        }

        const itemsHTML = this.cartState.items.slice(0, 3).map(item => `
            <div class="mini-cart-item">
                <img src="${item.image_url}" alt="${item.game_name}" class="item-image">
                <div class="item-details">
                    <h6>${item.game_name}</h6>
                    <span class="price">$${item.price} × ${item.quantity}</span>
                </div>
            </div>
        `).join('');

        const moreItems = this.cartState.items.length > 3 ? 
            `<p class="more-items">+${this.cartState.items.length - 3} more items</p>` : '';

        container.innerHTML = `
            ${itemsHTML}
            ${moreItems}
            <div class="mini-cart-footer">
                <div class="total">Total: $${this.cartState.total.toFixed(2)}</div>
                <a href="cart.html" class="btn btn-primary btn-sm">View Cart</a>
            </div>
        `;
    }

    extractGameId(element) {
        // Try multiple ways to get game ID
        return element.dataset.gameId || 
               element.closest('[data-game-id]')?.dataset.gameId ||
               new URLSearchParams(window.location.search).get('id');
    }

    showButtonLoading(button) {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Adding...';
    }

    hideButtonLoading(button) {
        button.disabled = false;
        button.textContent = button.dataset.originalText || 'Add to Cart';
    }

    showAddToCartSuccess(button) {
        const originalText = button.textContent;
        button.textContent = 'Added!';
        button.classList.add('btn-success');
        
        setTimeout(() => {
            button.textContent = originalText;
            button.classList.remove('btn-success');
        }, 2000);
    }

    showAddToCartError(button, error) {
        let message = 'Failed to add';
        
        if (error.status === 401) {
            message = 'Login required';
        } else if (error.status === 409) {
            message = 'Already in cart';
        } else if (error.status === 400) {
            message = 'Invalid selection';
        }

        const originalText = button.textContent;
        button.textContent = message;
        button.classList.add('btn-danger');
        
        setTimeout(() => {
            button.textContent = originalText;
            button.classList.remove('btn-danger');
        }, 3000);
    }
}

// Initialize cart integration when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.cartIntegration = new CartIntegration();
});
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
1. **API Service Layer Setup**
   - Implement centralized API client
   - Add authentication service
   - Create analytics tracking service
   - Set up error handling and retry logic

2. **Basic Integration Testing**
   - Test API connectivity through Istio Gateway
   - Verify JWT authentication flow
   - Validate analytics event collection
   - Test error handling and fallback mechanisms

### Phase 2: Homepage Enhancement (Week 2-3)
1. **Progressive Enhancement Implementation**
   - Dynamic trending games loading
   - Most played games integration
   - Newsletter subscription enhancement
   - User interaction tracking

2. **Performance Optimization**
   - Lazy loading for images
   - Async loading for non-critical sections
   - Caching strategy implementation
   - Loading state management

### Phase 3: E-commerce Integration (Week 3-4)
1. **Shopping Cart Functionality**
   - Add to cart integration
   - Guest cart management
   - Cart synchronization for logged-in users
   - Cart persistence across sessions

2. **User Authentication Flow**
   - Login/register page creation
   - Authentication state management
   - Redirect handling after login
   - Token refresh implementation

### Phase 4: Advanced Features (Week 4-5)
1. **Search and Discovery**
   - Shop page enhancement
   - Real-time search implementation
   - Category filtering
   - Pagination with URL state

2. **Product Details Enhancement**
   - Dynamic product information
   - Reviews and ratings system
   - Related products recommendations
   - Enhanced add to cart functionality

### Phase 5: Testing and Optimization (Week 5-6)
1. **Cross-browser Testing**
   - Chrome, Firefox, Safari, Edge compatibility
   - Mobile responsive testing
   - Performance testing
   - Accessibility compliance

2. **Analytics and Monitoring**
   - User behavior analysis
   - Performance monitoring
   - Error tracking and alerting
   - Conversion funnel optimization

---

## Testing Strategy

### Unit Testing
```javascript
// Example test for API service
describe('APIService', () => {
    test('should handle successful API calls', async () => {
        // Mock successful response
        global.fetch = jest.fn(() =>
            Promise.resolve({
                ok: true,
                json: () => Promise.resolve({ data: 'test' })
            })
        );

        const result = await apiService.get('/test');
        expect(result).toEqual({ data: 'test' });
        expect(fetch).toHaveBeenCalledWith(
            'https://lugxgaming.com/api/v1/test',
            expect.objectContaining({
                method: 'GET'
            })
        );
    });

    test('should handle API errors with retry', async () => {
        // Mock failed response
        global.fetch = jest.fn(() =>
            Promise.resolve({
                ok: false,
                status: 500,
                json: () => Promise.resolve({ message: 'Server error' })
            })
        );

        await expect(apiService.get('/test')).rejects.toThrow('Server error');
        expect(fetch).toHaveBeenCalledTimes(3); // Retry logic
    });
});
```

### Integration Testing
```javascript
// Example integration test
describe('Homepage Enhancement', () => {
    test('should enhance trending games section', async () => {
        // Mock API response
        const mockGames = [
            { id: 1, name: 'Test Game', price: 29.99, category: 'Action' }
        ];
        
        jest.spyOn(apiService, 'get').mockResolvedValue({ games: mockGames });

        // Setup DOM
        document.body.innerHTML = `
            <div class="trending-box">
                <div class="row"></div>
            </div>
        `;

        const enhancer = new HomepageEnhancer();
        await enhancer.enhanceTrendingGamesSection();

        // Verify DOM updates
        const gameElements = document.querySelectorAll('[data-game-id]');
        expect(gameElements).toHaveLength(1);
        expect(gameElements[0].textContent).toContain('Test Game');
    });
});
```

### End-to-End Testing
```javascript
// Example E2E test with Playwright
test('complete user journey', async ({ page }) => {
    // Navigate to homepage
    await page.goto('https://lugxgaming.com');

    // Wait for dynamic content to load
    await page.waitForSelector('[data-game-id]');

    // Click on a game
    await page.click('[data-game-id="1"] a');

    // Should navigate to product details
    await expect(page).toHaveURL(/.*product-details\.html\?id=1/);

    // Add to cart
    await page.click('.add-to-cart');

    // Verify cart badge updates
    await expect(page.locator('.cart-badge')).toHaveText('1');

    // Check analytics tracking
    const analyticsEvents = await page.evaluate(() => 
        window.analyticsService.eventQueue
    );
    expect(analyticsEvents).toContainEqual(
        expect.objectContaining({
            event: 'add_to_cart',
            properties: expect.objectContaining({
                game_id: '1'
            })
        })
    );
});
```

---

## Performance Considerations

### Loading Optimization
```javascript
// Lazy loading implementation
class LazyLoader {
    constructor() {
        this.imageObserver = new IntersectionObserver(this.handleImageIntersection);
        this.contentObserver = new IntersectionObserver(this.handleContentIntersection);
    }

    handleImageIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                this.imageObserver.unobserve(img);
            }
        });
    }

    handleContentIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const element = entry.target;
                const enhancer = element.dataset.enhancer;
                
                if (enhancer && window[enhancer]) {
                    window[enhancer].enhance(element);
                    this.contentObserver.unobserve(element);
                }
            }
        });
    }

    observeImages() {
        document.querySelectorAll('img[data-src]').forEach(img => {
            this.imageObserver.observe(img);
        });
    }

    observeContent() {
        document.querySelectorAll('[data-enhancer]').forEach(element => {
            this.contentObserver.observe(element);
        });
    }
}

// Initialize lazy loading
const lazyLoader = new LazyLoader();
document.addEventListener('DOMContentLoaded', () => {
    lazyLoader.observeImages();
    lazyLoader.observeContent();
});
```

### Caching Strategy
```javascript
// Intelligent caching for API responses
class APICache {
    constructor() {
        this.cache = new Map();
        this.cacheConfig = {
            '/games/trending': { ttl: 15 * 60 * 1000 }, // 15 minutes
            '/games/most-played': { ttl: 30 * 60 * 1000 }, // 30 minutes
            '/categories': { ttl: 60 * 60 * 1000 }, // 1 hour
            '/games/': { ttl: 5 * 60 * 1000 } // 5 minutes for individual games
        };
    }

    get(key) {
        const cached = this.cache.get(key);
        if (!cached) return null;

        const now = Date.now();
        if (now > cached.expires) {
            this.cache.delete(key);
            return null;
        }

        return cached.data;
    }

    set(key, data) {
        const config = this.getCacheConfig(key);
        if (!config) return; // Don't cache if no config

        const expires = Date.now() + config.ttl;
        this.cache.set(key, { data, expires });

        // Periodic cleanup
        if (this.cache.size > 100) {
            this.cleanup();
        }
    }

    getCacheConfig(key) {
        return Object.entries(this.cacheConfig)
            .find(([pattern]) => key.includes(pattern))?.[1];
    }

    cleanup() {
        const now = Date.now();
        for (const [key, value] of this.cache.entries()) {
            if (now > value.expires) {
                this.cache.delete(key);
            }
        }
    }
}

// Integrate caching with API service
const apiCache = new APICache();

// Modify API service to use cache
const originalGet = apiService.get;
apiService.get = async function(endpoint, params = {}) {
    const cacheKey = endpoint + JSON.stringify(params);
    
    // Try cache first
    const cached = apiCache.get(cacheKey);
    if (cached) {
        return cached;
    }

    // Fetch from API
    const result = await originalGet.call(this, endpoint, params);
    
    // Cache the result
    apiCache.set(cacheKey, result);
    
    return result;
};
```

---

## Monitoring and Analytics

### Performance Monitoring
```javascript
// Performance monitoring service
class PerformanceMonitor {
    constructor() {
        this.metrics = {};
        this.startTime = performance.now();
        this.setupPerformanceObserver();
    }

    setupPerformanceObserver() {
        // Monitor page load performance
        window.addEventListener('load', () => {
            setTimeout(() => this.collectPageLoadMetrics(), 0);
        });

        // Monitor API calls
        this.interceptFetch();

        // Monitor user interactions
        this.monitorInteractions();
    }

    collectPageLoadMetrics() {
        const perfData = performance.timing;
        const navigation = performance.getEntriesByType('navigation')[0];

        const metrics = {
            page_load_time: perfData.loadEventEnd - perfData.navigationStart,
            dom_ready_time: perfData.domContentLoadedEventEnd - perfData.navigationStart,
            first_byte_time: perfData.responseStart - perfData.navigationStart,
            dns_lookup_time: perfData.domainLookupEnd - perfData.domainLookupStart,
            connect_time: perfData.connectEnd - perfData.connectStart,
            download_time: perfData.responseEnd - perfData.responseStart,
            dom_interactive_time: perfData.domInteractive - perfData.navigationStart,
            load_event_time: perfData.loadEventEnd - perfData.loadEventStart
        };

        // Add Core Web Vitals if available
        if (navigation) {
            metrics.transfer_size = navigation.transferSize;
            metrics.encoded_body_size = navigation.encodedBodySize;
            metrics.decoded_body_size = navigation.decodedBodySize;
        }

        analyticsService.track('performance_metrics', metrics);
    }

    interceptFetch() {
        const originalFetch = window.fetch;
        
        window.fetch = async function(...args) {
            const startTime = performance.now();
            const url = args[0];
            
            try {
                const response = await originalFetch.apply(this, args);
                const endTime = performance.now();
                
                analyticsService.track('api_performance', {
                    url: url,
                    method: args[1]?.method || 'GET',
                    duration: endTime - startTime,
                    status: response.status,
                    success: response.ok
                });
                
                return response;
            } catch (error) {
                const endTime = performance.now();
                
                analyticsService.track('api_performance', {
                    url: url,
                    method: args[1]?.method || 'GET',
                    duration: endTime - startTime,
                    error: error.message,
                    success: false
                });
                
                throw error;
            }
        };
    }

    monitorInteractions() {
        // Monitor click responsiveness
        document.addEventListener('click', (e) => {
            const startTime = performance.now();
            
            // Use requestAnimationFrame to measure to next paint
            requestAnimationFrame(() => {
                const endTime = performance.now();
                const interactionTime = endTime - startTime;
                
                if (interactionTime > 100) { // More than 100ms is concerning
                    analyticsService.track('slow_interaction', {
                        element: e.target.tagName.toLowerCase(),
                        element_id: e.target.id,
                        element_class: e.target.className,
                        interaction_time: interactionTime
                    });
                }
            });
        });
    }

    trackCustomMetric(name, value, unit = 'ms') {
        this.metrics[name] = { value, unit, timestamp: Date.now() };
        
        analyticsService.track('custom_metric', {
            metric_name: name,
            metric_value: value,
            metric_unit: unit
        });
    }
}

// Initialize performance monitoring
const performanceMonitor = new PerformanceMonitor();
```

### Error Tracking
```javascript
// Global error tracking
class ErrorTracker {
    constructor() {
        this.setupGlobalErrorHandlers();
        this.setupUnhandledRejectionHandler();
        this.errorQueue = [];
        this.maxErrors = 50;
    }

    setupGlobalErrorHandlers() {
        window.addEventListener('error', (event) => {
            this.trackError({
                type: 'javascript_error',
                message: event.message,
                filename: event.filename,
                line: event.lineno,
                column: event.colno,
                stack: event.error?.stack,
                user_agent: navigator.userAgent,
                url: window.location.href
            });
        });

        window.addEventListener('unhandledrejection', (event) => {
            this.trackError({
                type: 'unhandled_promise_rejection',
                message: event.reason?.message || 'Unhandled promise rejection',
                stack: event.reason?.stack,
                user_agent: navigator.userAgent,
                url: window.location.href
            });
        });
    }

    trackError(errorData) {
        // Add timestamp and session info
        const enrichedError = {
            ...errorData,
            timestamp: new Date().toISOString(),
            session_id: analyticsService.getSessionId(),
            user_id: authService.getUser()?.id
        };

        // Add to queue
        this.errorQueue.push(enrichedError);

        // Keep queue size manageable
        if (this.errorQueue.length > this.maxErrors) {
            this.errorQueue.shift();
        }

        // Send to analytics immediately for critical errors
        analyticsService.track('error', enrichedError);

        // Also log to console for development
        if (process.env.NODE_ENV === 'development') {
            console.error('Tracked error:', enrichedError);
        }
    }

    getErrorSummary() {
        return {
            total_errors: this.errorQueue.length,
            error_types: this.errorQueue.reduce((acc, error) => {
                acc[error.type] = (acc[error.type] || 0) + 1;
                return acc;
            }, {}),
            recent_errors: this.errorQueue.slice(-5)
        };
    }
}

// Initialize error tracking
const errorTracker = new ErrorTracker();
```

---

## Security Considerations

### Content Security Policy
```html
<!-- Add to HTML head section -->
<meta http-equiv="Content-Security-Policy" content="
    default-src 'self';
    script-src 'self' 'unsafe-inline' https://lugxgaming.com;
    style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
    img-src 'self' data: https:;
    connect-src 'self' https://lugxgaming.com;
    font-src 'self' https://fonts.gstatic.com;
    frame-src 'none';
    object-src 'none';
    base-uri 'self';
    form-action 'self';
">
```

### XSS Prevention
```javascript
// Utility function for safe HTML insertion
function sanitizeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// Safe template rendering
function renderGameCard(game) {
    return `
        <div class="game-card" data-game-id="${sanitizeHTML(game.id)}">
            <h4>${sanitizeHTML(game.name)}</h4>
            <p>${sanitizeHTML(game.description)}</p>
            <span class="price">$${sanitizeHTML(game.price)}</span>
        </div>
    `;
}

// Input validation for forms
function validateInput(input, type) {
    const validators = {
        email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
        phone: /^\+?[\d\s\-\(\)]+$/,
        text: /^[a-zA-Z0-9\s\-_.,!?]+$/
    };

    const validator = validators[type];
    if (!validator) return false;

    return validator.test(input.trim());
}
```

### Authentication Security
```javascript
// Secure token handling
class SecureTokenManager {
    constructor() {
        this.tokenKey = 'lugx_auth_token';
        this.maxTokenAge = 24 * 60 * 60 * 1000; // 24 hours
    }

    setToken(token) {
        // Validate token format
        if (!this.isValidJWT(token)) {
            throw new Error('Invalid token format');
        }

        // Store with timestamp
        const tokenData = {
            token: token,
            timestamp: Date.now()
        };

        localStorage.setItem(this.tokenKey, JSON.stringify(tokenData));
    }

    getToken() {
        try {
            const tokenData = JSON.parse(localStorage.getItem(this.tokenKey));
            if (!tokenData) return null;

            // Check age
            const age = Date.now() - tokenData.timestamp;
            if (age > this.maxTokenAge) {
                this.removeToken();
                return null;
            }

            return tokenData.token;
        } catch {
            this.removeToken();
            return null;
        }
    }

    isValidJWT(token) {
        if (typeof token !== 'string') return false;
        
        const parts = token.split('.');
        if (parts.length !== 3) return false;

        try {
            // Validate base64 encoding
            atob(parts[0]);
            atob(parts[1]);
            return true;
        } catch {
            return false;
        }
    }

    removeToken() {
        localStorage.removeItem(this.tokenKey);
    }
}
```

This comprehensive Frontend Integration Strategy provides a complete roadmap for progressively enhancing the existing jQuery + Bootstrap frontend with modern API integration capabilities while preserving all existing functionality and ensuring optimal user experience.