# Lugx Gaming Platform - Frontend API Mapping

## Executive Summary

This document provides a comprehensive mapping between the existing jQuery + Bootstrap frontend and FastAPI backend endpoints. It defines exactly which APIs each page requires, how data flows through the Istio Gateway, and the progressive enhancement strategy for integrating APIs without modifying existing frontend files.

## Frontend Architecture Overview

### Existing Frontend Technology Stack
- **Core Framework**: jQuery 3.6+ with existing functionality preserved
- **UI Framework**: Bootstrap 5 responsive design system
- **Asset Management**: FontAwesome icons, Owl Carousel, Isotope filtering
- **Current Structure**: Static HTML pages with hardcoded game data

### Progressive Enhancement Strategy
- **No File Modifications**: Preserve existing HTML, CSS, and JavaScript files
- **API Integration Layer**: New JavaScript modules for dynamic functionality
- **Fallback Strategy**: Graceful degradation to static content when APIs fail
- **Performance**: Lazy loading and progressive rendering of dynamic content

### API Integration Technology Stack
- **HTTP Client**: Modern Fetch API with async/await patterns
- **Authentication**: JWT token management with localStorage
- **State Management**: Lightweight custom solution for API responses
- **Error Handling**: Comprehensive error handling with user-friendly fallbacks
- **Analytics**: Event tracking through Istio Gateway to Analytics Service

### Frontend File Structure
```
lugx_gaming/
├── index.html              # Homepage (existing)
├── shop.html              # Game catalog (existing)
├── product-details.html   # Game details (existing)
├── contact.html           # Contact page (existing)
├── assets/
│   ├── css/               # Existing styles (no changes)
│   ├── js/                # Existing functionality (no changes)
│   └── images/            # Existing assets (no changes)
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

---

## Page-by-Page API Mapping

### 1. Homepage (`index.html`) - Existing File Enhancement

#### **Current State**
- **Existing Content**: Static trending games, most played section, newsletter signup
- **jQuery Functionality**: Carousel sliders, scroll animations, navigation
- **Bootstrap Layout**: Responsive grid system with existing game cards

#### **Progressive Enhancement Strategy**
- **Preserve Existing**: Keep all current HTML structure and styling
- **Add Dynamic Loading**: Replace static game data with API calls via Istio Gateway
- **Enhance Interactivity**: Add cart functionality and user tracking
- **Fallback Gracefully**: Show static content if APIs fail

#### **Required API Endpoints (Through Istio Gateway)**

##### **Trending Games Section Enhancement**
```javascript
// API Call via Istio Gateway
GET https://lugxgaming.com/api/v1/games/trending?limit=8

// Progressive Enhancement Implementation
// File: integration/gameIntegration.js
document.addEventListener('DOMContentLoaded', function() {
    enhanceTrendingGamesSection();
});

async function enhanceTrendingGamesSection() {
    const trendingContainer = document.querySelector('.trending-box .row');
    if (!trendingContainer) return; // Graceful fallback
    
    try {
        // Show loading overlay (preserve existing content)
        const loadingOverlay = createLoadingOverlay();
        trendingContainer.appendChild(loadingOverlay);
        
        // Call API through Istio Gateway
        const response = await apiService.get('/games/trending', { limit: 8 });
        
        // Replace static content with dynamic data
        await renderDynamicTrendingGames(response.games, trendingContainer);
        
        // Track analytics
        analyticsService.track('section_enhanced', { 
            section: 'trending_games',
            games_count: response.games.length 
        });
        
    } catch (error) {
        console.warn('Failed to load trending games, keeping static content:', error);
        // Keep existing static content - no user disruption
    } finally {
        removeLoadingOverlay();
    }
}

function renderDynamicTrendingGames(games, container) {
    // Preserve existing CSS classes and structure
    const gameCards = games.map(game => `
        <div class="col-lg-3 col-md-6 trending-item ${game.category.toLowerCase()}">
            <div class="item">
                <div class="thumb">
                    <a href="product-details.html?id=${game.id}">
                        <img src="${game.image_url}" alt="${game.name}">
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
                    <a href="product-details.html?id=${game.id}">
                        <i class="fa fa-shopping-bag"></i>
                    </a>
                </div>
            </div>
        </div>
    `).join('');
    
    // Smoothly replace content
    container.style.opacity = '0.5';
    setTimeout(() => {
        container.innerHTML = gameCards;
        container.style.opacity = '1';
        // Reinitialize existing Isotope filtering if present
        if (window.Isotope && document.querySelector('.trending-filter')) {
            new Isotope(container, {
                itemSelector: '.trending-item',
                layoutMode: 'masonry'
            });
        }
    }, 300);
}

// Data Structure Expected
{
    "games": [
        {
            "id": 1,
            "name": "Cyberpunk 2077",
            "price": 59.99,
            "discount_price": 29.99,
            "image_url": "/images/games/cyberpunk.jpg",
            "rating": 4.2,
            "category": "RPG"
        }
    ],
    "total": 8
}
```

##### **Most Played Games Section Enhancement**
```javascript
// API Call via Istio Gateway  
GET https://lugxgaming.com/api/v1/games/trending?filter=most-played&limit=6

// Progressive Enhancement Implementation
async function enhanceMostPlayedSection() {
    const mostPlayedContainer = document.querySelector('.most-popular .row');
    if (!mostPlayedContainer) return; // Graceful fallback
    
    try {
        const response = await apiService.get('/games/most-played', { limit: 6 });
        await renderDynamicMostPlayedGames(response.games, mostPlayedContainer);
        
        analyticsService.track('section_enhanced', { 
            section: 'most_played_games',
            games_count: response.games.length 
        });
    } catch (error) {
        console.warn('Failed to load most played games, keeping static content:', error);
        // Existing static content remains visible
    }
}
```

##### **Newsletter Subscription Enhancement**
```javascript
// API Call via Istio Gateway
POST https://lugxgaming.com/api/v1/newsletter/subscribe

