/**
 * LugX Gaming API Service
 * Centralized HTTP client for all backend communication
 * Provides retry logic, error handling, and response caching
 */

class APIService {
    constructor() {
        // Environment-based configuration
        this.config = {
            baseURL: this.getBaseURL(),
            timeout: 30000, // 30 seconds
            retryAttempts: 3,
            retryDelay: 1000, // 1 second base delay
            apiVersion: 'v1'
        };
        
        // Request tracking for deduplication
        this.pendingRequests = new Map();
        
        // Response cache
        this.cache = new Map();
        this.cacheConfig = {
            '/games/trending': { ttl: 15 * 60 * 1000 }, // 15 minutes
            '/games/featured': { ttl: 30 * 60 * 1000 }, // 30 minutes
            '/games/on-sale': { ttl: 10 * 60 * 1000 }, // 10 minutes
            '/categories': { ttl: 60 * 60 * 1000 }, // 1 hour
            '/games/': { ttl: 5 * 60 * 1000 } // 5 minutes for individual games
        };
        
        this.initializeEndpoints();
        this.setupPeriodicCacheCleanup();
    }

    getBaseURL() {
        // Auto-detect environment
        const hostname = window.location.hostname;
        const protocol = window.location.protocol;
        
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            // Development environment - direct service access
            return {
                game: 'http://localhost:8001/api/v1',
                order: 'http://localhost:8002/api/v1',
                analytics: 'http://localhost:8003/api/v1'
            };
        } else {
            // Production environment - through Istio Gateway
            return {
                game: `${protocol}//${hostname}/api/v1`,
                order: `${protocol}//${hostname}/api/v1`,
                analytics: `${protocol}//${hostname}/api/v1`
            };
        }
    }

    initializeEndpoints() {
        this.endpoints = {
            // Game Service endpoints
            games: {
                list: '/games',
                trending: '/games/trending',
                featured: '/games/featured',
                onSale: '/games/on-sale',
                search: '/games/search',
                details: (id) => `/games/${id}`,
                related: (id) => `/games/${id}/related`,
                reviews: (id) => `/games/${id}/reviews`
            },
            
            // Category endpoints
            categories: {
                list: '/categories',
                popular: '/categories/popular',
                hierarchy: '/categories/hierarchy',
                details: (id) => `/categories/${id}`
            },
            
            // Publisher endpoints
            publishers: {
                list: '/publishers',
                details: (id) => `/publishers/${id}`
            },
            
            // Order Service endpoints
            auth: {
                login: '/auth/login',
                register: '/auth/register',
                refresh: '/auth/refresh',
                logout: '/auth/logout',
                profile: '/auth/me',
                forgotPassword: '/auth/forgot-password',
                resetPassword: '/auth/reset-password'
            },
            
            // Cart endpoints
            cart: {
                get: '/cart',
                addItem: '/cart/items',
                updateItem: (id) => `/cart/items/${id}`,
                removeItem: (id) => `/cart/items/${id}`,
                clear: '/cart/clear',
                applyPromo: '/cart/promo'
            },
            
            // Order endpoints
            orders: {
                create: '/orders',
                list: '/orders',
                details: (id) => `/orders/${id}`,
                cancel: (id) => `/orders/${id}/cancel`,
                payment: (id) => `/orders/${id}/payment`
            },
            
            // User endpoints
            users: {
                profile: '/users/profile',
                addresses: '/users/addresses',
                addAddress: '/users/addresses',
                updateAddress: (id) => `/users/addresses/${id}`,
                deleteAddress: (id) => `/users/addresses/${id}`
            },
            
            // Analytics endpoints
            analytics: {
                track: '/events',
                trackBatch: '/events/batch',
                pageView: '/events/pageview',
                click: '/events/click',
                purchase: '/events/purchase'
            }
        };
    }

    async request(service, endpoint, options = {}) {
        const url = this.buildURL(service, endpoint);
        const cacheKey = this.buildCacheKey(url, options);
        
        // Check cache first for GET requests
        if ((!options.method || options.method === 'GET') && this.shouldCache(endpoint)) {
            const cached = this.getFromCache(cacheKey);
            if (cached) {
                return cached;
            }
        }
        
        // Request deduplication for GET requests
        if (!options.method || options.method === 'GET') {
            if (this.pendingRequests.has(cacheKey)) {
                return this.pendingRequests.get(cacheKey);
            }
        }
        
        // Create the request promise
        const requestPromise = this.executeRequest(url, options);
        
        // Store pending request for deduplication
        if (!options.method || options.method === 'GET') {
            this.pendingRequests.set(cacheKey, requestPromise);
        }
        
        try {
            const result = await requestPromise;
            
            // Cache successful GET responses
            if ((!options.method || options.method === 'GET') && this.shouldCache(endpoint)) {
                this.setCache(cacheKey, result);
            }
            
            return result;
        } finally {
            // Remove from pending requests
            this.pendingRequests.delete(cacheKey);
        }
    }

    async executeRequest(url, options = {}) {
        const config = this.buildRequestConfig(options);
        
        // Implement retry logic with exponential backoff
        for (let attempt = 1; attempt <= this.config.retryAttempts; attempt++) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);
                
                config.signal = controller.signal;
                
                const response = await fetch(url, config);
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    const errorMessage = await this.extractErrorMessage(response);
                    throw new APIError(response.status, errorMessage, response);
                }
                
                // Parse JSON response
                const data = await response.json();
                
                // Track successful API call
                this.trackAPICall(url, config.method || 'GET', response.status, true);
                
                return data;
                
            } catch (error) {
                // Don't retry on certain errors
                if (error instanceof APIError && !this.shouldRetry(error.status)) {
                    this.trackAPICall(url, config.method || 'GET', error.status, false);
                    throw error;
                }
                
                // Don't retry if this is the last attempt
                if (attempt === this.config.retryAttempts) {
                    this.trackAPICall(url, config.method || 'GET', 0, false);
                    console.error(`API request failed after ${this.config.retryAttempts} attempts:`, error);
                    throw error;
                }
                
                // Calculate delay with exponential backoff + jitter
                const baseDelay = this.config.retryDelay * Math.pow(2, attempt - 1);
                const jitter = Math.random() * 1000; // 0-1 second jitter
                const delay = baseDelay + jitter;
                
                console.warn(`API request failed (attempt ${attempt}/${this.config.retryAttempts}), retrying in ${delay}ms:`, error);
                await this.delay(delay);
            }
        }
    }

    buildURL(service, endpoint) {
        const baseURL = this.config.baseURL[service];
        if (!baseURL) {
            throw new Error(`Unknown service: ${service}`);
        }
        
        // Handle endpoint functions
        const resolvedEndpoint = typeof endpoint === 'function' ? endpoint() : endpoint;
        
        return `${baseURL}${resolvedEndpoint}`;
    }

    buildRequestConfig(options = {}) {
        const config = {
            method: options.method || 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                ...this.getAuthHeaders(),
                ...options.headers
            }
        };

        // Add body for non-GET requests
        if (options.body && config.method !== 'GET') {
            if (typeof options.body === 'object') {
                config.body = JSON.stringify(options.body);
            } else {
                config.body = options.body;
            }
        }

        // Add query parameters for GET requests
        if (options.params && config.method === 'GET') {
            // This will be handled in the convenience methods
        }

        return config;
    }

    getAuthHeaders() {
        // This will be implemented by the AuthService
        if (window.authService && window.authService.getToken) {
            const token = window.authService.getToken();
            return token ? { 'Authorization': `Bearer ${token}` } : {};
        }
        return {};
    }

    async extractErrorMessage(response) {
        try {
            const errorData = await response.json();
            return errorData.detail || errorData.message || `HTTP ${response.status}: ${response.statusText}`;
        } catch {
            return `HTTP ${response.status}: ${response.statusText}`;
        }
    }

    shouldRetry(status) {
        // Retry on server errors and rate limiting, but not on client errors
        return status >= 500 || status === 429;
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Cache management
    buildCacheKey(url, options) {
        const method = options.method || 'GET';
        const params = options.params ? JSON.stringify(options.params) : '';
        return `${method}:${url}:${params}`;
    }

    shouldCache(endpoint) {
        return Object.keys(this.cacheConfig).some(pattern => endpoint.includes(pattern));
    }

    getFromCache(key) {
        const cached = this.cache.get(key);
        if (!cached) return null;

        const now = Date.now();
        if (now > cached.expires) {
            this.cache.delete(key);
            return null;
        }

        return cached.data;
    }

    setCache(key, data) {
        const endpoint = key.split(':')[1]; // Extract URL from cache key
        const config = this.getCacheConfig(endpoint);
        if (!config) return;

        const expires = Date.now() + config.ttl;
        this.cache.set(key, { data, expires });

        // Prevent cache from growing too large
        if (this.cache.size > 200) {
            this.cleanupCache();
        }
    }

    getCacheConfig(url) {
        return Object.entries(this.cacheConfig)
            .find(([pattern]) => url.includes(pattern))?.[1];
    }

    cleanupCache() {
        const now = Date.now();
        for (const [key, value] of this.cache.entries()) {
            if (now > value.expires) {
                this.cache.delete(key);
            }
        }
    }

    setupPeriodicCacheCleanup() {
        // Clean up expired cache entries every 5 minutes
        setInterval(() => {
            this.cleanupCache();
        }, 5 * 60 * 1000);
    }

    trackAPICall(url, method, status, success) {
        // Track API performance for analytics
        if (window.performanceMonitor) {
            window.performanceMonitor.trackAPICall({
                url,
                method,
                status,
                success,
                timestamp: Date.now()
            });
        }
    }

    // Convenience methods
    async get(service, endpoint, params = {}) {
        let url = endpoint;
        if (Object.keys(params).length > 0) {
            const queryString = new URLSearchParams();
            Object.keys(params).forEach(key => {
                if (params[key] !== null && params[key] !== undefined) {
                    if (Array.isArray(params[key])) {
                        params[key].forEach(value => queryString.append(key, value));
                    } else {
                        queryString.append(key, params[key]);
                    }
                }
            });
            url += `?${queryString.toString()}`;
        }
        
        return this.request(service, url);
    }

    async post(service, endpoint, data = {}) {
        return this.request(service, endpoint, {
            method: 'POST',
            body: data
        });
    }

    async put(service, endpoint, data = {}) {
        return this.request(service, endpoint, {
            method: 'PUT',
            body: data
        });
    }

    async delete(service, endpoint) {
        return this.request(service, endpoint, {
            method: 'DELETE'
        });
    }

    // Game Service API methods
    async getTrendingGames(limit = 20) {
        return this.get('game', this.endpoints.games.trending, { limit });
    }

    async getFeaturedGames(limit = 10) {
        return this.get('game', this.endpoints.games.featured, { limit });
    }

    async getGamesOnSale(limit = 50) {
        return this.get('game', this.endpoints.games.onSale, { limit });
    }

    async searchGames(searchParams = {}) {
        return this.get('game', this.endpoints.games.search, searchParams);
    }

    async getGameDetails(gameId) {
        return this.get('game', this.endpoints.games.details(gameId));
    }

    async getRelatedGames(gameId, limit = 6) {
        return this.get('game', this.endpoints.games.related(gameId), { limit });
    }

    async getGameReviews(gameId, page = 1, limit = 10) {
        return this.get('game', this.endpoints.games.reviews(gameId), { page, limit });
    }

    // Category API methods
    async getCategories(includeChildren = true, activeOnly = true) {
        return this.get('game', this.endpoints.categories.list, { 
            include_children: includeChildren, 
            active_only: activeOnly 
        });
    }

    async getPopularCategories(limit = 10) {
        return this.get('game', this.endpoints.categories.popular, { limit });
    }

    async getCategoryHierarchy() {
        return this.get('game', this.endpoints.categories.hierarchy);
    }

    // Health check method
    async healthCheck() {
        const services = ['game', 'order', 'analytics'];
        const results = {};

        const healthPromises = services.map(async (service) => {
            try {
                const startTime = Date.now();
                const response = await fetch(`${this.config.baseURL[service]}/health`);
                const endTime = Date.now();
                
                results[service] = {
                    status: response.ok ? 'healthy' : 'unhealthy',
                    responseTime: endTime - startTime,
                    httpStatus: response.status
                };
            } catch (error) {
                results[service] = {
                    status: 'unreachable',
                    error: error.message,
                    responseTime: null
                };
            }
        });

        await Promise.allSettled(healthPromises);
        return results;
    }

    // Configuration update
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
        if (newConfig.baseURL) {
            this.config.baseURL = { ...this.config.baseURL, ...newConfig.baseURL };
        }
    }

    // Cache control
    clearCache(pattern = null) {
        if (pattern) {
            for (const [key] of this.cache.entries()) {
                if (key.includes(pattern)) {
                    this.cache.delete(key);
                }
            }
        } else {
            this.cache.clear();
        }
    }

    getCacheStats() {
        const now = Date.now();
        let expired = 0;
        let active = 0;

        for (const [, value] of this.cache.entries()) {
            if (now > value.expires) {
                expired++;
            } else {
                active++;
            }
        }

        return {
            total: this.cache.size,
            active,
            expired,
            hitRate: this.cacheHits / (this.cacheHits + this.cacheMisses) || 0
        };
    }
}

// Custom error class for API errors
class APIError extends Error {
    constructor(status, message, response = null) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.response = response;
    }

    isClientError() {
        return this.status >= 400 && this.status < 500;
    }

    isServerError() {
        return this.status >= 500;
    }

    isUnauthorized() {
        return this.status === 401;
    }

    isForbidden() {
        return this.status === 403;
    }

    isNotFound() {
        return this.status === 404;
    }

    isRateLimited() {
        return this.status === 429;
    }
}

// Global API service instance
window.apiService = new APIService();

// Log initialization
console.log('LugX API Service initialized:', {
    environment: window.location.hostname === 'localhost' ? 'development' : 'production',
    baseURLs: window.apiService.config.baseURL,
    cacheEnabled: true,
    retryEnabled: true
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { APIService, APIError };
}