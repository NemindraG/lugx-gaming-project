/**
 * LugX Gaming Shopping Cart Integration
 * Handles cart operations for both guest and authenticated users
 * Provides seamless synchronization and real-time updates
 */

class CartIntegration {
    constructor() {
        this.cartState = {
            items: [],
            total: 0,
            subtotal: 0,
            tax: 0,
            shipping: 0,
            count: 0,
            currency: 'USD'
        };

        this.config = {
            guestStorageKey: 'lugx_guest_cart',
            syncOnLogin: true,
            enableRealTimeUpdates: true,
            taxRate: 0.08, // 8% tax
            freeShippingThreshold: 50,
            shippingCost: 5.99,
            enableDebugLogging: window.location.hostname === 'localhost'
        };

        this.isInitialized = false;
        this.syncPromise = null;
        
        this.initializeCart();
    }

    async initializeCart() {
        try {
            this.log('Initializing shopping cart...');

            // Wait for dependencies
            await this.waitForDependencies();

            // Load cart data based on authentication status
            if (window.authService && window.authService.isAuthenticated()) {
                await this.loadCartFromServer();
            } else {
                this.loadCartFromLocalStorage();
            }

            // Setup cart UI elements
            this.setupCartUI();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Update cart display
            this.updateCartDisplay();

            this.isInitialized = true;
            this.log('Cart initialized successfully:', this.cartState);

            // Track cart initialization
            if (window.analyticsService) {
                window.analyticsService.track('cart_initialized', {
                    user_type: window.authService?.isAuthenticated() ? 'authenticated' : 'guest',
                    item_count: this.cartState.count,
                    cart_total: this.cartState.total
                });
            }

        } catch (error) {
            console.error('Cart initialization failed:', error);
            
            // Fallback to empty cart
            this.cartState = this.getEmptyCartState();
            this.updateCartDisplay();

            if (window.analyticsService) {
                window.analyticsService.trackError(error, { 
                    context: 'cart_initialization' 
                });
            }
        }
    }

    async waitForDependencies() {
        const maxWaitTime = 5000; // 5 seconds
        const checkInterval = 100; // 100ms
        let waited = 0;

        while (waited < maxWaitTime) {
            if (window.apiService && window.analyticsService) {
                return;
            }
            await this.delay(checkInterval);
            waited += checkInterval;
        }

        this.log('Dependencies not fully ready, proceeding with available services');
    }

    async loadCartFromServer() {
        try {
            this.log('Loading cart from server...');
            
            const response = await window.apiService.get('order', '/cart');
            
            this.cartState = {
                items: response.items || [],
                total: response.total || 0,
                subtotal: response.subtotal || 0,
                tax: response.tax || 0,
                shipping: response.shipping || 0,
                count: response.total_items || 0,
                currency: response.currency || 'USD'
            };

            this.log('Cart loaded from server:', this.cartState);

        } catch (error) {
            this.log('Failed to load cart from server:', error);
            
            // If user session expired, clear local auth and load guest cart
            if (error.status === 401 && window.authService) {
                window.authService.clearAuthData();
                this.loadCartFromLocalStorage();
            } else {
                throw error;
            }
        }
    }

    loadCartFromLocalStorage() {
        try {
            const savedCart = localStorage.getItem(this.config.guestStorageKey);
            if (savedCart) {
                const parsedCart = JSON.parse(savedCart);
                this.cartState = {
                    ...this.getEmptyCartState(),
                    ...parsedCart
                };
                this.recalculateCartTotals();
                this.log('Cart loaded from localStorage:', this.cartState);
            } else {
                this.cartState = this.getEmptyCartState();
                this.log('No saved cart found, starting with empty cart');
            }
        } catch (error) {
            console.warn('Invalid cart data in localStorage:', error);
            this.cartState = this.getEmptyCartState();
            localStorage.removeItem(this.config.guestStorageKey);
        }
    }

