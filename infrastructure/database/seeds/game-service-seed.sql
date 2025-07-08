-- Game Service Seed Data
-- Realistic test data for development

SET search_path TO game_service, public;

-- Insert Publishers
INSERT INTO publishers (id, name, slug, description, website, country, founded_year) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'Epic Games Studios', 'epic-games', 'Creator of legendary gaming experiences', 'https://epicgames.com', 'USA', 1991),
('550e8400-e29b-41d4-a716-446655440002', 'Ninja Workshop', 'ninja-workshop', 'Independent game studio focused on action games', 'https://ninjaworkshop.com', 'Japan', 2010),
('550e8400-e29b-41d4-a716-446655440003', 'Pixel Forge', 'pixel-forge', 'Retro-style game development studio', 'https://pixelforge.io', 'Canada', 2015),
('550e8400-e29b-41d4-a716-446655440004', 'Quantum Studios', 'quantum-studios', 'Next-gen gaming experiences', 'https://quantumstudios.com', 'UK', 2018),
('550e8400-e29b-41d4-a716-446655440005', 'Thunder Games', 'thunder-games', 'AAA game development powerhouse', 'https://thundergames.com', 'USA', 2005);

-- Insert Categories
INSERT INTO categories (id, name, slug, description, display_order) VALUES
('650e8400-e29b-41d4-a716-446655440001', 'Action', 'action', 'Fast-paced action games', 1),
('650e8400-e29b-41d4-a716-446655440002', 'Adventure', 'adventure', 'Story-driven adventure games', 2),
('650e8400-e29b-41d4-a716-446655440003', 'RPG', 'rpg', 'Role-playing games', 3),
('650e8400-e29b-41d4-a716-446655440004', 'Strategy', 'strategy', 'Strategic thinking games', 4),
('650e8400-e29b-41d4-a716-446655440005', 'Sports', 'sports', 'Sports and racing games', 5),
('650e8400-e29b-41d4-a716-446655440006', 'Puzzle', 'puzzle', 'Mind-bending puzzle games', 6),
('650e8400-e29b-41d4-a716-446655440007', 'Multiplayer', 'multiplayer', 'Online multiplayer games', 7),
('650e8400-e29b-41d4-a716-446655440008', 'Indie', 'indie', 'Independent developer games', 8);

-- Insert Games
INSERT INTO games (
    id, title, slug, description, short_description, publisher_id, 
    release_date, price, discount_percentage, cover_image_url, thumbnail_url,
    platform, age_rating, metacritic_score, status, featured, trending_score
) VALUES
-- Featured Games
('750e8400-e29b-41d4-a716-446655440001', 
 'Cyborg Warrior: Revolution', 
 'cyborg-warrior-revolution',
 'In a dystopian future, you are the last hope of humanity. Enhanced with cybernetic implants, battle through hordes of enemies in this action-packed adventure.',
 'Futuristic action game with cybernetic enhancements',
 '550e8400-e29b-41d4-a716-446655440001',
 '2024-03-15',
 59.99,
 10,
 '/assets/images/featured-01.jpg',
 '/assets/images/trending-01.jpg',
 ARRAY['PC', 'PS5', 'XBOX'],
 'M',
 89,
 'active',
 true,
 95),

('750e8400-e29b-41d4-a716-446655440002',
 'Island Survival: Lost Paradise',
 'island-survival-lost-paradise',
 'Stranded on a mysterious island, craft, build, and survive against the elements and dangerous wildlife in this open-world survival game.',
 'Open-world survival on a mysterious island',
 '550e8400-e29b-41d4-a716-446655440002',
 '2024-02-20',
 49.99,
 0,
 '/assets/images/featured-02.jpg',
 '/assets/images/trending-02.jpg',
 ARRAY['PC', 'PS5'],
 'T',
 85,
 'active',
 true,
 88),

('750e8400-e29b-41d4-a716-446655440003',
 'World Racing Championship 2024',
 'world-racing-championship-2024',
 'Experience the thrill of professional racing with realistic physics, stunning graphics, and over 100 real-world tracks.',
 'Ultimate racing simulation experience',
 '550e8400-e29b-41d4-a716-446655440005',
 '2024-01-10',
 69.99,
 15,
 '/assets/images/featured-03.jpg',
 '/assets/images/trending-03.jpg',
 ARRAY['PC', 'PS5', 'XBOX'],
 'E',
 92,
 'active',
 true,
 90),

