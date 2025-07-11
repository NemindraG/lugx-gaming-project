/**
 * LugX Gaming Homepage Enhancement Module
 * Progressively enhances static content with dynamic API data
 * Maintains fallback functionality and preserves existing styling
 */

class HomepageEnhancer {
    constructor() {
        this.isEnhanced = false;
        this.enhancementStatus = {
            trending: false,
            mostPlayed: false,
            categories: false,
            search: false,
            newsletter: false
        };
        
        this.config = {
            enableLoadingStates: true,
            enableAnalytics: true,
            fallbackTimeout: 10000, // 10 seconds
            retryAttempts: 2,
            enableDebugLogging: window.location.hostname === 'localhost'
        };

        // Only initialize on homepage
        if (this.isHomepage()) {
            this.initializeEnhancements();
        }
    }

    async initializeEnhancements() {
        try {
            this.log('Starting homepage enhancement...');
            
            // Wait for API services to be ready
            await this.waitForDependencies();
            
            // Track homepage visit
            if (window.analyticsService) {
                window.analyticsService.trackPageView({
                    page_type: 'homepage',
                    enhancement_enabled: true
                });
            }

            // Enhance different sections concurrently for better performance
            const enhancementPromises = [
                this.enhanceTrendingGamesSection(),
                this.enhanceMostPlayedSection(),
                this.enhanceCategoriesSection(),
                this.enhanceSearchFunctionality(),
                this.enhanceNewsletterForm()
            ];

            // Execute all enhancements in parallel
            const results = await Promise.allSettled(enhancementPromises);
            
            // Log results
            results.forEach((result, index) => {
                const sectionNames = ['trending', 'mostPlayed', 'categories', 'search', 'newsletter'];
                if (result.status === 'fulfilled') {
                    this.log(`${sectionNames[index]} section enhanced successfully`);
                } else {
                    console.warn(`${sectionNames[index]} enhancement failed:`, result.reason);
                }
            });

            // Setup global interaction tracking
            this.setupInteractionTracking();
            
            // Setup scroll tracking
            this.setupScrollTracking();
            
            // Setup performance monitoring
            this.setupPerformanceMonitoring();

            this.isEnhanced = true;
            this.log('Homepage enhancement completed successfully');

            // Track enhancement completion
            if (window.analyticsService) {
                window.analyticsService.track('homepage_enhanced', {
                    sections_enhanced: Object.values(this.enhancementStatus).filter(Boolean).length,
                    total_sections: Object.keys(this.enhancementStatus).length,
                    enhancement_time: performance.now()
                });
            }

        } catch (error) {
            console.error('Homepage enhancement failed:', error);
            
            if (window.analyticsService) {
                window.analyticsService.trackError(error, { 
                    context: 'homepage_enhancement',
                    enhancement_status: this.enhancementStatus 
                });
            }
        }
    }

    async waitForDependencies() {
        const dependencies = ['apiService', 'authService', 'analyticsService'];
        const maxWaitTime = 5000; // 5 seconds
        const checkInterval = 100; // 100ms
        let waited = 0;

        while (waited < maxWaitTime) {
            const allReady = dependencies.every(dep => window[dep]);
            if (allReady) {
                this.log('All dependencies ready');
                return;
            }
            
            await this.delay(checkInterval);
            waited += checkInterval;
        }

        this.log('Some dependencies not ready, proceeding with available services');
    }

    isHomepage() {
        const path = window.location.pathname;
        return path === '/' || 
               path === '/index.html' || 
               path.endsWith('/index.html') ||
               path === '';
    }

    async enhanceTrendingGamesSection() {
        const trendingContainer = document.querySelector('.section.trending .row');
        if (!trendingContainer) {
            this.log('Trending games container not found');
            return;
        }

        try {
            this.log('Enhancing trending games section...');
            
            if (this.config.enableLoadingStates) {
                this.showSectionLoading(trendingContainer, 'Loading trending games...');
            }

            // Fetch trending games with fallback
            const response = await this.fetchWithFallback(
                () => window.apiService.getTrendingGames(8),
                this.generateFallbackTrendingGames()
            );

            // Render the games
            await this.renderTrendingGames(response.games || response, trendingContainer);
            
            this.enhancementStatus.trending = true;
            
            // Track successful enhancement
            if (window.analyticsService) {
                window.analyticsService.track('section_enhanced', {
                    section: 'trending_games',
                    games_count: (response.games || response).length,
                    data_source: response.games ? 'api' : 'fallback'
                });
            }

        } catch (error) {
            this.log('Failed to enhance trending games section:', error);
            
            if (window.analyticsService) {
                window.analyticsService.trackError(error, { 
                    context: 'trending_games_enhancement' 
                });
            }
        } finally {
            if (this.config.enableLoadingStates) {
                this.hideSectionLoading(trendingContainer);
            }
        }
    }

