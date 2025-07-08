-- Order Service Seed Data
-- Test users and sample orders for development

SET search_path TO order_service, public;

-- Insert test users (passwords are hashed versions of 'password123')
INSERT INTO users (
    id, email, username, password_hash, email_verified, 
    first_name, last_name, role, is_active
) VALUES
('850e8400-e29b-41d4-a716-446655440001', 
 'john.doe@example.com', 
 'johndoe',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGH1lrFBXIa',
 true,
 'John',
 'Doe',
 'customer',
 true),
 
('850e8400-e29b-41d4-a716-446655440002',
 'jane.smith@example.com',
 'janesmith', 
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGH1lrFBXIa',
 true,
 'Jane',
 'Smith',
 'customer',
 true),

('850e8400-e29b-41d4-a716-446655440003',
 'admin@lugxgaming.com',
 'admin',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGH1lrFBXIa',
 true,
 'Admin',
 'User',
 'admin',
 true),

('850e8400-e29b-41d4-a716-446655440004',
 'test.user@example.com',
 'testuser',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGH1lrFBXIa',
 false,
 'Test',
 'User',
 'customer',
 true);

-- Insert user addresses
INSERT INTO user_addresses (
    user_id, address_type, is_default, full_name,
    address_line1, city, state_province, postal_code, country_code
) VALUES
-- John Doe's addresses
('850e8400-e29b-41d4-a716-446655440001', 'shipping', true, 'John Doe',
 '123 Main Street', 'New York', 'NY', '10001', 'US'),
('850e8400-e29b-41d4-a716-446655440001', 'billing', true, 'John Doe',
 '123 Main Street', 'New York', 'NY', '10001', 'US'),
 
-- Jane Smith's addresses
('850e8400-e29b-41d4-a716-446655440002', 'shipping', true, 'Jane Smith',
 '456 Oak Avenue', 'Los Angeles', 'CA', '90001', 'US'),
('850e8400-e29b-41d4-a716-446655440002', 'billing', true, 'Jane Smith',
 '789 Pine Road', 'Los Angeles', 'CA', '90002', 'US');

-- Insert active shopping carts
INSERT INTO shopping_carts (
    id, user_id, session_id, status
) VALUES
('950e8400-e29b-41d4-a716-446655440001',
 '850e8400-e29b-41d4-a716-446655440001',
 'session_john_active',
 'active'),
 
('950e8400-e29b-41d4-a716-446655440002',
 '850e8400-e29b-41d4-a716-446655440002',
 'session_jane_active',
 'active'),

-- Guest cart
('950e8400-e29b-41d4-a716-446655440003',
 NULL,
 'session_guest_12345',
 'active');

-- Insert cart items
INSERT INTO cart_items (
    cart_id, game_id, quantity, price_at_time, discount_percentage
) VALUES
-- John's cart
('950e8400-e29b-41d4-a716-446655440001', '750e8400-e29b-41d4-a716-446655440001', 1, 59.99, 10),
('950e8400-e29b-41d4-a716-446655440001', '750e8400-e29b-41d4-a716-446655440003', 1, 69.99, 15),

-- Jane's cart
('950e8400-e29b-41d4-a716-446655440002', '750e8400-e29b-41d4-a716-446655440002', 1, 49.99, 0),

-- Guest cart
('950e8400-e29b-41d4-a716-446655440003', '750e8400-e29b-41d4-a716-446655440004', 2, 29.99, 25);

-- Insert completed orders
INSERT INTO orders (
    id, user_id, status,
    subtotal, tax_amount, shipping_amount, discount_amount, total_amount,
    billing_address, shipping_address,
    paid_at
) VALUES
('a50e8400-e29b-41d4-a716-446655440001',
 '850e8400-e29b-41d4-a716-446655440001',
 'delivered',
 119.98, 9.60, 0.00, 11.00, 118.58,
 '{"full_name": "John Doe", "address_line1": "123 Main Street", "city": "New York", "state_province": "NY", "postal_code": "10001", "country_code": "US"}',
 '{"full_name": "John Doe", "address_line1": "123 Main Street", "city": "New York", "state_province": "NY", "postal_code": "10001", "country_code": "US"}',
 CURRENT_TIMESTAMP - INTERVAL '5 days'),

('a50e8400-e29b-41d4-a716-446655440002',
 '850e8400-e29b-41d4-a716-446655440002',
 'processing',
 49.99, 4.00, 0.00, 0.00, 53.99,
 '{"full_name": "Jane Smith", "address_line1": "789 Pine Road", "city": "Los Angeles", "state_province": "CA", "postal_code": "90002", "country_code": "US"}',
 '{"full_name": "Jane Smith", "address_line1": "456 Oak Avenue", "city": "Los Angeles", "state_province": "CA", "postal_code": "90001", "country_code": "US"}',
 CURRENT_TIMESTAMP - INTERVAL '1 day');

-- Insert order items
INSERT INTO order_items (
    order_id, game_id, game_title, game_slug,
    quantity, unit_price, discount_percentage, total_price
) VALUES
-- John's order items
('a50e8400-e29b-41d4-a716-446655440001', '750e8400-e29b-41d4-a716-446655440001',
 'Cyborg Warrior: Revolution', 'cyborg-warrior-revolution',
 1, 59.99, 10, 53.99),
('a50e8400-e29b-41d4-a716-446655440001', '750e8400-e29b-41d4-a716-446655440003',
 'World Racing Championship 2024', 'world-racing-championship-2024',
 1, 69.99, 15, 59.49),

-- Jane's order items
('a50e8400-e29b-41d4-a716-446655440002', '750e8400-e29b-41d4-a716-446655440002',
 'Island Survival: Lost Paradise', 'island-survival-lost-paradise',
 1, 49.99, 0, 49.99);

-- Insert payments
INSERT INTO payments (
    order_id, payment_method, status, amount,
    gateway_name, gateway_transaction_id,
    card_last_four, card_brand,
    authorized_at, captured_at
) VALUES
('a50e8400-e29b-41d4-a716-446655440001',
 'credit_card', 'captured', 118.58,
 'stripe', 'pi_1234567890abcdef',
 '4242', 'visa',
 CURRENT_TIMESTAMP - INTERVAL '5 days',
 CURRENT_TIMESTAMP - INTERVAL '5 days'),

('a50e8400-e29b-41d4-a716-446655440002',
 'paypal', 'captured', 53.99,
 'paypal', 'PAY-1234567890ABCDEF',
 NULL, NULL,
 CURRENT_TIMESTAMP - INTERVAL '1 day',
 CURRENT_TIMESTAMP - INTERVAL '1 day');

-- Update order numbers using the trigger
UPDATE orders SET order_number = NULL WHERE order_number IS NULL;