-- Regular Games
('750e8400-e29b-41d4-a716-446655440004',
 'Puzzle Master: Mind Games',
 'puzzle-master-mind-games',
 'Challenge your intellect with over 1000 unique puzzles ranging from simple logic problems to complex brain teasers.',
 'Collection of challenging puzzles',
 '550e8400-e29b-41d4-a716-446655440003',
 '2023-11-05',
 29.99,
 25,
 '/assets/images/top-game-01.jpg',
 '/assets/images/top-game-01.jpg',
 ARRAY['PC', 'Mobile'],
 'E',
 78,
 'active',
 false,
 45),

('750e8400-e29b-41d4-a716-446655440005',
 'Medieval Conquest: Kings and Queens',
 'medieval-conquest-kings-queens',
 'Build your empire, command armies, and conquer territories in this epic medieval strategy game.',
 'Epic medieval strategy game',
 '550e8400-e29b-41d4-a716-446655440004',
 '2023-12-01',
 44.99,
 20,
 '/assets/images/top-game-02.jpg',
 '/assets/images/top-game-02.jpg',
 ARRAY['PC'],
 'T',
 83,
 'active',
 false,
 67),

('750e8400-e29b-41d4-a716-446655440006',
 'Space Explorer: Infinite Galaxy',
 'space-explorer-infinite-galaxy',
 'Explore the vast cosmos, discover alien civilizations, and unravel the mysteries of the universe.',
 'Space exploration adventure',
 '550e8400-e29b-41d4-a716-446655440004',
 '2024-01-25',
 54.99,
 0,
 '/assets/images/top-game-03.jpg',
 '/assets/images/top-game-03.jpg',
 ARRAY['PC', 'PS5', 'XBOX'],
 'T',
 87,
 'active',
 false,
 72),

('750e8400-e29b-41d4-a716-446655440007',
 'Ninja Legends: Shadow Strike',
 'ninja-legends-shadow-strike',
 'Master the art of stealth and combat in feudal Japan. Become the ultimate ninja warrior.',
 'Stealth action in feudal Japan',
 '550e8400-e29b-41d4-a716-446655440002',
 '2023-10-15',
 39.99,
 30,
 '/assets/images/top-game-04.jpg',
 '/assets/images/top-game-04.jpg',
 ARRAY['PC', 'PS5'],
 'M',
 81,
 'active',
 false,
 58),

('750e8400-e29b-41d4-a716-446655440008',
 'Pixel Quest: Retro Adventure',
 'pixel-quest-retro-adventure',
 'A nostalgic journey through pixelated worlds filled with secrets, treasures, and classic gameplay.',
 'Retro-style platformer adventure',
 '550e8400-e29b-41d4-a716-446655440003',
 '2023-09-20',
 19.99,
 0,
 '/assets/images/top-game-05.jpg',
 '/assets/images/top-game-05.jpg',
 ARRAY['PC', 'Switch'],
 'E',
 76,
 'active',
 false,
 42),

('750e8400-e29b-41d4-a716-446655440009',
 'Battle Arena: Champions',
 'battle-arena-champions',
 'Compete in intense 5v5 battles in this multiplayer online battle arena. Choose your champion and dominate!',
 'Competitive multiplayer MOBA',
 '550e8400-e29b-41d4-a716-446655440001',
 '2024-02-10',
 0.00,
 0,
 '/assets/images/top-game-06.jpg',
 '/assets/images/top-game-06.jpg',
 ARRAY['PC'],
 'T',
 84,
 'active',
 false,
 82);

