/**
 * LugX Gaming Authentication Service
 * Handles JWT tokens, user sessions, and authentication flows
 * Integrates with Order Service authentication endpoints
 */

class AuthService {
    constructor() {
        this.config = {
            tokenKey: 'lugx_auth_token',
            refreshKey: 'lugx_refresh_token',
            userKey: 'lugx_user_data',
            sessionKey: 'lugx_session_id',
            tokenRefreshThreshold: 5 * 60 * 1000, // 5 minutes before expiry
            maxLoginAttempts: 5,
            lockoutDuration: 15 * 60 * 1000 // 15 minutes
        };

        this.authState = {
            isAuthenticated: false,
            user: null,
            token: null,
            refreshToken: null,
            lastActivity: Date.now()
        };

        this.refreshPromise = null;
        this.eventListeners = new Map();

        this.initializeAuth();
        this.setupActivityTracking();
        this.setupAutomaticRefresh();
    }

    // Initialize authentication state from storage
    async initializeAuth() {
        try {
            // Load tokens from storage
            const token = this.getStoredToken();
            const refreshToken = this.getStoredRefreshToken();
            const user = this.getStoredUser();

            if (token && user) {
                // Validate token expiry
                if (this.isTokenValid(token)) {
                    this.authState = {
                        isAuthenticated: true,
                        user: user,
                        token: token,
                        refreshToken: refreshToken,
                        lastActivity: Date.now()
                    };

                    this.emitEvent('authStateChanged', { 
                        isAuthenticated: true, 
                        user: user 
                    });

                    // Schedule token refresh if needed
                    this.scheduleTokenRefresh(token);
                } else {
                    // Token expired, try to refresh
                    if (refreshToken) {
                        await this.refreshAuthToken();
                    } else {
                        this.clearAuthData();
                    }
                }
            }
        } catch (error) {
            console.warn('Auth initialization failed:', error);
            this.clearAuthData();
        }
    }

    // Token management
    setTokens(accessToken, refreshToken = null, user = null) {
        try {
            // Validate token format
            if (!this.isValidJWTFormat(accessToken)) {
                throw new Error('Invalid access token format');
            }

            // Store tokens
            localStorage.setItem(this.config.tokenKey, accessToken);
            if (refreshToken) {
                localStorage.setItem(this.config.refreshKey, refreshToken);
            }
            if (user) {
                localStorage.setItem(this.config.userKey, JSON.stringify(user));
            }

            // Update auth state
            this.authState = {
                isAuthenticated: true,
                user: user || this.authState.user,
                token: accessToken,
                refreshToken: refreshToken || this.authState.refreshToken,
                lastActivity: Date.now()
            };

            // Schedule automatic refresh
            this.scheduleTokenRefresh(accessToken);

            // Emit auth state change
            this.emitEvent('authStateChanged', { 
                isAuthenticated: true, 
                user: this.authState.user 
            });

            return true;
        } catch (error) {
            console.error('Failed to set tokens:', error);
            return false;
        }
    }

    getToken() {
        // Check if token is still valid
        if (this.authState.token && this.isTokenValid(this.authState.token)) {
            this.authState.lastActivity = Date.now();
            return this.authState.token;
        }
        return null;
    }

    getRefreshToken() {
        return this.authState.refreshToken || this.getStoredRefreshToken();
    }

    getUser() {
        return this.authState.user;
    }

    isAuthenticated() {
        return this.authState.isAuthenticated && this.getToken() !== null;
    }

    // Token validation
    isValidJWTFormat(token) {
        if (typeof token !== 'string') return false;
        
        const parts = token.split('.');
        if (parts.length !== 3) return false;

        try {
            // Validate base64 encoding of header and payload
            JSON.parse(atob(parts[0]));
            JSON.parse(atob(parts[1]));
            return true;
        } catch {
            return false;
        }
    }

    isTokenValid(token) {
        try {
            const payload = this.decodeTokenPayload(token);
            const currentTime = Math.floor(Date.now() / 1000);
            
            // Check if token has expiration and if it's still valid
            if (payload.exp && payload.exp <= currentTime) {
                return false;
            }

            return true;
        } catch (error) {
            console.warn('Token validation failed:', error);
            return false;
        }
    }

