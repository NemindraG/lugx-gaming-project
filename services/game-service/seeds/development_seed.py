#!/usr/bin/env python3
"""
Development seed data for Game Service.
Creates realistic test data for local development and testing.
"""

import asyncio
import os
import sys
from datetime import date
from decimal import Decimal
from uuid import uuid4

# Add the parent directory to Python path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.game import Publisher, Category, Game, GameCategory, Inventory, Review

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://game_service:game_secure_password_2024@localhost:5432/lugx_games",
)

# Seed data
PUBLISHERS_DATA = [
    {
        "name": "Epic Games",
        "slug": "epic-games",
        "description": "Epic Games, Inc. is an American video game and software developer and publisher.",
        "website": "https://www.epicgames.com",
        "country": "United States",
        "founded_year": 1991,
    },
    {
        "name": "Valve Corporation",
        "slug": "valve",
        "description": "Valve Corporation is an American video game developer and publisher.",
        "website": "https://www.valvesoftware.com",
        "country": "United States",
        "founded_year": 1996,
    },
    {
        "name": "CD Projekt",
        "slug": "cd-projekt",
        "description": "CD Projekt S.A. is a Polish video game developer and publisher.",
        "website": "https://cdprojekt.com",
        "country": "Poland",
        "founded_year": 1994,
    },
    {
        "name": "Rockstar Games",
        "slug": "rockstar-games",
        "description": "Rockstar Games, Inc. is an American video game publisher.",
        "website": "https://www.rockstargames.com",
        "country": "United States",
        "founded_year": 1998,
    },
    {
        "name": "FromSoftware",
        "slug": "fromsoftware",
        "description": "FromSoftware, Inc. is a Japanese video game development company.",
        "website": "https://www.fromsoftware.jp",
        "country": "Japan",
        "founded_year": 1986,
    },
]

CATEGORIES_DATA = [
    # Main categories
    {
        "name": "Action",
        "slug": "action",
        "description": "Fast-paced games requiring quick reflexes",
        "display_order": 1,
    },
    {
        "name": "Adventure",
        "slug": "adventure",
        "description": "Story-driven exploration games",
        "display_order": 2,
    },
    {
        "name": "RPG",
        "slug": "rpg",
        "description": "Role-playing games with character progression",
        "display_order": 3,
    },
    {
        "name": "Strategy",
        "slug": "strategy",
        "description": "Games requiring tactical thinking",
        "display_order": 4,
    },
    {
        "name": "Simulation",
        "slug": "simulation",
        "description": "Games that simulate real-world activities",
        "display_order": 5,
    },
    {
        "name": "Sports",
        "slug": "sports",
        "description": "Sports simulation and arcade games",
        "display_order": 6,
    },
    {
        "name": "Racing",
        "slug": "racing",
        "description": "Vehicle racing games",
        "display_order": 7,
    },
    {
        "name": "Fighting",
        "slug": "fighting",
        "description": "Combat-focused games",
        "display_order": 8,
    },
]

# Sub-categories will be added with parent relationships
SUB_CATEGORIES_DATA = [
    # Action sub-categories
    {
        "name": "First-Person Shooter",
        "slug": "fps",
        "parent": "action",
        "display_order": 1,
    },
    {
        "name": "Third-Person Shooter",
        "slug": "tps",
        "parent": "action",
        "display_order": 2,
    },
    {
        "name": "Platformer",
        "slug": "platformer",
        "parent": "action",
        "display_order": 3,
    },
    # Adventure sub-categories
    {
        "name": "Point and Click",
        "slug": "point-and-click",
        "parent": "adventure",
        "display_order": 1,
    },
    {
        "name": "Puzzle Adventure",
        "slug": "puzzle-adventure",
        "parent": "adventure",
        "display_order": 2,
    },
    # RPG sub-categories
    {"name": "JRPG", "slug": "jrpg", "parent": "rpg", "display_order": 1},
    {"name": "Western RPG", "slug": "western-rpg", "parent": "rpg", "display_order": 2},
    {"name": "Action RPG", "slug": "action-rpg", "parent": "rpg", "display_order": 3},
    # Strategy sub-categories
    {
        "name": "Real-Time Strategy",
        "slug": "rts",
        "parent": "strategy",
        "display_order": 1,
    },
    {
        "name": "Turn-Based Strategy",
        "slug": "turn-based",
        "parent": "strategy",
        "display_order": 2,
    },
]