-- Insert Game Categories (many-to-many relationships)
INSERT INTO game_categories (game_id, category_id, is_primary) VALUES
-- Cyborg Warrior
('750e8400-e29b-41d4-a716-446655440001', '650e8400-e29b-41d4-a716-446655440001', true),  -- Action (primary)
('750e8400-e29b-41d4-a716-446655440001', '650e8400-e29b-41d4-a716-446655440002', false), -- Adventure
-- Island Survival
('750e8400-e29b-41d4-a716-446655440002', '650e8400-e29b-41d4-a716-446655440002', true),  -- Adventure (primary)
('750e8400-e29b-41d4-a716-446655440002', '650e8400-e29b-41d4-a716-446655440001', false), -- Action
-- World Racing
('750e8400-e29b-41d4-a716-446655440003', '650e8400-e29b-41d4-a716-446655440005', true),  -- Sports (primary)
('750e8400-e29b-41d4-a716-446655440003', '650e8400-e29b-41d4-a716-446655440007', false), -- Multiplayer
-- Puzzle Master
('750e8400-e29b-41d4-a716-446655440004', '650e8400-e29b-41d4-a716-446655440006', true),  -- Puzzle (primary)
('750e8400-e29b-41d4-a716-446655440004', '650e8400-e29b-41d4-a716-446655440008', false), -- Indie
-- Medieval Conquest
('750e8400-e29b-41d4-a716-446655440005', '650e8400-e29b-41d4-a716-446655440004', true),  -- Strategy (primary)
('750e8400-e29b-41d4-a716-446655440005', '650e8400-e29b-41d4-a716-446655440007', false), -- Multiplayer
-- Space Explorer
('750e8400-e29b-41d4-a716-446655440006', '650e8400-e29b-41d4-a716-446655440002', true),  -- Adventure (primary)
('750e8400-e29b-41d4-a716-446655440006', '650e8400-e29b-41d4-a716-446655440003', false), -- RPG
-- Ninja Legends
('750e8400-e29b-41d4-a716-446655440007', '650e8400-e29b-41d4-a716-446655440001', true),  -- Action (primary)
('750e8400-e29b-41d4-a716-446655440007', '650e8400-e29b-41d4-a716-446655440002', false), -- Adventure
-- Pixel Quest
('750e8400-e29b-41d4-a716-446655440008', '650e8400-e29b-41d4-a716-446655440002', true),  -- Adventure (primary)
('750e8400-e29b-41d4-a716-446655440008', '650e8400-e29b-41d4-a716-446655440008', false), -- Indie
-- Battle Arena
('750e8400-e29b-41d4-a716-446655440009', '650e8400-e29b-41d4-a716-446655440007', true),  -- Multiplayer (primary)
('750e8400-e29b-41d4-a716-446655440009', '650e8400-e29b-41d4-a716-446655440001', false); -- Action

-- Insert Inventory
INSERT INTO inventory (game_id, quantity_available, quantity_reserved, inventory_type, max_per_order) VALUES
('750e8400-e29b-41d4-a716-446655440001', 999999, 0, 'digital', 5),
('750e8400-e29b-41d4-a716-446655440002', 999999, 0, 'digital', 5),
('750e8400-e29b-41d4-a716-446655440003', 999999, 0, 'digital', 5),
('750e8400-e29b-41d4-a716-446655440004', 999999, 0, 'digital', 10),
('750e8400-e29b-41d4-a716-446655440005', 999999, 0, 'digital', 5),
('750e8400-e29b-41d4-a716-446655440006', 999999, 0, 'digital', 5),
('750e8400-e29b-41d4-a716-446655440007', 999999, 0, 'digital', 5),
('750e8400-e29b-41d4-a716-446655440008', 999999, 0, 'digital', 10),
('750e8400-e29b-41d4-a716-446655440009', 999999, 0, 'digital', 1);

-- Insert some sample reviews
INSERT INTO reviews (game_id, user_id, rating, title, content, is_verified_purchase, status) VALUES
('750e8400-e29b-41d4-a716-446655440001', '850e8400-e29b-41d4-a716-446655440001', 5, 
 'Best Action Game Ever!', 
 'The cybernetic enhancements make combat incredibly satisfying. Graphics are stunning!',
 true, 'approved'),
('750e8400-e29b-41d4-a716-446655440001', '850e8400-e29b-41d4-a716-446655440002', 4,
 'Great game with minor issues',
 'Gameplay is fantastic but experienced some minor bugs in the later levels.',
 true, 'approved'),
('750e8400-e29b-41d4-a716-446655440003', '850e8400-e29b-41d4-a716-446655440003', 5,
 'Most realistic racing game',
 'Physics engine is incredible. Feels like driving a real car!',
 true, 'approved');