    decodeTokenPayload(token) {
        const payload = token.split('.')[1];
        return JSON.parse(atob(payload));
    }

    getTokenExpiryTime(token) {
        try {
            const payload = this.decodeTokenPayload(token);
            return payload.exp ? payload.exp * 1000 : null; // Convert to milliseconds
        } catch {
            return null;
        }
    }

    // Authentication methods
    async login(email, password) {
        try {
            // Check for rate limiting
            if (this.isLoginRateLimited()) {
                throw new Error('Too many login attempts. Please try again later.');
            }

            const response = await window.apiService.post('order', '/auth/login', {
                email: email.trim(),
                password: password
            });

            // Handle successful login
            this.setTokens(response.access_token, response.refresh_token, response.user);
            this.clearLoginAttempts();

            // Track login event
            this.trackAuthEvent('login_success', { user_id: response.user.id });

            return {
                success: true,
                user: response.user,
                message: 'Login successful'
            };

        } catch (error) {
            this.recordLoginAttempt();
            this.trackAuthEvent('login_failed', { error: error.message });

            return {
                success: false,
                error: this.getAuthErrorMessage(error),
                canRetry: !this.isLoginRateLimited()
            };
        }
    }

    async register(userData) {
        try {
            // Validate required fields
            const requiredFields = ['email', 'password', 'first_name', 'last_name'];
            for (const field of requiredFields) {
                if (!userData[field] || userData[field].trim() === '') {
                    throw new Error(`${field.replace('_', ' ')} is required`);
                }
            }

            // Additional validation
            if (!this.isValidEmail(userData.email)) {
                throw new Error('Please enter a valid email address');
            }

            if (!this.isValidPassword(userData.password)) {
                throw new Error('Password must be at least 8 characters long');
            }

            const response = await window.apiService.post('order', '/auth/register', {
                email: userData.email.trim(),
                password: userData.password,
                first_name: userData.first_name.trim(),
                last_name: userData.last_name.trim(),
                phone: userData.phone ? userData.phone.trim() : null
            });

            // Handle successful registration
            this.setTokens(response.access_token, response.refresh_token, response.user);

            // Track registration event
            this.trackAuthEvent('registration_success', { user_id: response.user.id });

            return {
                success: true,
                user: response.user,
                message: 'Registration successful'
            };

        } catch (error) {
            this.trackAuthEvent('registration_failed', { error: error.message });

            return {
                success: false,
                error: this.getAuthErrorMessage(error)
            };
        }
    }

    async logout() {
        try {
            // Attempt to invalidate token on server
            const token = this.getToken();
            if (token) {
                try {
                    await window.apiService.post('order', '/auth/logout');
                } catch (error) {
                    console.warn('Server logout failed, proceeding with local logout:', error);
                }
            }

            // Track logout event
            this.trackAuthEvent('logout', { user_id: this.authState.user?.id });

            // Clear all auth data
            this.clearAuthData();

            // Emit logout event
            this.emitEvent('userLoggedOut');

            return { success: true, message: 'Logged out successfully' };

        } catch (error) {
            console.error('Logout failed:', error);
            // Still clear local data even if server logout fails
            this.clearAuthData();
            this.emitEvent('userLoggedOut');

            return { success: false, error: 'Logout partially failed' };
        }
    }

    async refreshAuthToken() {
        // Prevent multiple simultaneous refresh attempts
        if (this.refreshPromise) {
            return this.refreshPromise;
        }

        this.refreshPromise = this.performTokenRefresh();
        
        try {
            const result = await this.refreshPromise;
            return result;
        } finally {
            this.refreshPromise = null;
        }
    }

    async performTokenRefresh() {
        try {
            const refreshToken = this.getRefreshToken();
            if (!refreshToken) {
                throw new Error('No refresh token available');
            }

            const response = await window.apiService.post('order', '/auth/refresh', {
                refresh_token: refreshToken
            });

            // Update tokens
            this.setTokens(response.access_token, response.refresh_token);

            this.trackAuthEvent('token_refreshed');

            return {
                success: true,
                token: response.access_token
            };

        } catch (error) {
            console.warn('Token refresh failed:', error);
            
            // Clear auth data if refresh fails
            this.clearAuthData();
            this.emitEvent('authExpired');
            
            this.trackAuthEvent('token_refresh_failed', { error: error.message });

            return {
                success: false,
                error: 'Session expired. Please login again.'
            };
        }
    }

