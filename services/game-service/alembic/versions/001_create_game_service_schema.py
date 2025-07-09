"""Create game service schema

Revision ID: 001_create_game_service_schema
Revises: 
Create Date: 2025-07-08 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_create_game_service_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create schema
    op.execute('CREATE SCHEMA IF NOT EXISTS game_service')
    
    # Create publishers table
    op.create_table('publishers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('founded_year', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('slug'),
        schema='game_service'
    )
    
    # Create categories table
    op.create_table('categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon_url', sa.String(length=500), nullable=True),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False, default=0),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['game_service.categories.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('slug'),
        schema='game_service'
    )
    
    # Create games table
    op.create_table('games',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('short_description', sa.String(length=500), nullable=True),
        sa.Column('publisher_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('release_date', sa.Date(), nullable=True),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('discount_percentage', sa.Integer(), nullable=False, default=0),
        sa.Column('cover_image_url', sa.String(length=500), nullable=True),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
        sa.Column('trailer_url', sa.String(length=500), nullable=True),
        sa.Column('screenshots', postgresql.ARRAY(sa.Text()), nullable=True, default=[]),
        sa.Column('platform', postgresql.ARRAY(sa.Text()), nullable=False, default=[]),
        sa.Column('system_requirements', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default={}),
        sa.Column('age_rating', sa.String(length=10), nullable=True),
        sa.Column('metacritic_score', sa.Integer(), nullable=True),
        sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, default='active'),
        sa.Column('featured', sa.Boolean(), nullable=False, default=False),
        sa.Column('trending_score', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('price >= 0', name='check_price_non_negative'),
        sa.CheckConstraint('discount_percentage >= 0 AND discount_percentage <= 100', name='check_discount_range'),
        sa.CheckConstraint('metacritic_score IS NULL OR (metacritic_score >= 0 AND metacritic_score <= 100)', name='check_metacritic_range'),
        sa.CheckConstraint('(discount_percentage = 0) OR (discount_percentage > 0 AND price > 0)', name='price_discount_check'),
        sa.ForeignKeyConstraint(['publisher_id'], ['game_service.publishers.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
        schema='game_service'
    )
    
    # Create game_categories association table
    op.create_table('game_categories',
        sa.Column('game_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['game_service.categories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['game_id'], ['game_service.games.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('game_id', 'category_id'),
        schema='game_service'
    )
    
    # Create inventory table
    op.create_table('inventory',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('game_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity_available', sa.Integer(), nullable=False, default=0),
        sa.Column('quantity_reserved', sa.Integer(), nullable=False, default=0),
        sa.Column('inventory_type', sa.String(length=20), nullable=False, default='digital'),
        sa.Column('restock_threshold', sa.Integer(), nullable=False, default=10),
        sa.Column('restock_quantity', sa.Integer(), nullable=False, default=100),
        sa.Column('last_restocked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('low_stock_alert', sa.Boolean(), nullable=False, default=False),
        sa.Column('max_per_order', sa.Integer(), nullable=False, default=5),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('quantity_available >= 0', name='check_quantity_available'),
        sa.CheckConstraint('quantity_reserved >= 0', name='check_quantity_reserved'),
        sa.CheckConstraint("inventory_type IN ('digital', 'physical')", name='check_inventory_type'),
        sa.CheckConstraint('quantity_available >= quantity_reserved', name='available_reserved_check'),
        sa.ForeignKeyConstraint(['game_id'], ['game_service.games.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('game_id', 'inventory_type'),
        schema='game_service'
    )
    
    # Create reviews table
    op.create_table('reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('game_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('is_verified_purchase', sa.Boolean(), nullable=False, default=False),
        sa.Column('helpful_count', sa.Integer(), nullable=False, default=0),
        sa.Column('reported_count', sa.Integer(), nullable=False, default=0),
        sa.Column('status', sa.String(length=20), nullable=False, default='pending'),
        sa.Column('moderated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('moderated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected', 'hidden')", name='check_review_status'),
        sa.ForeignKeyConstraint(['game_id'], ['game_service.games.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('game_id', 'user_id'),
        schema='game_service'
    )
    
    # Create indexes for performance
    op.create_index('idx_games_publisher_id', 'games', ['publisher_id'], schema='game_service')
    op.create_index('idx_games_status', 'games', ['status'], schema='game_service')
    op.create_index('idx_games_featured', 'games', ['featured'], schema='game_service')
    op.create_index('idx_games_trending_score', 'games', ['trending_score'], schema='game_service')
    op.create_index('idx_games_price', 'games', ['price'], schema='game_service')
    op.create_index('idx_games_release_date', 'games', ['release_date'], schema='game_service')
    op.create_index('idx_games_search_vector', 'games', ['search_vector'], postgresql_using='gin', schema='game_service')
    
    op.create_index('idx_categories_parent_id', 'categories', ['parent_id'], schema='game_service')
    op.create_index('idx_categories_display_order', 'categories', ['display_order'], schema='game_service')
    
    op.create_index('idx_game_categories_category_id', 'game_categories', ['category_id'], schema='game_service')
    op.create_index('idx_game_categories_is_primary', 'game_categories', ['is_primary'], schema='game_service')
    op.create_index('idx_game_primary_category', 'game_categories', ['game_id'], 
                   unique=True, postgresql_where=sa.text('is_primary = true'), schema='game_service')
    
    op.create_index('idx_inventory_game_id', 'inventory', ['game_id'], schema='game_service')
    op.create_index('idx_inventory_type', 'inventory', ['inventory_type'], schema='game_service')
    op.create_index('idx_inventory_low_stock', 'inventory', ['low_stock_alert'], schema='game_service')
    
    op.create_index('idx_reviews_game_id', 'reviews', ['game_id'], schema='game_service')
    op.create_index('idx_reviews_user_id', 'reviews', ['user_id'], schema='game_service')
    op.create_index('idx_reviews_status', 'reviews', ['status'], schema='game_service')
    op.create_index('idx_reviews_rating', 'reviews', ['rating'], schema='game_service')
    
    # Create trigger for updating search vector
    op.execute("""
        CREATE OR REPLACE FUNCTION game_service.update_search_vector()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector := to_tsvector('english', 
                COALESCE(NEW.title, '') || ' ' || 
                COALESCE(NEW.description, '') || ' ' || 
                COALESCE(NEW.short_description, '')
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER games_search_vector_update
        BEFORE INSERT OR UPDATE ON game_service.games
        FOR EACH ROW EXECUTE FUNCTION game_service.update_search_vector();
    """)
    
    # Create trigger for updating timestamps
    op.execute("""
        CREATE OR REPLACE FUNCTION game_service.update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Apply update trigger to all tables
    for table in ['publishers', 'categories', 'games', 'inventory', 'reviews']:
        op.execute(f"""
            CREATE TRIGGER {table}_update_updated_at
            BEFORE UPDATE ON game_service.{table}
            FOR EACH ROW EXECUTE FUNCTION game_service.update_updated_at_column();
        """)


def downgrade() -> None:
    # Drop triggers
    for table in ['publishers', 'categories', 'games', 'inventory', 'reviews']:
        op.execute(f'DROP TRIGGER IF EXISTS {table}_update_updated_at ON game_service.{table}')
    
    op.execute('DROP TRIGGER IF EXISTS games_search_vector_update ON game_service.games')
    op.execute('DROP FUNCTION IF EXISTS game_service.update_updated_at_column()')
    op.execute('DROP FUNCTION IF EXISTS game_service.update_search_vector()')
    
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('reviews', schema='game_service')
    op.drop_table('inventory', schema='game_service')
    op.drop_table('game_categories', schema='game_service')
    op.drop_table('games', schema='game_service')
    op.drop_table('categories', schema='game_service')
    op.drop_table('publishers', schema='game_service')
    
    # Drop schema
    op.execute('DROP SCHEMA IF EXISTS game_service CASCADE')