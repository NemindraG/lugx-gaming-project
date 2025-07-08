-- Order Service Schema Migration
-- Version: 001
-- Description: Initial schema for Order Service with users, carts, orders, and payments

-- Set search path
SET search_path TO order_service, public;

-- Users table (authentication and profile)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) UNIQUE,
    
    -- Authentication
    password_hash VARCHAR(255) NOT NULL,
    email_verified BOOLEAN DEFAULT false,
    email_verified_at TIMESTAMP WITH TIME ZONE,
    
    -- Profile
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    date_of_birth DATE,
    
    -- Preferences
    newsletter_subscribed BOOLEAN DEFAULT false,
    marketing_consent BOOLEAN DEFAULT false,
    preferred_language VARCHAR(10) DEFAULT 'en',
    preferred_currency VARCHAR(3) DEFAULT 'USD',
    
    -- Status
    role user_role DEFAULT 'customer',
    is_active BOOLEAN DEFAULT true,
    last_login_at TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for user queries
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username) WHERE username IS NOT NULL;
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = true;

-- User addresses table
CREATE TABLE IF NOT EXISTS user_addresses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Address details
    address_type VARCHAR(20) DEFAULT 'shipping' CHECK (address_type IN ('shipping', 'billing')),
    is_default BOOLEAN DEFAULT false,
    
    -- Address fields
    full_name VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    state_province VARCHAR(100),
    postal_code VARCHAR(20),
    country_code VARCHAR(2) NOT NULL,
    phone VARCHAR(20),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Ensure only one default address per type per user
CREATE UNIQUE INDEX idx_user_default_address ON user_addresses(user_id, address_type) 
    WHERE is_default = true;

-- Shopping cart table (session-based)
CREATE TABLE IF NOT EXISTS shopping_carts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    
    -- Cart metadata
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'abandoned', 'converted', 'expired')),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '7 days'),
    
    -- Tracking
    converted_to_order_id UUID,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Either user_id or session_id must be present
    CONSTRAINT cart_owner_check CHECK (user_id IS NOT NULL OR session_id IS NOT NULL)
);

-- Create indexes for cart queries
CREATE INDEX idx_carts_user ON shopping_carts(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_carts_session ON shopping_carts(session_id);
CREATE INDEX idx_carts_status ON shopping_carts(status);
CREATE INDEX idx_carts_expires ON shopping_carts(expires_at) WHERE status = 'active';

-- Cart items table
CREATE TABLE IF NOT EXISTS cart_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cart_id UUID NOT NULL REFERENCES shopping_carts(id) ON DELETE CASCADE,
    game_id UUID NOT NULL, -- References Game Service
    
    -- Item details
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    price_at_time DECIMAL(10, 2) NOT NULL CHECK (price_at_time >= 0),
    discount_percentage INTEGER DEFAULT 0 CHECK (discount_percentage >= 0 AND discount_percentage <= 100),
    
    -- Metadata
    added_from_page VARCHAR(255),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(cart_id, game_id)
);

-- Create index for cart item queries
CREATE INDEX idx_cart_items_cart ON cart_items(cart_id);

-- Orders table (completed purchases)
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_number VARCHAR(20) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    
    -- Order details
    status order_status DEFAULT 'pending',
    
    -- Pricing
    subtotal DECIMAL(10, 2) NOT NULL CHECK (subtotal >= 0),
    tax_amount DECIMAL(10, 2) DEFAULT 0 CHECK (tax_amount >= 0),
    shipping_amount DECIMAL(10, 2) DEFAULT 0 CHECK (shipping_amount >= 0),
    discount_amount DECIMAL(10, 2) DEFAULT 0 CHECK (discount_amount >= 0),
    total_amount DECIMAL(10, 2) NOT NULL CHECK (total_amount >= 0),
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Addresses (denormalized for history)
    billing_address JSONB NOT NULL,
    shipping_address JSONB,
    
    -- Metadata
    customer_notes TEXT,
    internal_notes TEXT,
    ip_address INET,
    user_agent TEXT,
    
    -- Status timestamps
    paid_at TIMESTAMP WITH TIME ZONE,
    shipped_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    refunded_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for order queries
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created ON orders(created_at DESC);
CREATE INDEX idx_orders_number ON orders(order_number);