    async renderTrendingGames(games, container) {
        if (!games || games.length === 0) {
            this.log('No trending games to render');
            return;
        }

        const gamesHTML = games.slice(0, 8).map(game => `
            <div class="col-lg-3 col-md-6 trending-item ${(game.category || 'action').toLowerCase()}" 
                 data-game-id="${game.id}" 
                 data-track-section="trending">
                <div class="item">
                    <div class="thumb">
                        <a href="product-details.html?id=${game.id}" 
                           data-track-click="game-card"
                           data-game-id="${game.id}">
                            <img src="${game.image_url || 'assets/images/trending-01.jpg'}" 
                                 alt="${game.name || game.title}" 
                                 loading="lazy"
                                 onerror="this.src='assets/images/trending-01.jpg'">
                        </a>
                        <span class="price">
                            ${this.renderPriceDisplay(game)}
                        </span>
                    </div>
                    <div class="down-content">
                        <span class="category">${game.category || 'Action'}</span>
                        <h4>${game.name || game.title}</h4>
                        <a href="product-details.html?id=${game.id}" 
                           data-track-click="explore-button"
                           data-game-id="${game.id}">
                            <i class="fa fa-shopping-bag"></i>
                        </a>
                    </div>
                </div>
            </div>
        `).join('');

        // Smooth content transition
        await this.smoothContentTransition(container, gamesHTML);
        
        // Reinitialize Isotope filtering if present
        this.reinitializeIsotope(container);
    }

    async enhanceMostPlayedSection() {
        const mostPlayedContainer = document.querySelector('.section.most-played .row');
        if (!mostPlayedContainer) {
            this.log('Most played container not found');
            return;
        }

        try {
            this.log('Enhancing most played section...');
            
            if (this.config.enableLoadingStates) {
                this.showSectionLoading(mostPlayedContainer, 'Loading popular games...');
            }

            // Fetch most played games with fallback
            const response = await this.fetchWithFallback(
                () => window.apiService.get('game', '/games', { 
                    sort: 'popularity', 
                    limit: 6 
                }),
                this.generateFallbackMostPlayedGames()
            );

            await this.renderMostPlayedGames(response.games || response, mostPlayedContainer);
            
            this.enhancementStatus.mostPlayed = true;
            
            if (window.analyticsService) {
                window.analyticsService.track('section_enhanced', {
                    section: 'most_played_games',
                    games_count: (response.games || response).length,
                    data_source: response.games ? 'api' : 'fallback'
                });
            }

        } catch (error) {
            this.log('Failed to enhance most played section:', error);
            
            if (window.analyticsService) {
                window.analyticsService.trackError(error, { 
                    context: 'most_played_enhancement' 
                });
            }
        } finally {
            if (this.config.enableLoadingStates) {
                this.hideSectionLoading(mostPlayedContainer);
            }
        }
    }

    async renderMostPlayedGames(games, container) {
        if (!games || games.length === 0) {
            this.log('No most played games to render');
            return;
        }

        const gamesHTML = games.slice(0, 6).map(game => `
            <div class="col-lg-2 col-md-6 col-sm-6" data-game-id="${game.id}">
                <div class="item">
                    <div class="thumb">
                        <a href="product-details.html?id=${game.id}" 
                           data-track-click="popular-game"
                           data-game-id="${game.id}">
                            <img src="${game.image_url || 'assets/images/top-game-01.jpg'}" 
                                 alt="${game.name || game.title}"
                                 loading="lazy"
                                 onerror="this.src='assets/images/top-game-01.jpg'">
                        </a>
                    </div>
                    <div class="down-content">
                        <span class="category">${game.category || 'Adventure'}</span>
                        <h4>${game.name || game.title}</h4>
                        <a href="product-details.html?id=${game.id}">Explore</a>
                    </div>
                </div>
            </div>
        `).join('');

        await this.smoothContentTransition(container, gamesHTML);
    }

