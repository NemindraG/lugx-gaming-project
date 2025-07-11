"""Create Order Service schema

Revision ID: 001
Revises: 
Create Date: 2024-12-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Order Service database schema."""
    
    # Create schema if it doesn't exist
    op.execute('CREATE SCHEMA IF NOT EXISTS order_service')
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('username', sa.String(50), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, default=False),
        sa.Column('first_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('date_of_birth', sa.DateTime(timezone=True), nullable=True),
        sa.Column('preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default={}),
        sa.Column('notification_settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, default=0),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_reset_token', sa.String(255), nullable=True),
        sa.Column('password_reset_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('email_verification_token', sa.String(255), nullable=True),
        sa.Column('email_verification_expires', sa.DateTime(timezone=True), nullable=True),
        schema='order_service'
    )
    
    # Create indexes for users table
    op.create_index('idx_users_email', 'users', ['email'], unique=True, schema='order_service')
    op.create_index('idx_users_username', 'users', ['username'], unique=True, schema='order_service')
    op.create_index('idx_users_created_at', 'users', ['created_at'], schema='order_service')
    op.create_index('idx_users_last_login', 'users', ['last_login_at'], schema='order_service')
    
    # Create user_addresses table
    op.create_table(
        'user_addresses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('address_type', sa.String(20), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('company', sa.String(100), nullable=True),
        sa.Column('address_line_1', sa.String(255), nullable=False),
        sa.Column('address_line_2', sa.String(255), nullable=True),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('state_province', sa.String(100), nullable=False),
        sa.Column('postal_code', sa.String(20), nullable=False),
        sa.Column('country', sa.String(100), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('is_default_shipping', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_default_billing', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['order_service.users.id'], ondelete='CASCADE'),
        schema='order_service'
    )
    
    # Create indexes for user_addresses table
    op.create_index('idx_user_addresses_user_id', 'user_addresses', ['user_id'], schema='order_service')
    op.create_index('idx_user_addresses_is_default', 'user_addresses', ['is_default_shipping', 'is_default_billing'], schema='order_service')
    
    # Create cart_items table
    op.create_table(
        'cart_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('game_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False, default=1),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('discount_percentage', sa.Integer(), nullable=False, default=0),
        sa.Column('game_title', sa.String(255), nullable=False),
        sa.Column('game_slug', sa.String(255), nullable=False),
        sa.Column('game_image_url', sa.String(500), nullable=True),
        sa.Column('inventory_type', sa.String(20), nullable=False, default='digital'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['order_service.users.id'], ondelete='CASCADE'),
        schema='order_service'
    )
    
    # Create indexes for cart_items table
    op.create_index('idx_cart_items_user_id', 'cart_items', ['user_id'], schema='order_service')
    op.create_index('idx_cart_items_game_id', 'cart_items', ['game_id'], schema='order_service')
    op.create_index('idx_cart_items_session_id', 'cart_items', ['session_id'], schema='order_service')
    op.create_index('idx_cart_items_expires_at', 'cart_items', ['expires_at'], schema='order_service')
    op.create_index('idx_cart_items_user_game', 'cart_items', ['user_id', 'game_id'], unique=True, schema='order_service')
    
    # Create cart_sessions table
    op.create_table(
        'cart_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', sa.String(255), nullable=False, unique=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('total_items', sa.Integer(), nullable=False, default=0),
        sa.Column('total_amount', sa.Numeric(10, 2), nullable=False, default=0.00),
        sa.Column('currency', sa.String(3), nullable=False, default='USD'),
        sa.Column('locale', sa.String(10), nullable=False, default='en-US'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['order_service.users.id'], ondelete='CASCADE'),
        schema='order_service'
    )
    
    # Create indexes for cart_sessions table
    op.create_index('idx_cart_sessions_session_id', 'cart_sessions', ['session_id'], unique=True, schema='order_service')
    op.create_index('idx_cart_sessions_user_id', 'cart_sessions', ['user_id'], schema='order_service')
    op.create_index('idx_cart_sessions_expires_at', 'cart_sessions', ['expires_at'], schema='order_service')
    
    # Create orders table
    op.create_table(
        'orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_number', sa.String(50), nullable=False, unique=True),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('subtotal', sa.Numeric(10, 2), nullable=False),
        sa.Column('tax_amount', sa.Numeric(10, 2), nullable=False, default=0.00),
        sa.Column('shipping_amount', sa.Numeric(10, 2), nullable=False, default=0.00),
        sa.Column('discount_amount', sa.Numeric(10, 2), nullable=False, default=0.00),
        sa.Column('total_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, default='USD'),
        sa.Column('customer_email', sa.String(255), nullable=False),
        sa.Column('customer_phone', sa.String(20), nullable=True),
        sa.Column('shipping_address', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('billing_address', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('payment_method', sa.String(50), nullable=False),
        sa.Column('payment_status', sa.String(20), nullable=False, default='pending'),
        sa.Column('payment_reference', sa.String(255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default={}),
        sa.Column('fulfillment_status', sa.String(20), nullable=False, default='pending'),
        sa.Column('tracking_number', sa.String(100), nullable=True),
        sa.Column('shipping_carrier', sa.String(50), nullable=True),
        sa.Column('estimated_delivery', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_delivery', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('shipped_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['order_service.users.id'], ondelete='CASCADE'),
        schema='order_service'
    )
    
    # Create indexes for orders table
    op.create_index('idx_orders_user_id', 'orders', ['user_id'], schema='order_service')
    op.create_index('idx_orders_order_number', 'orders', ['order_number'], unique=True, schema='order_service')
    op.create_index('idx_orders_status', 'orders', ['status'], schema='order_service')
    op.create_index('idx_orders_created_at', 'orders', ['created_at'], schema='order_service')
    op.create_index('idx_orders_total_amount', 'orders', ['total_amount'], schema='order_service')
    
    # Create order_items table
    op.create_table(
        'order_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('game_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sku', sa.String(100), nullable=False),
        sa.Column('game_title', sa.String(255), nullable=False),
        sa.Column('game_slug', sa.String(255), nullable=False),
        sa.Column('game_image_url', sa.String(500), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False, default=1),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('discount_percentage', sa.Integer(), nullable=False, default=0),
        sa.Column('discount_amount', sa.Numeric(10, 2), nullable=False, default=0.00),
        sa.Column('total_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('inventory_type', sa.String(20), nullable=False, default='digital'),
        sa.Column('license_key', sa.String(255), nullable=True),
        sa.Column('fulfillment_status', sa.String(20), nullable=False, default='pending'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('fulfilled_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['order_service.orders.id'], ondelete='CASCADE'),
        schema='order_service'
    )
    
    # Create indexes for order_items table
    op.create_index('idx_order_items_order_id', 'order_items', ['order_id'], schema='order_service')
    op.create_index('idx_order_items_game_id', 'order_items', ['game_id'], schema='order_service')
    op.create_index('idx_order_items_sku', 'order_items', ['sku'], schema='order_service')
    
    # Create payment_transactions table
    op.create_table(
        'payment_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_id', sa.String(255), nullable=False, unique=True),
        sa.Column('payment_method', sa.String(50), nullable=False),
        sa.Column('payment_processor', sa.String(50), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, default='USD'),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('external_transaction_id', sa.String(255), nullable=True),
        sa.Column('authorization_code', sa.String(100), nullable=True),
        sa.Column('processor_response', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_code', sa.String(100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['order_service.orders.id'], ondelete='CASCADE'),
        schema='order_service'
    )
    
    # Create indexes for payment_transactions table
    op.create_index('idx_payment_transactions_order_id', 'payment_transactions', ['order_id'], schema='order_service')
    op.create_index('idx_payment_transactions_transaction_id', 'payment_transactions', ['transaction_id'], unique=True, schema='order_service')
    op.create_index('idx_payment_transactions_status', 'payment_transactions', ['status'], schema='order_service')
    op.create_index('idx_payment_transactions_created_at', 'payment_transactions', ['created_at'], schema='order_service')
    
    # Create saved_items table
    op.create_table(
        'saved_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('game_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('game_title', sa.String(255), nullable=False),
        sa.Column('game_slug', sa.String(255), nullable=False),
        sa.Column('game_image_url', sa.String(500), nullable=True),
        sa.Column('price_at_save', sa.Numeric(10, 2), nullable=False),
        sa.Column('notify_on_sale', sa.Boolean(), nullable=False, default=True),
        sa.Column('notify_on_availability', sa.Boolean(), nullable=False, default=True),
        sa.Column('target_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['order_service.users.id'], ondelete='CASCADE'),
        schema='order_service'
    )
    
    # Create indexes for saved_items table
    op.create_index('idx_saved_items_user_id', 'saved_items', ['user_id'], schema='order_service')
    op.create_index('idx_saved_items_game_id', 'saved_items', ['game_id'], schema='order_service')
    op.create_index('idx_saved_items_user_game', 'saved_items', ['user_id', 'game_id'], unique=True, schema='order_service')
    op.create_index('idx_saved_items_created_at', 'saved_items', ['created_at'], schema='order_service')
    
    # Create user_reviews table
    op.create_table(
        'user_reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('game_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('is_verified_purchase', sa.Boolean(), nullable=False, default=False),
        sa.Column('helpful_count', sa.Integer(), nullable=False, default=0),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['order_service.users.id'], ondelete='CASCADE'),
        schema='order_service'
    )
    
    # Create indexes for user_reviews table
    op.create_index('idx_user_reviews_user_id', 'user_reviews', ['user_id'], schema='order_service')
    op.create_index('idx_user_reviews_game_id', 'user_reviews', ['game_id'], schema='order_service')
    op.create_index('idx_user_reviews_rating', 'user_reviews', ['rating'], schema='order_service')
    op.create_index('idx_user_reviews_created_at', 'user_reviews', ['created_at'], schema='order_service')
    
    # Create triggers for automatic timestamp updates
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Apply update triggers to all tables
    tables = [
        'users', 'user_addresses', 'cart_items', 'cart_sessions', 'orders',
        'order_items', 'payment_transactions', 'saved_items', 'user_reviews'
    ]
    
    for table in tables:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at
            BEFORE UPDATE ON order_service.{table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    """Drop Order Service database schema."""
    
    # Drop triggers first
    tables = [
        'users', 'user_addresses', 'cart_items', 'cart_sessions', 'orders',
        'order_items', 'payment_transactions', 'saved_items', 'user_reviews'
    ]
    
    for table in tables:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON order_service.{table};")
    
    # Drop function
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    
    # Drop tables in reverse order of creation
    op.drop_table('user_reviews', schema='order_service')
    op.drop_table('saved_items', schema='order_service')
    op.drop_table('payment_transactions', schema='order_service')
    op.drop_table('order_items', schema='order_service')
    op.drop_table('orders', schema='order_service')
    op.drop_table('cart_sessions', schema='order_service')
    op.drop_table('cart_items', schema='order_service')
    op.drop_table('user_addresses', schema='order_service')
    op.drop_table('users', schema='order_service')
    
    # Drop schema
    op.execute('DROP SCHEMA IF EXISTS order_service CASCADE')