    // Password reset functionality
    async requestPasswordReset(email) {
        try {
            await window.apiService.post('order', '/auth/forgot-password', {
                email: email.trim()
            });

            this.trackAuthEvent('password_reset_requested');

            return {
                success: true,
                message: 'Password reset instructions sent to your email'
            };

        } catch (error) {
            this.trackAuthEvent('password_reset_failed', { error: error.message });

            return {
                success: false,
                error: this.getAuthErrorMessage(error)
            };
        }
    }

    async resetPassword(token, newPassword) {
        try {
            if (!this.isValidPassword(newPassword)) {
                throw new Error('Password must be at least 8 characters long');
            }

            await window.apiService.post('order', '/auth/reset-password', {
                token: token,
                new_password: newPassword
            });

            this.trackAuthEvent('password_reset_completed');

            return {
                success: true,
                message: 'Password reset successful. You can now login with your new password.'
            };

        } catch (error) {
            this.trackAuthEvent('password_reset_completion_failed', { error: error.message });

            return {
                success: false,
                error: this.getAuthErrorMessage(error)
            };
        }
    }

    // User profile management
    async updateProfile(profileData) {
        try {
            if (!this.isAuthenticated()) {
                throw new Error('Authentication required');
            }

            const response = await window.apiService.put('order', '/auth/me', profileData);

            // Update stored user data
            this.authState.user = { ...this.authState.user, ...response.user };
            localStorage.setItem(this.config.userKey, JSON.stringify(this.authState.user));

            this.emitEvent('userProfileUpdated', { user: this.authState.user });
            this.trackAuthEvent('profile_updated');

            return {
                success: true,
                user: this.authState.user,
                message: 'Profile updated successfully'
            };

        } catch (error) {
            this.trackAuthEvent('profile_update_failed', { error: error.message });

            return {
                success: false,
                error: this.getAuthErrorMessage(error)
            };
        }
    }

    // Route protection
    requireAuth(redirectUrl = null) {
        if (!this.isAuthenticated()) {
            const currentUrl = redirectUrl || window.location.href;
            const loginUrl = `login.html?redirect=${encodeURIComponent(currentUrl)}`;
            window.location.href = loginUrl;
            return false;
        }
        return true;
    }

    // Activity tracking and automatic refresh
    setupActivityTracking() {
        // Track user activity for session management
        const activityEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
        
        const updateActivity = () => {
            if (this.isAuthenticated()) {
                this.authState.lastActivity = Date.now();
            }
        };

        activityEvents.forEach(event => {
            document.addEventListener(event, updateActivity, { passive: true });
        });
    }

    setupAutomaticRefresh() {
        // Check for token refresh every minute
        setInterval(() => {
            if (this.isAuthenticated() && this.shouldRefreshToken()) {
                this.refreshAuthToken();
            }
        }, 60 * 1000); // 1 minute
    }

    shouldRefreshToken() {
        const token = this.authState.token;
        if (!token) return false;

        const expiryTime = this.getTokenExpiryTime(token);
        if (!expiryTime) return false;

        const timeUntilExpiry = expiryTime - Date.now();
        return timeUntilExpiry <= this.config.tokenRefreshThreshold;
    }

    scheduleTokenRefresh(token) {
        const expiryTime = this.getTokenExpiryTime(token);
        if (!expiryTime) return;

        const refreshTime = expiryTime - this.config.tokenRefreshThreshold;
        const delay = refreshTime - Date.now();

        if (delay > 0) {
            setTimeout(() => {
                if (this.isAuthenticated()) {
                    this.refreshAuthToken();
                }
            }, delay);
        }
    }

    // Rate limiting for login attempts
    isLoginRateLimited() {
        const attempts = this.getLoginAttempts();
        return attempts.count >= this.config.maxLoginAttempts && 
               (Date.now() - attempts.lastAttempt) < this.config.lockoutDuration;
    }

    recordLoginAttempt() {
        const attempts = this.getLoginAttempts();
        attempts.count++;
        attempts.lastAttempt = Date.now();
        localStorage.setItem('lugx_login_attempts', JSON.stringify(attempts));
    }

    clearLoginAttempts() {
        localStorage.removeItem('lugx_login_attempts');
    }

