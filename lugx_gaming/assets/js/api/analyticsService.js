/**
 * LugX Gaming Analytics Service
 * Handles user behavior tracking, event collection, and performance monitoring
 * Integrates with Analytics Service for real-time insights
 */

class AnalyticsService {
    constructor() {
        this.config = {
            batchSize: 50,
            flushInterval: 5000, // 5 seconds
            maxRetries: 3,
            retryDelay: 1000, // 1 second
            maxQueueSize: 1000,
            enableDebugLogging: window.location.hostname === 'localhost'
        };

        this.eventQueue = [];
        this.isOnline = navigator.onLine;
        this.isProcessing = false;
        this.retryCount = 0;
        
        // Performance tracking
        this.performanceData = {
            pageLoadStart: performance.now(),
            apiCalls: [],
            errors: [],
            userInteractions: []
        };

        // Event type definitions
        this.eventTypes = {
            PAGE_VIEW: 'page_view',
            CLICK: 'click',
            SCROLL: 'scroll',
            SEARCH: 'search',
            CART_ADD: 'cart_add',
            CART_REMOVE: 'cart_remove',
            CART_VIEW: 'cart_view',
            CHECKOUT_START: 'checkout_start',
            PURCHASE: 'purchase',
            USER_REGISTER: 'user_register',
            USER_LOGIN: 'user_login',
            USER_LOGOUT: 'user_logout',
            GAME_VIEW: 'game_view',
            GAME_LIKE: 'game_like',
            FILTER_APPLY: 'filter_apply',
            ERROR: 'error',
            PERFORMANCE: 'performance'
        };

        this.initializeAnalytics();
    }

    initializeAnalytics() {
        this.setupBatchProcessor();
        this.setupNetworkStatusMonitoring();
        this.setupPageUnloadHandler();
        this.setupPerformanceMonitoring();
        this.setupGlobalEventTracking();
        
        // Track initial page view
        this.trackPageView();
        
        this.log('Analytics Service initialized');
    }

    // Core tracking methods
    track(eventType, properties = {}) {
        try {
            const event = this.buildEvent(eventType, properties);
            this.addToQueue(event);
            
            // Flush immediately for critical events
            if (this.isCriticalEvent(eventType)) {
                this.flush();
            }
            
            this.log('Event tracked:', eventType, properties);
        } catch (error) {
            console.error('Failed to track event:', error);
        }
    }

    buildEvent(eventType, properties = {}) {
        const baseEvent = {
            event_type: eventType,
            timestamp: new Date().toISOString(),
            session_id: this.getSessionId(),
            page_url: window.location.href,
            page_title: document.title,
            page_path: window.location.pathname,
            referrer: document.referrer,
            user_agent: navigator.userAgent,
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            },
            device_type: this.getDeviceType(),
            browser: this.getBrowser(),
            os: this.getOperatingSystem()
        };

        // Add user context if available
        if (window.authService && window.authService.isAuthenticated()) {
            const user = window.authService.getUser();
            baseEvent.user_id = user.id;
            baseEvent.user_email = user.email;
        }