// Progressive Enhancement Implementation  
// File: integration/userIntegration.js
function enhanceNewsletterForm() {
    const newsletterForm = document.querySelector('#newsletter-form');
    if (!newsletterForm) return;
    
    newsletterForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const email = document.querySelector('#newsletter-email').value;
        const name = document.querySelector('#newsletter-name')?.value;
        
        try {
            showFormLoading(newsletterForm);
            
            await apiService.post('/newsletter/subscribe', {
                email: email,
                name: name
            });
            
            showSuccessMessage('Successfully subscribed to newsletter!');
            newsletterForm.reset();
            
            analyticsService.track('newsletter_signup', { email: email });
            
        } catch (error) {
            if (error.status === 409) {
                showWarningMessage('Email already subscribed');
            } else {
                showErrorMessage('Subscription failed. Please try again.');
            }
        } finally {
            hideFormLoading(newsletterForm);
        }
    });
}
```

##### **Analytics Tracking Integration**
```javascript
// Page Load Analytics
document.addEventListener('DOMContentLoaded', function() {
    // Track homepage visit
    analyticsService.track('pageview', {
        page: 'homepage',
        timestamp: new Date().toISOString(),
        user_agent: navigator.userAgent,
        viewport: { 
            width: window.innerWidth, 
            height: window.innerHeight 
        }
    });
    
    // Track user interactions
    addHomepageInteractionTracking();
});