GAMES_DATA = [
    {
        "title": "Fortnite",
        "slug": "fortnite",
        "description": "Fortnite is a survival game where 100 players fight against each other in player versus player combat to be the last one standing.",
        "short_description": "Battle Royale game with building mechanics",
        "publisher": "epic-games",
        "release_date": date(2017, 9, 26),
        "price": Decimal("0.00"),
        "discount_percentage": 0,
        "platform": ["PC", "PlayStation", "Xbox", "Nintendo Switch", "Mobile"],
        "age_rating": "T",
        "metacritic_score": 81,
        "status": "active",
        "featured": True,
        "trending_score": 95,
        "categories": ["action", "fps"],
    },
    {
        "title": "Half-Life: Alyx",
        "slug": "half-life-alyx",
        "description": "Half-Life: Alyx is Valve's VR return to the Half-Life series. It's the story of an impossible fight against a vicious alien race known as the Combine.",
        "short_description": "VR adventure in the Half-Life universe",
        "publisher": "valve",
        "release_date": date(2020, 3, 23),
        "price": Decimal("59.99"),
        "discount_percentage": 15,
        "platform": ["PC VR"],
        "age_rating": "M",
        "metacritic_score": 93,
        "status": "active",
        "featured": True,
        "trending_score": 88,
        "categories": ["adventure", "action"],
    },
    {
        "title": "Cyberpunk 2077",
        "slug": "cyberpunk-2077",
        "description": "Cyberpunk 2077 is an open-world, action-adventure story set in Night City, a megalopolis obsessed with power, glamour and body modification.",
        "short_description": "Open-world RPG set in a dystopian future",
        "publisher": "cd-projekt",
        "release_date": date(2020, 12, 10),
        "price": Decimal("59.99"),
        "discount_percentage": 50,
        "platform": ["PC", "PlayStation", "Xbox"],
        "age_rating": "M",
        "metacritic_score": 86,
        "status": "active",
        "featured": True,
        "trending_score": 92,
        "categories": ["rpg", "action-rpg", "action"],
    },
    {
        "title": "Grand Theft Auto V",
        "slug": "gta-v",
        "description": "Grand Theft Auto V for PC offers players the option to explore the award-winning world of Los Santos and Blaine County in resolutions of up to 4K and beyond.",
        "short_description": "Open-world crime action game",
        "publisher": "rockstar-games",
        "release_date": date(2013, 9, 17),
        "price": Decimal("29.99"),
        "discount_percentage": 0,
        "platform": ["PC", "PlayStation", "Xbox"],
        "age_rating": "M",
        "metacritic_score": 97,
        "status": "active",
        "featured": False,
        "trending_score": 85,
        "categories": ["action", "tps"],
    },
    {
        "title": "Elden Ring",
        "slug": "elden-ring",
        "description": "THE NEW FANTASY ACTION RPG. Rise, Tarnished, and be guided by grace to brandish the power of the Elden Ring and become an Elden Lord in the Lands Between.",
        "short_description": "Fantasy action RPG from FromSoftware",
        "publisher": "fromsoftware",
        "release_date": date(2022, 2, 25),
        "price": Decimal("59.99"),
        "discount_percentage": 25,
        "platform": ["PC", "PlayStation", "Xbox"],
        "age_rating": "M",
        "metacritic_score": 96,
        "status": "active",
        "featured": True,
        "trending_score": 98,
        "categories": ["rpg", "action-rpg", "action"],
    },
    {
        "title": "Portal 2",
        "slug": "portal-2",
        "description": "Portal 2 draws from the award-winning formula of innovative gameplay, story, and music that earned the original Portal over 70 industry accolades.",
        "short_description": "Physics-based puzzle platformer",
        "publisher": "valve",
        "release_date": date(2011, 4, 19),
        "price": Decimal("9.99"),
        "discount_percentage": 0,
        "platform": ["PC", "PlayStation", "Xbox"],
        "age_rating": "E10+",
        "metacritic_score": 95,
        "status": "active",
        "featured": False,
        "trending_score": 75,
        "categories": ["puzzle-adventure", "platformer"],
    },
    {
        "title": "The Witcher 3: Wild Hunt",
        "slug": "witcher-3",
        "description": "You are Geralt of Rivia, mercenary monster slayer. Before you stands a war-torn, monster-infested continent you can explore at will.",
        "short_description": "Open-world fantasy RPG",
        "publisher": "cd-projekt",
        "release_date": date(2015, 5, 19),
        "price": Decimal("39.99"),
        "discount_percentage": 70,
        "platform": ["PC", "PlayStation", "Xbox", "Nintendo Switch"],
        "age_rating": "M",
        "metacritic_score": 93,
        "status": "active",
        "featured": True,
        "trending_score": 90,
        "categories": ["rpg", "western-rpg", "action-rpg"],
    },
    {
        "title": "Counter-Strike 2",
        "slug": "counter-strike-2",
        "description": "For over two decades, Counter-Strike has offered an elite competitive experience, one shaped by millions of players from across the globe.",
        "short_description": "Competitive tactical FPS",
        "publisher": "valve",
        "release_date": date(2023, 9, 27),
        "price": Decimal("0.00"),
        "discount_percentage": 0,
        "platform": ["PC"],
        "age_rating": "M",
        "metacritic_score": 83,
        "status": "active",
        "featured": True,
        "trending_score": 94,
        "categories": ["fps", "action"],
    },
]


