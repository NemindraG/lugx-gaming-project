/**
 * Game Integration Module
 * Handles dynamic game content loading and user interactions
 * Transforms static game listings into live API-driven content
 */

class GameIntegration {
    constructor() {
        this.apiService = window.apiService;
        this.analyticsService = window.analyticsService;
        this.isLoading = false;
        this.loadedGames = new Map();
        this.searchTimeout = null;
        this.currentSearchQuery = '';
        this.currentFilters = {};
        
        this.initializeEventListeners();
        this.setupErrorHandling();
        this.loadInitialContent();
    }

    /**
     * Initialize all event listeners for game interactions
     */
    initializeEventListeners() {
        // Search functionality
        this.initializeSearch();
        
        // Game card interactions
        this.initializeGameCards();
        
        // Category filtering
        this.initializeCategoryFilters();
        
        // Load more functionality
        this.initializeLoadMore();
        
        // Price filtering
        this.initializePriceFilters();
        
        // Platform filtering
        this.initializePlatformFilters();
        
        // Sort controls
        this.initializeSortControls();
    }

    /**
     * Initialize search functionality with debouncing
     */
    initializeSearch() {
        const searchInput = document.getElementById('game-search');
        const searchButton = document.getElementById('search-button');
        const searchSuggestions = document.getElementById('search-suggestions');
        
        if (searchInput) {
            // Real-time search with debouncing
            searchInput.addEventListener('input', (e) => {
                clearTimeout(this.searchTimeout);
                const query = e.target.value.trim();
                
                if (query.length >= 2) {
                    this.searchTimeout = setTimeout(() => {
                        this.performSearch(query);
                    }, 300);
                } else if (query.length === 0) {
                    this.clearSearch();
                }
            });

            // Search on Enter key
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.performSearch(e.target.value.trim());
                }
            });
        }

        if (searchButton) {
            searchButton.addEventListener('click', () => {
                const query = searchInput ? searchInput.value.trim() : '';
                this.performSearch(query);
            });
        }
    }

    /**
     * Initialize game card interactions
     */
    initializeGameCards() {
        document.addEventListener('click', (e) => {
            // Add to cart functionality
            if (e.target.matches('.add-to-cart-btn, .add-to-cart-btn *')) {
                e.preventDefault();
                const button = e.target.closest('.add-to-cart-btn');
                const gameId = button.dataset.gameId;
                const gameTitle = button.dataset.gameTitle;
                this.addToCart(gameId, gameTitle);
            }
            
            // View details functionality
            if (e.target.matches('.view-details-btn, .view-details-btn *')) {
                e.preventDefault();
                const button = e.target.closest('.view-details-btn');
                const gameId = button.dataset.gameId;
                this.viewGameDetails(gameId);
            }
            
            // Quick view functionality
            if (e.target.matches('.quick-view-btn, .quick-view-btn *')) {
                e.preventDefault();
                const button = e.target.closest('.quick-view-btn');
                const gameId = button.dataset.gameId;
                this.showQuickView(gameId);
            }
        });
    }

    /**
     * Initialize category filtering
     */
    initializeCategoryFilters() {
        const categoryFilters = document.querySelectorAll('.category-filter');
        categoryFilters.forEach(filter => {
            filter.addEventListener('click', (e) => {
                e.preventDefault();
                const category = e.target.dataset.category;
                this.filterByCategory(category);
            });
        });
    }

    /**
     * Initialize load more functionality
     */
    initializeLoadMore() {
        const loadMoreBtn = document.getElementById('load-more-games');
        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', () => {
                this.loadMoreGames();
            });
        }
    }

    /**
     * Initialize price filtering
     */
    initializePriceFilters() {
        const priceFilters = document.querySelectorAll('.price-filter');
        priceFilters.forEach(filter => {
            filter.addEventListener('change', () => {
                this.updatePriceFilters();
            });
        });
    }

    /**
     * Initialize platform filtering
     */
    initializePlatformFilters() {
        const platformFilters = document.querySelectorAll('.platform-filter');
        platformFilters.forEach(filter => {
            filter.addEventListener('change', () => {
                this.updatePlatformFilters();
            });
        });
    }

    /**
     * Initialize sort controls
     */
    initializeSortControls() {
        const sortSelect = document.getElementById('sort-games');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.sortGames(e.target.value);
            });
        }
    }

    /**
     * Load initial content for the page
     */
    async loadInitialContent() {
        try {
            // Determine page type and load appropriate content
            const pathname = window.location.pathname;
            
            if (pathname.includes('index.html') || pathname === '/') {
                await this.loadHomepageContent();
            } else if (pathname.includes('shop.html')) {
                await this.loadShopContent();
            } else if (pathname.includes('product-details.html')) {
                await this.loadProductDetails();
            }
        } catch (error) {
            console.error('Failed to load initial content:', error);
            this.showError('Failed to load games. Please refresh the page.');
        }
    }

    /**
     * Load homepage content (trending, featured, on-sale games)
     */
    async loadHomepageContent() {
        this.showLoading();
        
        try {
            // Load trending games
            await this.loadTrendingGames();
            
            // Load featured games
            await this.loadFeaturedGames();
            
            // Load games on sale
            await this.loadSaleGames();
            
            // Load popular categories
            await this.loadPopularCategories();
            
        } catch (error) {
            console.error('Failed to load homepage content:', error);
            this.showError('Some content failed to load. Please refresh the page.');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Load trending games section
     */
    async loadTrendingGames() {
        try {
            const trendingGames = await this.apiService.getTrendingGames(8);
            this.renderTrendingGames(trendingGames);
            
            // Track analytics
            if (this.analyticsService) {
                this.analyticsService.trackEvent('games_loaded', {
                    section: 'trending',
                    count: trendingGames.length
                });
            }
        } catch (error) {
            console.error('Failed to load trending games:', error);
            this.showSectionError('trending-games-section', 'Failed to load trending games');
        }
    }

    /**
     * Load featured games section
     */
    async loadFeaturedGames() {
        try {
            const featuredGames = await this.apiService.getFeaturedGames(6);
            this.renderFeaturedGames(featuredGames);
            
            // Track analytics
            if (this.analyticsService) {
                this.analyticsService.trackEvent('games_loaded', {
                    section: 'featured',
                    count: featuredGames.length
                });
            }
        } catch (error) {
            console.error('Failed to load featured games:', error);
            this.showSectionError('featured-games-section', 'Failed to load featured games');
        }
    }

    /**
     * Load games on sale section
     */
    async loadSaleGames() {
        try {
            const saleGames = await this.apiService.getGamesOnSale(12);
            this.renderSaleGames(saleGames);
            
            // Track analytics
            if (this.analyticsService) {
                this.analyticsService.trackEvent('games_loaded', {
                    section: 'sale',
                    count: saleGames.length
                });
            }
        } catch (error) {
            console.error('Failed to load sale games:', error);
            this.showSectionError('sale-games-section', 'Failed to load sale games');
        }
    }

    /**
     * Load popular categories
     */
    async loadPopularCategories() {
        try {
            const categories = await this.apiService.getPopularCategories(8);
            this.renderPopularCategories(categories);
        } catch (error) {
            console.error('Failed to load categories:', error);
            this.showSectionError('categories-section', 'Failed to load categories');
        }
    }

    /**
     * Load shop page content
     */
    async loadShopContent() {
        this.showLoading();
        
        try {
            // Load initial games with pagination
            const searchParams = this.buildSearchParams();
            const gamesData = await this.apiService.searchGames(searchParams);
            
            this.renderShopGames(gamesData);
            this.updatePaginationInfo(gamesData);
            
        } catch (error) {
            console.error('Failed to load shop content:', error);
            this.showError('Failed to load games. Please refresh the page.');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Load product details
     */
    async loadProductDetails() {
        const gameId = this.getGameIdFromURL();
        if (!gameId) {
            this.showError('Game not found.');
            return;
        }

        this.showLoading();
        
        try {
            // Load game details
            const gameDetails = await this.apiService.getGameDetails(gameId);
            this.renderGameDetails(gameDetails);
            
            // Load related games
            const relatedGames = await this.apiService.getRelatedGames(gameId, 6);
            this.renderRelatedGames(relatedGames);
            
            // Load reviews
            const reviews = await this.apiService.getGameReviews(gameId, 1, 5);
            this.renderGameReviews(reviews);
            
        } catch (error) {
            console.error('Failed to load product details:', error);
            this.showError('Failed to load game details. Please refresh the page.');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Perform search with given query
     */
    async performSearch(query) {
        if (this.isLoading) return;
        
        this.currentSearchQuery = query;
        this.showLoading();
        
        try {
            const searchParams = {
                q: query,
                ...this.currentFilters,
                page: 1,
                per_page: 20
            };
            
            const searchResults = await this.apiService.searchGames(searchParams);
            this.renderSearchResults(searchResults);
            
            // Track search analytics
            if (this.analyticsService) {
                this.analyticsService.trackEvent('search_performed', {
                    query: query,
                    results_count: searchResults.games.length
                });
            }
            
        } catch (error) {
            console.error('Search failed:', error);
            this.showError('Search failed. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Clear search and show default content
     */
    clearSearch() {
        this.currentSearchQuery = '';
        this.currentFilters = {};
        this.loadInitialContent();
    }

    /**
     * Add game to cart
     */
    async addToCart(gameId, gameTitle) {
        if (!window.authService || !window.authService.isAuthenticated()) {
            this.showLoginPrompt();
            return;
        }

        try {
            const button = document.querySelector(`[data-game-id="${gameId}"]`);
            if (button) {
                button.disabled = true;
                button.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Adding...';
            }

            // Add to cart via API
            await this.apiService.post('order', '/cart/items', {
                game_id: gameId,
                quantity: 1
            });

            // Update cart UI
            this.updateCartIndicator();
            
            // Show success message
            this.showSuccessMessage(`${gameTitle} added to cart!`);
            
            // Track analytics
            if (this.analyticsService) {
                this.analyticsService.trackEvent('add_to_cart', {
                    game_id: gameId,
                    game_title: gameTitle
                });
            }

        } catch (error) {
            console.error('Failed to add to cart:', error);
            this.showError('Failed to add to cart. Please try again.');
        } finally {
            const button = document.querySelector(`[data-game-id="${gameId}"]`);
            if (button) {
                button.disabled = false;
                button.innerHTML = '<i class="fa fa-shopping-cart"></i> Add to Cart';
            }
        }
    }

    /**
     * View game details
     */
    viewGameDetails(gameId) {
        // Track analytics
        if (this.analyticsService) {
            this.analyticsService.trackEvent('game_view', {
                game_id: gameId
            });
        }

        // Navigate to product details page
        window.location.href = `product-details.html?id=${gameId}`;
    }

    /**
     * Show quick view modal
     */
    async showQuickView(gameId) {
        try {
            const gameDetails = await this.apiService.getGameDetails(gameId);
            this.renderQuickViewModal(gameDetails);
            
            // Track analytics
            if (this.analyticsService) {
                this.analyticsService.trackEvent('quick_view', {
                    game_id: gameId
                });
            }
        } catch (error) {
            console.error('Failed to load quick view:', error);
            this.showError('Failed to load game details.');
        }
    }

    /**
     * Render trending games section
     */
    renderTrendingGames(games) {
        const container = document.getElementById('trending-games-container');
        if (!container) return;

        const html = games.map(game => this.createGameCard(game, 'trending')).join('');
        container.innerHTML = html;
    }

    /**
     * Render featured games section
     */
    renderFeaturedGames(games) {
        const container = document.getElementById('featured-games-container');
        if (!container) return;

        const html = games.map(game => this.createGameCard(game, 'featured')).join('');
        container.innerHTML = html;
    }

    /**
     * Render sale games section
     */
    renderSaleGames(games) {
        const container = document.getElementById('sale-games-container');
        if (!container) return;

        const html = games.map(game => this.createGameCard(game, 'sale')).join('');
        container.innerHTML = html;
    }

    /**
     * Render popular categories
     */
    renderPopularCategories(categories) {
        const container = document.getElementById('categories-container');
        if (!container) return;

        const html = categories.map(category => this.createCategoryCard(category)).join('');
        container.innerHTML = html;
    }

    /**
     * Create game card HTML
     */
    createGameCard(game, type = 'default') {
        const discountBadge = game.is_on_sale ? 
            `<div class="discount-badge">-${game.discount_percentage}%</div>` : '';
        
        const priceHTML = game.is_on_sale ? 
            `<span class="original-price">$${game.price}</span>
             <span class="discounted-price">$${game.discounted_price}</span>` :
            `<span class="price">$${game.price}</span>`;

        return `
            <div class="col-lg-3 col-md-6 col-sm-12">
                <div class="game-card" data-game-id="${game.id}">
                    ${discountBadge}
                    <div class="game-image">
                        <img src="${game.cover_image_url}" alt="${game.title}" class="img-fluid">
                        <div class="game-overlay">
                            <button class="btn btn-primary quick-view-btn" data-game-id="${game.id}">
                                <i class="fa fa-eye"></i> Quick View
                            </button>
                        </div>
                    </div>
                    <div class="game-info">
                        <h4 class="game-title">${game.title}</h4>
                        <p class="game-publisher">${game.publisher?.name || 'Unknown Publisher'}</p>
                        <div class="game-rating">
                            ${this.renderStarRating(game.average_rating || 0)}
                            <span class="rating-count">(${game.review_count || 0})</span>
                        </div>
                        <div class="game-price">
                            ${priceHTML}
                        </div>
                        <div class="game-platforms">
                            ${this.renderPlatforms(game.platform)}
                        </div>
                        <div class="game-actions">
                            <button class="btn btn-success add-to-cart-btn" 
                                    data-game-id="${game.id}" 
                                    data-game-title="${game.title}">
                                <i class="fa fa-shopping-cart"></i> Add to Cart
                            </button>
                            <button class="btn btn-outline-primary view-details-btn" 
                                    data-game-id="${game.id}">
                                <i class="fa fa-info-circle"></i> Details
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Create category card HTML
     */
    createCategoryCard(category) {
        return `
            <div class="col-lg-3 col-md-6 col-sm-12">
                <div class="category-card category-filter" data-category="${category.slug}">
                    <div class="category-image">
                        <img src="${category.image_url}" alt="${category.name}" class="img-fluid">
                    </div>
                    <div class="category-info">
                        <h4 class="category-name">${category.name}</h4>
                        <p class="category-count">${category.game_count} games</p>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render star rating
     */
    renderStarRating(rating) {
        const stars = [];
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 !== 0;

        for (let i = 0; i < fullStars; i++) {
            stars.push('<i class="fa fa-star"></i>');
        }

        if (hasHalfStar) {
            stars.push('<i class="fa fa-star-half-o"></i>');
        }

        const emptyStars = 5 - Math.ceil(rating);
        for (let i = 0; i < emptyStars; i++) {
            stars.push('<i class="fa fa-star-o"></i>');
        }

        return stars.join('');
    }

    /**
     * Render platforms
     */
    renderPlatforms(platforms) {
        if (!platforms || platforms.length === 0) return '';
        
        return platforms.map(platform => 
            `<span class="platform-badge platform-${platform.toLowerCase()}">${platform}</span>`
        ).join('');
    }

    /**
     * Show loading indicator
     */
    showLoading() {
        this.isLoading = true;
        const loadingIndicator = document.getElementById('loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'block';
        }
    }

    /**
     * Hide loading indicator
     */
    hideLoading() {
        this.isLoading = false;
        const loadingIndicator = document.getElementById('loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        // Create or update error message element
        let errorElement = document.getElementById('error-message');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.id = 'error-message';
            errorElement.className = 'alert alert-danger';
            document.body.appendChild(errorElement);
        }

        errorElement.innerHTML = `
            <i class="fa fa-exclamation-triangle"></i> ${message}
            <button type="button" class="btn-close" onclick="this.parentElement.style.display='none'"></button>
        `;
        errorElement.style.display = 'block';

        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorElement.style.display = 'none';
        }, 5000);
    }

    /**
     * Show success message
     */
    showSuccessMessage(message) {
        // Create or update success message element
        let successElement = document.getElementById('success-message');
        if (!successElement) {
            successElement = document.createElement('div');
            successElement.id = 'success-message';
            successElement.className = 'alert alert-success';
            document.body.appendChild(successElement);
        }

        successElement.innerHTML = `
            <i class="fa fa-check-circle"></i> ${message}
            <button type="button" class="btn-close" onclick="this.parentElement.style.display='none'"></button>
        `;
        successElement.style.display = 'block';

        // Auto-hide after 3 seconds
        setTimeout(() => {
            successElement.style.display = 'none';
        }, 3000);
    }

    /**
     * Setup error handling
     */
    setupErrorHandling() {
        window.addEventListener('error', (event) => {
            console.error('JavaScript error:', event.error);
            this.showError('Something went wrong. Please refresh the page.');
        });

        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            this.showError('A network error occurred. Please check your connection.');
        });
    }

    /**
     * Get game ID from URL parameters
     */
    getGameIdFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('id');
    }

    /**
     * Build search parameters object
     */
    buildSearchParams() {
        return {
            q: this.currentSearchQuery,
            ...this.currentFilters,
            page: 1,
            per_page: 20
        };
    }

    /**
     * Show login prompt
     */
    showLoginPrompt() {
        if (confirm('You need to log in to add items to your cart. Would you like to log in now?')) {
            window.location.href = 'login.html';
        }
    }

    /**
     * Update cart indicator
     */
    async updateCartIndicator() {
        try {
            const cartData = await this.apiService.get('order', '/cart');
            const cartCount = cartData.items ? cartData.items.length : 0;
            
            const cartIndicator = document.getElementById('cart-count');
            if (cartIndicator) {
                cartIndicator.textContent = cartCount;
                cartIndicator.style.display = cartCount > 0 ? 'inline' : 'none';
            }
        } catch (error) {
            console.error('Failed to update cart indicator:', error);
        }
    }

    // Additional methods for filtering, sorting, etc. would go here
    // These methods are placeholders for future implementation
    
    filterByCategory(category) {
        this.currentFilters.category = category;
        this.performSearch(this.currentSearchQuery);
    }

    updatePriceFilters() {
        // Implementation for price filtering
        console.log('Price filters updated');
    }

    updatePlatformFilters() {
        // Implementation for platform filtering
        console.log('Platform filters updated');
    }

    sortGames(sortBy) {
        this.currentFilters.sort_by = sortBy;
        this.performSearch(this.currentSearchQuery);
    }

    loadMoreGames() {
        // Implementation for loading more games
        console.log('Loading more games...');
    }

    showSectionError(sectionId, message) {
        const section = document.getElementById(sectionId);
        if (section) {
            section.innerHTML = `<div class="alert alert-warning">${message}</div>`;
        }
    }

    renderSearchResults(searchResults) {
        // Implementation for rendering search results
        console.log('Rendering search results:', searchResults);
    }

    renderShopGames(gamesData) {
        // Implementation for rendering shop games
        console.log('Rendering shop games:', gamesData);
    }

    updatePaginationInfo(gamesData) {
        // Implementation for updating pagination
        console.log('Updating pagination:', gamesData);
    }

    renderGameDetails(gameDetails) {
        // Implementation for rendering game details
        console.log('Rendering game details:', gameDetails);
    }

    renderRelatedGames(relatedGames) {
        // Implementation for rendering related games
        console.log('Rendering related games:', relatedGames);
    }

    renderGameReviews(reviews) {
        // Implementation for rendering game reviews
        console.log('Rendering game reviews:', reviews);
    }

    renderQuickViewModal(gameDetails) {
        // Implementation for rendering quick view modal
        console.log('Rendering quick view modal:', gameDetails);
    }
}

// Initialize game integration when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Wait for API service to be ready
    if (window.apiService) {
        window.gameIntegration = new GameIntegration();
        console.log('Game Integration initialized');
    } else {
        console.error('API Service not available');
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GameIntegration;
}