    async enhanceCategoriesSection() {
        const categoriesContainer = document.querySelector('.section.categories .row');
        if (!categoriesContainer) {
            this.log('Categories container not found');
            return;
        }

        try {
            this.log('Enhancing categories section...');
            
            if (this.config.enableLoadingStates) {
                this.showSectionLoading(categoriesContainer, 'Loading categories...');
            }

            // Fetch popular categories
            const response = await this.fetchWithFallback(
                () => window.apiService.getPopularCategories(5),
                this.generateFallbackCategories()
            );

            await this.renderCategories(response.categories || response, categoriesContainer);
            
            this.enhancementStatus.categories = true;
            
            if (window.analyticsService) {
                window.analyticsService.track('section_enhanced', {
                    section: 'categories',
                    categories_count: (response.categories || response).length,
                    data_source: response.categories ? 'api' : 'fallback'
                });
            }

        } catch (error) {
            this.log('Failed to enhance categories section:', error);
            
            if (window.analyticsService) {
                window.analyticsService.trackError(error, { 
                    context: 'categories_enhancement' 
                });
            }
        } finally {
            if (this.config.enableLoadingStates) {
                this.hideSectionLoading(categoriesContainer);
            }
        }
    }

    async renderCategories(categories, container) {
        if (!categories || categories.length === 0) {
            this.log('No categories to render');
            return;
        }

        const categoriesHTML = categories.slice(0, 5).map(category => `
            <div class="col-lg col-sm-6 col-xs-12">
                <div class="item">
                    <h4>${category.name}</h4>
                    <div class="thumb">
                        <a href="shop.html?category=${category.id}" 
                           data-track-click="category"
                           data-category-id="${category.id}">
                            <img src="${category.image_url || 'assets/images/categories-01.jpg'}" 
                                 alt="${category.name}"
                                 loading="lazy"
                                 onerror="this.src='assets/images/categories-01.jpg'">
                        </a>
                    </div>
                </div>
            </div>
        `).join('');

        await this.smoothContentTransition(container, categoriesHTML);
    }

    async enhanceSearchFunctionality() {
        const searchForm = document.querySelector('#search, .search-input form');
        if (!searchForm) {
            this.log('Search form not found');
            return;
        }

        try {
            this.log('Enhancing search functionality...');
            
            // Add enhanced search functionality
            searchForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleSearchSubmit(searchForm);
            });

            // Add search autocomplete if input exists
            const searchInput = searchForm.querySelector('input[type="text"]');
            if (searchInput) {
                this.setupSearchAutocomplete(searchInput);
            }
            
            this.enhancementStatus.search = true;
            