    getLoginAttempts() {
        try {
            const stored = localStorage.getItem('lugx_login_attempts');
            return stored ? JSON.parse(stored) : { count: 0, lastAttempt: 0 };
        } catch {
            return { count: 0, lastAttempt: 0 };
        }
    }

    // Storage helpers
    getStoredToken() {
        return localStorage.getItem(this.config.tokenKey);
    }

    getStoredRefreshToken() {
        return localStorage.getItem(this.config.refreshKey);
    }

    getStoredUser() {
        try {
            const userData = localStorage.getItem(this.config.userKey);
            return userData ? JSON.parse(userData) : null;
        } catch {
            return null;
        }
    }

    clearAuthData() {
        // Clear all authentication data
        localStorage.removeItem(this.config.tokenKey);
        localStorage.removeItem(this.config.refreshKey);
        localStorage.removeItem(this.config.userKey);

        // Reset auth state
        this.authState = {
            isAuthenticated: false,
            user: null,
            token: null,
            refreshToken: null,
            lastActivity: Date.now()
        };

        // Emit state change
        this.emitEvent('authStateChanged', { 
            isAuthenticated: false, 
            user: null 
        });
    }

    // Validation helpers
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    isValidPassword(password) {
        return typeof password === 'string' && password.length >= 8;
    }

    // Error handling
    getAuthErrorMessage(error) {
        if (error instanceof window.APIError) {
            switch (error.status) {
                case 401:
                    return 'Invalid email or password';
                case 409:
                    return 'An account with this email already exists';
                case 422:
                    return 'Please check your input and try again';
                case 429:
                    return 'Too many attempts. Please try again later';
                case 500:
                    return 'Server error. Please try again later';
                default:
                    return error.message || 'Authentication failed';
            }
        }
        return error.message || 'An unexpected error occurred';
    }

    // Event system
    addEventListener(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    removeEventListener(event, callback) {
        if (this.eventListeners.has(event)) {
            const listeners = this.eventListeners.get(event);
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    emitEvent(event, data = null) {
        if (this.eventListeners.has(event)) {
            this.eventListeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in auth event listener for ${event}:`, error);
                }
            });
        }
    }

    // Analytics tracking
    trackAuthEvent(event, data = {}) {
        if (window.analyticsService) {
            window.analyticsService.track(`auth_${event}`, {
                ...data,
                timestamp: new Date().toISOString(),
                user_agent: navigator.userAgent
            });
        }
    }

    // Session ID management
    getSessionId() {
        let sessionId = sessionStorage.getItem(this.config.sessionKey);
        if (!sessionId) {
            sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            sessionStorage.setItem(this.config.sessionKey, sessionId);
        }
        return sessionId;
    }

    // Debugging helpers
    getAuthState() {
        return {
            ...this.authState,
            tokenExpiry: this.authState.token ? this.getTokenExpiryTime(this.authState.token) : null,
            isRateLimited: this.isLoginRateLimited(),
            sessionId: this.getSessionId()
        };
    }
}

// Global auth service instance
window.authService = new AuthService();

// Set up global auth event handlers
window.authService.addEventListener('authStateChanged', (data) => {
    // Update UI elements based on auth state
    document.dispatchEvent(new CustomEvent('authStateChanged', { detail: data }));
});

window.authService.addEventListener('userLoggedOut', () => {
    // Handle logout cleanup
    document.dispatchEvent(new CustomEvent('userLoggedOut'));
    
    // Redirect to homepage if on protected page
    const protectedPages = ['cart.html', 'profile.html', 'orders.html'];
    const currentPage = window.location.pathname.split('/').pop();
    
    if (protectedPages.includes(currentPage)) {
        window.location.href = 'index.html';
    }
});

window.authService.addEventListener('authExpired', () => {
    // Handle session expiry
    document.dispatchEvent(new CustomEvent('authExpired'));
    
    // Show notification to user
    if (window.notificationService) {
        window.notificationService.show('Your session has expired. Please login again.', 'warning');
    }
});

// Log initialization
console.log('LugX Auth Service initialized:', {
    isAuthenticated: window.authService.isAuthenticated(),
    user: window.authService.getUser()?.email || 'anonymous',
    sessionId: window.authService.getSessionId()
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AuthService };
}