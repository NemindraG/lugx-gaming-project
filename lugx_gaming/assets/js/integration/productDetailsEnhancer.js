/**
 * LugX Gaming Product Details Enhancement
 * Transforms static product page into dynamic, API-driven experience
 * Provides real-time game data, reviews, recommendations, and purchasing
 */

class ProductDetailsEnhancer {
    constructor() {
        this.config = {
            reviewsPerPage: 10,
            relatedGamesCount: 5,
            maxImageGallery: 6,
            autoplayInterval: 5000,
            enableDebugLogging: window.location.hostname === 'localhost'
        };

        this.state = {
            gameId: null,
            gameData: null,
            reviews: [],
            relatedGames: [],
            currentImageIndex: 0,
            currentReviewPage: 1,
            totalReviewPages: 1,
            selectedQuantity: 1,
            loading: false,
            error: null
        };

        this.cache = new Map();
        this.imageGallery = null;
        this.reviewsLoaded = false;
        this.isInitialized = false;

        this.initializeProductDetails();
    }

    async initializeProductDetails() {
        try {
            this.log('Initializing product details enhancement...');

            // Extract game ID from URL
            this.state.gameId = this.extractGameIdFromURL();
            if (!this.state.gameId) {
                throw new Error('No game ID found in URL');
            }

            // Wait for dependencies
            await this.waitForDependencies();

            // Setup enhanced UI
            this.setupProductUI();

            // Load initial data
            await this.loadInitialData();

            // Setup event listeners
            this.setupEventListeners();

            this.isInitialized = true;
            this.log('Product details enhancement initialized successfully');

            // Track product view
            if (window.analyticsService) {
                window.analyticsService.trackProductView(
                    this.state.gameId,
                    this.state.gameData?.name || 'Unknown Game',
                    this.state.gameData?.category || 'Unknown',
                    this.state.gameData?.price || 0
                );
            }

        } catch (error) {
            console.error('Product details enhancement initialization failed:', error);
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

    extractGameIdFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('id') || urlParams.get('gameId');
    }

    setupProductUI() {
        this.enhanceProductHeader();
        this.enhanceProductDetails();
        this.enhanceImageGallery();
        this.enhanceReviewsSection();
        this.enhanceRelatedGames();
        this.addProductStyles();
        this.setupLoadingStates();
    }

    enhanceProductHeader() {
        const headerSection = document.querySelector('.page-heading');
        if (!headerSection) return;

        // Add dynamic breadcrumb container
        const breadcrumbElement = headerSection.querySelector('.breadcrumb');
        if (breadcrumbElement) {
            breadcrumbElement.id = 'dynamicBreadcrumb';
        }

        // Add product page header enhancement
        const headerTitle = headerSection.querySelector('h3');
        if (headerTitle) {
            headerTitle.id = 'dynamicTitle';
        }
    }

    enhanceProductDetails() {
        const productSection = document.querySelector('.single-product');
        if (!productSection) return;

        // Add loading overlay
        const loadingHTML = `
            <div class="product-loading" id="productLoading" style="display: flex;">
                <div class="loading-content">
                    <div class="spinner-border text-primary" role="status">
                        <span class="sr-only">Loading...</span>
                    </div>
                    <p class="mt-3">Loading product details...</p>
                </div>
            </div>
        `;

        productSection.insertAdjacentHTML('afterbegin', loadingHTML);

        // Enhance product form
        this.enhanceAddToCartForm();
        
        // Add product specifications container
        const productInfo = document.querySelector('.single-product .col-lg-6.align-self-center');
        if (productInfo) {
            const specsHTML = `
                <div class="product-specifications" id="productSpecs" style="display: none;">
                    <h5>Specifications</h5>
                    <div class="specs-grid">
                        <!-- Specs will be loaded dynamically -->
                    </div>
                </div>
            `;
            productInfo.insertAdjacentHTML('beforeend', specsHTML);
        }
    }

    enhanceAddToCartForm() {
        const form = document.getElementById('qty');
        if (!form) return;

        // Replace existing form with enhanced version
        const enhancedFormHTML = `
            <div class="product-purchase">
                <div class="quantity-selector">
                    <label for="quantity">Quantity:</label>
                    <div class="quantity-controls">
                        <button type="button" class="qty-btn minus" onclick="window.productDetailsEnhancer.adjustQuantity(-1)">-</button>
                        <input type="number" id="quantity" class="form-control" value="1" min="1" max="10">
                        <button type="button" class="qty-btn plus" onclick="window.productDetailsEnhancer.adjustQuantity(1)">+</button>
                    </div>
                </div>
                <div class="purchase-buttons">
                    <button type="button" class="btn-add-to-cart" id="addToCartBtn" disabled>
                        <i class="fa fa-shopping-bag"></i> 
                        <span class="btn-text">Add to Cart</span>
                    </button>
                    <button type="button" class="btn-buy-now" id="buyNowBtn" disabled>
                        <i class="fa fa-credit-card"></i> 
                        Buy Now
                    </button>
                    <button type="button" class="btn-wishlist" id="wishlistBtn" title="Add to Wishlist">
                        <i class="fa fa-heart-o"></i>
                    </button>
                </div>
                <div class="product-availability" id="productAvailability">
                    <!-- Availability status will be loaded dynamically -->
                </div>
            </div>
        `;

        form.outerHTML = enhancedFormHTML;
    }

    enhanceImageGallery() {
        const imageContainer = document.querySelector('.left-image');
        if (!imageContainer) return;

        // Replace with enhanced gallery
        const galleryHTML = `
            <div class="product-gallery">
                <div class="main-image-container">
                    <img id="mainProductImage" src="assets/images/single-game.jpg" alt="Product Image" class="main-product-image">
                    <div class="image-navigation">
                        <button class="nav-btn prev" onclick="window.productDetailsEnhancer.previousImage()">
                            <i class="fa fa-chevron-left"></i>
                        </button>
                        <button class="nav-btn next" onclick="window.productDetailsEnhancer.nextImage()">
                            <i class="fa fa-chevron-right"></i>
                        </button>
                    </div>
                    <div class="discount-badge" id="discountBadge" style="display: none;">
                        <span>-20%</span>
                    </div>
                </div>
                <div class="thumbnail-gallery" id="thumbnailGallery">
                    <!-- Thumbnails will be loaded dynamically -->
                </div>
            </div>
        `;

        imageContainer.innerHTML = galleryHTML;
    }

    enhanceReviewsSection() {
        const reviewsTab = document.getElementById('reviews');
        if (!reviewsTab) return;

        const enhancedReviewsHTML = `
            <div class="reviews-section">
                <div class="reviews-summary" id="reviewsSummary">
                    <!-- Summary will be loaded dynamically -->
                </div>
                <div class="reviews-list" id="reviewsList">
                    <div class="reviews-loading">
                        <div class="spinner-border spinner-border-sm"></div>
                        <span>Loading reviews...</span>
                    </div>
                </div>
                <div class="reviews-pagination" id="reviewsPagination">
                    <!-- Pagination will be loaded dynamically -->
                </div>
                <div class="write-review-section">
                    <button class="btn btn-outline-primary" onclick="window.productDetailsEnhancer.showReviewForm()">
                        <i class="fa fa-edit"></i> Write a Review
                    </button>
                </div>
            </div>
        `;

        reviewsTab.innerHTML = enhancedReviewsHTML;
    }

    enhanceRelatedGames() {
        const relatedSection = document.querySelector('.related-games');
        if (!relatedSection) return;

        // Add loading state for related games
        const gamesContainer = relatedSection.querySelector('.row');
        if (gamesContainer) {
            gamesContainer.id = 'relatedGamesContainer';
        }
    }

    addProductStyles() {
        if (document.getElementById('product-details-styles')) {
            return; // Styles already added
        }

        const styles = `
            <style id="product-details-styles">
                .product-loading {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(255,255,255,0.9);
                    z-index: 9999;
                    align-items: center;
                    justify-content: center;
                    flex-direction: column;
                }
                
                .loading-content {
                    text-align: center;
                }
                
                .product-gallery {
                    position: relative;
                }
                
                .main-image-container {
                    position: relative;
                    margin-bottom: 20px;
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                }
                
                .main-product-image {
                    width: 100%;
                    height: 400px;
                    object-fit: cover;
                    transition: transform 0.3s ease;
                }
                
                .main-product-image:hover {
                    transform: scale(1.05);
                }
                
                .image-navigation {
                    position: absolute;
                    top: 50%;
                    transform: translateY(-50%);
                    width: 100%;
                    display: flex;
                    justify-content: space-between;
                    padding: 0 15px;
                    opacity: 0;
                    transition: opacity 0.3s ease;
                }
                
                .main-image-container:hover .image-navigation {
                    opacity: 1;
                }
                
                .nav-btn {
                    background: rgba(0,0,0,0.5);
                    border: none;
                    color: white;
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    cursor: pointer;
                    transition: background-color 0.3s ease;
                }
                
                .nav-btn:hover {
                    background: rgba(0,0,0,0.8);
                }
                
                .discount-badge {
                    position: absolute;
                    top: 15px;
                    right: 15px;
                    background: #dc3545;
                    color: white;
                    padding: 8px 12px;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 14px;
                }
                
                .thumbnail-gallery {
                    display: flex;
                    gap: 10px;
                    overflow-x: auto;
                    padding: 10px 0;
                }
                
                .thumbnail-item {
                    flex-shrink: 0;
                    width: 80px;
                    height: 80px;
                    border-radius: 8px;
                    overflow: hidden;
                    cursor: pointer;
                    border: 2px solid transparent;
                    transition: border-color 0.3s ease;
                }
                
                .thumbnail-item.active {
                    border-color: #007bff;
                }
                
                .thumbnail-item img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                }
                
                .product-purchase {
                    margin-top: 30px;
                }
                
                .quantity-selector {
                    margin-bottom: 20px;
                }
                
                .quantity-selector label {
                    display: block;
                    margin-bottom: 8px;
                    font-weight: 600;
                    color: #333;
                }
                
                .quantity-controls {
                    display: flex;
                    align-items: center;
                    border: 2px solid #e1e5e9;
                    border-radius: 8px;
                    overflow: hidden;
                    width: fit-content;
                }
                
                .qty-btn {
                    background: #f8f9fa;
                    border: none;
                    width: 40px;
                    height: 40px;
                    cursor: pointer;
                    font-weight: bold;
                    transition: background-color 0.3s ease;
                }
                
                .qty-btn:hover {
                    background: #e9ecef;
                }
                
                .quantity-controls input {
                    border: none;
                    width: 60px;
                    height: 40px;
                    text-align: center;
                    font-weight: 600;
                }
                
                .quantity-controls input:focus {
                    outline: none;
                }
                
                .purchase-buttons {
                    display: flex;
                    gap: 15px;
                    margin-bottom: 20px;
                    flex-wrap: wrap;
                }
                
                .btn-add-to-cart,
                .btn-buy-now {
                    flex: 1;
                    min-width: 150px;
                    padding: 12px 20px;
                    border: none;
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                }
                
                .btn-add-to-cart {
                    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                    color: white;
                }
                
                .btn-add-to-cart:hover:not(:disabled) {
                    transform: translateY(-2px);
                    box-shadow: 0 8px 25px rgba(40,167,69,0.3);
                }
                
                .btn-buy-now {
                    background: linear-gradient(135deg, #007bff 0%, #6610f2 100%);
                    color: white;
                }
                
                .btn-buy-now:hover:not(:disabled) {
                    transform: translateY(-2px);
                    box-shadow: 0 8px 25px rgba(0,123,255,0.3);
                }
                
                .btn-wishlist {
                    width: 50px;
                    height: 50px;
                    background: white;
                    border: 2px solid #e1e5e9;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 18px;
                    color: #666;
                }
                
                .btn-wishlist:hover {
                    border-color: #dc3545;
                    color: #dc3545;
                }
                
                .btn-wishlist.active {
                    background: #dc3545;
                    border-color: #dc3545;
                    color: white;
                }
                
                .purchase-buttons button:disabled {
                    opacity: 0.6;
                    cursor: not-allowed;
                    transform: none !important;
                }
                
                .product-availability {
                    padding: 15px;
                    border-radius: 8px;
                    font-weight: 500;
                }
                
                .availability-in-stock {
                    background: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                }
                
                .availability-low-stock {
                    background: #fff3cd;
                    color: #856404;
                    border: 1px solid #ffeaa7;
                }
                
                .availability-out-of-stock {
                    background: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                }
                
                .product-specifications {
                    margin-top: 30px;
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 8px;
                }
                
                .product-specifications h5 {
                    margin-bottom: 15px;
                    color: #333;
                }
                
                .specs-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                }
                
                .spec-item {
                    display: flex;
                    justify-content: space-between;
                    padding: 8px 0;
                    border-bottom: 1px solid #dee2e6;
                }
                
                .spec-label {
                    font-weight: 500;
                    color: #666;
                }
                
                .spec-value {
                    color: #333;
                }
                
                .reviews-section {
                    padding: 20px 0;
                }
                
                .reviews-summary {
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    display: flex;
                    align-items: center;
                    gap: 20px;
                }
                
                .rating-overview {
                    text-align: center;
                }
                
                .rating-score {
                    font-size: 48px;
                    font-weight: bold;
                    color: #333;
                    line-height: 1;
                }
                
                .rating-stars {
                    color: #ffc107;
                    font-size: 20px;
                    margin: 5px 0;
                }
                
                .rating-count {
                    color: #666;
                    font-size: 14px;
                }
                
                .rating-breakdown {
                    flex: 1;
                }
                
                .rating-bar {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    margin-bottom: 8px;
                }
                
                .rating-bar-label {
                    min-width: 60px;
                    font-size: 14px;
                    color: #666;
                }
                
                .rating-bar-fill {
                    flex: 1;
                    height: 8px;
                    background: #e9ecef;
                    border-radius: 4px;
                    overflow: hidden;
                }
                
                .rating-bar-progress {
                    height: 100%;
                    background: #ffc107;
                    transition: width 0.3s ease;
                }
                
                .rating-bar-count {
                    min-width: 40px;
                    font-size: 14px;
                    color: #666;
                    text-align: right;
                }
                
                .review-item {
                    border-bottom: 1px solid #e9ecef;
                    padding: 20px 0;
                }
                
                .review-item:last-child {
                    border-bottom: none;
                }
                
                .review-header {
                    display: flex;
                    align-items: center;
                    gap: 15px;
                    margin-bottom: 10px;
                }
                
                .reviewer-avatar {
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    background: #e9ecef;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                    color: #666;
                }
                
                .reviewer-info {
                    flex: 1;
                }
                
                .reviewer-name {
                    font-weight: 600;
                    color: #333;
                    margin-bottom: 2px;
                }
                
                .review-date {
                    font-size: 14px;
                    color: #666;
                }
                
                .review-rating {
                    color: #ffc107;
                    font-size: 16px;
                }
                
                .review-content {
                    color: #333;
                    line-height: 1.6;
                    margin-bottom: 10px;
                }
                
                .review-helpful {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    font-size: 14px;
                    color: #666;
                }
                
                .helpful-btn {
                    background: none;
                    border: 1px solid #e9ecef;
                    padding: 4px 8px;
                    border-radius: 4px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                }
                
                .helpful-btn:hover {
                    background: #f8f9fa;
                }
                
                .helpful-btn.voted {
                    background: #007bff;
                    color: white;
                    border-color: #007bff;
                }
                
                .related-game-item {
                    transition: transform 0.3s ease;
                    cursor: pointer;
                }
                
                .related-game-item:hover {
                    transform: translateY(-5px);
                }
                
                @media (max-width: 768px) {
                    .purchase-buttons {
                        flex-direction: column;
                    }
                    
                    .btn-add-to-cart,
                    .btn-buy-now {
                        min-width: 100%;
                    }
                    
                    .reviews-summary {
                        flex-direction: column;
                        text-align: center;
                    }
                    
                    .rating-breakdown {
                        width: 100%;
                    }
                }
            </style>
        `;

        document.head.insertAdjacentHTML('beforeend', styles);
    }

    setupLoadingStates() {
        // Loading states are already added in UI enhancement methods
    }

    async loadInitialData() {
        try {
            this.showLoading();

            // Load game details
            await this.loadGameDetails();

            // Update UI with game data
            this.updateProductDisplay();

            // Load related data
            await Promise.all([
                this.loadRelatedGames(),
                this.loadReviewsSummary()
            ]);

            this.updateRelatedGamesDisplay();

        } catch (error) {
            this.handleLoadError(error);
        } finally {
            this.hideLoading();
        }
    }

    async loadGameDetails() {
        try {
            this.log('Loading game details for ID:', this.state.gameId);
            
            const cacheKey = `game_details_${this.state.gameId}`;
            if (this.cache.has(cacheKey)) {
                this.state.gameData = this.cache.get(cacheKey);
                return;
            }

            const gameData = await window.apiService.getGameDetails(this.state.gameId);
            this.state.gameData = gameData;

            // Cache for 5 minutes
            this.cache.set(cacheKey, gameData);
            setTimeout(() => this.cache.delete(cacheKey), 5 * 60 * 1000);

            this.log('Game details loaded:', this.state.gameData);

        } catch (error) {
            this.log('Failed to load game details:', error);
            // Use fallback data
            this.state.gameData = this.generateFallbackGameData();
        }
    }

    generateFallbackGameData() {
        return {
            id: this.state.gameId,
            name: 'Call of Duty®: Modern Warfare® II',
            category: 'Action',
            price: 69.99,
            discount_price: 49.99,
            rating: 4.5,
            review_count: 1250,
            description: 'Experience the most advanced Call of Duty ever created. Modern Warfare® II drops players into an unprecedented global conflict that features the return of the iconic Operators of Task Force 141.',
            features: [
                'Single Player Campaign',
                'Multiplayer Mode',
                'Special Ops Co-Op',
                'Cross-Platform Play',
                '4K Ultra HD Support',
                'HDR Compatible'
            ],
            specifications: {
                'Developer': 'Infinity Ward',
                'Publisher': 'Activision',
                'Release Date': 'October 28, 2022',
                'Platform': 'PC, PlayStation, Xbox',
                'Genre': 'First-Person Shooter',
                'ESRB Rating': 'M (Mature 17+)',
                'File Size': '125 GB',
                'Languages': 'English, Spanish, French, German'
            },
            images: [
                'assets/images/single-game.jpg',
                'assets/images/trending-01.jpg',
                'assets/images/trending-02.jpg',
                'assets/images/trending-03.jpg'
            ],
            tags: ['fps', 'multiplayer', 'campaign', 'action'],
            availability: 'in_stock',
            stock_count: 500
        };
    }

    async loadRelatedGames() {
        try {
            const response = await window.apiService.getRelatedGames(
                this.state.gameId, 
                this.config.relatedGamesCount
            );
            this.state.relatedGames = response.games || [];
        } catch (error) {
            this.log('Failed to load related games:', error);
            this.state.relatedGames = this.generateFallbackRelatedGames();
        }
    }

    generateFallbackRelatedGames() {
        return [
            {
                id: 'related-1',
                name: 'Call of Duty: Warzone',
                category: 'Action',
                price: 0,
                image_url: 'assets/images/categories-01.jpg'
            },
            {
                id: 'related-2',
                name: 'Battlefield 2042',
                category: 'Action',
                price: 59.99,
                image_url: 'assets/images/categories-02.jpg'
            },
            {
                id: 'related-3',
                name: 'Apex Legends',
                category: 'Action',
                price: 0,
                image_url: 'assets/images/categories-03.jpg'
            }
        ];
    }

    async loadReviewsSummary() {
        try {
            const response = await window.apiService.getGameReviews(
                this.state.gameId, 
                1, 
                this.config.reviewsPerPage
            );
            
            this.state.reviews = response.reviews || [];
            this.state.totalReviewPages = response.total_pages || 1;
            
            this.updateReviewsDisplay();
        } catch (error) {
            this.log('Failed to load reviews:', error);
            this.generateFallbackReviews();
        }
    }

    generateFallbackReviews() {
        this.state.reviews = [
            {
                id: 1,
                user_name: 'GamerPro2023',
                rating: 5,
                content: 'Amazing game! The graphics are stunning and the multiplayer is incredibly fun. Best COD in years!',
                created_at: '2023-11-15T10:30:00Z',
                helpful_count: 45
            },
            {
                id: 2,
                user_name: 'ActionFan',
                rating: 4,
                content: 'Great campaign mode and solid multiplayer. Some balancing issues but overall very enjoyable.',
                created_at: '2023-11-10T14:22:00Z',
                helpful_count: 23
            },
            {
                id: 3,
                user_name: 'CompetitivePlayer',
                rating: 4,
                content: 'Excellent for competitive play. The new mechanics add depth to the gameplay.',
                created_at: '2023-11-08T09:15:00Z',
                helpful_count: 18
            }
        ];
        this.updateReviewsDisplay();
    }

    updateProductDisplay() {
        if (!this.state.gameData) return;

        const game = this.state.gameData;

        // Update page title and breadcrumb
        this.updatePageTitle(game.name);
        this.updateBreadcrumb(game.name, game.category);

        // Update product details
        this.updateProductInfo(game);
        this.updateProductImages(game.images);
        this.updateProductSpecs(game.specifications);
        this.updateAvailability(game.availability, game.stock_count);
        this.updatePricing(game.price, game.discount_price);

        // Enable purchase buttons
        this.enablePurchaseButtons();
    }

    updatePageTitle(gameName) {
        const titleElement = document.getElementById('dynamicTitle');
        if (titleElement) {
            titleElement.textContent = gameName;
        }
        
        // Update document title
        document.title = `${gameName} - Lugx Gaming`;
    }

    updateBreadcrumb(gameName, category) {
        const breadcrumbElement = document.getElementById('dynamicBreadcrumb');
        if (breadcrumbElement) {
            breadcrumbElement.innerHTML = `
                <a href="index.html">Home</a> > 
                <a href="shop.html">Shop</a> > 
                <a href="shop.html?category=${category.toLowerCase()}">${category}</a> > 
                ${gameName}
            `;
        }
    }

    updateProductInfo(game) {
        const productSection = document.querySelector('.single-product .col-lg-6.align-self-center');
        if (!productSection) return;

        // Update product title
        const titleElement = productSection.querySelector('h4');
        if (titleElement) {
            titleElement.textContent = game.name;
        }

        // Update description
        const descElement = productSection.querySelector('p');
        if (descElement) {
            descElement.textContent = game.description;
        }

        // Update product info list
        const infoList = productSection.querySelector('ul');
        if (infoList) {
            infoList.innerHTML = `
                <li><span>Game ID:</span> ${game.id}</li>
                <li><span>Genre:</span> <a href="shop.html?category=${game.category.toLowerCase()}">${game.category}</a></li>
                <li><span>Rating:</span> ${this.renderStars(game.rating)} (${game.review_count || 0} reviews)</li>
                <li><span>Tags:</span> ${game.tags ? game.tags.map(tag => `<a href="shop.html?tag=${tag}">${tag}</a>`).join(', ') : 'N/A'}</li>
            `;
        }
    }

    updateProductImages(images) {
        if (!images || images.length === 0) return;

        const mainImage = document.getElementById('mainProductImage');
        const thumbnailGallery = document.getElementById('thumbnailGallery');

        if (mainImage) {
            mainImage.src = images[0];
            mainImage.alt = this.state.gameData.name;
        }

        if (thumbnailGallery) {
            const thumbnailsHTML = images.map((image, index) => `
                <div class="thumbnail-item ${index === 0 ? 'active' : ''}" 
                     onclick="window.productDetailsEnhancer.selectImage(${index})">
                    <img src="${image}" alt="Product Image ${index + 1}">
                </div>
            `).join('');

            thumbnailGallery.innerHTML = thumbnailsHTML;
        }

        this.imageGallery = images;
    }

    updateProductSpecs(specifications) {
        const specsContainer = document.querySelector('.specs-grid');
        const specsSection = document.getElementById('productSpecs');
        
        if (!specsContainer || !specifications) return;

        const specsHTML = Object.entries(specifications).map(([key, value]) => `
            <div class="spec-item">
                <span class="spec-label">${key}:</span>
                <span class="spec-value">${value}</span>
            </div>
        `).join('');

        specsContainer.innerHTML = specsHTML;
        if (specsSection) {
            specsSection.style.display = 'block';
        }
    }

    updateAvailability(availability, stockCount) {
        const availabilityElement = document.getElementById('productAvailability');
        if (!availabilityElement) return;

        let availabilityClass = '';
        let availabilityText = '';

        switch (availability) {
            case 'in_stock':
                availabilityClass = 'availability-in-stock';
                availabilityText = `✓ In Stock (${stockCount || 'Available'})`;
                break;
            case 'low_stock':
                availabilityClass = 'availability-low-stock';
                availabilityText = `⚠ Low Stock (${stockCount} remaining)`;
                break;
            case 'out_of_stock':
                availabilityClass = 'availability-out-of-stock';
                availabilityText = '✗ Out of Stock';
                break;
            default:
                availabilityClass = 'availability-in-stock';
                availabilityText = '✓ Available';
        }

        availabilityElement.className = `product-availability ${availabilityClass}`;
        availabilityElement.innerHTML = `
            <i class="fa fa-info-circle"></i>
            ${availabilityText}
        `;
    }

    updatePricing(price, discountPrice) {
        const priceElement = document.querySelector('.single-product .price');
        if (!priceElement) return;

        if (discountPrice && discountPrice < price) {
            const discountPercentage = Math.round(((price - discountPrice) / price) * 100);
            priceElement.innerHTML = `<em>$${price.toFixed(2)}</em> $${discountPrice.toFixed(2)}`;
            
            // Show discount badge
            const discountBadge = document.getElementById('discountBadge');
            if (discountBadge) {
                discountBadge.innerHTML = `<span>-${discountPercentage}%</span>`;
                discountBadge.style.display = 'block';
            }
        } else {
            priceElement.innerHTML = `$${price.toFixed(2)}`;
        }
    }

    enablePurchaseButtons() {
        const addToCartBtn = document.getElementById('addToCartBtn');
        const buyNowBtn = document.getElementById('buyNowBtn');

        if (addToCartBtn) {
            addToCartBtn.disabled = false;
            addToCartBtn.dataset.gameId = this.state.gameId;
        }

        if (buyNowBtn) {
            buyNowBtn.disabled = false;
        }
    }

    updateReviewsDisplay() {
        this.updateReviewsSummary();
        this.updateReviewsList();
    }

    updateReviewsSummary() {
        const summaryElement = document.getElementById('reviewsSummary');
        if (!summaryElement || !this.state.gameData) return;

        const game = this.state.gameData;
        const rating = game.rating || 0;
        const reviewCount = game.review_count || 0;

        // Calculate rating distribution (mock data)
        const ratingDistribution = [
            { stars: 5, count: Math.floor(reviewCount * 0.6) },
            { stars: 4, count: Math.floor(reviewCount * 0.25) },
            { stars: 3, count: Math.floor(reviewCount * 0.1) },
            { stars: 2, count: Math.floor(reviewCount * 0.03) },
            { stars: 1, count: Math.floor(reviewCount * 0.02) }
        ];

        const summaryHTML = `
            <div class="rating-overview">
                <div class="rating-score">${rating.toFixed(1)}</div>
                <div class="rating-stars">${this.renderStars(rating)}</div>
                <div class="rating-count">${reviewCount} reviews</div>
            </div>
            <div class="rating-breakdown">
                ${ratingDistribution.map(dist => `
                    <div class="rating-bar">
                        <span class="rating-bar-label">${dist.stars} stars</span>
                        <div class="rating-bar-fill">
                            <div class="rating-bar-progress" style="width: ${(dist.count / reviewCount * 100)}%"></div>
                        </div>
                        <span class="rating-bar-count">${dist.count}</span>
                    </div>
                `).join('')}
            </div>
        `;

        summaryElement.innerHTML = summaryHTML;
    }

    updateReviewsList() {
        const reviewsList = document.getElementById('reviewsList');
        if (!reviewsList) return;

        if (this.state.reviews.length === 0) {
            reviewsList.innerHTML = `
                <div class="text-center py-4">
                    <i class="fa fa-comment-o fa-3x text-muted mb-3"></i>
                    <p class="text-muted">No reviews yet. Be the first to review this game!</p>
                </div>
            `;
            return;
        }

        const reviewsHTML = this.state.reviews.map(review => this.renderReviewItem(review)).join('');
        reviewsList.innerHTML = reviewsHTML;
    }

    renderReviewItem(review) {
        const reviewDate = new Date(review.created_at).toLocaleDateString();
        const initials = review.user_name.substring(0, 2).toUpperCase();

        return `
            <div class="review-item">
                <div class="review-header">
                    <div class="reviewer-avatar">${initials}</div>
                    <div class="reviewer-info">
                        <div class="reviewer-name">${review.user_name}</div>
                        <div class="review-date">${reviewDate}</div>
                    </div>
                    <div class="review-rating">${this.renderStars(review.rating)}</div>
                </div>
                <div class="review-content">${review.content}</div>
                <div class="review-helpful">
                    <span>Was this helpful?</span>
                    <button class="helpful-btn" onclick="window.productDetailsEnhancer.markHelpful(${review.id}, true)">
                        <i class="fa fa-thumbs-up"></i> Yes (${review.helpful_count || 0})
                    </button>
                    <button class="helpful-btn" onclick="window.productDetailsEnhancer.markHelpful(${review.id}, false)">
                        <i class="fa fa-thumbs-down"></i> No
                    </button>
                </div>
            </div>
        `;
    }

    updateRelatedGamesDisplay() {
        const container = document.getElementById('relatedGamesContainer');
        if (!container) return;

        // Update section header
        const sectionHeading = container.querySelector('.section-heading');
        if (sectionHeading && this.state.gameData) {
            sectionHeading.innerHTML = `
                <h6>${this.state.gameData.category}</h6>
                <h2>Related Games</h2>
            `;
        }

        // Clear existing content and add related games
        const gameColumns = container.querySelectorAll('.col-lg');
        gameColumns.forEach(col => {
            if (!col.querySelector('.section-heading') && !col.querySelector('.main-button')) {
                col.remove();
            }
        });

        // Add related games
        this.state.relatedGames.forEach(game => {
            const gameHTML = `
                <div class="col-lg col-sm-6 col-xs-12">
                    <div class="item related-game-item" onclick="window.location.href='product-details.html?id=${game.id}'">
                        <h4>${game.name}</h4>
                        <div class="thumb">
                            <img src="${game.image_url}" alt="${game.name}">
                            ${game.price > 0 ? `<span class="price">$${game.price.toFixed(2)}</span>` : '<span class="price">Free</span>'}
                        </div>
                    </div>
                </div>
            `;
            container.insertAdjacentHTML('beforeend', gameHTML);
        });
    }

    setupEventListeners() {
        // Add to cart button
        document.addEventListener('click', async (e) => {
            if (e.target.matches('#addToCartBtn') || e.target.closest('#addToCartBtn')) {
                e.preventDefault();
                await this.handleAddToCart();
            }
        });

        // Buy now button
        document.addEventListener('click', (e) => {
            if (e.target.matches('#buyNowBtn') || e.target.closest('#buyNowBtn')) {
                e.preventDefault();
                this.handleBuyNow();
            }
        });

        // Wishlist button
        document.addEventListener('click', (e) => {
            if (e.target.matches('#wishlistBtn') || e.target.closest('#wishlistBtn')) {
                e.preventDefault();
                this.handleWishlist();
            }
        });

        // Quantity input changes
        const quantityInput = document.getElementById('quantity');
        if (quantityInput) {
            quantityInput.addEventListener('change', (e) => {
                this.state.selectedQuantity = parseInt(e.target.value) || 1;
            });
        }

        // Reviews tab activation
        const reviewsTab = document.getElementById('reviews-tab');
        if (reviewsTab) {
            reviewsTab.addEventListener('click', () => {
                if (!this.reviewsLoaded) {
                    this.loadReviewsSummary();
                    this.reviewsLoaded = true;
                }
            });
        }
    }

    async handleAddToCart() {
        try {
            const button = document.getElementById('addToCartBtn');
            const originalText = button.innerHTML;
            
            // Show loading state
            button.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Adding...';
            button.disabled = true;

            // Add to cart via cart integration
            if (window.cartIntegration) {
                await window.cartIntegration.addItem(this.state.gameId, this.state.selectedQuantity);
                
                // Show success
                button.innerHTML = '<i class="fa fa-check"></i> Added to Cart!';
                button.classList.add('btn-success');
                
                setTimeout(() => {
                    button.innerHTML = originalText;
                    button.disabled = false;
                    button.classList.remove('btn-success');
                }, 2000);

                // Track add to cart
                if (window.analyticsService) {
                    window.analyticsService.trackCartAdd(
                        this.state.gameId,
                        this.state.gameData.name,
                        this.state.gameData.discount_price || this.state.gameData.price,
                        this.state.selectedQuantity
                    );
                }
            }

        } catch (error) {
            console.error('Add to cart failed:', error);
            const button = document.getElementById('addToCartBtn');
            button.innerHTML = '<i class="fa fa-exclamation"></i> Failed';
            button.classList.add('btn-danger');
            
            setTimeout(() => {
                button.innerHTML = '<i class="fa fa-shopping-bag"></i> <span class="btn-text">Add to Cart</span>';
                button.disabled = false;
                button.classList.remove('btn-danger');
            }, 3000);
        }
    }

    handleBuyNow() {
        // Redirect to checkout with this item
        const checkoutUrl = `checkout.html?game_id=${this.state.gameId}&quantity=${this.state.selectedQuantity}`;
        window.location.href = checkoutUrl;

        // Track buy now
        if (window.analyticsService) {
            window.analyticsService.track('buy_now_clicked', {
                game_id: this.state.gameId,
                game_name: this.state.gameData.name,
                quantity: this.state.selectedQuantity,
                price: this.state.gameData.discount_price || this.state.gameData.price
            });
        }
    }

    handleWishlist() {
        const button = document.getElementById('wishlistBtn');
        const isActive = button.classList.contains('active');
        
        if (isActive) {
            button.classList.remove('active');
            button.innerHTML = '<i class="fa fa-heart-o"></i>';
            button.title = 'Add to Wishlist';
        } else {
            button.classList.add('active');
            button.innerHTML = '<i class="fa fa-heart"></i>';
            button.title = 'Remove from Wishlist';
        }

        // Track wishlist action
        if (window.analyticsService) {
            window.analyticsService.track('wishlist_toggled', {
                game_id: this.state.gameId,
                game_name: this.state.gameData.name,
                action: isActive ? 'removed' : 'added'
            });
        }
    }

    // Image gallery methods
    selectImage(index) {
        if (!this.imageGallery || index < 0 || index >= this.imageGallery.length) return;

        this.state.currentImageIndex = index;
        
        const mainImage = document.getElementById('mainProductImage');
        if (mainImage) {
            mainImage.src = this.imageGallery[index];
        }

        // Update thumbnail active state
        document.querySelectorAll('.thumbnail-item').forEach((item, i) => {
            item.classList.toggle('active', i === index);
        });
    }

    nextImage() {
        const nextIndex = (this.state.currentImageIndex + 1) % this.imageGallery.length;
        this.selectImage(nextIndex);
    }

    previousImage() {
        const prevIndex = this.state.currentImageIndex === 0 
            ? this.imageGallery.length - 1 
            : this.state.currentImageIndex - 1;
        this.selectImage(prevIndex);
    }

    // Quantity adjustment methods
    adjustQuantity(change) {
        const quantityInput = document.getElementById('quantity');
        if (!quantityInput) return;

        const currentValue = parseInt(quantityInput.value) || 1;
        const newValue = Math.max(1, Math.min(10, currentValue + change));
        
        quantityInput.value = newValue;
        this.state.selectedQuantity = newValue;
    }

    // Review interaction methods
    markHelpful(reviewId, isHelpful) {
        // Implementation for marking reviews as helpful
        const button = event.target.closest('.helpful-btn');
        if (button && !button.classList.contains('voted')) {
            button.classList.add('voted');
            
            if (isHelpful) {
                const count = button.textContent.match(/\d+/);
                if (count) {
                    const newCount = parseInt(count[0]) + 1;
                    button.innerHTML = `<i class="fa fa-thumbs-up"></i> Yes (${newCount})`;
                }
            }
        }
    }

    showReviewForm() {
        // Implementation for showing review form modal
        alert('Review form would open here. This feature requires user authentication.');
    }

    // Utility methods
    renderStars(rating) {
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 >= 0.5;
        const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

        return '★'.repeat(fullStars) + 
               (hasHalfStar ? '☆' : '') + 
               '☆'.repeat(emptyStars);
    }

    showLoading() {
        this.state.loading = true;
        const loadingElement = document.getElementById('productLoading');
        if (loadingElement) {
            loadingElement.style.display = 'flex';
        }
    }

    hideLoading() {
        this.state.loading = false;
        const loadingElement = document.getElementById('productLoading');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }

    handleLoadError(error) {
        console.error('Failed to load product data:', error);
        
        // Show error message
        const productSection = document.querySelector('.single-product .container');
        if (productSection) {
            productSection.innerHTML = `
                <div class="row">
                    <div class="col-12">
                        <div class="alert alert-warning text-center">
                            <h4>Product Not Found</h4>
                            <p>The requested product could not be loaded. It may have been removed or the ID is invalid.</p>
                            <a href="shop.html" class="btn btn-primary">Browse All Games</a>
                        </div>
                    </div>
                </div>
            `;
        }

        if (window.analyticsService) {
            window.analyticsService.trackError(error, { 
                context: 'product_details_load_error',
                game_id: this.state.gameId
            });
        }
    }

    handleInitializationError(error) {
        console.error('Product details enhancement initialization failed:', error);
        // Continue with basic functionality
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    log(...args) {
        if (this.config.enableDebugLogging) {
            console.log('[ProductDetailsEnhancer]', ...args);
        }
    }

    // Public API methods
    getProductData() {
        return { ...this.state.gameData };
    }

    getCurrentQuantity() {
        return this.state.selectedQuantity;
    }

    async refreshProductData() {
        this.cache.clear();
        await this.loadInitialData();
    }
}

// Initialize product details enhancement when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.productDetailsEnhancer = new ProductDetailsEnhancer();
});

// Log initialization
console.log('LugX Product Details Enhancement loaded');

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ProductDetailsEnhancer };
}