    saveCartToLocalStorage() {
        try {
            localStorage.setItem(this.config.guestStorageKey, JSON.stringify(this.cartState));
            this.log('Cart saved to localStorage');
        } catch (error) {
            console.warn('Failed to save cart to localStorage:', error);
        }
    }

    setupCartUI() {
        // Add cart widget to navigation if it doesn't exist
        this.addCartWidgetToNavigation();
        
        // Setup mini cart dropdown
        this.setupMiniCartDropdown();
        
        // Add cart styles
        this.addCartStyles();
    }

    addCartWidgetToNavigation() {
        const nav = document.querySelector('.header-area nav ul');
        if (!nav || document.querySelector('.cart-widget')) {
            return; // Cart widget already exists or nav not found
        }

        const cartWidgetHTML = `
            <li class="cart-widget">
                <a href="#" class="cart-link" data-track-click="cart-icon">
                    <i class="fa fa-shopping-cart"></i>
                    <span class="cart-badge" style="display: none;">0</span>
                </a>
                <div class="mini-cart-dropdown" style="display: none;">
                    <div class="mini-cart-content">
                        <!-- Cart items will be inserted here -->
                    </div>
                </div>
            </li>
        `;

        nav.insertAdjacentHTML('beforeend', cartWidgetHTML);

        // Add click handler for cart widget
        const cartLink = nav.querySelector('.cart-link');
        if (cartLink) {
            cartLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleMiniCart();
            });
        }
    }

    setupMiniCartDropdown() {
        // Close mini cart when clicking outside
        document.addEventListener('click', (e) => {
            const miniCart = document.querySelector('.mini-cart-dropdown');
            const cartWidget = document.querySelector('.cart-widget');
            
            if (miniCart && !cartWidget?.contains(e.target)) {
                miniCart.style.display = 'none';
            }
        });
    }

    addCartStyles() {
        if (document.getElementById('cart-integration-styles')) {
            return; // Styles already added
        }

        const styles = `
            <style id="cart-integration-styles">
                .cart-widget {
                    position: relative;
                }
                
                .cart-link {
                    position: relative;
                    padding: 10px 15px;
                    text-decoration: none;
                    color: #333;
                }
                
                .cart-badge {
                    position: absolute;
                    top: 5px;
                    right: 8px;
                    background: #e74c3c;
                    color: white;
                    border-radius: 50%;
                    padding: 2px 6px;
                    font-size: 11px;
                    font-weight: bold;
                    min-width: 18px;
                    text-align: center;
                }
                
                .mini-cart-dropdown {
                    position: absolute;
                    top: 100%;
                    right: 0;
                    width: 300px;
                    background: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    z-index: 1000;
                    max-height: 400px;
                    overflow-y: auto;
                }
                
                .mini-cart-content {
                    padding: 15px;
                }
                
                .mini-cart-item {
                    display: flex;
                    align-items: center;
                    padding: 10px 0;
                    border-bottom: 1px solid #eee;
                }
                
                .mini-cart-item:last-child {
                    border-bottom: none;
                }
                
                .mini-cart-item img {
                    width: 50px;
                    height: 50px;
                    object-fit: cover;
                    border-radius: 4px;
                    margin-right: 10px;
                }
                
                .mini-cart-item-details {
                    flex: 1;
                }
                
                .mini-cart-item-name {
                    font-weight: bold;
                    font-size: 14px;
                    margin-bottom: 4px;
                }
                
                .mini-cart-item-price {
                    color: #666;
                    font-size: 12px;
                }
                
                .mini-cart-footer {
                    border-top: 1px solid #eee;
                    padding-top: 15px;
                    margin-top: 15px;
                }
                
                .mini-cart-total {
                    text-align: center;
                    font-weight: bold;
                    margin-bottom: 10px;
                    font-size: 16px;
                }
                
                .mini-cart-buttons {
                    display: flex;
                    gap: 10px;
                }
                
                .mini-cart-buttons .btn {
                    flex: 1;
                    padding: 8px 12px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    text-decoration: none;
                    text-align: center;
                    font-size: 14px;
                }
                
                .btn-outline {
                    background: transparent;
                    border: 1px solid #007bff;
                    color: #007bff;
                }
                
                .btn-primary {
                    background: #007bff;
                    color: white;
                }
                
                .empty-cart {
                    text-align: center;
                    color: #666;
                    padding: 20px;
                }
                
                .cart-item-loading {
                    opacity: 0.6;
                    pointer-events: none;
                }
                
                .add-to-cart-success {
                    background-color: #28a745 !important;
                    color: white !important;
                }
                
                .add-to-cart-error {
                    background-color: #dc3545 !important;
                    color: white !important;
                }
            </style>
        `;
        
        document.head.insertAdjacentHTML('beforeend', styles);
    }

    setupEventListeners() {
        // Listen for add to cart button clicks
        document.addEventListener('click', async (e) => {
            if (e.target.matches('.add-to-cart, [data-action="add-to-cart"]') ||
                e.target.closest('.add-to-cart, [data-action="add-to-cart"]')) {
                e.preventDefault();
                const button = e.target.matches('.add-to-cart, [data-action="add-to-cart"]') 
                    ? e.target 
                    : e.target.closest('.add-to-cart, [data-action="add-to-cart"]');
                await this.handleAddToCart(button);
            }
        });

        // Listen for cart removal actions
        document.addEventListener('click', async (e) => {
            if (e.target.matches('.remove-from-cart, [data-action="remove-from-cart"]') ||
                e.target.closest('.remove-from-cart, [data-action="remove-from-cart"]')) {
                e.preventDefault();
                const button = e.target.matches('.remove-from-cart, [data-action="remove-from-cart"]') 
                    ? e.target 
                    : e.target.closest('.remove-from-cart, [data-action="remove-from-cart"]');
                await this.handleRemoveFromCart(button);
            }
        });

        // Listen for quantity changes
        document.addEventListener('change', async (e) => {
            if (e.target.matches('.cart-quantity-input')) {
                await this.handleQuantityChange(e.target);
            }
        });

        // Sync cart when user logs in
        if (window.authService) {
            window.authService.addEventListener('authStateChanged', async (data) => {
                if (data.isAuthenticated && this.config.syncOnLogin) {
                    await this.syncGuestCartToServer();
                }
            });

            window.authService.addEventListener('userLoggedOut', () => {
                this.loadCartFromLocalStorage();
                this.updateCartDisplay();
            });
        }
    }

    async handleAddToCart(button) {
        const gameId = this.extractGameId(button);
        const quantity = parseInt(button.dataset.quantity) || 1;

        if (!gameId) {
            console.warn('No game ID found for add to cart action');
            return;
        }

        try {
            this.log('Adding to cart:', { gameId, quantity });
            
            this.showButtonLoading(button, 'Adding...');

            let cartItem;
            if (window.authService && window.authService.isAuthenticated()) {
                cartItem = await this.addToServerCart(gameId, quantity);
            } else {
                cartItem = await this.addToGuestCart(gameId, quantity);
            }

            this.showAddToCartSuccess(button);
            this.updateCartDisplay();

            // Track add to cart event
            if (window.analyticsService) {
                window.analyticsService.trackCartAdd(
                    gameId,
                    cartItem.game_name,
                    cartItem.price,
                    quantity,
                    {
                        cart_total: this.cartState.total,
                        user_type: window.authService?.isAuthenticated() ? 'authenticated' : 'guest',
                        source_page: window.location.pathname
                    }
                );
            }

        } catch (error) {
            this.log('Add to cart failed:', error);
            this.showAddToCartError(button, error);
            
            if (window.analyticsService) {
                window.analyticsService.trackError(error, { 
                    context: 'add_to_cart',
                    game_id: gameId,
                    quantity: quantity
                });
            }
        } finally {
            this.hideButtonLoading(button);
        }
    }

    async addToServerCart(gameId, quantity) {
        const response = await window.apiService.post('order', '/cart/items', {
            game_id: gameId,
            quantity: quantity
        });

        // Reload cart from server to get updated state
        await this.loadCartFromServer();
        
        return response.item;
    }

    async addToGuestCart(gameId, quantity) {
        // Get game details first
        const gameDetails = await window.apiService.getGameDetails(gameId);
        
        // Check if item already exists in cart
        const existingItemIndex = this.cartState.items.findIndex(item => item.game_id === gameId);
        
        let cartItem;
        if (existingItemIndex >= 0) {
            // Update existing item
            this.cartState.items[existingItemIndex].quantity += quantity;
            cartItem = this.cartState.items[existingItemIndex];
        } else {
            // Add new item
            cartItem = {
                id: `guest_${Date.now()}_${gameId}`,
                game_id: gameId,
                game_name: gameDetails.name,
                price: gameDetails.discount_price || gameDetails.price,
                original_price: gameDetails.price,
                quantity: quantity,
                image_url: gameDetails.image_url,
                category: gameDetails.category
            };
            this.cartState.items.push(cartItem);
        }

        // Recalculate cart totals
        this.recalculateCartTotals();
        
        // Save to localStorage
        this.saveCartToLocalStorage();
        
        return cartItem;
    }

    async handleRemoveFromCart(button) {
        const itemId = button.dataset.itemId || button.closest('[data-item-id]')?.dataset.itemId;
        const gameId = button.dataset.gameId || button.closest('[data-game-id]')?.dataset.gameId;
        
        if (!itemId && !gameId) {
            console.warn('No item ID or game ID found for remove action');
            return;
        }

        try {
            this.log('Removing from cart:', { itemId, gameId });
            
            if (window.authService && window.authService.isAuthenticated()) {
                await window.apiService.delete('order', `/cart/items/${itemId}`);
                await this.loadCartFromServer();
            } else {
                if (itemId) {
                    this.cartState.items = this.cartState.items.filter(item => item.id !== itemId);
                } else if (gameId) {
                    this.cartState.items = this.cartState.items.filter(item => item.game_id !== gameId);
                }
                this.recalculateCartTotals();
                this.saveCartToLocalStorage();
            }

            this.updateCartDisplay();

            // Track removal
            if (window.analyticsService) {
                window.analyticsService.trackCartRemove(gameId || 'unknown', 'Unknown Game', {
                    item_id: itemId,
                    cart_total: this.cartState.total,
                    user_type: window.authService?.isAuthenticated() ? 'authenticated' : 'guest'
                });
            }

        } catch (error) {
            console.error('Failed to remove item from cart:', error);
            
            if (window.analyticsService) {
                window.analyticsService.trackError(error, { 
                    context: 'remove_from_cart',
                    item_id: itemId,
                    game_id: gameId
                });
            }
        }
    }

    async handleQuantityChange(input) {
        const newQuantity = parseInt(input.value);
        const itemId = input.dataset.itemId || input.closest('[data-item-id]')?.dataset.itemId;
        
        if (!itemId || newQuantity < 1) {
            return;
        }

        try {
            if (window.authService && window.authService.isAuthenticated()) {
                await window.apiService.put('order', `/cart/items/${itemId}`, {
                    quantity: newQuantity
                });
                await this.loadCartFromServer();
            } else {
                const item = this.cartState.items.find(item => item.id === itemId);
                if (item) {
                    item.quantity = newQuantity;
                    this.recalculateCartTotals();
                    this.saveCartToLocalStorage();
                }
            }

            this.updateCartDisplay();

        } catch (error) {
            console.error('Failed to update quantity:', error);
            // Revert input value
            const item = this.cartState.items.find(item => item.id === itemId);
            if (item) {
                input.value = item.quantity;
            }
        }
    }

    async syncGuestCartToServer() {
        if (this.cartState.items.length === 0 || this.syncPromise) {
            return;
        }

        this.syncPromise = this.performCartSync();
        
        try {
            await this.syncPromise;
        } finally {
            this.syncPromise = null;
        }
    }

    async performCartSync() {
        try {
            this.log('Syncing guest cart to server...');
            
            // Add guest cart items to server cart
            for (const item of this.cartState.items) {
                try {
                    await window.apiService.post('order', '/cart/items', {
                        game_id: item.game_id,
                        quantity: item.quantity
                    });
                } catch (error) {
                    console.warn(`Failed to sync item ${item.game_id}:`, error);
                    // Continue with other items
                }
            }

            // Clear guest cart
            this.cartState = this.getEmptyCartState();
            localStorage.removeItem(this.config.guestStorageKey);

            // Load synchronized cart from server
            await this.loadCartFromServer();
            this.updateCartDisplay();

            this.log('Cart sync completed successfully');

            // Track sync event
            if (window.analyticsService) {
                window.analyticsService.track('cart_synced', {
                    synced_items: this.cartState.items.length,
                    new_total: this.cartState.total
                });
            }

        } catch (error) {
            console.warn('Failed to sync guest cart to server:', error);
            
            if (window.analyticsService) {
                window.analyticsService.trackError(error, { 
                    context: 'cart_sync' 
                });
            }
        }
    }

    recalculateCartTotals() {
        this.cartState.subtotal = this.cartState.items.reduce(
            (total, item) => total + (item.price * item.quantity), 
            0
        );
        
        this.cartState.count = this.cartState.items.reduce(
            (count, item) => count + item.quantity, 
            0
        );

        // Calculate tax
        this.cartState.tax = this.cartState.subtotal * this.config.taxRate;

        // Calculate shipping
        if (this.cartState.subtotal >= this.config.freeShippingThreshold) {
            this.cartState.shipping = 0;
        } else if (this.cartState.subtotal > 0) {
            this.cartState.shipping = this.config.shippingCost;
        } else {
            this.cartState.shipping = 0;
        }

        // Calculate total
        this.cartState.total = this.cartState.subtotal + this.cartState.tax + this.cartState.shipping;
    }

    updateCartDisplay() {
        this.updateCartBadge();
        this.updateMiniCart();
        this.updateCartPage();
    }

    updateCartBadge() {
        const cartBadge = document.querySelector('.cart-badge');
        if (cartBadge) {
            cartBadge.textContent = this.cartState.count;
            cartBadge.style.display = this.cartState.count > 0 ? 'inline-block' : 'none';
        }
    }

    updateMiniCart() {
        const miniCartContent = document.querySelector('.mini-cart-content');
        if (!miniCartContent) return;

        if (this.cartState.items.length === 0) {
            miniCartContent.innerHTML = '<div class="empty-cart">Your cart is empty</div>';
            return;
        }

        const itemsHTML = this.cartState.items.slice(0, 3).map(item => `
            <div class="mini-cart-item" data-item-id="${item.id}">
                <img src="${item.image_url || 'assets/images/default-game.jpg'}" 
                     alt="${item.game_name}"
                     onerror="this.src='assets/images/default-game.jpg'">
                <div class="mini-cart-item-details">
                    <div class="mini-cart-item-name">${item.game_name}</div>
                    <div class="mini-cart-item-price">$${item.price} × ${item.quantity}</div>
                </div>
            </div>
        `).join('');

        const moreItems = this.cartState.items.length > 3 
            ? `<div class="more-items" style="text-align: center; color: #666; font-size: 12px; padding: 5px;">
                 +${this.cartState.items.length - 3} more items
               </div>` 
            : '';

        miniCartContent.innerHTML = `
            ${itemsHTML}
            ${moreItems}
            <div class="mini-cart-footer">
                <div class="mini-cart-total">Total: $${this.cartState.total.toFixed(2)}</div>
                <div class="mini-cart-buttons">
                    <a href="cart.html" class="btn btn-outline">View Cart</a>
                    <a href="checkout.html" class="btn btn-primary">Checkout</a>
                </div>
            </div>
        `;
    }

    updateCartPage() {
        // This would update a dedicated cart page if it exists
        const cartPageContainer = document.querySelector('.cart-page-container');
        if (!cartPageContainer) return;

        // Implementation for cart page updates would go here
        this.renderFullCartPage(cartPageContainer);
    }

    toggleMiniCart() {
        const miniCart = document.querySelector('.mini-cart-dropdown');
        if (!miniCart) return;

        const isVisible = miniCart.style.display !== 'none';
        miniCart.style.display = isVisible ? 'none' : 'block';

        if (!isVisible && window.analyticsService) {
            window.analyticsService.track('mini_cart_opened', {
                item_count: this.cartState.count,
                cart_total: this.cartState.total
            });
        }
    }

    // Utility methods
    extractGameId(element) {
        return element.dataset.gameId || 
               element.closest('[data-game-id]')?.dataset.gameId ||
               new URLSearchParams(window.location.search).get('id');
    }

    showButtonLoading(button, text = 'Loading...') {
        if (!button) return;
        
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.innerHTML = `<span class="spinner-border spinner-border-sm me-1" style="width: 12px; height: 12px;"></span>${text}`;
    }

    hideButtonLoading(button) {
        if (!button) return;
        
        button.disabled = false;
        button.textContent = button.dataset.originalText || 'Add to Cart';
    }

    showAddToCartSuccess(button) {
        const originalText = button.textContent;
        const originalClass = button.className;
        
        button.textContent = 'Added!';
        button.classList.add('add-to-cart-success');
        
        setTimeout(() => {
            button.textContent = originalText;
            button.className = originalClass;
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
        const originalClass = button.className;
        
        button.textContent = message;
        button.classList.add('add-to-cart-error');
        
        setTimeout(() => {
            button.textContent = originalText;
            button.className = originalClass;
        }, 3000);
    }

    getEmptyCartState() {
        return {
            items: [],
            total: 0,
            subtotal: 0,
            tax: 0,
            shipping: 0,
            count: 0,
            currency: 'USD'
        };
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    log(...args) {
        if (this.config.enableDebugLogging) {
            console.log('[CartIntegration]', ...args);
        }
    }

    // Public API methods
    async addItem(gameId, quantity = 1) {
        const mockButton = { 
            dataset: { gameId: gameId, quantity: quantity } 
        };
        return this.handleAddToCart(mockButton);
    }

    async removeItem(itemId) {
        const mockButton = { 
            dataset: { itemId: itemId } 
        };
        return this.handleRemoveFromCart(mockButton);
    }

    async updateQuantity(itemId, quantity) {
        const mockInput = { 
            value: quantity,
            dataset: { itemId: itemId }
        };
        return this.handleQuantityChange(mockInput);
    }

    async clearCart() {
        try {
            if (window.authService && window.authService.isAuthenticated()) {
                await window.apiService.delete('order', '/cart/clear');
                await this.loadCartFromServer();
            } else {
                this.cartState = this.getEmptyCartState();
                this.saveCartToLocalStorage();
            }
            
            this.updateCartDisplay();
            
            if (window.analyticsService) {
                window.analyticsService.track('cart_cleared', {
                    user_type: window.authService?.isAuthenticated() ? 'authenticated' : 'guest'
                });
            }
            
        } catch (error) {
            console.error('Failed to clear cart:', error);
            throw error;
        }
    }

    getCartState() {
        return { ...this.cartState };
    }

    getCartSummary() {
        return {
            itemCount: this.cartState.count,
            subtotal: this.cartState.subtotal,
            tax: this.cartState.tax,
            shipping: this.cartState.shipping,
            total: this.cartState.total,
            currency: this.cartState.currency,
            isEmpty: this.cartState.items.length === 0
        };
    }

    // Event system for cart updates
    onCartUpdate(callback) {
        document.addEventListener('cartUpdated', callback);
    }

    offCartUpdate(callback) {
        document.removeEventListener('cartUpdated', callback);
    }

    emitCartUpdate() {
        document.dispatchEvent(new CustomEvent('cartUpdated', {
            detail: this.getCartSummary()
        }));
    }
}

// Initialize cart integration when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.cartIntegration = new CartIntegration();
});

// Log initialization
console.log('LugX Cart Integration loaded');

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CartIntegration };
}