        // Add UTM parameters if present
        const urlParams = new URLSearchParams(window.location.search);
        const utmParams = {};
        ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content'].forEach(param => {
            if (urlParams.has(param)) {
                utmParams[param] = urlParams.get(param);
            }
        });
        
        if (Object.keys(utmParams).length > 0) {
            baseEvent.utm_parameters = utmParams;
        }

        // Merge custom properties
        return {
            ...baseEvent,
            properties: {
                ...properties,
                client_timestamp: Date.now(),
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                language: navigator.language
            }
        };
    }

    addToQueue(event) {
        // Prevent queue from growing too large
        if (this.eventQueue.length >= this.config.maxQueueSize) {
            this.log('Event queue full, removing oldest events');
            this.eventQueue.splice(0, this.config.batchSize);
        }
        
        this.eventQueue.push(event);
    }

    async flush() {
        if (this.isProcessing || this.eventQueue.length === 0) {
            return;
        }

        this.isProcessing = true;
        
        try {
            const eventsToSend = this.eventQueue.splice(0, this.config.batchSize);
            await this.sendEvents(eventsToSend);
            
            this.retryCount = 0;
            this.log(`Successfully sent ${eventsToSend.length} events`);
            
        } catch (error) {
            this.handleSendError(error);
        } finally {
            this.isProcessing = false;
        }
    }

    async sendEvents(events) {
        if (!this.isOnline) {
            throw new Error('Network offline');
        }

        try {
            await window.apiService.post('analytics', '/events/batch', {
                events: events,
                batch_id: `batch_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
            });
        } catch (error) {
            // Re-add events to queue for retry
            this.eventQueue.unshift(...events);
            throw error;
        }
    }

    handleSendError(error) {
        this.retryCount++;
        
        if (this.retryCount <= this.config.maxRetries) {
            const delay = this.config.retryDelay * Math.pow(2, this.retryCount - 1);
            this.log(`Analytics send failed, retrying in ${delay}ms (attempt ${this.retryCount}/${this.config.maxRetries})`);
            
            setTimeout(() => {
                this.flush();
            }, delay);
        } else {
            console.warn('Analytics send failed after maximum retries:', error);
            this.retryCount = 0;
        }
    }

    // Specific tracking methods
    trackPageView(customProperties = {}) {
        const properties = {
            page_type: this.getPageType(),
            loading_time: performance.now() - this.performanceData.pageLoadStart,
            ...customProperties
        };
        
        this.track(this.eventTypes.PAGE_VIEW, properties);
    }

    trackClick(element, customProperties = {}) {
        const properties = {
            element_type: element.tagName.toLowerCase(),
            element_id: element.id || null,
            element_class: element.className || null,
            element_text: element.textContent ? element.textContent.trim().substring(0, 100) : null,
            element_href: element.href || null,
            click_position: {
                x: event.clientX,
                y: event.clientY
            },
            ...customProperties
        };
        
        this.track(this.eventTypes.CLICK, properties);
    }

    trackScroll(scrollDepth, customProperties = {}) {
        const properties = {
            scroll_depth: scrollDepth,
            scroll_position: window.scrollY,
            document_height: document.body.scrollHeight,
            viewport_height: window.innerHeight,
            ...customProperties
        };
        
        this.track(this.eventTypes.SCROLL, properties);
    }

    trackSearch(query, resultsCount = null, customProperties = {}) {
        const properties = {
            search_query: query.trim(),
            search_results_count: resultsCount,
            search_length: query.trim().length,
            ...customProperties
        };
        
        this.track(this.eventTypes.SEARCH, properties);
    }

    trackCartAdd(gameId, gameName, price, quantity = 1, customProperties = {}) {
        const properties = {
            game_id: gameId,
            game_name: gameName,
            price: price,
            quantity: quantity,
            total_amount: price * quantity,
            ...customProperties
        };
        
        this.track(this.eventTypes.CART_ADD, properties);
    }

    trackCartRemove(gameId, gameName, customProperties = {}) {
        const properties = {
            game_id: gameId,
            game_name: gameName,
            ...customProperties
        };
        
        this.track(this.eventTypes.CART_REMOVE, properties);
    }

    trackPurchase(orderId, totalAmount, items, customProperties = {}) {
        const properties = {
            order_id: orderId,
            total_amount: totalAmount,
            item_count: items.length,
            items: items.map(item => ({
                game_id: item.game_id,
                game_name: item.game_name,
                price: item.price,
                quantity: item.quantity
            })),
            payment_method: customProperties.payment_method || 'unknown',
            ...customProperties
        };
        
        this.track(this.eventTypes.PURCHASE, properties);
    }

    trackError(error, context = {}) {
        const properties = {
            error_message: error.message,
            error_type: error.name,
            error_stack: error.stack ? error.stack.substring(0, 1000) : null,
            context: context,
            url: window.location.href,
            user_agent: navigator.userAgent,
            timestamp: new Date().toISOString()
        };
        
        this.track(this.eventTypes.ERROR, properties);
    }

    trackPerformance(metrics) {
        this.track(this.eventTypes.PERFORMANCE, metrics);
    }

    // Performance monitoring
    setupPerformanceMonitoring() {
        // Track page load performance
        window.addEventListener('load', () => {
            setTimeout(() => {
                this.collectPageLoadMetrics();
            }, 100);
        });

        // Track API call performance
        this.interceptAPICallsForPerformance();
    }

    collectPageLoadMetrics() {
        try {
            const perfData = performance.timing;
            const navigation = performance.getEntriesByType('navigation')[0];
            
            const metrics = {
                page_load_time: perfData.loadEventEnd - perfData.navigationStart,
                dom_ready_time: perfData.domContentLoadedEventEnd - perfData.navigationStart,
                first_byte_time: perfData.responseStart - perfData.navigationStart,
                dns_lookup_time: perfData.domainLookupEnd - perfData.domainLookupStart,
                connect_time: perfData.connectEnd - perfData.connectStart,
                download_time: perfData.responseEnd - perfData.responseStart,
                dom_interactive_time: perfData.domInteractive - perfData.navigationStart
            };

            // Add Core Web Vitals if available
            if (navigation) {
                metrics.transfer_size = navigation.transferSize;
                metrics.encoded_body_size = navigation.encodedBodySize;
                metrics.decoded_body_size = navigation.decodedBodySize;
            }

            this.trackPerformance(metrics);
        } catch (error) {
            console.warn('Failed to collect performance metrics:', error);
        }
    }

    interceptAPICallsForPerformance() {
        const originalFetch = window.fetch;
        
        window.fetch = async function(...args) {
            const startTime = performance.now();
            const url = args[0];
            const method = args[1]?.method || 'GET';
            
            try {
                const response = await originalFetch.apply(this, args);
                const endTime = performance.now();
                
                // Track API performance
                if (window.analyticsService) {
                    window.analyticsService.performanceData.apiCalls.push({
                        url,
                        method,
                        duration: endTime - startTime,
                        status: response.status,
                        success: response.ok,
                        timestamp: Date.now()
                    });
                }
                
                return response;
            } catch (error) {
                const endTime = performance.now();
                
                // Track API errors
                if (window.analyticsService) {
                    window.analyticsService.performanceData.apiCalls.push({
                        url,
                        method,
                        duration: endTime - startTime,
                        error: error.message,
                        success: false,
                        timestamp: Date.now()
                    });
                }
                
                throw error;
            }
        };
    }

    // Automatic event tracking setup
    setupGlobalEventTracking() {
        // Track clicks on trackable elements
        document.addEventListener('click', (e) => {
            const trackableElement = e.target.closest('[data-track-click]');
            if (trackableElement) {
                const trackType = trackableElement.dataset.trackClick;
                const context = this.getElementContext(trackableElement);
                
                this.trackClick(trackableElement, {
                    track_type: trackType,
                    context: context
                });
            }
        });

        // Track scroll depth
        this.setupScrollTracking();
        
        // Track form submissions
        this.setupFormTracking();
        
        // Track video interactions
        this.setupVideoTracking();
    }

    setupScrollTracking() {
        let maxScrollDepth = 0;
        const scrollMilestones = [25, 50, 75, 100];
        let trackedMilestones = new Set();

        const throttledScrollHandler = this.throttle(() => {
            const scrollPercent = Math.round(
                (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100
            );

            if (scrollPercent > maxScrollDepth) {
                maxScrollDepth = scrollPercent;

                // Track milestone scroll depths
                scrollMilestones.forEach(milestone => {
                    if (scrollPercent >= milestone && !trackedMilestones.has(milestone)) {
                        trackedMilestones.add(milestone);
                        this.trackScroll(milestone, {
                            page_type: this.getPageType(),
                            scroll_direction: 'down'
                        });
                    }
                });
            }
        }, 250);

        window.addEventListener('scroll', throttledScrollHandler, { passive: true });
    }

    setupFormTracking() {
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.tagName === 'FORM') {
                const formData = new FormData(form);
                const formFields = {};
                
                for (const [key, value] of formData.entries()) {
                    // Don't track sensitive data
                    if (!key.toLowerCase().includes('password') && 
                        !key.toLowerCase().includes('credit') &&
                        !key.toLowerCase().includes('ssn')) {
                        formFields[key] = typeof value === 'string' ? value.substring(0, 100) : value;
                    }
                }
                
                this.track('form_submit', {
                    form_id: form.id,
                    form_action: form.action,
                    form_method: form.method,
                    field_count: formData.entries().length,
                    fields: formFields
                });
            }
        });
    }

    setupVideoTracking() {
        document.addEventListener('play', (e) => {
            if (e.target.tagName === 'VIDEO') {
                this.track('video_play', {
                    video_src: e.target.src,
                    video_duration: e.target.duration
                });
            }
        }, true);

        document.addEventListener('pause', (e) => {
            if (e.target.tagName === 'VIDEO') {
                this.track('video_pause', {
                    video_src: e.target.src,
                    current_time: e.target.currentTime,
                    video_duration: e.target.duration
                });
            }
        }, true);
    }

    // Batch processing
    setupBatchProcessor() {
        // Process events at regular intervals
        setInterval(() => {
            if (this.eventQueue.length > 0) {
                this.flush();
            }
        }, this.config.flushInterval);
    }

    setupNetworkStatusMonitoring() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.log('Network back online, attempting to flush queued events');
            this.flush();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.log('Network offline, events will be queued');
        });
    }

    setupPageUnloadHandler() {
        // Flush events when user leaves the page
        window.addEventListener('beforeunload', () => {
            if (this.eventQueue.length > 0) {
                this.sendBeacon();
            }
        });

        // Also flush on visibility change (when tab becomes hidden)
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'hidden' && this.eventQueue.length > 0) {
                this.sendBeacon();
            }
        });
    }

    sendBeacon() {
        if (this.eventQueue.length === 0 || !navigator.sendBeacon) {
            return;
        }

        try {
            const events = this.eventQueue.splice(0);
            const data = JSON.stringify({
                events: events,
                batch_id: `beacon_${Date.now()}`
            });

            const baseURL = window.apiService.config.baseURL.analytics;
            navigator.sendBeacon(`${baseURL}/events/batch`, data);
            
            this.log(`Sent ${events.length} events via beacon`);
        } catch (error) {
            console.warn('Failed to send events via beacon:', error);
        }
    }

    // Utility methods
    getSessionId() {
        if (window.authService) {
            return window.authService.getSessionId();
        }
        
        let sessionId = sessionStorage.getItem('lugx_analytics_session');
        if (!sessionId) {
            sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            sessionStorage.setItem('lugx_analytics_session', sessionId);
        }
        return sessionId;
    }

    getPageType() {
        const path = window.location.pathname;
        const filename = path.split('/').pop() || 'index.html';
        
        const pageTypes = {
            'index.html': 'homepage',
            'shop.html': 'shop',
            'product-details.html': 'product_details',
            'cart.html': 'cart',
            'checkout.html': 'checkout',
            'login.html': 'login',
            'register.html': 'register',
            'contact.html': 'contact',
            'about.html': 'about'
        };
        
        return pageTypes[filename] || 'other';
    }

    getDeviceType() {
        const userAgent = navigator.userAgent.toLowerCase();
        
        if (/tablet|ipad/.test(userAgent)) {
            return 'tablet';
        } else if (/mobile|android|iphone/.test(userAgent)) {
            return 'mobile';
        } else {
            return 'desktop';
        }
    }

    getBrowser() {
        const userAgent = navigator.userAgent.toLowerCase();
        
        if (userAgent.includes('chrome')) return 'Chrome';
        if (userAgent.includes('firefox')) return 'Firefox';
        if (userAgent.includes('safari')) return 'Safari';
        if (userAgent.includes('edge')) return 'Edge';
        if (userAgent.includes('opera')) return 'Opera';
        
        return 'Other';
    }

    getOperatingSystem() {
        const userAgent = navigator.userAgent.toLowerCase();
        
        if (userAgent.includes('windows')) return 'Windows';
        if (userAgent.includes('mac')) return 'macOS';
        if (userAgent.includes('linux')) return 'Linux';
        if (userAgent.includes('android')) return 'Android';
        if (userAgent.includes('ios')) return 'iOS';
        
        return 'Other';
    }

    getElementContext(element) {
        const contexts = {
            '.trending': 'trending_section',
            '.most-played': 'most_played_section',
            '.featured': 'featured_section',
            '.categories': 'categories_section',
            '.newsletter': 'newsletter_section',
            '.header-area': 'header',
            '.footer': 'footer',
            '.shop': 'shop_page',
            '.cart': 'cart_page'
        };
        
        for (const [selector, context] of Object.entries(contexts)) {
            if (element.closest(selector)) {
                return context;
            }
        }
        
        return 'unknown';
    }

    isCriticalEvent(eventType) {
        const criticalEvents = [
            this.eventTypes.CART_ADD,
            this.eventTypes.CART_REMOVE,
            this.eventTypes.CHECKOUT_START,
            this.eventTypes.PURCHASE,
            this.eventTypes.USER_REGISTER,
            this.eventTypes.USER_LOGIN,
            this.eventTypes.ERROR
        ];
        
        return criticalEvents.includes(eventType);
    }

    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    log(...args) {
        if (this.config.enableDebugLogging) {
            console.log('[Analytics]', ...args);
        }
    }

    // Public API for debugging and monitoring
    getQueueStatus() {
        return {
            queueLength: this.eventQueue.length,
            isProcessing: this.isProcessing,
            isOnline: this.isOnline,
            retryCount: this.retryCount,
            sessionId: this.getSessionId()
        };
    }

    getPerformanceData() {
        return {
            ...this.performanceData,
            totalAPICallsFailed: this.performanceData.apiCalls.filter(call => !call.success).length,
            averageAPICallDuration: this.performanceData.apiCalls.length > 0 
                ? this.performanceData.apiCalls.reduce((sum, call) => sum + call.duration, 0) / this.performanceData.apiCalls.length 
                : 0
        };
    }

    clearQueue() {
        this.eventQueue = [];
        this.log('Event queue cleared');
    }
}

// Global analytics service instance
window.analyticsService = new AnalyticsService();

// Log initialization
console.log('LugX Analytics Service initialized:', {
    batchSize: window.analyticsService.config.batchSize,
    flushInterval: window.analyticsService.config.flushInterval,
    sessionId: window.analyticsService.getSessionId(),
    pageType: window.analyticsService.getPageType()
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AnalyticsService };
}