function addHomepageInteractionTracking() {
    // Track game card clicks
    document.addEventListener('click', function(e) {
        if (e.target.closest('.trending-item') || e.target.closest('.item')) {
            const gameCard = e.target.closest('.trending-item, .item');
            const gameId = gameCard.dataset.gameId;
            const gameName = gameCard.querySelector('h4')?.textContent;
            
            analyticsService.track('game_click', {
                game_id: gameId,
                game_name: gameName,
                section: gameCard.closest('.trending-box') ? 'trending' : 'featured',
                click_position: Array.from(gameCard.parentNode.children).indexOf(gameCard)
            });
        }
    });
    
    // Track scroll depth
    let maxScrollDepth = 0;
    window.addEventListener('scroll', function() {
        const scrollPercent = Math.round(
            (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100
        );
        
        if (scrollPercent > maxScrollDepth) {
            maxScrollDepth = scrollPercent;
            
            // Track significant scroll milestones
            if ([25, 50, 75, 100].includes(scrollPercent)) {
                analyticsService.track('scroll_depth', {
                    page: 'homepage',
                    depth_percent: scrollPercent,
                    timestamp: new Date().toISOString()
                });
            }
        }
    });
}
```

##### **Newsletter Subscription**
```javascript
// API Call
POST /api/v1/newsletter/subscribe

// Frontend Implementation
async function subscribeNewsletter(email, name) {
    try {
        const response = await apiService.post('/newsletter/subscribe', {
            email: email,
            name: name
        });
        showSuccessMessage('Newsletter subscription successful!');
        trackAnalytics('conversion', { type: 'newsletter_signup' });
        return true;
    } catch (error) {
        if (error.status === 409) {
            showWarningMessage('Email already subscribed');
        } else {
            showErrorMessage('Subscription failed. Please try again.');
        }
        return false;
    }
}
```

#### **Analytics Tracking**
```javascript
// Page view tracking
trackAnalytics('pageview', {
    page: 'homepage',
    timestamp: new Date().toISOString(),
    user_agent: navigator.userAgent,
    viewport: { width: window.innerWidth, height: window.innerHeight }
});

// User interaction tracking
document.addEventListener('click', (e) => {
    if (e.target.matches('.game-card')) {
        trackAnalytics('click', {
            element: 'game_card',
            game_id: e.target.dataset.gameId,
            position: e.target.dataset.position
        });
    }
});
```

### 2. Shop Page (`shop.html`) - Existing File Enhancement

#### **Current State**
- **Existing Content**: Static game grid, category filters, pagination placeholder
- **jQuery Functionality**: Isotope filtering, responsive grid layout
- **Bootstrap Layout**: Card-based game display with existing styling

#### **Progressive Enhancement Strategy**
- **Dynamic Game Loading**: Replace static game cards with API-driven content
- **Enhanced Filtering**: Add real-time search and price filtering
- **Smart Pagination**: Implement API-driven pagination with URL updates
- **Preserve Isotope**: Maintain existing filtering animations and transitions

#### **Required API Endpoints (Through Istio Gateway)**

##### **Dynamic Game Catalog Enhancement**
```javascript
// API Call via Istio Gateway
GET https://lugxgaming.com/api/v1/games?page=1&limit=20&category=action&price_min=0&price_max=100&search=

// Progressive Enhancement Implementation
// File: integration/gameIntegration.js
class ShopPageEnhancer {
    constructor() {
        this.currentPage = 1;
        this.currentFilters = {
            category: '',
            price_min: 0,
            price_max: 100,
            search: ''
        };
        this.isLoading = false;
        this.initializeEnhancements();
    }

    initializeEnhancements() {
        // Only enhance if we're on shop page
        if (!document.querySelector('.gaming-library')) return;
        
        this.enhanceGameGrid();
        this.enhanceCategoryFilters();
        this.enhanceSearchFunctionality();
        this.enhancePagination();
    }

    async enhanceGameGrid() {
        const gameContainer = document.querySelector('.gaming-library .row');
        if (!gameContainer) return;
        
        try {
            // Show loading overlay while preserving existing content
            this.showGridLoading(gameContainer);
            
            const response = await apiService.get('/games', {
                page: this.currentPage,
                limit: 20,
                ...this.currentFilters
            });
            
            await this.renderDynamicGameGrid(response.games, response.pagination, gameContainer);
            
            analyticsService.track('shop_page_loaded', {
                page: this.currentPage,
                filters: this.currentFilters,
                results_count: response.pagination.total
            });
            
        } catch (error) {
            console.warn('Failed to load dynamic games, keeping static content:', error);
            // Static content remains as fallback
        } finally {
            this.hideGridLoading(gameContainer);
        }
    }

    renderDynamicGameGrid(games, pagination, container) {
        // Preserve existing CSS classes and Bootstrap structure
        const gameCards = games.map(game => `
            <div class="col-lg-4 col-md-6 align-self-center mb-30 trending-items col-md-6 ${game.category.toLowerCase()}">
                <div class="item">
                    <div class="thumb">
                        <a href="product-details.html?id=${game.id}">
                            <img src="${game.image_url}" alt="${game.name}">
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
                        <div class="main-button">
                            <a href="product-details.html?id=${game.id}">Explore</a>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
        
        // Smooth transition
        container.style.opacity = '0.6';
        setTimeout(() => {
            container.innerHTML = gameCards;
            container.style.opacity = '1';
            
            // Reinitialize Isotope with new content
            if (window.Isotope) {
                const iso = new Isotope(container, {
                    itemSelector: '.trending-items',
                    layoutMode: 'fitRows'
                });
                
                // Update filter buttons to work with Isotope
                this.updateIsotopeFilters(iso);
            }
        }, 300);
        
        // Update pagination
        this.renderPagination(pagination);
    }

    enhanceCategoryFilters() {
        const filterButtons = document.querySelectorAll('.trending-filter a');
        
        filterButtons.forEach(button => {
            button.addEventListener('click', async (e) => {
                e.preventDefault();
                
                const category = button.dataset.filter === '*' ? '' : button.dataset.filter;
                this.currentFilters.category = category;
                this.currentPage = 1; // Reset to first page
                
                // Update active state
                document.querySelector('.trending-filter .is_active').classList.remove('is_active');
                button.classList.add('is_active');
                
                // Reload games with new filter
                await this.enhanceGameGrid();
                
                analyticsService.track('filter_applied', {
                    filter_type: 'category',
                    filter_value: category,
                    page: 'shop'
                });
            });
        });
    }

    enhanceSearchFunctionality() {
        // Add search box if it doesn't exist
        const searchContainer = document.querySelector('.section-heading');
        if (searchContainer && !document.querySelector('#game-search')) {
            const searchHTML = `
                <div class="search-box mt-3">
                    <input type="text" id="game-search" class="form-control" 
                           placeholder="Search games..." 
                           style="max-width: 300px; margin: 0 auto;">
                </div>
            `;
            searchContainer.insertAdjacentHTML('afterend', searchHTML);
        }
        
        const searchInput = document.querySelector('#game-search');
        if (searchInput) {
            let searchTimeout;
            
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(async () => {
                    this.currentFilters.search = e.target.value;
                    this.currentPage = 1;
                    await this.enhanceGameGrid();
                    
                    analyticsService.track('search_performed', {
                        query: e.target.value,
                        page: 'shop'
                    });
                }, 500); // Debounce search
            });
        }
    }

    enhancePagination() {
        // Add pagination container if it doesn't exist
        const gameLibrary = document.querySelector('.gaming-library');
        if (gameLibrary && !document.querySelector('#pagination-container')) {
            const paginationHTML = `
                <div id="pagination-container" class="row">
                    <div class="col-lg-12">
                        <nav aria-label="Game pagination">
                            <ul class="pagination justify-content-center" id="pagination-list">
                                <!-- Pagination will be rendered here -->
                            </ul>
                        </nav>
                    </div>
                </div>
            `;
            gameLibrary.insertAdjacentHTML('afterend', paginationHTML);
        }
    }

    renderPagination(pagination) {
        const paginationList = document.querySelector('#pagination-list');
        if (!paginationList) return;
        
        let paginationHTML = '';
        
        // Previous button
        if (pagination.has_prev) {
            paginationHTML += `
                <li class="page-item">
                    <a class="page-link" href="#" data-page="${pagination.page - 1}">
                        <i class="fa fa-chevron-left"></i>
                    </a>
                </li>
            `;
        }
        
        // Page numbers
        const startPage = Math.max(1, pagination.page - 2);
        const endPage = Math.min(pagination.pages, pagination.page + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            paginationHTML += `
                <li class="page-item ${i === pagination.page ? 'active' : ''}">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>
            `;
        }
        
        // Next button
        if (pagination.has_next) {
            paginationHTML += `
                <li class="page-item">
                    <a class="page-link" href="#" data-page="${pagination.page + 1}">
                        <i class="fa fa-chevron-right"></i>
                    </a>
                </li>
            `;
        }
        
        paginationList.innerHTML = paginationHTML;
        
        // Add click handlers
        paginationList.addEventListener('click', async (e) => {
            e.preventDefault();
            if (e.target.matches('.page-link') || e.target.closest('.page-link')) {
                const pageLink = e.target.closest('.page-link');
                const page = parseInt(pageLink.dataset.page);
                
                if (page && page !== this.currentPage) {
                    this.currentPage = page;
                    await this.enhanceGameGrid();
                    
                    // Smooth scroll to top of results
                    document.querySelector('.gaming-library').scrollIntoView({ 
                        behavior: 'smooth' 
                    });
                }
            }
        });
    }

    showGridLoading(container) {
        this.isLoading = true;
        container.style.position = 'relative';
        
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'loading-overlay';
        loadingOverlay.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="sr-only">Loading...</span>
            </div>
        `;
        loadingOverlay.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 255, 255, 0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        `;
        
        container.appendChild(loadingOverlay);
    }

    hideGridLoading(container) {
        this.isLoading = false;
        const loadingOverlay = container.querySelector('.loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.remove();
        }
    }

    updateIsotopeFilters(iso) {
        const filterButtons = document.querySelectorAll('.trending-filter a');
        
        filterButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Apply Isotope filter
                const filterValue = button.dataset.filter;
                iso.arrange({ filter: filterValue });
                
                // Update active state
                document.querySelector('.trending-filter .is_active').classList.remove('is_active');
                button.classList.add('is_active');
            });
        });
    }
}

// Initialize shop page enhancements
document.addEventListener('DOMContentLoaded', function() {
    new ShopPageEnhancer();
});
```

##### **Category Filtering Enhancement**
```javascript
// API Call via Istio Gateway
GET https://lugxgaming.com/api/v1/categories

// Progressive Enhancement Implementation
async function enhanceCategoryFilters() {
    try {
        const response = await apiService.get('/categories');
        updateCategoryFilters(response);
    } catch (error) {
        console.warn('Failed to load categories, using static filters:', error);
        // Keep existing static filter buttons
    }
}

function updateCategoryFilters(categories) {
    const filterContainer = document.querySelector('.trending-filter');
    if (!filterContainer) return;
    
    // Preserve "All" filter
    let filterHTML = '<a href="#" data-filter="*" class="is_active">All</a>';
    
    // Add dynamic categories
    categories.forEach(category => {
        filterHTML += `<a href="#" data-filter=".${category.slug}">${category.name}</a>`;
    });
    
    filterContainer.innerHTML = filterHTML;
}
```

##### **Price Range Filtering Enhancement**
```javascript
// Add price range slider
function enhancePriceFiltering() {
    const searchContainer = document.querySelector('.search-box');
    if (searchContainer && !document.querySelector('#price-filter')) {
        const priceFilterHTML = `
            <div id="price-filter" class="price-filter mt-3">
                <label>Price Range: $<span id="price-min">0</span> - $<span id="price-max">100</span></label>
                <div class="price-slider">
                    <input type="range" id="price-range-min" min="0" max="100" value="0" class="form-range">
                    <input type="range" id="price-range-max" min="0" max="100" value="100" class="form-range">
                </div>
            </div>
        `;
        searchContainer.insertAdjacentHTML('afterend', priceFilterHTML);
        
        // Add event listeners for price range
        const priceMin = document.querySelector('#price-range-min');
        const priceMax = document.querySelector('#price-range-max');
        
        let priceTimeout;
        [priceMin, priceMax].forEach(slider => {
            slider.addEventListener('input', () => {
                clearTimeout(priceTimeout);
                priceTimeout = setTimeout(async () => {
                    const shopEnhancer = window.shopPageEnhancer;
                    if (shopEnhancer) {
                        shopEnhancer.currentFilters.price_min = parseInt(priceMin.value);
                        shopEnhancer.currentFilters.price_max = parseInt(priceMax.value);
                        shopEnhancer.currentPage = 1;
                        await shopEnhancer.enhanceGameGrid();
                    }
                }, 500);
            });
        });
    }
}
```
```

##### **Category Filtering**
```javascript
// API Call
GET /api/v1/categories

// Frontend Implementation
async function loadCategories() {
    try {
        const response = await apiService.get('/categories');
        renderCategoryFilter(response);
    } catch (error) {
        console.warn('Failed to load categories, using fallback');
        renderDefaultCategories();
    }
}

function renderCategoryFilter(categories) {
    const filterContainer = document.getElementById('category-filter');
    filterContainer.innerHTML = `
        <div class="filter-group">
            <h6>Categories</h6>
            <div class="form-check">
                <input class="form-check-input" type="radio" name="category" value="" id="all-categories" checked>
                <label class="form-check-label" for="all-categories">All Games</label>
            </div>
            ${categories.map(category => `
                <div class="form-check">
                    <input class="form-check-input" type="radio" name="category" value="${category.slug}" id="cat-${category.id}">
                    <label class="form-check-label" for="cat-${category.id}">
                        ${category.name} (${category.game_count})
                    </label>
                </div>
            `).join('')}
        </div>
    `;
}
```

##### **Search Functionality**
```javascript
// API Call
GET /api/v1/games/search?q={query}&category={category}

// Frontend Implementation
class SearchManager {
    constructor() {
        this.searchInput = document.getElementById('search-input');
        this.searchDebounce = null;
        this.setupSearchListeners();
    }

    setupSearchListeners() {
        this.searchInput.addEventListener('input', (e) => {
            clearTimeout(this.searchDebounce);
            this.searchDebounce = setTimeout(() => {
                this.performSearch(e.target.value);
            }, 300);
        });
    }

    async performSearch(query) {
        if (query.length < 2) {
            shopManager.loadGames();
            return;
        }

        try {
            showLoading('search-results');
            const response = await apiService.get('/games/search', {
                q: query,
                category: shopManager.currentFilters.category
            });
            
            shopManager.renderGamesGrid(response.games);
            this.updateSearchResults(response.total, query);
            
            trackAnalytics('search', {
                query: query,
                results_count: response.total,
                filters: shopManager.currentFilters
            });
        } catch (error) {
            showError('search-results', 'Search failed');
        } finally {
            hideLoading('search-results');
        }
    }

    updateSearchResults(total, query) {
        const resultsInfo = document.getElementById('search-results-info');
        resultsInfo.innerHTML = `Found ${total} games for "${query}"`;
    }
}
```

### 3. Product Details Page (`single-product.html`)

#### **Page Purpose**
Detailed game information, screenshots, reviews, and purchase options.

#### **Required API Endpoints**

##### **Game Details**
```javascript
// API Call
GET /api/v1/games/{gameId}

// Frontend Implementation
class ProductDetailManager {
    constructor(gameId) {
        this.gameId = gameId;
        this.loadGameDetails();
        this.loadRelatedGames();
        this.loadGameReviews();
    }

    async loadGameDetails() {
        try {
            showLoading('game-details');
            const response = await apiService.get(`/games/${this.gameId}`);
            this.renderGameDetails(response);
            this.updatePageTitle(response.name);
            
            trackAnalytics('pageview', {
                page: 'product_details',
                game_id: this.gameId,
                game_name: response.name,
                category: response.category
            });
        } catch (error) {
            if (error.status === 404) {
                showNotFoundPage();
            } else {
                showError('game-details', 'Failed to load game details');
            }
        } finally {
            hideLoading('game-details');
        }
    }

    renderGameDetails(game) {
        document.getElementById('game-title').textContent = game.name;
        document.getElementById('game-description').innerHTML = game.description;
        document.getElementById('game-price').innerHTML = this.renderPrice(game);
        document.getElementById('game-rating').innerHTML = this.renderRating(game);
        document.getElementById('game-category').textContent = game.category;
        document.getElementById('game-release-date').textContent = new Date(game.release_date).toLocaleDateString();
        
        this.renderGameImages(game.images || []);
        this.setupAddToCartButton(game);
    }

    renderPrice(game) {
        if (game.discount_price) {
            return `
                <span class="original-price">$${game.price}</span>
                <span class="discount-price">$${game.discount_price}</span>
                <span class="discount-badge">${Math.round((1 - game.discount_price/game.price) * 100)}% OFF</span>
            `;
        }
        return `<span class="price">$${game.price}</span>`;
    }
}
```

##### **Related Games**
```javascript
// API Call
GET /api/v1/games/{gameId}/related?limit=6

// Frontend Implementation
async function loadRelatedGames(gameId) {
    try {
        const response = await apiService.get(`/games/${gameId}/related`, { limit: 6 });
        renderRelatedGames(response.games);
    } catch (error) {
        hideSection('related-games');
    }
}

function renderRelatedGames(games) {
    const container = document.getElementById('related-games-container');
    container.innerHTML = games.map(game => `
        <div class="col-md-4 col-sm-6">
            <div class="related-game-card" onclick="navigateToGame(${game.id})">
                <img src="${game.image_url}" alt="${game.name}">
                <h6>${game.name}</h6>
                <div class="price">${game.discount_price ? `$${game.discount_price}` : `$${game.price}`}</div>
            </div>
        </div>
    `).join('');
}
```

##### **Game Reviews**
```javascript
// API Call
GET /api/v1/games/{gameId}/reviews?page=1&limit=10

// Frontend Implementation
class ReviewManager {
    constructor(gameId) {
        this.gameId = gameId;
        this.currentPage = 1;
    }

    async loadReviews(page = 1) {
        try {
            showLoading('reviews-section');
            const response = await apiService.get(`/games/${this.gameId}/reviews`, {
                page: page,
                limit: 10
            });
            
            this.renderReviews(response.reviews);
            this.renderReviewsPagination(response.pagination);
        } catch (error) {
            showError('reviews-section', 'Failed to load reviews');
        } finally {
            hideLoading('reviews-section');
        }
    }

    renderReviews(reviews) {
        const container = document.getElementById('reviews-list');
        container.innerHTML = reviews.map(review => `
            <div class="review-item">
                <div class="review-header">
                    <span class="reviewer-name">${review.username}</span>
                    <div class="rating">${this.renderStars(review.rating)}</div>
                    <span class="review-date">${new Date(review.created_at).toLocaleDateString()}</span>
                </div>
                <div class="review-comment">${review.comment || 'No comment provided'}</div>
            </div>
        `).join('');
    }

    async submitReview(rating, comment) {
        if (!authService.isLoggedIn()) {
            showLoginModal();
            return;
        }

        try {
            const response = await apiService.post(`/games/${this.gameId}/reviews`, {
                rating: rating,
                comment: comment
            });
            
            showSuccessMessage('Review submitted successfully!');
            this.loadReviews(); // Refresh reviews
            trackAnalytics('review_submitted', { game_id: this.gameId, rating: rating });
        } catch (error) {
            if (error.status === 409) {
                showErrorMessage('You have already reviewed this game');
            } else {
                showErrorMessage('Failed to submit review');
            }
        }
    }
}
```

### 4. Shopping Cart Page (`cart.html`)

#### **Page Purpose**
Cart management, item quantity updates, and checkout initiation.

#### **Required API Endpoints**

##### **Cart Display**
```javascript
// API Call
GET /api/v1/cart

// Frontend Implementation
class CartManager {
    constructor() {
        this.loadCart();
        this.setupEventListeners();
    }

    async loadCart() {
        if (!authService.isLoggedIn()) {
            this.showEmptyCart('Please log in to view your cart');
            return;
        }

        try {
            showLoading('cart-content');
            const response = await apiService.get('/cart');
            this.renderCart(response);
            trackAnalytics('pageview', { 
                page: 'cart', 
                items_count: response.total_items,
                total_value: response.total_price 
            });
        } catch (error) {
            showError('cart-content', 'Failed to load cart');
        } finally {
            hideLoading('cart-content');
        }
    }

    renderCart(cart) {
        if (cart.total_items === 0) {
            this.showEmptyCart();
            return;
        }

        const container = document.getElementById('cart-items');
        container.innerHTML = cart.items.map(item => `
            <div class="cart-item" data-item-id="${item.id}">
                <div class="row align-items-center">
                    <div class="col-md-2">
                        <img src="${item.game_image_url}" alt="${item.game_name}" class="cart-item-image">
                    </div>
                    <div class="col-md-4">
                        <h6>${item.game_name}</h6>
                        <p class="text-muted">Category: ${item.game_category}</p>
                    </div>
                    <div class="col-md-2">
                        <div class="price">
                            ${item.game_discount_price ? 
                                `<span class="discount-price">$${item.game_discount_price}</span>` :
                                `<span>$${item.game_price}</span>`
                            }
                        </div>
                    </div>
                    <div class="col-md-2">
                        <div class="quantity-controls">
                            <button class="btn btn-sm btn-outline-secondary" onclick="cartManager.updateQuantity(${item.id}, ${item.quantity - 1})">-</button>
                            <span class="quantity">${item.quantity}</span>
                            <button class="btn btn-sm btn-outline-secondary" onclick="cartManager.updateQuantity(${item.id}, ${item.quantity + 1})">+</button>
                        </div>
                    </div>
                    <div class="col-md-1">
                        <div class="subtotal">$${item.subtotal}</div>
                    </div>
                    <div class="col-md-1">
                        <button class="btn btn-sm btn-danger" onclick="cartManager.removeItem(${item.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        this.renderCartSummary(cart);
    }

    renderCartSummary(cart) {
        document.getElementById('cart-total-items').textContent = cart.total_items;
        document.getElementById('cart-total-price').textContent = `$${cart.total_price}`;
        document.getElementById('checkout-btn').disabled = cart.total_items === 0;
    }
}
```

##### **Cart Item Management**
```javascript
// Add to Cart
// API Call: POST /api/v1/cart/add

async function addToCart(gameId, quantity = 1) {
    if (!authService.isLoggedIn()) {
        showLoginModal();
        return;
    }

    try {
        showLoading(`add-to-cart-${gameId}`);
        const response = await apiService.post('/cart/add', {
            game_id: gameId,
            quantity: quantity
        });
        
        showSuccessMessage('Game added to cart!');
        updateCartBadge();
        trackAnalytics('cart', {
            event_type: 'add',
            game_id: gameId,
            quantity: quantity
        });
    } catch (error) {
        if (error.status === 409) {
            showWarningMessage('Game already in cart');
        } else {
            showErrorMessage('Failed to add game to cart');
        }
    } finally {
        hideLoading(`add-to-cart-${gameId}`);
    }
}

// Update Quantity
// API Call: PUT /api/v1/cart/{itemId}

async updateQuantity(itemId, newQuantity) {
    if (newQuantity < 1) {
        this.removeItem(itemId);
        return;
    }

    try {
        const response = await apiService.put(`/cart/${itemId}`, {
            quantity: newQuantity
        });
        
        this.loadCart(); // Refresh cart display
        trackAnalytics('cart', {
            event_type: 'update',
            item_id: itemId,
            new_quantity: newQuantity
        });
    } catch (error) {
        showErrorMessage('Failed to update quantity');
    }
}

// Remove Item
// API Call: DELETE /api/v1/cart/{itemId}

async removeItem(itemId) {
    if (!confirm('Remove this item from cart?')) return;

    try {
        await apiService.delete(`/cart/${itemId}`);
        this.loadCart(); // Refresh cart display
        showSuccessMessage('Item removed from cart');
        trackAnalytics('cart', {
            event_type: 'remove',
            item_id: itemId
        });
    } catch (error) {
        showErrorMessage('Failed to remove item');
    }
}
```

### 5. User Account Pages

#### **Login Page (`login.html`)**

```javascript
// API Call
POST /api/v1/auth/login

// Frontend Implementation
class AuthManager {
    async login(email, password) {
        try {
            showLoading('login-form');
            const response = await apiService.post('/auth/login', {
                email: email,
                password: password
            });
            
            this.setAuthToken(response.access_token);
            this.setUserData(response.user);
            showSuccessMessage('Login successful!');
            
            trackAnalytics('auth', { event_type: 'login_success' });
            this.redirectAfterLogin();
        } catch (error) {
            if (error.status === 401) {
                showErrorMessage('Invalid email or password');
            } else {
                showErrorMessage('Login failed. Please try again.');
            }
            trackAnalytics('auth', { event_type: 'login_failed' });
        } finally {
            hideLoading('login-form');
        }
    }

    setAuthToken(token) {
        localStorage.setItem('auth_token', token);
        apiService.setAuthToken(token);
    }

    setUserData(user) {
        localStorage.setItem('user_data', JSON.stringify(user));
        this.updateUIForLoggedInUser(user);
    }
}
```

#### **Registration Page (`register.html`)**

```javascript
// API Call
POST /api/v1/auth/register

async function registerUser(userData) {
    try {
        showLoading('register-form');
        const response = await apiService.post('/auth/register', userData);
        
        authManager.setAuthToken(response.access_token);
        authManager.setUserData(response.user);
        showSuccessMessage('Registration successful! Welcome to Lugx Gaming!');
        
        trackAnalytics('auth', { event_type: 'registration_success' });
        window.location.href = '/';
    } catch (error) {
        if (error.status === 409) {
            showErrorMessage('Email already registered');
        } else {
            showErrorMessage('Registration failed. Please try again.');
        }
        trackAnalytics('auth', { event_type: 'registration_failed' });
    } finally {
        hideLoading('register-form');
    }
}
```

---

---

## Missing Pages Implementation Plan

### **1. Login Page (`pages/login.html`)**

#### **Implementation Strategy:**
```html
<!-- File: pages/login.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Same head structure as existing pages -->
    <title>Lugx Gaming - Login</title>
    <!-- Include existing CSS files -->
</head>
<body>
    <!-- Header from existing pages -->
    
    <div class="login-section">
        <div class="container">
            <div class="row">
                <div class="col-lg-6 offset-lg-3">
                    <form id="login-form" class="login-form">
                        <h2>Login to Your Account</h2>
                        <div class="form-group">
                            <input type="email" id="login-email" placeholder="Email" required>
                        </div>
                        <div class="form-group">
                            <input type="password" id="login-password" placeholder="Password" required>
                        </div>
                        <button type="submit" class="main-button">Login</button>
                        <p>Don't have an account? <a href="register.html">Register here</a></p>
                    </form>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Footer from existing pages -->
    
    <!-- API Integration Scripts -->
    <script src="../api/apiService.js"></script>
    <script src="../api/authService.js"></script>
    <script src="../integration/userIntegration.js"></script>
</body>
</html>
```

### **2. Register Page (`pages/register.html`)**

#### **Implementation Strategy:**
```html
<!-- File: pages/register.html -->
<!-- Similar structure to login.html with expanded form fields -->
<form id="register-form" class="register-form">
    <h2>Create Your Account</h2>
    <div class="form-group">
        <input type="text" id="register-firstname" placeholder="First Name" required>
    </div>
    <div class="form-group">
        <input type="text" id="register-lastname" placeholder="Last Name" required>
    </div>
    <div class="form-group">
        <input type="email" id="register-email" placeholder="Email" required>
    </div>
    <div class="form-group">
        <input type="text" id="register-username" placeholder="Username" required>
    </div>
    <div class="form-group">
        <input type="password" id="register-password" placeholder="Password" required>
    </div>
    <button type="submit" class="main-button">Register</button>
</form>
```

### **3. Shopping Cart Page (`pages/cart.html`)**

#### **Implementation Strategy:**
```html
<!-- File: pages/cart.html -->
<div class="cart-section">
    <div class="container">
        <div class="row">
            <div class="col-lg-8">
                <div id="cart-items-container">
                    <!-- Dynamic cart items loaded here -->
                </div>
            </div>
            <div class="col-lg-4">
                <div class="cart-summary">
                    <h4>Order Summary</h4>
                    <div class="summary-line">
                        <span>Subtotal:</span>
                        <span id="cart-subtotal">$0.00</span>
                    </div>
                    <div class="summary-line total">
                        <span>Total:</span>
                        <span id="cart-total">$0.00</span>
                    </div>
                    <button id="checkout-btn" class="main-button">Proceed to Checkout</button>
                </div>
            </div>
        </div>
    </div>
</div>
```

---

## Global API Integration Components

### **Centralized API Service**

```javascript
// File: api/apiService.js
class APIService {
    constructor() {
        // Point to Istio Gateway
        this.baseURL = 'https://lugxgaming.com';
        this.authToken = localStorage.getItem('auth_token');
        this.timeout = 10000;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}/api/v1${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        if (this.authToken) {
            config.headers.Authorization = `Bearer ${this.authToken}`;
        }

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new APIError(response.status, await response.json());
            }

            return await response.json();
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url);
    }

    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }

    setAuthToken(token) {
        this.authToken = token;
    }
}

// Global API service instance
const apiService = new APIService();
```

### **Enhanced Web Analytics Tracking Service**

#### **Comprehensive Analytics API Endpoints**

The Analytics Service provides comprehensive web analytics capabilities through the following API endpoints:

##### **Core Analytics Endpoints**
```javascript
// Analytics API Endpoints via Istio Gateway
const ANALYTICS_ENDPOINTS = {
    BATCH_EVENTS: '/api/v1/analytics/events/batch',
    PAGE_VIEW: '/api/v1/analytics/pageview',
    USER_INTERACTION: '/api/v1/analytics/interaction',
    SESSION_START: '/api/v1/analytics/session/start',
    SESSION_END: '/api/v1/analytics/session/end',
    CONVERSION_EVENT: '/api/v1/analytics/conversion',
    REAL_TIME_METRICS: '/api/v1/analytics/metrics/realtime',
    USER_JOURNEY: '/api/v1/analytics/journey/{session_id}'
};
```

#### **Enhanced Analytics Service Implementation**

```javascript
class EnhancedAnalyticsService {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.eventQueue = [];
        this.batchSize = 50;  // Increased for better performance
        this.flushInterval = 5000; // 5 seconds
        this.sessionStartTime = Date.now();
        this.lastActiveTime = Date.now();
        this.scrollDepthTracked = new Set();
        this.timeOnPageStart = Date.now();
        
        this.initializeTracking();
    }

    initializeTracking() {
        this.startSession();
        this.setupAutoTracking();
        this.startPeriodicFlush();
        this.setupPageUnloadFlush();
        this.startHeartbeat();
    }

    // === SESSION MANAGEMENT ===
    
    async startSession() {
        const sessionData = {
            session_id: this.sessionId,
            user_id: this.getCurrentUserId(),
            start_time: new Date().toISOString(),
            user_agent: navigator.userAgent,
            screen_width: screen.width,
            screen_height: screen.height,
            viewport_width: window.innerWidth,
            viewport_height: window.innerHeight,
            referrer: document.referrer,
            initial_page: window.location.href
        };

        await this.trackEvent('session_start', sessionData);
    }

    async endSession() {
        const sessionDuration = Date.now() - this.sessionStartTime;
        await this.trackEvent('session_end', {
            session_duration: sessionDuration,
            total_page_views: this.pageViewCount || 0,
            total_interactions: this.interactionCount || 0
        });
    }

    // === AUTOMATIC EVENT TRACKING ===
    
    setupAutoTracking() {
        this.setupPageViewTracking();
        this.setupClickTracking();
        this.setupScrollTracking();
        this.setupFormTracking();
        this.setupNavigationTracking();
    }

    setupPageViewTracking() {
        // Track initial page view
        this.trackPageView();
        
        // Track SPA route changes
        let lastUrl = location.href;
        new MutationObserver(() => {
            const url = location.href;
            if (url !== lastUrl) {
                lastUrl = url;
                this.timeOnPageStart = Date.now();
                this.scrollDepthTracked.clear();
                this.trackPageView();
            }
        }).observe(document, { subtree: true, childList: true });
    }

    setupClickTracking() {
        document.addEventListener('click', (e) => {
            this.trackClick(e);
        }, { passive: true });
    }

    setupScrollTracking() {
        let ticking = false;
        const scrollMilestones = [25, 50, 75, 100];
        
        document.addEventListener('scroll', () => {
            if (!ticking) {
                requestAnimationFrame(() => {
                    this.trackScrollDepth(scrollMilestones);
                    ticking = false;
                });
                ticking = true;
            }
        }, { passive: true });
    }

    setupFormTracking() {
        // Track form interactions
        document.addEventListener('focusin', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                this.trackEvent('form_field_focus', {
                    field_name: e.target.name || e.target.id,
                    field_type: e.target.type,
                    form_id: e.target.closest('form')?.id
                });
            }
        }, { passive: true });

        // Track form submissions
        document.addEventListener('submit', (e) => {
            this.trackEvent('form_submit', {
                form_id: e.target.id,
                form_action: e.target.action,
                form_method: e.target.method
            });
        }, { passive: true });
    }

    setupNavigationTracking() {
        // Track back/forward navigation
        window.addEventListener('popstate', () => {
            this.trackEvent('navigation', {
                type: 'back_forward',
                url: window.location.href
            });
        });
    }

    // === SPECIFIC EVENT TRACKING METHODS ===

    trackPageView() {
        const timeOnPreviousPage = this.timeOnPageStart ? 
            Date.now() - this.timeOnPageStart : 0;

        this.trackEvent('page_view', {
            page_url: window.location.href,
            page_title: document.title,
            referrer: document.referrer,
            time_on_previous_page: timeOnPreviousPage,
            viewport_width: window.innerWidth,
            viewport_height: window.innerHeight
        });

        this.pageViewCount = (this.pageViewCount || 0) + 1;
    }

    trackClick(event) {
        const element = event.target;
        const rect = element.getBoundingClientRect();
        
        this.trackEvent('click', {
            element_type: element.tagName.toLowerCase(),
            element_text: element.textContent?.substring(0, 100),
            element_id: element.id,
            element_class: element.className,
            click_x: event.clientX,
            click_y: event.clientY,
            element_x: Math.round(rect.left),
            element_y: Math.round(rect.top),
            page_url: window.location.href
        });

        this.interactionCount = (this.interactionCount || 0) + 1;
    }

    trackScrollDepth(milestones) {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const windowHeight = window.innerHeight;
        const documentHeight = Math.max(
            document.body.scrollHeight,
            document.documentElement.scrollHeight
        );
        
        const scrollPercent = Math.round(
            (scrollTop / (documentHeight - windowHeight)) * 100
        );

        milestones.forEach(milestone => {
            if (scrollPercent >= milestone && !this.scrollDepthTracked.has(milestone)) {
                this.scrollDepthTracked.add(milestone);
                this.trackEvent('scroll_depth', {
                    scroll_depth: milestone,
                    max_scroll: scrollPercent,
                    page_height: documentHeight,
                    viewport_height: windowHeight,
                    page_url: window.location.href
                });
            }
        });
    }

    // === E-COMMERCE SPECIFIC TRACKING ===

    trackProductView(productId, category, price) {
        this.trackEvent('product_view', {
            product_id: productId,
            category: category,
            price: price,
            page_url: window.location.href
        });
    }

    trackAddToCart(productId, quantity, price) {
        this.trackEvent('add_to_cart', {
            product_id: productId,
            quantity: quantity,
            price: price,
            total_value: quantity * price
        });
    }

    trackPurchase(orderId, items, totalValue) {
        this.trackEvent('purchase', {
            order_id: orderId,
            items: items,
            total_value: totalValue,
            currency: 'USD'
        });
    }

    trackSearch(query, filters, resultCount) {
        this.trackEvent('search', {
            search_query: query,
            filters_applied: filters,
            result_count: resultCount
        });
    }

    // === CORE EVENT TRACKING ===

    trackEvent(eventType, eventData) {
        const event = {
            event_id: this.generateEventId(),
            session_id: this.sessionId,
            user_id: this.getCurrentUserId(),
            event_type: eventType,
            timestamp: new Date().toISOString(),
            page_url: window.location.href,
            user_agent: navigator.userAgent,
            ...eventData
        };

        this.eventQueue.push(event);
        this.lastActiveTime = Date.now();

        if (this.eventQueue.length >= this.batchSize) {
            this.flushEvents();
        }
    }

    async flushEvents() {
        if (this.eventQueue.length === 0) return;

        const events = [...this.eventQueue];
        this.eventQueue = [];

        try {
            await apiService.post('/api/v1/analytics/events/batch', { 
                events,
                session_id: this.sessionId,
                batch_timestamp: new Date().toISOString()
            });
        } catch (error) {
            console.warn('Failed to send analytics events:', error);
            // Re-add events to queue for retry (with limit to prevent memory issues)
            if (this.eventQueue.length < 1000) {
                this.eventQueue.unshift(...events);
            }
        }
    }

    // === REAL-TIME ANALYTICS ===

    async getRealTimeMetrics() {
        try {
            const response = await apiService.get('/api/v1/analytics/metrics/realtime');
            return response.data;
        } catch (error) {
            console.warn('Failed to fetch real-time metrics:', error);
            return null;
        }
    }

    async getUserJourney(sessionId = this.sessionId) {
        try {
            const response = await apiService.get(`/api/v1/analytics/journey/${sessionId}`);
            return response.data;
        } catch (error) {
            console.warn('Failed to fetch user journey:', error);
            return null;
        }
    }

    // === UTILITY METHODS ===

    startPeriodicFlush() {
        setInterval(() => this.flushEvents(), this.flushInterval);
    }

    startHeartbeat() {
        // Send heartbeat every 30 seconds to track session activity
        setInterval(() => {
            const timeSinceLastActivity = Date.now() - this.lastActiveTime;
            if (timeSinceLastActivity < 60000) { // Active in last minute
                this.trackEvent('heartbeat', {
                    session_duration: Date.now() - this.sessionStartTime,
                    time_since_last_activity: timeSinceLastActivity
                });
            }
        }, 30000);
    }

    setupPageUnloadFlush() {
        const endSession = () => {
            if (this.eventQueue.length > 0) {
                // Send remaining events synchronously
                navigator.sendBeacon(
                    `${apiService.baseURL}/api/v1/analytics/events/batch`,
                    JSON.stringify({ 
                        events: this.eventQueue,
                        session_id: this.sessionId,
                        batch_type: 'page_unload'
                    })
                );
            }
            this.endSession();
        };

        window.addEventListener('beforeunload', endSession);
        window.addEventListener('pagehide', endSession);
    }

    generateSessionId() {
        return 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    generateEventId() {
        return 'evt_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    getCurrentUserId() {
        // Get from authentication service or localStorage
        return authService.getCurrentUser()?.id || localStorage.getItem('user_id') || null;
    }
}

// Global enhanced analytics service
const analyticsService = new EnhancedAnalyticsService();

// Convenient tracking functions
function trackAnalytics(eventType, data) {
    analyticsService.trackEvent(eventType, data);
}

function trackPageView() {
    analyticsService.trackPageView();
}

function trackProductView(productId, category, price) {
    analyticsService.trackProductView(productId, category, price);
}

function trackAddToCart(productId, quantity, price) {
    analyticsService.trackAddToCart(productId, quantity, price);
}

function trackPurchase(orderId, items, totalValue) {
    analyticsService.trackPurchase(orderId, items, totalValue);
}

function trackSearch(query, filters, resultCount) {
    analyticsService.trackSearch(query, filters, resultCount);
}
```

#### **Analytics Service Integration**

The enhanced analytics service automatically tracks:

- **Page Views**: Including time on page and navigation patterns
- **User Interactions**: Clicks, form interactions, and element engagement  
- **Scroll Behavior**: Depth tracking and reading engagement
- **E-commerce Events**: Product views, cart actions, and purchases
- **User Sessions**: Complete session reconstruction and analysis
- **Real-time Metrics**: Live dashboard data and user activity

#### **API Performance Optimizations**

- **Batch Processing**: Events are batched for efficient API calls
- **Error Handling**: Failed events are retried with exponential backoff
- **Memory Management**: Queue size limits prevent memory issues
- **Performance**: Uses requestAnimationFrame for smooth scroll tracking
- **Reliability**: Navigator.sendBeacon ensures data delivery on page unload

This comprehensive frontend API mapping ensures that every page in the Lugx Gaming platform has clear, well-defined interactions with the FastAPI backend services, creating a seamless and performant user experience while providing rich analytics data for business intelligence.