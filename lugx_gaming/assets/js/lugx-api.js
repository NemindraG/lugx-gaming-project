/**
 * LugX Gaming API Integration
 * Legacy wrapper for backward compatibility
 * Delegates to the new comprehensive API service layer
 */

class LugxAPI {
    constructor() {
        // Legacy configuration for backward compatibility
        this.config = {
            gameService: 'http://localhost:8001',
            orderService: 'http://localhost:8002',
            analyticsService: 'http://localhost:8003',
            apiPrefix: '/api/v1'
        };
        
        // Initialize API endpoints
        this.initializeEndpoints();
        
        // Setup request interceptors
        this.setupInterceptors();
        
        // Wait for new API service to be available
        this.waitForAPIService();
    }

    async waitForAPIService() {
        // Wait for the new API service to be initialized
        let attempts = 0;
        const maxAttempts = 50; // 5 seconds max
        
        while (!window.apiService && attempts < maxAttempts) {
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
        
        if (window.apiService) {
            console.log('LugX API: Delegating to new API service layer');
            this.useNewAPIService = true;
        } else {
            console.warn('LugX API: Falling back to legacy implementation');
            this.useNewAPIService = false;
        }
    }

    initializeEndpoints() {
        this.endpoints = {
            games: {
                trending: `${this.config.gameService}${this.config.apiPrefix}/games/trending`,
                featured: `${this.config.gameService}${this.config.apiPrefix}/games/featured`,
                onSale: `${this.config.gameService}${this.config.apiPrefix}/games/on-sale`,
                search: `${this.config.gameService}${this.config.apiPrefix}/games/search`,
                details: (id) => `${this.config.gameService}${this.config.apiPrefix}/games/${id}`,
                related: (id) => `${this.config.gameService}${this.config.apiPrefix}/games/${id}/related`
            },
            categories: {
                all: `${this.config.gameService}${this.config.apiPrefix}/categories/`,
                popular: `${this.config.gameService}${this.config.apiPrefix}/categories/popular`,
                hierarchy: `${this.config.gameService}${this.config.apiPrefix}/categories/hierarchy`,
                details: (id) => `${this.config.gameService}${this.config.apiPrefix}/categories/${id}`,
                search: (query) => `${this.config.gameService}${this.config.apiPrefix}/categories/search/${query}`
            },
            publishers: {
                all: `${this.config.gameService}${this.config.apiPrefix}/publishers/`,
                details: (id) => `${this.config.gameService}${this.config.apiPrefix}/publishers/${id}`
            }
        };
    }

    setupInterceptors() {
        // Default headers for all requests
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
    }

    async makeRequest(url, options = {}) {
        try {
            const config = {
                method: 'GET',
                headers: { ...this.defaultHeaders, ...options.headers },
                ...options
            };

            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    // Game API Methods - Delegate to new API service when available
    async getTrendingGames(limit = 20) {
        if (this.useNewAPIService && window.apiService) {
            return await window.apiService.getTrendingGames(limit);
        }
        return this.makeRequest(`${this.endpoints.games.trending}?limit=${limit}`);
    }

    async getFeaturedGames(limit = 10) {
        if (this.useNewAPIService && window.apiService) {
            return await window.apiService.getFeaturedGames(limit);
        }
        return this.makeRequest(`${this.endpoints.games.featured}?limit=${limit}`);
    }

    async getGamesOnSale(limit = 50) {
        if (this.useNewAPIService && window.apiService) {
            return await window.apiService.getGamesOnSale(limit);
        }
        return this.makeRequest(`${this.endpoints.games.onSale}?limit=${limit}`);
    }

    async searchGames(params = {}) {
        if (this.useNewAPIService && window.apiService) {
            return await window.apiService.searchGames(params);
        }
        
        const searchParams = new URLSearchParams();
        
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined) {
                if (Array.isArray(params[key])) {
                    params[key].forEach(value => searchParams.append(key, value));
                } else {
                    searchParams.append(key, params[key]);
                }
            }
        });

        return this.makeRequest(`${this.endpoints.games.search}?${searchParams}`);
    }