-- Order items table
CREATE TABLE IF NOT EXISTS order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    game_id UUID NOT NULL, -- References Game Service
    
    -- Item details (denormalized for history)
    game_title VARCHAR(255) NOT NULL,
    game_slug VARCHAR(255) NOT NULL,
    game_cover_url VARCHAR(500),
    
    -- Pricing
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    unit_price DECIMAL(10, 2) NOT NULL CHECK (unit_price >= 0),
    discount_percentage INTEGER DEFAULT 0 CHECK (discount_percentage >= 0 AND discount_percentage <= 100),
    total_price DECIMAL(10, 2) NOT NULL CHECK (total_price >= 0),
    
    -- Digital delivery
    download_url VARCHAR(500),
    download_expires_at TIMESTAMP WITH TIME ZONE,
    download_count INTEGER DEFAULT 0,
    license_key VARCHAR(255),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for order item queries
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_game ON order_items(game_id);

-- Payments table
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    
    -- Payment details
    payment_method payment_method NOT NULL,
    status payment_status DEFAULT 'pending',
    amount DECIMAL(10, 2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Gateway information
    gateway_name VARCHAR(50), -- stripe, paypal, etc.
    gateway_transaction_id VARCHAR(255),
    gateway_response JSONB,
    
    -- Card details (masked)
    card_last_four VARCHAR(4),
    card_brand VARCHAR(20),
    card_exp_month INTEGER CHECK (card_exp_month >= 1 AND card_exp_month <= 12),
    card_exp_year INTEGER CHECK (card_exp_year >= 2024),
    
    -- Status tracking
    authorized_at TIMESTAMP WITH TIME ZONE,
    captured_at TIMESTAMP WITH TIME ZONE,
    failed_at TIMESTAMP WITH TIME ZONE,
    refunded_at TIMESTAMP WITH TIME ZONE,
    refund_amount DECIMAL(10, 2) DEFAULT 0 CHECK (refund_amount >= 0),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for payment queries
CREATE INDEX idx_payments_order ON payments(order_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_gateway_transaction ON payments(gateway_transaction_id) WHERE gateway_transaction_id IS NOT NULL;

-- Password reset tokens
CREATE TABLE IF NOT EXISTS password_resets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for token lookup
CREATE INDEX idx_password_resets_token ON password_resets(token_hash);
CREATE INDEX idx_password_resets_expires ON password_resets(expires_at) WHERE used_at IS NULL;

-- Session management
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token_hash VARCHAR(255) NOT NULL UNIQUE,
    
    -- Session metadata
    ip_address INET,
    user_agent TEXT,
    
    -- Expiration
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for session queries
CREATE INDEX idx_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_sessions_token ON user_sessions(session_token_hash);
CREATE INDEX idx_sessions_expires ON user_sessions(expires_at) WHERE revoked_at IS NULL;

-- Function to generate order numbers
CREATE SEQUENCE IF NOT EXISTS order_number_seq;

CREATE OR REPLACE FUNCTION generate_order_number() RETURNS VARCHAR AS $$
DECLARE
    new_number VARCHAR;
BEGIN
    new_number := 'ORD-' || TO_CHAR(CURRENT_DATE, 'YYYYMMDD') || '-' || 
                  LPAD(nextval('order_number_seq')::text, 6, '0');
    RETURN new_number;
END;
$$ LANGUAGE plpgsql;

-- Trigger to set order number
CREATE OR REPLACE FUNCTION set_order_number() RETURNS trigger AS $$
BEGIN
    IF NEW.order_number IS NULL THEN
        NEW.order_number := generate_order_number();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_order_number_trigger
    BEFORE INSERT ON orders
    FOR EACH ROW
    EXECUTE FUNCTION set_order_number();

-- Apply updated_at trigger to all tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_addresses_updated_at BEFORE UPDATE ON user_addresses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_shopping_carts_updated_at BEFORE UPDATE ON shopping_carts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cart_items_updated_at BEFORE UPDATE ON cart_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_payments_updated_at BEFORE UPDATE ON payments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE users IS 'User accounts with authentication and profile information';
COMMENT ON TABLE user_addresses IS 'User shipping and billing addresses';
COMMENT ON TABLE shopping_carts IS 'Shopping cart sessions for users and guests';
COMMENT ON TABLE cart_items IS 'Items in shopping carts';
COMMENT ON TABLE orders IS 'Completed purchase orders';
COMMENT ON TABLE order_items IS 'Line items within orders';
COMMENT ON TABLE payments IS 'Payment transactions for orders';
COMMENT ON TABLE password_resets IS 'Password reset tokens';
COMMENT ON TABLE user_sessions IS 'Active user sessions for authentication';

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA order_service TO order_service;
GRANT ALL ON ALL SEQUENCES IN SCHEMA order_service TO order_service;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA order_service TO order_service;