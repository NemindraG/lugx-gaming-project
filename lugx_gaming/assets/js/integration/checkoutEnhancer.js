/**
 * LugX Gaming Checkout Enhancement
 * Comprehensive checkout flow with payment processing, validation, and order creation
 * Supports guest and authenticated users with seamless cart integration
 */

class CheckoutEnhancer {
    constructor() {
        this.config = {
            enableGuestCheckout: true,
            enablePayPal: true,
            enableApplePay: window.ApplePaySession?.canMakePayments() || false,
            taxRate: 0.08, // 8% tax
            freeShippingThreshold: 50,
            shippingCost: 5.99,
            enableDebugLogging: window.location.hostname === 'localhost'
        };

        this.state = {
            cartItems: [],
            cartSummary: null,
            isAuthenticated: false,
            currentUser: null,
            selectedPaymentMethod: 'credit_card',
            shippingInfo: {},
            paymentInfo: {},
            orderTotal: 0,
            loading: false,
            step: 'review', // review, processing, complete
            orderId: null
        };

        this.validationRules = {
            email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
            zipCode: /^\d{5}(-\d{4})?$/,
            cardNumber: /^\d{4}\s?\d{4}\s?\d{4}\s?\d{4}$/,
            cvv: /^\d{3,4}$/
        };

        this.isInitialized = false;
        this.orderProcessing = false;

        this.initializeCheckout();
    }