    async getGameDetails(gameId) {
        if (this.useNewAPIService && window.apiService) {
            return await window.apiService.getGameDetails(gameId);
        }
        return this.makeRequest(this.endpoints.games.details(gameId));
    }

    async getRelatedGames(gameId, limit = 10) {
        if (this.useNewAPIService && window.apiService) {
            return await window.apiService.getRelatedGames(gameId, limit);
        }
        return this.makeRequest(`${this.endpoints.games.related(gameId)}?limit=${limit}`);
    }

    // Category API Methods
    async getCategories(includeChildren = true, activeOnly = true) {
        return this.makeRequest(`${this.endpoints.categories.all}?include_children=${includeChildren}&active_only=${activeOnly}`);
    }

    async getPopularCategories(limit = 10) {
        return this.makeRequest(`${this.endpoints.categories.popular}?limit=${limit}`);
    }

    async getCategoryHierarchy() {
        return this.makeRequest(this.endpoints.categories.hierarchy);
    }

    async getCategoryDetails(categoryId) {
        return this.makeRequest(this.endpoints.categories.details(categoryId));
    }

    async searchCategories(query, limit = 20) {
        return this.makeRequest(`${this.endpoints.categories.search(query)}?limit=${limit}`);
    }

    // Publisher API Methods
    async getPublishers() {
        return this.makeRequest(this.endpoints.publishers.all);
    }

    async getPublisherDetails(publisherId) {
        return this.makeRequest(this.endpoints.publishers.details(publisherId));
    }

    // Analytics tracking (for user behavior) - Delegate to new analytics service
    async trackEvent(eventData) {
        try {
            // Use new analytics service if available
            if (window.analyticsService) {
                window.analyticsService.track(eventData.type || 'page_view', eventData);
                return;
            }

            // Fallback to legacy tracking
            const event = {
                event_type: eventData.type || 'page_view',
                page_url: window.location.href,
                timestamp: new Date().toISOString(),
                session_id: this.getSessionId(),
                user_agent: navigator.userAgent,
                ...eventData
            };

            // Send to analytics service (non-blocking)
            fetch(`${this.config.analyticsService}${this.config.apiPrefix}/events`, {
                method: 'POST',
                headers: this.defaultHeaders,
                body: JSON.stringify(event)
            }).catch(err => console.warn('Analytics tracking failed:', err));
        } catch (error) {
            console.warn('Analytics tracking error:', error);
        }
    }

    getSessionId() {
        let sessionId = sessionStorage.getItem('lugx_session_id');
        if (!sessionId) {
            sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            sessionStorage.setItem('lugx_session_id', sessionId);
        }
        return sessionId;
    }

    // Utility methods
    formatPrice(price, currency = 'USD') {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency
        }).format(price);
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    calculateDiscountedPrice(originalPrice, discountPercentage) {
        if (!discountPercentage || discountPercentage <= 0) return originalPrice;
        return originalPrice * (1 - discountPercentage / 100);
    }

    // Configuration update methods
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
        this.initializeEndpoints();
    }

    // Health check method
    async healthCheck() {
        const services = ['gameService', 'orderService', 'analyticsService'];
        const results = {};

        for (const service of services) {
            try {
                const response = await fetch(`${this.config[service]}/health`);
                results[service] = {
                    status: response.ok ? 'healthy' : 'unhealthy',
                    responseTime: Date.now()
                };
            } catch (error) {
                results[service] = {
                    status: 'unreachable',
                    error: error.message
                };
            }
        }

        return results;
    }
}

// Global API instance
window.lugxAPI = new LugxAPI();

// Environment-specific configuration
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    // Development environment
    console.log('LugX API initialized for development environment');
} else {
    // Production environment - update API endpoints
    window.lugxAPI.updateConfig({
        gameService: window.location.protocol + '//' + window.location.hostname + ':8001',
        orderService: window.location.protocol + '//' + window.location.hostname + ':8002',
        analyticsService: window.location.protocol + '//' + window.location.hostname + ':8003'
    });
    console.log('LugX API initialized for production environment');
}

// Track initial page view
document.addEventListener('DOMContentLoaded', () => {
    window.lugxAPI.trackEvent({
        type: 'page_view',
        page_title: document.title,
        referrer: document.referrer
    });
});
