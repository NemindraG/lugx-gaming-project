/**
 * LugX Gaming Shop Page Enhancement
 * Transforms static shop page into dynamic, API-driven shopping experience
 * Provides pagination, filtering, search, and real-time game data
 */

class ShopEnhancer {
    constructor() {
        this.config = {
            gamesPerPage: 12,
            defaultCategory: 'all',
            defaultSort: 'featured',
            searchDebounceDelay: 300,
            maxRetries: 3,
            cacheTimeout: 5 * 60 * 1000, // 5 minutes
            enableDebugLogging: window.location.hostname === 'localhost'
        };

        this.state = {
            currentPage: 1,
            totalPages: 1,
            totalGames: 0,
            currentCategory: this.config.defaultCategory,
            currentSort: this.config.defaultSort,
            searchQuery: '',
            games: [],
            categories: [],
            loading: false,
            filters: {
                priceRange: { min: 0, max: 100 },
                rating: 0,
                platform: 'all'
            }
        };

        this.cache = new Map();
        this.searchTimeout = null;
        this.isInitialized = false;

        this.initializeShop();
    }

    async initializeShop() {
        try {
            this.log('Initializing shop enhancement...');

            // Wait for dependencies
            await this.waitForDependencies();

            // Setup shop UI components
            this.setupShopUI();

            // Load initial data
            await this.loadInitialData();

            // Setup event listeners
            this.setupEventListeners();

            this.isInitialized = true;
            this.log('Shop enhancement initialized successfully');

            // Track shop page view
            if (window.analyticsService) {
                window.analyticsService.trackPageView({
                    page_type: 'shop',
                    category: this.state.currentCategory,
                    sort_by: this.state.currentSort
                });
            }

        } catch (error) {
            console.error('Shop enhancement initialization failed:', error);
            this.handleInitializationError(error);
        }
    }

    async waitForDependencies() {
        const maxWaitTime = 5000; // 5 seconds
        const checkInterval = 100; // 100ms
        let waited = 0;

        while (waited < maxWaitTime) {
            if (window.apiService && window.analyticsService && window.cartIntegration) {
                return;
            }
            await this.delay(checkInterval);
            waited += checkInterval;
        }

        this.log('Dependencies not fully ready, proceeding with available services');
    }

    setupShopUI() {
        this.enhanceFilterSection();
        this.addSearchAndSortControls();
        this.setupLoadingStates();
        this.addShopStyles();
    }

    enhanceFilterSection() {
        const filterContainer = document.querySelector('.trending-filter');
        if (!filterContainer) return;

        // Add enhanced filter controls
        const enhancedFilterHTML = `
            <div class="shop-controls">
                <div class="row">
                    <div class="col-lg-4">
                        <div class="search-container">
                            <input type="text" id="gameSearch" class="search-input" 
                                   placeholder="Search games..." autocomplete="off">
                            <i class="fa fa-search search-icon"></i>
                        </div>
                    </div>
                    <div class="col-lg-2">
                        <select id="sortSelect" class="sort-select">
                            <option value="featured">Featured</option>
                            <option value="name_asc">Name A-Z</option>
                            <option value="name_desc">Name Z-A</option>
                            <option value="price_asc">Price Low-High</option>
                            <option value="price_desc">Price High-Low</option>
                            <option value="rating_desc">Highest Rated</option>
                            <option value="newest">Newest First</option>
                        </select>
                    </div>
                    <div class="col-lg-2">
                        <select id="platformSelect" class="platform-select">
                            <option value="all">All Platforms</option>
                            <option value="pc">PC</option>
                            <option value="playstation">PlayStation</option>
                            <option value="xbox">Xbox</option>
                            <option value="nintendo">Nintendo</option>
                        </select>
                    </div>
                    <div class="col-lg-2">
                        <div class="price-filter">
                            <select id="priceFilter" class="price-filter-select">
                                <option value="all">All Prices</option>
                                <option value="0-20">Under $20</option>
                                <option value="20-40">$20 - $40</option>
                                <option value="40-60">$40 - $60</option>
                                <option value="60-100">$60+</option>
                            </select>
                        </div>
                    </div>
                    <div class="col-lg-2">
                        <button id="clearFilters" class="clear-filters-btn">
                            <i class="fa fa-times"></i> Clear
                        </button>
                    </div>
                </div>
            </div>
        `;

        filterContainer.insertAdjacentHTML('afterend', enhancedFilterHTML);
    }