    async initializeCheckout() {
        try {
            this.log('Initializing checkout enhancement...');

            // Wait for dependencies
            await this.waitForDependencies();

            // Check authentication status
            this.checkAuthenticationStatus();

            // Load cart data
            await this.loadCartData();

            // Setup checkout UI
            this.setupCheckoutUI();

            // Setup event listeners
            this.setupEventListeners();

            // Validate checkout state
            this.validateCheckoutState();

            this.isInitialized = true;
            this.log('Checkout enhancement initialized successfully');

            // Track checkout start
            if (window.analyticsService) {
                window.analyticsService.track('checkout_started', {
                    cart_value: this.state.orderTotal,
                    item_count: this.state.cartItems.length,
                    user_type: this.state.isAuthenticated ? 'authenticated' : 'guest'
                });
            }

        } catch (error) {
            console.error('Checkout enhancement initialization failed:', error);
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

    checkAuthenticationStatus() {
        if (window.authService && window.authService.isAuthenticated()) {
            this.state.isAuthenticated = true;
            this.state.currentUser = window.authService.getCurrentUser();
            this.showAuthenticatedUserInfo();
        } else {
            this.state.isAuthenticated = false;
            this.showGuestCheckout();
        }
    }

    showAuthenticatedUserInfo() {
        const guestSection = document.getElementById('guestCheckout');
        const authSection = document.getElementById('authenticatedUser');
        const userNameElement = document.getElementById('userName');
        const userEmailElement = document.getElementById('userEmail');

        if (guestSection) guestSection.style.display = 'none';
        if (authSection) authSection.style.display = 'block';

        if (this.state.currentUser) {
            if (userNameElement) {
                userNameElement.textContent = `Welcome back, ${this.state.currentUser.first_name}!`;
            }
            if (userEmailElement) {
                userEmailElement.textContent = this.state.currentUser.email;
            }

            // Pre-fill shipping information if available
            this.prefillShippingInfo();
        }
    }

    showGuestCheckout() {
        const guestSection = document.getElementById('guestCheckout');
        const authSection = document.getElementById('authenticatedUser');

        if (guestSection) guestSection.style.display = 'block';
        if (authSection) authSection.style.display = 'none';
    }

    prefillShippingInfo() {
        // Pre-fill shipping information from user profile if available
        if (this.state.currentUser && this.state.currentUser.shipping_address) {
            const address = this.state.currentUser.shipping_address;
            
            this.setValue('firstName', address.first_name || this.state.currentUser.first_name);
            this.setValue('lastName', address.last_name || this.state.currentUser.last_name);
            this.setValue('address', address.street_address);
            this.setValue('addressLine2', address.address_line2);
            this.setValue('city', address.city);
            this.setValue('state', address.state);
            this.setValue('zipCode', address.zip_code);
            this.setValue('country', address.country || 'US');
        }
    }

    async loadCartData() {
        try {
            if (!window.cartIntegration) {
                throw new Error('Cart integration not available');
            }

            const cartState = window.cartIntegration.getCartState();
            this.state.cartItems = cartState.items || [];
            this.state.cartSummary = window.cartIntegration.getCartSummary();

            if (this.state.cartItems.length === 0) {
                this.showEmptyCartState();
                return;
            }

            this.updateOrderSummary();
            this.showCheckoutContent();

        } catch (error) {
            this.log('Failed to load cart data:', error);
            this.showEmptyCartState();
        }
    }

    setupCheckoutUI() {
        this.setupPaymentMethodToggle();
        this.setupFormValidation();
        this.setupCardNumberFormatting();
        this.populateYearOptions();
        this.addCheckoutStyles();
    }

    setupPaymentMethodToggle() {
        const paymentMethods = document.querySelectorAll('input[name="paymentMethod"]');
        paymentMethods.forEach(method => {
            method.addEventListener('change', (e) => {
                this.handlePaymentMethodChange(e.target.value);
            });
        });
    }

    handlePaymentMethodChange(method) {
        this.state.selectedPaymentMethod = method;

        // Hide all payment forms
        document.querySelectorAll('.payment-form').forEach(form => {
            form.style.display = 'none';
        });

        // Show selected payment form
        const selectedForm = document.getElementById(`${method}Form`);
        if (selectedForm) {
            selectedForm.style.display = 'block';
        }

        // Track payment method selection
        if (window.analyticsService) {
            window.analyticsService.track('checkout_payment_method_selected', {
                payment_method: method
            });
        }
    }

    setupCardNumberFormatting() {
        const cardNumberInput = document.getElementById('cardNumber');
        if (cardNumberInput) {
            cardNumberInput.addEventListener('input', (e) => {
                let value = e.target.value.replace(/\D/g, '');
                value = value.replace(/(\d{4})(?=\d)/g, '$1 ');
                e.target.value = value;
                
                // Validate card number
                this.validateCardNumber(value);
            });
        }

        const cvvInput = document.getElementById('cvv');
        if (cvvInput) {
            cvvInput.addEventListener('input', (e) => {
                e.target.value = e.target.value.replace(/\D/g, '');
            });
        }
    }

    populateYearOptions() {
        const yearSelect = document.getElementById('expiryYear');
        if (yearSelect) {
            const currentYear = new Date().getFullYear();
            for (let i = 0; i < 20; i++) {
                const year = currentYear + i;
                const option = document.createElement('option');
                option.value = year;
                option.textContent = year;
                yearSelect.appendChild(option);
            }
        }
    }

    addCheckoutStyles() {
        if (document.getElementById('checkout-enhancer-styles')) {
            return; // Styles already added
        }

        const styles = `
            <style id="checkout-enhancer-styles">
                .checkout-container {
                    padding: 60px 0;
                    min-height: 600px;
                }
                
                .checkout-loading {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    min-height: 400px;
                    flex-direction: column;
                }
                
                .checkout-content {
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
                    overflow: hidden;
                }
                
                .checkout-section {
                    margin-bottom: 30px;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                    overflow: hidden;
                }
                
                .section-header {
                    background: #f8f9fa;
                    padding: 15px 20px;
                    border-bottom: 1px solid #e9ecef;
                }
                
                .section-header h4 {
                    margin: 0;
                    color: #333;
                    font-size: 18px;
                }
                
                .section-header i {
                    margin-right: 10px;
                    color: #007bff;
                }
                
                .section-content {
                    padding: 20px;
                }
                
                .form-group {
                    margin-bottom: 20px;
                }
                
                .form-group label {
                    display: block;
                    margin-bottom: 8px;
                    font-weight: 500;
                    color: #333;
                }
                
                .form-control {
                    width: 100%;
                    padding: 12px 16px;
                    border: 2px solid #e1e5e9;
                    border-radius: 8px;
                    font-size: 16px;
                    transition: border-color 0.3s ease;
                }
                
                .form-control:focus {
                    outline: none;
                    border-color: #007bff;
                    box-shadow: 0 0 0 3px rgba(0,123,255,0.1);
                }
                
                .form-control.is-invalid {
                    border-color: #dc3545;
                }
                
                .form-control.is-valid {
                    border-color: #28a745;
                }
                
                .invalid-feedback {
                    display: block;
                    color: #dc3545;
                    font-size: 14px;
                    margin-top: 5px;
                }
                
                .user-info {
                    display: flex;
                    align-items: center;
                    gap: 15px;
                    padding: 15px;
                    background: #f8f9fa;
                    border-radius: 8px;
                }
                
                .user-avatar {
                    font-size: 40px;
                    color: #007bff;
                }
                
                .user-details {
                    flex: 1;
                }
                
                .user-details h5 {
                    margin: 0 0 5px 0;
                    color: #333;
                }
                
                .user-details p {
                    margin: 0;
                    color: #666;
                    font-size: 14px;
                }
                
                .payment-methods {
                    margin-bottom: 20px;
                }
                
                .payment-method {
                    margin-bottom: 15px;
                }
                
                .payment-method input[type="radio"] {
                    margin-right: 10px;
                }
                
                .payment-method label {
                    display: flex;
                    align-items: center;
                    padding: 12px 16px;
                    border: 2px solid #e9ecef;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    font-weight: 500;
                }
                
                .payment-method label:hover {
                    border-color: #007bff;
                    background: #f8f9fa;
                }
                
                .payment-method input[type="radio"]:checked + label {
                    border-color: #007bff;
                    background: #e7f3ff;
                }
                
                .payment-method label i {
                    margin-right: 10px;
                    font-size: 18px;
                    width: 20px;
                }
                
                .payment-form {
                    margin-top: 20px;
                }
                
                .btn-paypal {
                    background: #0070ba;
                    color: white;
                    border: none;
                    padding: 12px 30px;
                    border-radius: 8px;
                    font-size: 16px;
                    cursor: pointer;
                    transition: background-color 0.3s ease;
                }
                
                .btn-paypal:hover {
                    background: #005ea6;
                }
                
                .btn-apple-pay {
                    background: #000;
                    color: white;
                    border: none;
                    padding: 12px 30px;
                    border-radius: 8px;
                    font-size: 16px;
                    cursor: pointer;
                    transition: background-color 0.3s ease;
                }
                
                .btn-apple-pay:hover {
                    background: #333;
                }
                
                .order-summary {
                    background: white;
                    border: 1px solid #e9ecef;
                    border-radius: 12px;
                    padding: 20px;
                    position: sticky;
                    top: 20px;
                }
                
                .order-summary h4 {
                    margin-bottom: 20px;
                    color: #333;
                    border-bottom: 1px solid #e9ecef;
                    padding-bottom: 15px;
                }
                
                .order-summary h4 i {
                    margin-right: 10px;
                    color: #007bff;
                }
                
                .order-items {
                    margin-bottom: 20px;
                }
                
                .order-item {
                    display: flex;
                    align-items: center;
                    gap: 15px;
                    padding: 15px 0;
                    border-bottom: 1px solid #f0f0f0;
                }
                
                .order-item:last-child {
                    border-bottom: none;
                }
                
                .order-item-image {
                    width: 60px;
                    height: 60px;
                    border-radius: 8px;
                    object-fit: cover;
                }
                
                .order-item-details {
                    flex: 1;
                }
                
                .order-item-name {
                    font-weight: 600;
                    color: #333;
                    margin-bottom: 5px;
                    font-size: 14px;
                }
                
                .order-item-category {
                    color: #666;
                    font-size: 12px;
                    margin-bottom: 5px;
                }
                
                .order-item-quantity {
                    color: #666;
                    font-size: 12px;
                }
                
                .order-item-price {
                    font-weight: 600;
                    color: #333;
                    font-size: 14px;
                }
                
                .order-calculations {
                    border-top: 1px solid #e9ecef;
                    padding-top: 15px;
                    margin-bottom: 20px;
                }
                
                .calculation-row {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 8px 0;
                    font-size: 14px;
                }
                
                .calculation-row.total {
                    font-size: 18px;
                    font-weight: 600;
                    color: #333;
                    border-top: 2px solid #e9ecef;
                    margin-top: 10px;
                    padding-top: 15px;
                }
                
                .btn-place-order {
                    width: 100%;
                    padding: 15px;
                    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    margin-bottom: 15px;
                }
                
                .btn-place-order:hover:not(:disabled) {
                    transform: translateY(-2px);
                    box-shadow: 0 8px 25px rgba(40,167,69,0.3);
                }
                
                .btn-place-order:disabled {
                    opacity: 0.6;
                    cursor: not-allowed;
                    transform: none;
                }
                
                .security-note {
                    text-align: center;
                    font-size: 12px;
                    color: #666;
                    margin-bottom: 20px;
                }
                
                .security-note i {
                    color: #28a745;
                    margin-right: 5px;
                }
                
                .return-policy {
                    border-top: 1px solid #e9ecef;
                    padding-top: 15px;
                }
                
                .return-policy h5 {
                    font-size: 14px;
                    color: #333;
                    margin-bottom: 8px;
                }
                
                .return-policy p {
                    font-size: 12px;
                    color: #666;
                    margin: 0;
                    line-height: 1.4;
                }
                
                .empty-cart-state {
                    text-align: center;
                    padding: 80px 20px;
                }
                
                .empty-cart-content i {
                    font-size: 64px;
                    color: #ddd;
                    margin-bottom: 20px;
                }
                
                .empty-cart-content h3 {
                    color: #333;
                    margin-bottom: 15px;
                }
                
                .empty-cart-content p {
                    color: #666;
                    margin-bottom: 30px;
                }
                
                .processing-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(255,255,255,0.95);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 9999;
                    flex-direction: column;
                }
                
                .processing-content {
                    text-align: center;
                }
                
                .processing-content h3 {
                    margin-top: 20px;
                    color: #333;
                }
                
                .processing-content p {
                    color: #666;
                    margin-bottom: 0;
                }
                
                @media (max-width: 768px) {
                    .checkout-container {
                        padding: 30px 0;
                    }
                    
                    .order-summary {
                        position: static;
                        margin-top: 30px;
                    }
                    
                    .section-content {
                        padding: 15px;
                    }
                    
                    .order-item {
                        flex-direction: column;
                        text-align: center;
                        gap: 10px;
                    }
                }
            </style>
        `;

        document.head.insertAdjacentHTML('beforeend', styles);
    }

    setupFormValidation() {
        // Real-time validation for key fields
        const emailInput = document.getElementById('checkoutEmail');
        if (emailInput) {
            emailInput.addEventListener('blur', () => {
                this.validateEmail(emailInput.value);
            });
        }

        const zipCodeInput = document.getElementById('zipCode');
        if (zipCodeInput) {
            zipCodeInput.addEventListener('blur', () => {
                this.validateZipCode(zipCodeInput.value);
            });
        }

        const cardNumberInput = document.getElementById('cardNumber');
        if (cardNumberInput) {
            cardNumberInput.addEventListener('blur', () => {
                this.validateCardNumber(cardNumberInput.value);
            });
        }

        const cvvInput = document.getElementById('cvv');
        if (cvvInput) {
            cvvInput.addEventListener('blur', () => {
                this.validateCVV(cvvInput.value);
            });
        }
    }

    setupEventListeners() {
        // Place order button
        const placeOrderBtn = document.getElementById('placeOrderBtn');
        if (placeOrderBtn) {
            placeOrderBtn.addEventListener('click', async () => {
                await this.handlePlaceOrder();
            });
        }

        // Form input changes
        document.addEventListener('input', (e) => {
            if (e.target.matches('.form-control')) {
                this.clearFieldValidation(e.target);
                this.validateFormCompleteness();
            }
        });

        // Payment method changes
        document.addEventListener('change', (e) => {
            if (e.target.name === 'paymentMethod') {
                this.validateFormCompleteness();
            }
        });
    }

    updateOrderSummary() {
        const orderItemsContainer = document.getElementById('orderItems');
        const subtotalElement = document.getElementById('orderSubtotal');
        const taxElement = document.getElementById('orderTax');
        const shippingElement = document.getElementById('orderShipping');
        const totalElement = document.getElementById('orderTotal');

        if (!this.state.cartSummary) return;

        // Render order items
        if (orderItemsContainer) {
            const itemsHTML = this.state.cartItems.map(item => `
                <div class="order-item">
                    <img src="${item.image_url || 'assets/images/default-game.jpg'}" 
                         alt="${item.game_name}" 
                         class="order-item-image"
                         onerror="this.src='assets/images/default-game.jpg'">
                    <div class="order-item-details">
                        <div class="order-item-name">${item.game_name}</div>
                        <div class="order-item-category">${item.category || 'Game'}</div>
                        <div class="order-item-quantity">Qty: ${item.quantity}</div>
                    </div>
                    <div class="order-item-price">$${(item.price * item.quantity).toFixed(2)}</div>
                </div>
            `).join('');

            orderItemsContainer.innerHTML = itemsHTML;
        }

        // Update calculations
        if (subtotalElement) subtotalElement.textContent = `$${this.state.cartSummary.subtotal.toFixed(2)}`;
        if (taxElement) taxElement.textContent = `$${this.state.cartSummary.tax.toFixed(2)}`;
        if (shippingElement) {
            shippingElement.textContent = this.state.cartSummary.shipping === 0 
                ? 'FREE' 
                : `$${this.state.cartSummary.shipping.toFixed(2)}`;
        }
        if (totalElement) totalElement.textContent = `$${this.state.cartSummary.total.toFixed(2)}`;

        this.state.orderTotal = this.state.cartSummary.total;
    }

    showCheckoutContent() {
        const loadingElement = document.getElementById('checkoutLoading');
        const contentElement = document.getElementById('checkoutContent');
        const emptyCartElement = document.getElementById('emptyCartState');

        if (loadingElement) loadingElement.style.display = 'none';
        if (contentElement) contentElement.style.display = 'block';
        if (emptyCartElement) emptyCartElement.style.display = 'none';
    }

    showEmptyCartState() {
        const loadingElement = document.getElementById('checkoutLoading');
        const contentElement = document.getElementById('checkoutContent');
        const emptyCartElement = document.getElementById('emptyCartState');

        if (loadingElement) loadingElement.style.display = 'none';
        if (contentElement) contentElement.style.display = 'none';
        if (emptyCartElement) emptyCartElement.style.display = 'block';
    }

    validateCheckoutState() {
        this.validateFormCompleteness();
    }

    validateFormCompleteness() {
        const isFormComplete = this.isFormComplete();
        const placeOrderBtn = document.getElementById('placeOrderBtn');
        
        if (placeOrderBtn) {
            placeOrderBtn.disabled = !isFormComplete || this.orderProcessing;
        }
    }

    isFormComplete() {
        // Check email (for guest) or authentication
        if (!this.state.isAuthenticated) {
            const email = this.getValue('checkoutEmail');
            if (!email || !this.validationRules.email.test(email)) {
                return false;
            }
        }

        // Check shipping information
        const requiredShippingFields = ['firstName', 'lastName', 'address', 'city', 'state', 'zipCode', 'country'];
        for (const field of requiredShippingFields) {
            if (!this.getValue(field)) {
                return false;
            }
        }

        // Check payment information based on selected method
        if (this.state.selectedPaymentMethod === 'credit_card') {
            const requiredPaymentFields = ['cardNumber', 'expiryMonth', 'expiryYear', 'cvv', 'cardName'];
            for (const field of requiredPaymentFields) {
                if (!this.getValue(field)) {
                    return false;
                }
            }

            // Additional validation for card details
            const cardNumber = this.getValue('cardNumber');
            const cvv = this.getValue('cvv');
            if (!this.validationRules.cardNumber.test(cardNumber.replace(/\s/g, ''))) {
                return false;
            }
            if (!this.validationRules.cvv.test(cvv)) {
                return false;
            }
        }

        return true;
    }

    async handlePlaceOrder() {
        if (this.orderProcessing) return;

        try {
            this.orderProcessing = true;
            this.showProcessingOverlay();

            // Validate form
            if (!this.validateAllFields()) {
                this.hideProcessingOverlay();
                this.orderProcessing = false;
                return;
            }

            // Collect order data
            const orderData = this.collectOrderData();

            // Process payment
            const paymentResult = await this.processPayment(orderData);

            if (paymentResult.success) {
                // Create order
                const order = await this.createOrder(orderData, paymentResult);

                // Clear cart
                if (window.cartIntegration) {
                    await window.cartIntegration.clearCart();
                }

                // Track successful order
                if (window.analyticsService) {
                    window.analyticsService.trackPurchase(
                        order.id,
                        order.total,
                        order.items,
                        {
                            payment_method: this.state.selectedPaymentMethod,
                            user_type: this.state.isAuthenticated ? 'authenticated' : 'guest'
                        }
                    );
                }

                // Redirect to success page
                this.redirectToOrderSuccess(order.id);

            } else {
                throw new Error(paymentResult.error || 'Payment failed');
            }

        } catch (error) {
            console.error('Order placement failed:', error);
            this.handleOrderError(error);
        } finally {
            this.hideProcessingOverlay();
            this.orderProcessing = false;
        }
    }

    collectOrderData() {
        const data = {
            // Customer information
            customer: {
                email: this.state.isAuthenticated 
                    ? this.state.currentUser.email 
                    : this.getValue('checkoutEmail'),
                first_name: this.getValue('firstName'),
                last_name: this.getValue('lastName')
            },

            // Shipping information
            shipping_address: {
                first_name: this.getValue('firstName'),
                last_name: this.getValue('lastName'),
                street_address: this.getValue('address'),
                address_line2: this.getValue('addressLine2'),
                city: this.getValue('city'),
                state: this.getValue('state'),
                zip_code: this.getValue('zipCode'),
                country: this.getValue('country')
            },

            // Order items
            items: this.state.cartItems.map(item => ({
                game_id: item.game_id,
                quantity: item.quantity,
                price: item.price
            })),

            // Order totals
            subtotal: this.state.cartSummary.subtotal,
            tax: this.state.cartSummary.tax,
            shipping: this.state.cartSummary.shipping,
            total: this.state.cartSummary.total,

            // Payment method
            payment_method: this.state.selectedPaymentMethod,

            // Order notes
            notes: this.getValue('orderNotes')
        };

        return data;
    }

    async processPayment(orderData) {
        try {
            const paymentData = {
                amount: orderData.total,
                currency: 'USD',
                payment_method: this.state.selectedPaymentMethod
            };

            switch (this.state.selectedPaymentMethod) {
                case 'credit_card':
                    paymentData.card = {
                        number: this.getValue('cardNumber').replace(/\s/g, ''),
                        expiry_month: this.getValue('expiryMonth'),
                        expiry_year: this.getValue('expiryYear'),
                        cvv: this.getValue('cvv'),
                        name: this.getValue('cardName')
                    };
                    break;

                case 'paypal':
                    // PayPal integration would go here
                    paymentData.paypal_token = 'mock_paypal_token';
                    break;

                case 'apple_pay':
                    // Apple Pay integration would go here
                    paymentData.apple_pay_token = 'mock_apple_pay_token';
                    break;
            }

            // Process payment through order service
            const response = await window.apiService.post('order', '/payments/process', paymentData);
            return response;

        } catch (error) {
            console.error('Payment processing failed:', error);
            return {
                success: false,
                error: error.message || 'Payment processing failed'
            };
        }
    }

    async createOrder(orderData, paymentResult) {
        const orderPayload = {
            ...orderData,
            payment_id: paymentResult.payment_id,
            payment_status: 'completed'
        };

        const response = await window.apiService.post('order', '/orders', orderPayload);
        return response;
    }

    redirectToOrderSuccess(orderId) {
        window.location.href = `order-success.html?order_id=${orderId}`;
    }

    showProcessingOverlay() {
        const overlay = document.createElement('div');
        overlay.id = 'processingOverlay';
        overlay.className = 'processing-overlay';
        overlay.innerHTML = `
            <div class="processing-content">
                <div class="spinner-border text-primary" style="width: 3rem; height: 3rem;" role="status">
                    <span class="sr-only">Processing...</span>
                </div>
                <h3>Processing Your Order</h3>
                <p>Please do not close this window or navigate away from this page.</p>
            </div>
        `;

        document.body.appendChild(overlay);
    }

    hideProcessingOverlay() {
        const overlay = document.getElementById('processingOverlay');
        if (overlay) {
            overlay.remove();
        }
    }

    handleOrderError(error) {
        let errorMessage = 'There was an error processing your order. Please try again.';

        if (error.message.includes('payment')) {
            errorMessage = 'Payment processing failed. Please check your payment information and try again.';
        } else if (error.message.includes('network')) {
            errorMessage = 'Network error. Please check your connection and try again.';
        } else if (error.message.includes('validation')) {
            errorMessage = 'Please check your information and try again.';
        }

        // Show error alert
        const alertHTML = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                <strong>Order Failed:</strong> ${errorMessage}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        const checkoutContent = document.getElementById('checkoutContent');
        if (checkoutContent) {
            checkoutContent.insertAdjacentHTML('afterbegin', alertHTML);
        }

        // Track error
        if (window.analyticsService) {
            window.analyticsService.trackError(error, {
                context: 'checkout_order_placement',
                order_total: this.state.orderTotal
            });
        }
    }

    // Validation methods
    validateAllFields() {
        let isValid = true;

        // Validate email for guest checkout
        if (!this.state.isAuthenticated) {
            const email = this.getValue('checkoutEmail');
            if (!this.validateEmail(email)) isValid = false;
        }

        // Validate shipping fields
        const shippingFields = [
            { id: 'firstName', name: 'First name', required: true },
            { id: 'lastName', name: 'Last name', required: true },
            { id: 'address', name: 'Address', required: true },
            { id: 'city', name: 'City', required: true },
            { id: 'state', name: 'State', required: true },
            { id: 'zipCode', name: 'ZIP code', required: true },
            { id: 'country', name: 'Country', required: true }
        ];

        shippingFields.forEach(field => {
            const value = this.getValue(field.id);
            if (field.required && !value) {
                this.showFieldError(field.id, `${field.name} is required`);
                isValid = false;
            } else if (field.id === 'zipCode' && value && !this.validationRules.zipCode.test(value)) {
                this.showFieldError(field.id, 'Please enter a valid ZIP code');
                isValid = false;
            }
        });

        // Validate payment fields
        if (this.state.selectedPaymentMethod === 'credit_card') {
            const cardNumber = this.getValue('cardNumber');
            const cvv = this.getValue('cvv');
            const cardName = this.getValue('cardName');
            const expiryMonth = this.getValue('expiryMonth');
            const expiryYear = this.getValue('expiryYear');

            if (!this.validateCardNumber(cardNumber)) isValid = false;
            if (!this.validateCVV(cvv)) isValid = false;
            if (!cardName) {
                this.showFieldError('cardName', 'Name on card is required');
                isValid = false;
            }
            if (!expiryMonth || !expiryYear) {
                if (!expiryMonth) this.showFieldError('expiryMonth', 'Month is required');
                if (!expiryYear) this.showFieldError('expiryYear', 'Year is required');
                isValid = false;
            }
        }

        return isValid;
    }

    validateEmail(email) {
        const input = document.getElementById('checkoutEmail');
        if (!email) {
            this.showFieldError('checkoutEmail', 'Email address is required');
            return false;
        } else if (!this.validationRules.email.test(email)) {
            this.showFieldError('checkoutEmail', 'Please enter a valid email address');
            return false;
        } else {
            this.showFieldSuccess('checkoutEmail');
            return true;
        }
    }

    validateZipCode(zipCode) {
        if (!zipCode) {
            this.showFieldError('zipCode', 'ZIP code is required');
            return false;
        } else if (!this.validationRules.zipCode.test(zipCode)) {
            this.showFieldError('zipCode', 'Please enter a valid ZIP code');
            return false;
        } else {
            this.showFieldSuccess('zipCode');
            return true;
        }
    }

    validateCardNumber(cardNumber) {
        const cleanNumber = cardNumber.replace(/\s/g, '');
        if (!cleanNumber) {
            this.showFieldError('cardNumber', 'Card number is required');
            return false;
        } else if (!this.validationRules.cardNumber.test(cleanNumber)) {
            this.showFieldError('cardNumber', 'Please enter a valid card number');
            return false;
        } else {
            this.showFieldSuccess('cardNumber');
            return true;
        }
    }

    validateCVV(cvv) {
        if (!cvv) {
            this.showFieldError('cvv', 'CVV is required');
            return false;
        } else if (!this.validationRules.cvv.test(cvv)) {
            this.showFieldError('cvv', 'Please enter a valid CVV');
            return false;
        } else {
            this.showFieldSuccess('cvv');
            return true;
        }
    }

    // UI Helper methods
    getValue(fieldId) {
        const field = document.getElementById(fieldId);
        return field ? field.value.trim() : '';
    }

    setValue(fieldId, value) {
        const field = document.getElementById(fieldId);
        if (field && value) {
            field.value = value;
        }
    }

    showFieldError(fieldId, message) {
        const field = document.getElementById(fieldId);
        if (!field) return;

        field.classList.remove('is-valid');
        field.classList.add('is-invalid');

        const feedback = field.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.textContent = message;
        }
    }

    showFieldSuccess(fieldId) {
        const field = document.getElementById(fieldId);
        if (!field) return;

        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
    }

    clearFieldValidation(field) {
        field.classList.remove('is-valid', 'is-invalid');
    }

    handleInitializationError(error) {
        console.error('Checkout enhancement initialization failed:', error);
        this.showEmptyCartState();
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    log(...args) {
        if (this.config.enableDebugLogging) {
            console.log('[CheckoutEnhancer]', ...args);
        }
    }
}

// Initialize checkout enhancement when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.checkoutEnhancer = new CheckoutEnhancer();
});

// Log initialization
console.log('LugX Checkout Enhancement loaded');

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CheckoutEnhancer };
}