async def create_seed_data():
    """Create comprehensive seed data for development."""
    print("🌱 Starting Game Service seed data creation...")

    # Create async engine and session
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Create publishers
            print("📚 Creating publishers...")
            publisher_objects = {}
            for pub_data in PUBLISHERS_DATA:
                publisher = Publisher(
                    id=uuid4(),
                    name=pub_data["name"],
                    slug=pub_data["slug"],
                    description=pub_data["description"],
                    website=pub_data["website"],
                    country=pub_data["country"],
                    founded_year=pub_data["founded_year"],
                )
                session.add(publisher)
                publisher_objects[pub_data["slug"]] = publisher

            await session.flush()  # Get IDs for foreign keys

            # Create main categories
            print("🏷️  Creating categories...")
            category_objects = {}
            for cat_data in CATEGORIES_DATA:
                category = Category(
                    id=uuid4(),
                    name=cat_data["name"],
                    slug=cat_data["slug"],
                    description=cat_data["description"],
                    display_order=cat_data["display_order"],
                )
                session.add(category)
                category_objects[cat_data["slug"]] = category

            await session.flush()

            # Create sub-categories
            print("🏷️  Creating sub-categories...")
            for sub_cat_data in SUB_CATEGORIES_DATA:
                parent_category = category_objects[sub_cat_data["parent"]]
                sub_category = Category(
                    id=uuid4(),
                    name=sub_cat_data["name"],
                    slug=sub_cat_data["slug"],
                    parent_id=parent_category.id,
                    display_order=sub_cat_data["display_order"],
                )
                session.add(sub_category)
                category_objects[sub_cat_data["slug"]] = sub_category

            await session.flush()

            # Create games
            print("🎮 Creating games...")
            game_objects = {}
            for game_data in GAMES_DATA:
                publisher = publisher_objects[game_data["publisher"]]
                game = Game(
                    id=uuid4(),
                    title=game_data["title"],
                    slug=game_data["slug"],
                    description=game_data["description"],
                    short_description=game_data["short_description"],
                    publisher_id=publisher.id,
                    release_date=game_data["release_date"],
                    price=game_data["price"],
                    discount_percentage=game_data["discount_percentage"],
                    platform=game_data["platform"],
                    age_rating=game_data["age_rating"],
                    metacritic_score=game_data["metacritic_score"],
                    status=game_data["status"],
                    featured=game_data["featured"],
                    trending_score=game_data["trending_score"],
                )
                session.add(game)
                game_objects[game_data["slug"]] = game

            await session.flush()

            # Create game-category associations
            print("🔗 Creating game-category associations...")
            for game_data in GAMES_DATA:
                game = game_objects[game_data["slug"]]
                for i, category_slug in enumerate(game_data["categories"]):
                    if category_slug in category_objects:
                        category = category_objects[category_slug]
                        game_category = GameCategory(
                            game_id=game.id,
                            category_id=category.id,
                            is_primary=(i == 0),  # First category is primary
                        )
                        session.add(game_category)

            # Create inventory for all games
            print("📦 Creating inventory...")
            for game_slug, game in game_objects.items():
                # Digital inventory (unlimited for most games)
                digital_inventory = Inventory(
                    id=uuid4(),
                    game_id=game.id,
                    quantity_available=(
                        999999 if game.price > 0 else 999999
                    ),  # Unlimited for free-to-play
                    quantity_reserved=0,
                    inventory_type="digital",
                    restock_threshold=100,
                    restock_quantity=1000000,
                    low_stock_alert=False,
                    max_per_order=1,
                )
                session.add(digital_inventory)

                # Physical inventory for some games
                if game.price > 20:  # Only expensive games have physical copies
                    physical_inventory = Inventory(
                        id=uuid4(),
                        game_id=game.id,
                        quantity_available=50,
                        quantity_reserved=5,
                        inventory_type="physical",
                        restock_threshold=10,
                        restock_quantity=100,
                        low_stock_alert=True,
                        max_per_order=2,
                    )
                    session.add(physical_inventory)

            # Create sample reviews
            print("⭐ Creating reviews...")
            sample_user_ids = [uuid4() for _ in range(10)]  # Simulate 10 users

            for game_slug, game in game_objects.items():
                # Create 2-5 reviews per game
                num_reviews = min(5, max(2, int(game.trending_score / 20)))
                for i in range(num_reviews):
                    user_id = sample_user_ids[i % len(sample_user_ids)]
                    # Check if this user already reviewed this game
                    existing_reviews = len(
                        [
                            r
                            for r in session.new
                            if isinstance(r, Review)
                            and r.game_id == game.id
                            and r.user_id == user_id
                        ]
                    )
                    if existing_reviews == 0:
                        rating = max(
                            1,
                            min(
                                5,
                                int((game.metacritic_score or 75) / 20)
                                + (-1 if i % 3 == 0 else 0 if i % 2 == 0 else 1),
                            ),
                        )
                        review = Review(
                            id=uuid4(),
                            game_id=game.id,
                            user_id=user_id,
                            rating=rating,
                            title=(
                                "Great game!"
                                if rating >= 4
                                else (
                                    "Could be better"
                                    if rating >= 3
                                    else "Not impressed"
                                )
                            ),
                            content=f"This is a {'fantastic' if rating >= 4 else 'decent' if rating >= 3 else 'disappointing'} game. I {'highly recommend' if rating >= 4 else 'somewhat recommend' if rating >= 3 else 'cannot recommend'} it.",
                            is_verified_purchase=True,
                            helpful_count=max(0, rating * 2 - 2),
                            status="approved",
                        )
                        session.add(review)

            # Commit all changes
            await session.commit()
            print("✅ Seed data created successfully!")

            # Print summary
            print(
                f"""
📊 Seed Data Summary:
   • Publishers: {len(PUBLISHERS_DATA)}
   • Categories: {len(CATEGORIES_DATA) + len(SUB_CATEGORIES_DATA)}
   • Games: {len(GAMES_DATA)}
   • Inventory items: ~{len(GAMES_DATA) * 1.5:.0f}
   • Reviews: ~{len(GAMES_DATA) * 3}
            """
            )

        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating seed data: {e}")
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_seed_data())
