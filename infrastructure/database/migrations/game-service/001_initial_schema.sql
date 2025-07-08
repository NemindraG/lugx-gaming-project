-- Game Service Schema Migration
-- Version: 001
-- Description: Initial schema for Game Service with publishers, categories, games, and inventory

-- Set search path
SET search_path TO game_service, public;

-- Publishers table (game studios/publishers)
CREATE TABLE IF NOT EXISTS publishers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    slug VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    website VARCHAR(500),
    logo_url VARCHAR(500),
    country VARCHAR(100),
    founded_year INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for slug lookups
CREATE INDEX idx_publishers_slug ON publishers(slug);
CREATE INDEX idx_publishers_active ON publishers(is_active) WHERE is_active = true;

-- Categories table (game genres/categories)
CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    icon_url VARCHAR(500),
    parent_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for category navigation
CREATE INDEX idx_categories_slug ON categories(slug);
CREATE INDEX idx_categories_parent ON categories(parent_id);
CREATE INDEX idx_categories_order ON categories(display_order);

-- Games table (main product catalog)
CREATE TABLE IF NOT EXISTS games (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    short_description VARCHAR(500),
    publisher_id UUID NOT NULL REFERENCES publishers(id) ON DELETE RESTRICT,
    release_date DATE,
    
    -- Pricing
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    discount_percentage INTEGER DEFAULT 0 CHECK (discount_percentage >= 0 AND discount_percentage <= 100),
    
    -- Media
    cover_image_url VARCHAR(500),
    thumbnail_url VARCHAR(500),
    trailer_url VARCHAR(500),
    screenshots TEXT[], -- Array of screenshot URLs
    
    -- Metadata
    platform TEXT[] DEFAULT '{}', -- Array of platforms: PC, PS5, XBOX, etc.
    system_requirements JSONB DEFAULT '{}',
    age_rating game_rating,
    metacritic_score INTEGER CHECK (metacritic_score >= 0 AND metacritic_score <= 100),
    
    -- Search optimization
    search_vector tsvector,
    
    -- Status
    status game_status DEFAULT 'active',
    featured BOOLEAN DEFAULT false,
    trending_score INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT price_discount_check CHECK (
        (discount_percentage = 0) OR 
        (discount_percentage > 0 AND price > 0)
    )
);

-- Create indexes for game queries
CREATE INDEX idx_games_slug ON games(slug);
CREATE INDEX idx_games_publisher ON games(publisher_id);
CREATE INDEX idx_games_status ON games(status) WHERE status = 'active';
CREATE INDEX idx_games_featured ON games(featured) WHERE featured = true;
CREATE INDEX idx_games_price ON games(price);
CREATE INDEX idx_games_release_date ON games(release_date DESC);
CREATE INDEX idx_games_trending ON games(trending_score DESC) WHERE status = 'active';

-- Full-text search index
CREATE INDEX idx_games_search ON games USING gin(search_vector);

-- Game categories (many-to-many relationship)
CREATE TABLE IF NOT EXISTS game_categories (
    game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    category_id UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (game_id, category_id)
);

-- Ensure only one primary category per game
CREATE UNIQUE INDEX idx_game_primary_category ON game_categories(game_id) WHERE is_primary = true;

-- Inventory table (stock management)
CREATE TABLE IF NOT EXISTS inventory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    
    -- Stock levels
    quantity_available INTEGER NOT NULL DEFAULT 0 CHECK (quantity_available >= 0),
    quantity_reserved INTEGER NOT NULL DEFAULT 0 CHECK (quantity_reserved >= 0),
    
    -- Digital vs Physical
    inventory_type VARCHAR(20) NOT NULL DEFAULT 'digital' CHECK (inventory_type IN ('digital', 'physical')),
    
    -- Restock information
    restock_threshold INTEGER DEFAULT 10,
    restock_quantity INTEGER DEFAULT 100,
    last_restocked_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    low_stock_alert BOOLEAN DEFAULT false,
    max_per_order INTEGER DEFAULT 5,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(game_id, inventory_type),
    CONSTRAINT available_reserved_check CHECK (quantity_available >= quantity_reserved)
);

-- Create index for inventory queries
CREATE INDEX idx_inventory_game ON inventory(game_id);
CREATE INDEX idx_inventory_low_stock ON inventory(low_stock_alert) WHERE low_stock_alert = true;

-- Reviews table (customer feedback)
CREATE TABLE IF NOT EXISTS reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    user_id UUID NOT NULL, -- References Order Service users
    
    -- Review content
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(255),
    content TEXT,
    
    -- Review metadata
    is_verified_purchase BOOLEAN DEFAULT false,
    helpful_count INTEGER DEFAULT 0,
    reported_count INTEGER DEFAULT 0,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'hidden')),
    moderated_at TIMESTAMP WITH TIME ZONE,
    moderated_by UUID,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(game_id, user_id)
);

-- Create indexes for review queries
CREATE INDEX idx_reviews_game ON reviews(game_id);
CREATE INDEX idx_reviews_user ON reviews(user_id);
CREATE INDEX idx_reviews_status ON reviews(status);
CREATE INDEX idx_reviews_rating ON reviews(rating);

-- Trigger to update search vector when game data changes
CREATE OR REPLACE FUNCTION update_game_search_vector() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.short_description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_game_search_vector_trigger
    BEFORE INSERT OR UPDATE OF title, short_description, description
    ON games
    FOR EACH ROW
    EXECUTE FUNCTION update_game_search_vector();

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to all tables
CREATE TRIGGER update_publishers_updated_at BEFORE UPDATE ON publishers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_games_updated_at BEFORE UPDATE ON games
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_inventory_updated_at BEFORE UPDATE ON inventory
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reviews_updated_at BEFORE UPDATE ON reviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE publishers IS 'Game publishers and development studios';
COMMENT ON TABLE categories IS 'Game categories/genres with hierarchical support';
COMMENT ON TABLE games IS 'Main game catalog with pricing and metadata';
COMMENT ON TABLE game_categories IS 'Many-to-many relationship between games and categories';
COMMENT ON TABLE inventory IS 'Stock management for games (digital and physical)';
COMMENT ON TABLE reviews IS 'Customer reviews and ratings for games';

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA game_service TO game_service;
GRANT ALL ON ALL SEQUENCES IN SCHEMA game_service TO game_service;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA game_service TO game_service;