            if (window.analyticsService) {
                window.analyticsService.track('section_enhanced', {
                    section: 'search',
                    has_autocomplete: !!searchInput
                });
            }

        } catch (error) {
            this.log('Failed to enhance search functionality:', error);
            
            if (window.analyticsService) {
                window.analyticsService.trackError(error, { 
                    context: 'search_enhancement' 
                });
            }
        }
    }

    async handleSearchSubmit(form) {
        const searchInput = form.querySelector('input[type="text"]');
        const query = searchInput?.value?.trim();
        
        if (!query) {
            this.showSearchMessage('Please enter a search term', 'warning');
            return;
        }

        try {
            // Track search event
            if (window.analyticsService) {
                window.analyticsService.trackSearch(query);
            }

            // Show loading state
            const submitButton = form.querySelector('button, input[type="submit"]');
            this.showButtonLoading(submitButton, 'Searching...');

            // Perform search
            const results = await window.apiService.searchGames({
                query: query,
                limit: 20
            });

            // Redirect to shop page with search results
            const searchUrl = `shop.html?search=${encodeURIComponent(query)}`;
            window.location.href = searchUrl;

        } catch (error) {
            this.log('Search failed:', error);
            this.showSearchMessage('Search failed. Please try again.', 'error');
            
            if (window.analyticsService) {
                window.analyticsService.trackError(error, { 
                    context: 'search_submit',
                    query: query
                });
            }
        }
    }

    setupSearchAutocomplete(input) {
        let searchTimeout;
        let autocompleteContainer;

        // Create autocomplete container
        autocompleteContainer = document.createElement('div');
        autocompleteContainer.className = 'search-autocomplete';
        autocompleteContainer.style.cssText = `
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #ddd;
            border-top: none;
            max-height: 200px;
            overflow-y: auto;
            z-index: 1000;
            display: none;
        `;
        
        input.parentNode.style.position = 'relative';
        input.parentNode.appendChild(autocompleteContainer);

        input.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            
            clearTimeout(searchTimeout);
            
            if (query.length < 2) {
                autocompleteContainer.style.display = 'none';
                return;
            }

            searchTimeout = setTimeout(async () => {
                await this.fetchSearchSuggestions(query, autocompleteContainer);
            }, 300);
        });

        // Hide autocomplete when clicking outside
        document.addEventListener('click', (e) => {
            if (!input.parentNode.contains(e.target)) {
                autocompleteContainer.style.display = 'none';
            }
        });
    }

    async fetchSearchSuggestions(query, container) {
        try {
            const results = await window.apiService.searchGames({
                query: query,
                limit: 5
            });

            const suggestions = (results.games || []).map(game => `
                <div class="search-suggestion" 
                     data-game-id="${game.id}"
                     style="padding: 8px 12px; cursor: pointer; border-bottom: 1px solid #eee;">
                    <div style="font-weight: bold;">${game.name}</div>
                    <div style="font-size: 12px; color: #666;">${game.category} - $${game.price}</div>
                </div>
            `).join('');

            if (suggestions) {
                container.innerHTML = suggestions;
                container.style.display = 'block';

                // Add click handlers
                container.querySelectorAll('.search-suggestion').forEach(suggestion => {
                    suggestion.addEventListener('click', () => {
                        const gameId = suggestion.dataset.gameId;
                        window.location.href = `product-details.html?id=${gameId}`;
                    });
                });
            } else {
                container.style.display = 'none';
            }

        } catch (error) {
            this.log('Search suggestions failed:', error);
            container.style.display = 'none';
        }
    }

    async enhanceNewsletterForm() {
        const newsletterForm = document.querySelector('#subscribe, .subscribe form, .newsletter form');
        if (!newsletterForm) {
            this.log('Newsletter form not found');
            return;
        }

        try {
            this.log('Enhancing newsletter form...');
            
            newsletterForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleNewsletterSubmit(newsletterForm);
            });
            
            this.enhancementStatus.newsletter = true;
            
            if (window.analyticsService) {
                window.analyticsService.track('section_enhanced', {
                    section: 'newsletter'
                });
            }

        } catch (error) {
            this.log('Failed to enhance newsletter form:', error);
            
            if (window.analyticsService) {
                window.analyticsService.trackError(error, { 
                    context: 'newsletter_enhancement' 
                });
            }
        }
    }

    async handleNewsletterSubmit(form) {
        const emailInput = form.querySelector('input[type="email"]');
        const email = emailInput?.value?.trim();

        if (!email) {
            this.showFormMessage(form, 'Please enter your email address', 'warning');
            return;
        }

        if (!this.isValidEmail(email)) {
            this.showFormMessage(form, 'Please enter a valid email address', 'warning');
            return;
        }

        try {
            this.showFormLoading(form);

            // Simulate newsletter subscription (would connect to actual service)
            await this.delay(1000);

            this.showFormMessage(form, 'Successfully subscribed to newsletter!', 'success');
            form.reset();

            // Track newsletter signup
            if (window.analyticsService) {
                window.analyticsService.track('newsletter_signup', {
                    email_domain: email.split('@')[1],
                    source: 'homepage'
                });
            }

        } catch (error) {
            this.log('Newsletter subscription failed:', error);
            this.showFormMessage(form, 'Subscription failed. Please try again.', 'error');
            
            if (window.analyticsService) {
                window.analyticsService.trackError(error, { 
                    context: 'newsletter_signup',
                    email_domain: email.split('@')[1]
                });
            }
        } finally {
            this.hideFormLoading(form);
        }
    }

    // Interaction tracking
    setupInteractionTracking() {
        // Track clicks on enhanced elements
        document.addEventListener('click', (e) => {
            const trackableElement = e.target.closest('[data-track-click]');
            if (trackableElement && window.analyticsService) {
                const trackType = trackableElement.dataset.trackClick;
                const gameId = trackableElement.dataset.gameId;
                const section = trackableElement.closest('[data-track-section]')?.dataset.trackSection;
                
                window.analyticsService.trackClick(trackableElement, {
                    track_type: trackType,
                    game_id: gameId,
                    section: section || this.getElementSection(trackableElement),
                    page: 'homepage'
                });
            }
        });
    }

    setupScrollTracking() {
        if (!window.analyticsService) return;

        let maxScrollDepth = 0;
        const scrollMilestones = [25, 50, 75, 100];
        const trackedMilestones = new Set();

        const throttledScrollHandler = this.throttle(() => {
            const scrollPercent = Math.round(
                (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100
            );

            if (scrollPercent > maxScrollDepth) {
                maxScrollDepth = scrollPercent;

                scrollMilestones.forEach(milestone => {
                    if (scrollPercent >= milestone && !trackedMilestones.has(milestone)) {
                        trackedMilestones.add(milestone);
                        window.analyticsService.trackScroll(milestone, {
                            page: 'homepage',
                            section_visible: this.getVisibleSection()
                        });
                    }
                });
            }
        }, 250);

        window.addEventListener('scroll', throttledScrollHandler, { passive: true });
    }

    setupPerformanceMonitoring() {
        if (!window.analyticsService) return;

        // Track section load times
        Object.keys(this.enhancementStatus).forEach(section => {
            if (this.enhancementStatus[section]) {
                const sectionElement = document.querySelector(`.section.${section.replace(/([A-Z])/g, '-$1').toLowerCase()}`);
                if (sectionElement) {
                    const observer = new IntersectionObserver((entries) => {
                        entries.forEach(entry => {
                            if (entry.isIntersecting) {
                                window.analyticsService.track('section_viewed', {
                                    section: section,
                                    viewport_ratio: entry.intersectionRatio,
                                    time_to_view: performance.now()
                                });
                                observer.unobserve(entry.target);
                            }
                        });
                    });
                    observer.observe(sectionElement);
                }
            }
        });
    }

    // Utility methods
    async fetchWithFallback(apiCall, fallbackData) {
        try {
            const result = await Promise.race([
                apiCall(),
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('API timeout')), this.config.fallbackTimeout)
                )
            ]);
            return result;
        } catch (error) {
            this.log('API call failed, using fallback data:', error);
            return fallbackData;
        }
    }

    generateFallbackTrendingGames() {
        return Array.from({ length: 4 }, (_, i) => ({
            id: `fallback-trending-${i + 1}`,
            name: `Trending Game ${i + 1}`,
            category: ['Action', 'Adventure', 'Strategy', 'Racing'][i],
            price: [29.99, 39.99, 49.99, 59.99][i],
            discount_price: i % 2 === 0 ? [19.99, null, 34.99, null][i] : null,
            image_url: `assets/images/trending-0${i + 1}.jpg`
        }));
    }

    generateFallbackMostPlayedGames() {
        return Array.from({ length: 6 }, (_, i) => ({
            id: `fallback-popular-${i + 1}`,
            name: `Popular Game ${i + 1}`,
            category: 'Adventure',
            image_url: `assets/images/top-game-0${i + 1}.jpg`
        }));
    }

    generateFallbackCategories() {
        return [
            { id: 1, name: 'Action', image_url: 'assets/images/categories-01.jpg' },
            { id: 2, name: 'Adventure', image_url: 'assets/images/categories-02.jpg' },
            { id: 3, name: 'Strategy', image_url: 'assets/images/categories-03.jpg' },
            { id: 4, name: 'Racing', image_url: 'assets/images/categories-04.jpg' },
            { id: 5, name: 'Sports', image_url: 'assets/images/categories-05.jpg' }
        ];
    }

    renderPriceDisplay(game) {
        if (game.discount_price && game.discount_price < game.price) {
            return `<em>$${game.price}</em>$${game.discount_price}`;
        }
        return `$${game.price || '29.99'}`;
    }

    async smoothContentTransition(container, newHTML) {
        return new Promise(resolve => {
            container.style.opacity = '0.6';
            container.style.transition = 'opacity 0.3s ease';
            
            setTimeout(() => {
                container.innerHTML = newHTML;
                container.style.opacity = '1';
                
                setTimeout(() => {
                    container.style.transition = '';
                    resolve();
                }, 300);
            }, 150);
        });
    }

    reinitializeIsotope(container) {
        if (typeof Isotope !== 'undefined') {
            setTimeout(() => {
                const iso = new Isotope(container, {
                    itemSelector: '.trending-item',
                    layoutMode: 'fitRows'
                });
                
                // Update filter buttons
                const filterButtons = document.querySelectorAll('.trending-filter a');
                filterButtons.forEach(button => {
                    button.addEventListener('click', (e) => {
                        e.preventDefault();
                        
                        const filterValue = button.dataset.filter;
                        iso.arrange({ filter: filterValue });
                        
                        // Update active state
                        document.querySelector('.trending-filter .is_active')?.classList.remove('is_active');
                        button.classList.add('is_active');
                        
                        // Track filter usage
                        if (window.analyticsService) {
                            window.analyticsService.track('filter_applied', {
                                filter_type: 'category',
                                filter_value: filterValue,
                                page: 'homepage'
                            });
                        }
                    });
                });
            }, 100);
        }
    }

    // UI helper methods
    showSectionLoading(container, message) {
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'loading-overlay';
        loadingOverlay.innerHTML = `
            <div class="loading-spinner text-center">
                <div class="spinner-border text-primary mb-2" role="status">
                    <span class="sr-only">Loading...</span>
                </div>
                <div class="loading-text">${message}</div>
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
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
        }
    }

    hideFormLoading(form) {
        const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.textContent = submitButton.dataset.originalText || 'Submit';
        }
    }

    showButtonLoading(button, text = 'Loading...') {
        if (button) {
            button.disabled = true;
            button.dataset.originalText = button.textContent;
            button.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span>${text}`;
        }
    }

    hideButtonLoading(button) {
        if (button) {
            button.disabled = false;
            button.textContent = button.dataset.originalText || 'Submit';
        }
    }

    showFormMessage(form, message, type = 'info') {
        this.clearFormMessages(form);

        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${this.getBootstrapAlertClass(type)} mt-3`;
        alertDiv.textContent = message;

        form.appendChild(alertDiv);

        if (type === 'success') {
            setTimeout(() => {
                alertDiv.remove();
            }, 5000);
        }
    }

    showSearchMessage(message, type = 'info') {
        // Implementation for search-specific messages
        console.log(`Search ${type}:`, message);
    }

    clearFormMessages(form) {
        const existingAlerts = form.querySelectorAll('.alert');
        existingAlerts.forEach(alert => alert.remove());
    }

    getBootstrapAlertClass(type) {
        const typeMap = {
            'success': 'success',
            'error': 'danger',
            'warning': 'warning',
            'info': 'info'
        };
        return typeMap[type] || 'info';
    }

    getElementSection(element) {
        const sections = {
            '.trending': 'trending',
            '.most-played': 'most_played',
            '.categories': 'categories',
            '.search-input': 'search',
            '.subscribe': 'newsletter'
        };
        
        for (const [selector, section] of Object.entries(sections)) {
            if (element.closest(selector)) {
                return section;
            }
        }
        
        return 'unknown';
    }

    getVisibleSection() {
        const sections = document.querySelectorAll('.section');
        for (const section of sections) {
            const rect = section.getBoundingClientRect();
            if (rect.top <= window.innerHeight / 2 && rect.bottom >= window.innerHeight / 2) {
                return section.className.split(' ').find(cls => cls !== 'section') || 'unknown';
            }
        }
        return 'header';
    }

    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
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

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    log(...args) {
        if (this.config.enableDebugLogging) {
            console.log('[HomepageEnhancer]', ...args);
        }
    }

    // Public API for debugging
    getEnhancementStatus() {
        return {
            isEnhanced: this.isEnhanced,
            sectionsStatus: this.enhancementStatus,
            config: this.config
        };
    }

    forceRefresh() {
        this.isEnhanced = false;
        Object.keys(this.enhancementStatus).forEach(key => {
            this.enhancementStatus[key] = false;
        });
        this.initializeEnhancements();
    }
}

// Initialize homepage enhancer when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.homepageEnhancer = new HomepageEnhancer();
});

// Log initialization
console.log('LugX Homepage Enhancer loaded');

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { HomepageEnhancer };
}