    addSearchAndSortControls() {
        // Already added in enhanceFilterSection
        this.setupSearchAutocomplete();
    }

    setupSearchAutocomplete() {
        const searchInput = document.getElementById('gameSearch');
        if (!searchInput) return;

        let autocompleteContainer = document.querySelector('.search-autocomplete');
        if (!autocompleteContainer) {
            autocompleteContainer = document.createElement('div');
            autocompleteContainer.className = 'search-autocomplete';
            searchInput.parentNode.appendChild(autocompleteContainer);
        }

        searchInput.addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.handleSearchInput(e.target.value);
            }, this.config.searchDebounceDelay);
        });

        searchInput.addEventListener('blur', () => {
            setTimeout(() => {
                autocompleteContainer.style.display = 'none';
            }, 200);
        });

        searchInput.addEventListener('focus', () => {
            if (searchInput.value.length > 2) {
                this.showSearchSuggestions(searchInput.value);
            }
        });
    }

    setupLoadingStates() {
        const gamesContainer = document.querySelector('.trending-box');
        if (!gamesContainer) return;

        // Add loading overlay
        const loadingHTML = `
            <div class="shop-loading" id="shopLoading" style="display: none;">
                <div class="loading-content">
                    <div class="spinner-border text-primary" role="status">
                        <span class="sr-only">Loading...</span>
                    </div>
                    <p class="mt-3">Loading games...</p>
                </div>
            </div>
        `;

        gamesContainer.insertAdjacentHTML('beforebegin', loadingHTML);
    }

    addShopStyles() {
        if (document.getElementById('shop-enhancer-styles')) {
            return; // Styles already added
        }

        const styles = `
            <style id="shop-enhancer-styles">
                .shop-controls {
                    background: white;
                    padding: 20px;
                    border-radius: 12px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                    margin-bottom: 30px;
                }
                
                .search-container {
                    position: relative;
                }
                
                .search-input {
                    width: 100%;
                    padding: 12px 40px 12px 16px;
                    border: 2px solid #e1e5e9;
                    border-radius: 8px;
                    font-size: 16px;
                    transition: border-color 0.3s ease;
                }
                
                .search-input:focus {
                    outline: none;
                    border-color: #007bff;
                    box-shadow: 0 0 0 3px rgba(0,123,255,0.1);
                }
                
                .search-icon {
                    position: absolute;
                    right: 12px;
                    top: 50%;
                    transform: translateY(-50%);
                    color: #666;
                }
                
                .search-autocomplete {
                    position: absolute;
                    top: 100%;
                    left: 0;
                    right: 0;
                    background: white;
                    border: 1px solid #ddd;
                    border-top: none;
                    border-radius: 0 0 8px 8px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    z-index: 1000;
                    max-height: 200px;
                    overflow-y: auto;
                    display: none;
                }
                
                .autocomplete-item {
                    padding: 10px 16px;
                    cursor: pointer;
                    border-bottom: 1px solid #eee;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                
                .autocomplete-item:hover {
                    background: #f8f9fa;
                }
                
                .autocomplete-item img {
                    width: 30px;
                    height: 30px;
                    object-fit: cover;
                    border-radius: 4px;
                }
                
                .sort-select, .platform-select, .price-filter-select {
                    width: 100%;
                    padding: 12px 16px;
                    border: 2px solid #e1e5e9;
                    border-radius: 8px;
                    font-size: 16px;
                    background: white;
                    cursor: pointer;
                }
                
                .clear-filters-btn {
                    width: 100%;
                    padding: 12px 16px;
                    background: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 16px;
                    cursor: pointer;
                    transition: background-color 0.3s ease;
                }
                
                .clear-filters-btn:hover {
                    background: #5a6268;
                }
                
                .shop-loading {
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(255,255,255,0.9);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 100;
                    border-radius: 12px;
                }
                
                .loading-content {
                    text-align: center;
                }
                
                .game-item-enhanced {
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                }
                
                .game-item-enhanced:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 10px 25px rgba(0,0,0,0.15);
                }
                
                .game-rating {
                    display: flex;
                    align-items: center;
                    gap: 5px;
                    margin-top: 8px;
                    font-size: 14px;
                    color: #666;
                }
                
                .game-rating .stars {
                    color: #ffc107;
                }
                
                .game-actions {
                    display: flex;
                    gap: 10px;
                    align-items: center;
                    margin-top: 10px;
                }
                
                .quick-view-btn {
                    background: none;
                    border: 1px solid #007bff;
                    color: #007bff;
                    padding: 6px 12px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 14px;
                    transition: all 0.3s ease;
                }
                
                .quick-view-btn:hover {
                    background: #007bff;
                    color: white;
                }
                
                .add-to-cart-enhanced {
                    background: #28a745;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 14px;
                    transition: background-color 0.3s ease;
                }
                
                .add-to-cart-enhanced:hover {
                    background: #218838;
                }
                
                .game-tag {
                    display: inline-block;
                    background: #007bff;
                    color: white;
                    padding: 2px 8px;
                    border-radius: 12px;
                    font-size: 12px;
                    margin-right: 5px;
                    margin-bottom: 5px;
                }
                
                .game-tag.sale {
                    background: #dc3545;
                }
                
                .game-tag.new {
                    background: #28a745;
                }
                
                .pagination-enhanced {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    gap: 10px;
                    margin-top: 40px;
                }
                
                .pagination-enhanced button {
                    padding: 8px 16px;
                    border: 1px solid #007bff;
                    background: white;
                    color: #007bff;
                    border-radius: 4px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                }
                
                .pagination-enhanced button:hover:not(:disabled) {
                    background: #007bff;
                    color: white;
                }
                
                .pagination-enhanced button:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }
                
                .pagination-enhanced button.active {
                    background: #007bff;
                    color: white;
                }
                
                .results-info {
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    text-align: center;
                    color: #666;
                }
                
                .no-results {
                    text-align: center;
                    padding: 60px 20px;
                    color: #666;
                }
                
                .no-results i {
                    font-size: 48px;
                    color: #ddd;
                    margin-bottom: 20px;
                }
                
                @media (max-width: 768px) {
                    .shop-controls .row > div {
                        margin-bottom: 15px;
                    }
                    
                    .game-actions {
                        flex-direction: column;
                        gap: 8px;
                    }
                    
                    .quick-view-btn,
                    .add-to-cart-enhanced {
                        width: 100%;
                        text-align: center;
                    }
                }
            </style>
        `;

        document.head.insertAdjacentHTML('beforeend', styles);
    }

    async loadInitialData() {
        try {
            this.showLoading();

            // Load categories and initial games
            await Promise.all([
                this.loadCategories(),
                this.loadGames()
            ]);

            this.renderGameGrid();
            this.updateResultsInfo();
            this.updatePagination();

        } catch (error) {
            this.handleLoadError(error);
        } finally {
            this.hideLoading();
        }
    }

    async loadCategories() {
        try {
            const cacheKey = 'categories';
            
            if (this.cache.has(cacheKey)) {
                this.state.categories = this.cache.get(cacheKey);
                return;
            }

            this.log('Loading game categories...');
            const response = await window.apiService.get('game', '/games/categories');
            
            this.state.categories = response.categories || [];
            this.cache.set(cacheKey, this.state.categories);

            this.updateCategoryFilter();

        } catch (error) {
            this.log('Failed to load categories:', error);
            // Use fallback categories
            this.state.categories = [
                { id: 'action', name: 'Action', count: 0 },
                { id: 'adventure', name: 'Adventure', count: 0 },
                { id: 'strategy', name: 'Strategy', count: 0 },
                { id: 'racing', name: 'Racing', count: 0 }
            ];
        }
    }

    async loadGames() {
        try {
            this.log('Loading games...', this.state);

            const params = {
                page: this.state.currentPage,
                limit: this.config.gamesPerPage,
                category: this.state.currentCategory !== 'all' ? this.state.currentCategory : undefined,
                sort: this.state.currentSort,
                search: this.state.searchQuery || undefined,
                platform: this.state.filters.platform !== 'all' ? this.state.filters.platform : undefined,
                min_price: this.state.filters.priceRange.min,
                max_price: this.state.filters.priceRange.max > 0 ? this.state.filters.priceRange.max : undefined,
                min_rating: this.state.filters.rating > 0 ? this.state.filters.rating : undefined
            };

            // Remove undefined values
            Object.keys(params).forEach(key => {
                if (params[key] === undefined) {
                    delete params[key];
                }
            });

            const cacheKey = JSON.stringify(params);
            
            if (this.cache.has(cacheKey)) {
                const cachedData = this.cache.get(cacheKey);
                if (Date.now() - cachedData.timestamp < this.config.cacheTimeout) {
                    this.state.games = cachedData.games;
                    this.state.totalGames = cachedData.totalGames;
                    this.state.totalPages = cachedData.totalPages;
                    return;
                }
            }

            const response = await window.apiService.get('game', '/games', params);

            this.state.games = response.games || [];
            this.state.totalGames = response.total || 0;
            this.state.totalPages = Math.ceil(this.state.totalGames / this.config.gamesPerPage);

            // Cache the response
            this.cache.set(cacheKey, {
                games: this.state.games,
                totalGames: this.state.totalGames,
                totalPages: this.state.totalPages,
                timestamp: Date.now()
            });

        } catch (error) {
            this.log('Failed to load games:', error);
            
            if (this.state.currentPage === 1) {
                // Use fallback games for first page
                this.state.games = this.generateFallbackGames();
                this.state.totalGames = this.state.games.length;
                this.state.totalPages = 1;
            } else {
                throw error;
            }
        }
    }

    generateFallbackGames() {
        return [
            {
                id: 'fallback-1',
                name: 'Assassin\'s Creed Valhalla',
                category: 'Action',
                price: 59.99,
                discount_price: 39.99,
                rating: 4.5,
                image_url: 'assets/images/trending-01.jpg',
                platform: ['PC', 'PlayStation', 'Xbox'],
                tags: ['new', 'sale']
            },
            {
                id: 'fallback-2',
                name: 'Cyberpunk 2077',
                category: 'Action',
                price: 49.99,
                discount_price: 29.99,
                rating: 4.2,
                image_url: 'assets/images/trending-02.jpg',
                platform: ['PC', 'PlayStation', 'Xbox'],
                tags: ['sale']
            },
            {
                id: 'fallback-3',
                name: 'The Witcher 3',
                category: 'Adventure',
                price: 39.99,
                discount_price: 19.99,
                rating: 4.8,
                image_url: 'assets/images/trending-03.jpg',
                platform: ['PC', 'PlayStation', 'Xbox', 'Nintendo'],
                tags: ['sale']
            },
            {
                id: 'fallback-4',
                name: 'Civilization VI',
                category: 'Strategy',
                price: 59.99,
                discount_price: null,
                rating: 4.6,
                image_url: 'assets/images/trending-04.jpg',
                platform: ['PC'],
                tags: []
            }
        ];
    }

    setupEventListeners() {
        // Category filter clicks
        document.addEventListener('click', (e) => {
            if (e.target.matches('.trending-filter a')) {
                e.preventDefault();
                this.handleCategoryChange(e.target);
            }
        });

        // Sort selection
        const sortSelect = document.getElementById('sortSelect');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.handleSortChange(e.target.value);
            });
        }

        // Platform filter
        const platformSelect = document.getElementById('platformSelect');
        if (platformSelect) {
            platformSelect.addEventListener('change', (e) => {
                this.handlePlatformChange(e.target.value);
            });
        }

        // Price filter
        const priceFilter = document.getElementById('priceFilter');
        if (priceFilter) {
            priceFilter.addEventListener('change', (e) => {
                this.handlePriceFilterChange(e.target.value);
            });
        }

        // Clear filters
        const clearFiltersBtn = document.getElementById('clearFilters');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => {
                this.clearAllFilters();
            });
        }

        // Quick view buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('.quick-view-btn') || e.target.closest('.quick-view-btn')) {
                e.preventDefault();
                const gameId = this.extractGameId(e.target);
                this.handleQuickView(gameId);
            }
        });

        // Pagination
        document.addEventListener('click', (e) => {
            if (e.target.matches('.pagination-btn')) {
                e.preventDefault();
                const page = parseInt(e.target.dataset.page);
                this.handlePageChange(page);
            }
        });
    }

    async handleSearchInput(query) {
        this.state.searchQuery = query.trim();
        this.state.currentPage = 1;

        if (query.length > 2) {
            this.showSearchSuggestions(query);
        } else {
            this.hideSearchSuggestions();
        }

        await this.refreshGames();

        // Track search
        if (window.analyticsService && query.length > 2) {
            window.analyticsService.track('shop_search', {
                query: query,
                results_count: this.state.totalGames
            });
        }
    }

    async showSearchSuggestions(query) {
        try {
            const response = await window.apiService.get('game', '/games/search/suggest', {
                q: query,
                limit: 5
            });

            const suggestions = response.suggestions || [];
            this.renderSearchSuggestions(suggestions);

        } catch (error) {
            this.log('Failed to load search suggestions:', error);
        }
    }

    renderSearchSuggestions(suggestions) {
        const container = document.querySelector('.search-autocomplete');
        if (!container) return;

        if (suggestions.length === 0) {
            container.style.display = 'none';
            return;
        }

        const suggestionsHTML = suggestions.map(game => `
            <div class="autocomplete-item" data-game-id="${game.id}">
                <img src="${game.image_url || 'assets/images/default-game.jpg'}" 
                     alt="${game.name}" 
                     onerror="this.src='assets/images/default-game.jpg'">
                <div>
                    <div class="suggestion-name">${game.name}</div>
                    <div class="suggestion-category">${game.category}</div>
                </div>
            </div>
        `).join('');

        container.innerHTML = suggestionsHTML;
        container.style.display = 'block';

        // Add click handlers for suggestions
        container.querySelectorAll('.autocomplete-item').forEach(item => {
            item.addEventListener('click', () => {
                const gameName = item.querySelector('.suggestion-name').textContent;
                document.getElementById('gameSearch').value = gameName;
                this.handleSearchInput(gameName);
                container.style.display = 'none';
            });
        });
    }

    hideSearchSuggestions() {
        const container = document.querySelector('.search-autocomplete');
        if (container) {
            container.style.display = 'none';
        }
    }

    async handleCategoryChange(link) {
        // Update active state
        document.querySelectorAll('.trending-filter a').forEach(a => {
            a.classList.remove('is_active');
        });
        link.classList.add('is_active');

        // Extract category from data-filter attribute
        const filter = link.dataset.filter;
        this.state.currentCategory = filter === '*' ? 'all' : this.mapFilterToCategory(filter);
        this.state.currentPage = 1;

        await this.refreshGames();

        // Track category change
        if (window.analyticsService) {
            window.analyticsService.track('shop_category_change', {
                category: this.state.currentCategory
            });
        }
    }

    mapFilterToCategory(filter) {
        const filterMap = {
            '.adv': 'adventure',
            '.str': 'strategy',
            '.rac': 'racing',
            '.act': 'action'
        };
        return filterMap[filter] || 'all';
    }

    async handleSortChange(sort) {
        this.state.currentSort = sort;
        this.state.currentPage = 1;
        await this.refreshGames();

        // Track sort change
        if (window.analyticsService) {
            window.analyticsService.track('shop_sort_change', {
                sort_by: sort
            });
        }
    }

    async handlePlatformChange(platform) {
        this.state.filters.platform = platform;
        this.state.currentPage = 1;
        await this.refreshGames();
    }

    async handlePriceFilterChange(priceRange) {
        if (priceRange === 'all') {
            this.state.filters.priceRange = { min: 0, max: 0 };
        } else {
            const [min, max] = priceRange.split('-').map(Number);
            this.state.filters.priceRange = { min, max: max || 999 };
        }
        
        this.state.currentPage = 1;
        await this.refreshGames();
    }

    async clearAllFilters() {
        this.state.currentCategory = this.config.defaultCategory;
        this.state.currentSort = this.config.defaultSort;
        this.state.searchQuery = '';
        this.state.currentPage = 1;
        this.state.filters = {
            priceRange: { min: 0, max: 0 },
            rating: 0,
            platform: 'all'
        };

        // Reset UI controls
        document.getElementById('gameSearch').value = '';
        document.getElementById('sortSelect').value = this.config.defaultSort;
        document.getElementById('platformSelect').value = 'all';
        document.getElementById('priceFilter').value = 'all';

        // Reset category filter
        document.querySelectorAll('.trending-filter a').forEach(a => {
            a.classList.remove('is_active');
        });
        document.querySelector('.trending-filter a[data-filter="*"]')?.classList.add('is_active');

        await this.refreshGames();
    }

    async handlePageChange(page) {
        if (page < 1 || page > this.state.totalPages || page === this.state.currentPage) {
            return;
        }

        this.state.currentPage = page;
        await this.refreshGames();

        // Scroll to top of games section
        document.querySelector('.trending-box')?.scrollIntoView({ 
            behavior: 'smooth' 
        });
    }

    async handleQuickView(gameId) {
        try {
            // Track quick view
            if (window.analyticsService) {
                window.analyticsService.track('game_quick_view', {
                    game_id: gameId,
                    source: 'shop_page'
                });
            }

            // Redirect to product details page
            window.location.href = `product-details.html?id=${gameId}`;

        } catch (error) {
            console.error('Quick view failed:', error);
        }
    }

    async refreshGames() {
        try {
            this.showLoading();
            await this.loadGames();
            this.renderGameGrid();
            this.updateResultsInfo();
            this.updatePagination();
        } catch (error) {
            this.handleLoadError(error);
        } finally {
            this.hideLoading();
        }
    }

    renderGameGrid() {
        const container = document.querySelector('.trending-box');
        if (!container) return;

        if (this.state.games.length === 0) {
            this.renderNoResults(container);
            return;
        }

        const gamesHTML = this.state.games.map(game => this.renderGameCard(game)).join('');
        container.innerHTML = gamesHTML;

        // Add enhanced styling and interactions
        container.querySelectorAll('.item').forEach(item => {
            item.classList.add('game-item-enhanced');
        });
    }

    renderGameCard(game) {
        const discountPercentage = game.discount_price 
            ? Math.round(((game.price - game.discount_price) / game.price) * 100)
            : 0;

        const currentPrice = game.discount_price || game.price;
        const originalPrice = game.discount_price ? game.price : null;

        const tagsHTML = game.tags && game.tags.length > 0 
            ? game.tags.map(tag => `<span class="game-tag ${tag}">${tag.toUpperCase()}</span>`).join('')
            : '';

        const ratingHTML = game.rating 
            ? `<div class="game-rating">
                 <span class="stars">${'★'.repeat(Math.floor(game.rating))}</span>
                 <span>${game.rating.toFixed(1)}</span>
               </div>`
            : '';

        return `
            <div class="col-lg-3 col-md-6 align-self-center mb-30 trending-items" data-game-id="${game.id}">
                <div class="item">
                    <div class="thumb">
                        <a href="product-details.html?id=${game.id}">
                            <img src="${game.image_url || 'assets/images/default-game.jpg'}" 
                                 alt="${game.name}"
                                 onerror="this.src='assets/images/default-game.jpg'">
                        </a>
                        <span class="price">
                            ${originalPrice ? `<em>$${originalPrice.toFixed(2)}</em>` : ''}
                            $${currentPrice.toFixed(2)}
                        </span>
                        ${discountPercentage > 0 ? `<span class="discount">-${discountPercentage}%</span>` : ''}
                    </div>
                    <div class="down-content">
                        ${tagsHTML}
                        <span class="category">${game.category}</span>
                        <h4>${game.name}</h4>
                        ${ratingHTML}
                        <div class="game-actions">
                            <button class="quick-view-btn" data-game-id="${game.id}" title="Quick View">
                                <i class="fa fa-eye"></i> View
                            </button>
                            <button class="add-to-cart-enhanced add-to-cart" 
                                    data-game-id="${game.id}" 
                                    data-track-click="add-to-cart"
                                    title="Add to Cart">
                                <i class="fa fa-shopping-bag"></i> Add
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderNoResults(container) {
        container.innerHTML = `
            <div class="col-12">
                <div class="no-results">
                    <i class="fa fa-search"></i>
                    <h3>No games found</h3>
                    <p>Try adjusting your search or filters to find what you're looking for.</p>
                    <button class="btn btn-primary" onclick="window.shopEnhancer.clearAllFilters()">
                        Clear All Filters
                    </button>
                </div>
            </div>
        `;
    }

    updateResultsInfo() {
        let resultsContainer = document.querySelector('.results-info');
        if (!resultsContainer) {
            const shopSection = document.querySelector('.section.trending .container');
            if (shopSection) {
                resultsContainer = document.createElement('div');
                resultsContainer.className = 'results-info';
                shopSection.insertBefore(resultsContainer, document.querySelector('.trending-box'));
            }
        }

        if (!resultsContainer) return;

        const startItem = (this.state.currentPage - 1) * this.config.gamesPerPage + 1;
        const endItem = Math.min(startItem + this.state.games.length - 1, this.state.totalGames);

        let infoText = `Showing ${startItem}-${endItem} of ${this.state.totalGames} games`;

        if (this.state.searchQuery) {
            infoText += ` for "${this.state.searchQuery}"`;
        }

        if (this.state.currentCategory !== 'all') {
            infoText += ` in ${this.state.currentCategory}`;
        }

        resultsContainer.textContent = infoText;
    }

    updatePagination() {
        const existingPagination = document.querySelector('.pagination');
        if (existingPagination) {
            existingPagination.parentNode.innerHTML = this.renderPagination();
        }
    }

    renderPagination() {
        if (this.state.totalPages <= 1) {
            return '<div class="col-lg-12"></div>';
        }

        const currentPage = this.state.currentPage;
        const totalPages = this.state.totalPages;
        
        let paginationHTML = '<div class="pagination-enhanced">';

        // Previous button
        paginationHTML += `
            <button class="pagination-btn" 
                    data-page="${currentPage - 1}" 
                    ${currentPage === 1 ? 'disabled' : ''}>
                <i class="fa fa-chevron-left"></i> Previous
            </button>
        `;

        // Page numbers
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);

        if (startPage > 1) {
            paginationHTML += `<button class="pagination-btn" data-page="1">1</button>`;
            if (startPage > 2) {
                paginationHTML += '<span class="pagination-ellipsis">...</span>';
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            paginationHTML += `
                <button class="pagination-btn ${i === currentPage ? 'active' : ''}" 
                        data-page="${i}">
                    ${i}
                </button>
            `;
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                paginationHTML += '<span class="pagination-ellipsis">...</span>';
            }
            paginationHTML += `<button class="pagination-btn" data-page="${totalPages}">${totalPages}</button>`;
        }

        // Next button
        paginationHTML += `
            <button class="pagination-btn" 
                    data-page="${currentPage + 1}" 
                    ${currentPage === totalPages ? 'disabled' : ''}>
                Next <i class="fa fa-chevron-right"></i>
            </button>
        `;

        paginationHTML += '</div>';

        return `<div class="col-lg-12">${paginationHTML}</div>`;
    }

    updateCategoryFilter() {
        // This would update the category filter with actual categories from API
        // For now, we'll keep the existing static filters
    }

    showLoading() {
        this.state.loading = true;
        const loadingElement = document.getElementById('shopLoading');
        if (loadingElement) {
            loadingElement.style.display = 'flex';
        }
    }

    hideLoading() {
        this.state.loading = false;
        const loadingElement = document.getElementById('shopLoading');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }

    handleLoadError(error) {
        console.error('Failed to load shop data:', error);
        
        // Show error message
        const container = document.querySelector('.trending-box');
        if (container) {
            container.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-warning text-center">
                        <h4>Unable to load games</h4>
                        <p>There was a problem loading the games. Please try again later.</p>
                        <button class="btn btn-primary" onclick="window.location.reload()">
                            Retry
                        </button>
                    </div>
                </div>
            `;
        }

        if (window.analyticsService) {
            window.analyticsService.trackError(error, { 
                context: 'shop_load_error' 
            });
        }
    }

    handleInitializationError(error) {
        console.error('Shop enhancement initialization failed:', error);
        
        // Continue with basic functionality
        this.setupBasicEventListeners();
    }

    setupBasicEventListeners() {
        // Basic category filtering for static content
        document.addEventListener('click', (e) => {
            if (e.target.matches('.trending-filter a')) {
                e.preventDefault();
                
                document.querySelectorAll('.trending-filter a').forEach(a => {
                    a.classList.remove('is_active');
                });
                e.target.classList.add('is_active');
                
                // Simple isotope filtering (if isotope is available)
                if (window.$ && window.$.fn.isotope) {
                    const filter = e.target.dataset.filter;
                    $('.trending-box').isotope({ filter: filter });
                }
            }
        });
    }

    // Utility methods
    extractGameId(element) {
        return element.dataset.gameId || 
               element.closest('[data-game-id]')?.dataset.gameId ||
               new URLSearchParams(window.location.search).get('id');
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    log(...args) {
        if (this.config.enableDebugLogging) {
            console.log('[ShopEnhancer]', ...args);
        }
    }

    // Public API methods
    async searchGames(query) {
        document.getElementById('gameSearch').value = query;
        await this.handleSearchInput(query);
    }

    async filterByCategory(category) {
        const filterLink = document.querySelector(`[data-filter="${category}"]`);
        if (filterLink) {
            await this.handleCategoryChange(filterLink);
        }
    }

    async sortGames(sortBy) {
        const sortSelect = document.getElementById('sortSelect');
        if (sortSelect) {
            sortSelect.value = sortBy;
            await this.handleSortChange(sortBy);
        }
    }

    getShopState() {
        return { ...this.state };
    }
}

// Initialize shop enhancement when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.shopEnhancer = new ShopEnhancer();
});

// Log initialization
console.log('LugX Shop Enhancement loaded');

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ShopEnhancer };
}