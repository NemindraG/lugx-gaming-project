"""
Game Repository
Specialized repository for game entities with advanced querying capabilities.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal

from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game, Category, Publisher, GameCategory, Inventory, Review
from app.repositories.base_repository import BaseRepository


class GameRepository(BaseRepository[Game]):
    """Repository for game entities with specialized gaming queries."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Game)

    def _apply_default_relationships(self, query: Select[Any]) -> Select[Any]:
        """Load default relationships for games."""
        return query.options(
            selectinload(Game.publisher),
            selectinload(Game.game_categories).selectinload(GameCategory.category),
            selectinload(Game.inventory),
            selectinload(Game.reviews),
        )

    async def search(
        self,
        query_text: str,
        limit: int = 50,
        offset: int = 0,
        category_filter: Optional[str] = None,
        price_range: Optional[Dict[str, Decimal]] = None,
        platforms: Optional[List[str]] = None,
    ) -> List[Game]:
        """
        Full-text search for games with filters.
        Uses PostgreSQL's full-text search capabilities.
        """
        query = select(Game)

        # Full-text search
        if query_text:
            # Use PostgreSQL's full-text search
            search_query = func.plainto_tsquery("english", query_text)
            query = query.where(
                or_(
                    Game.search_vector.op("@@")(search_query),
                    Game.title.ilike(f"%{query_text}%"),
                    Game.description.ilike(f"%{query_text}%"),
                )
            )

        # Category filter
        if category_filter:
            query = (
                query.join(Game.game_categories)
                .join(GameCategory.category)
                .where(Category.slug == category_filter)
            )

        # Price range filter
        if price_range:
            if "min" in price_range:
                query = query.where(Game.price >= price_range["min"])
            if "max" in price_range:
                query = query.where(Game.price <= price_range["max"])

        # Platform filter
        if platforms:
            query = query.where(Game.platform.op("&&")(platforms))

        # Only active games
        query = query.where(Game.status == "active")

        # Apply relationships and pagination
        query = self._apply_default_relationships(query)
        query = query.limit(limit).offset(offset)

        # Order by relevance (trending score for now)
        query = query.order_by(Game.trending_score.desc(), Game.created_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_featured_games(self, limit: int = 10) -> List[Game]:
        """Get featured games for homepage."""
        query = (
            select(Game)
            .where(and_(Game.featured.is_(True), Game.status == "active"))
            .order_by(Game.trending_score.desc())
            .limit(limit)
        )

        query = self._apply_default_relationships(query)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_trending_games(self, limit: int = 20) -> List[Game]:
        """Get trending games based on trending score."""
        query = (
            select(Game)
            .where(Game.status == "active")
            .order_by(Game.trending_score.desc(), Game.created_at.desc())
            .limit(limit)
        )

        query = self._apply_default_relationships(query)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_games_on_sale(self, limit: int = 50) -> List[Game]:
        """Get games currently on sale."""
        query = (
            select(Game)
            .where(and_(Game.discount_percentage > 0, Game.status == "active"))
            .order_by(Game.discount_percentage.desc(), Game.trending_score.desc())
            .limit(limit)
        )

        query = self._apply_default_relationships(query)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_games_by_category(
        self,
        category_slug: str,
        limit: int = 50,
        offset: int = 0,
        include_subcategories: bool = True,
    ) -> List[Game]:
        """Get games by category with optional subcategory inclusion."""
        query = select(Game).join(Game.game_categories).join(GameCategory.category)

        if include_subcategories:
            # Include parent category and all subcategories
            subquery = select(Category.id).where(
                or_(
                    Category.slug == category_slug,
                    Category.parent_id.in_(
                        select(Category.id).where(Category.slug == category_slug)
                    ),
                )
            )
            query = query.where(Category.id.in_(subquery))
        else:
            query = query.where(Category.slug == category_slug)

        query = query.where(Game.status == "active")
        query = query.order_by(Game.trending_score.desc())
        query = query.limit(limit).offset(offset)

        query = self._apply_default_relationships(query)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_games_by_publisher(
        self, publisher_slug: str, limit: int = 50, offset: int = 0
    ) -> List[Game]:
        """Get games by publisher."""
        query = (
            select(Game)
            .join(Game.publisher)
            .where(and_(Publisher.slug == publisher_slug, Game.status == "active"))
            .order_by(Game.release_date.desc())
            .limit(limit)
            .offset(offset)
        )

        query = self._apply_default_relationships(query)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_similar_games(self, game_id: UUID, limit: int = 10) -> List[Game]:
        """Get similar games based on categories and publisher."""
        # Get the reference game
        reference_game = await self.get_by_id(game_id)
        if not reference_game:
            return []

        # Get game categories
        category_ids = [gc.category_id for gc in reference_game.game_categories]

        query = (
            select(Game)
            .where(
                and_(
                    Game.id != game_id,
                    Game.status == "active",
                    or_(
                        # Same publisher
                        Game.publisher_id == reference_game.publisher_id,
                        # Same categories
                        Game.game_categories.any(
                            GameCategory.category_id.in_(category_ids)
                        ),
                    ),
                )
            )
            .order_by(Game.trending_score.desc())
            .limit(limit)
        )

        query = self._apply_default_relationships(query)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_new_releases(self, days: int = 30, limit: int = 20) -> List[Game]:
        """Get recently released games."""
        cutoff_date = func.now() - text(f"INTERVAL '{days} days'")

        query = (
            select(Game)
            .where(and_(Game.release_date >= cutoff_date, Game.status == "active"))
            .order_by(Game.release_date.desc(), Game.trending_score.desc())
            .limit(limit)
        )

        query = self._apply_default_relationships(query)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_games_with_inventory(
        self, inventory_type: str = "digital", in_stock_only: bool = True
    ) -> List[Game]:
        """Get games with available inventory."""
        query = (
            select(Game)
            .join(Game.inventory)
            .where(Inventory.inventory_type == inventory_type)
        )

        if in_stock_only:
            query = query.where(
                Inventory.quantity_available > Inventory.quantity_reserved
            )

        query = query.where(Game.status == "active")
        query = query.order_by(Game.trending_score.desc())

        query = self._apply_default_relationships(query)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_games_by_price_range(
        self, min_price: Decimal, max_price: Decimal, limit: int = 50
    ) -> List[Game]:
        """Get games within a specific price range."""
        query = (
            select(Game)
            .where(
                and_(
                    Game.price >= min_price,
                    Game.price <= max_price,
                    Game.status == "active",
                )
            )
            .order_by(Game.trending_score.desc())
            .limit(limit)
        )

        query = self._apply_default_relationships(query)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_top_rated_games(self, limit: int = 20) -> List[Game]:
        """Get top-rated games based on reviews."""
        query = (
            select(Game)
            .join(Game.reviews)
            .where(and_(Game.status == "active", Review.status == "approved"))
            .group_by(Game.id)
            .having(func.count(Review.id) >= 3)  # At least 3 reviews
            .order_by(func.avg(Review.rating).desc(), func.count(Review.id).desc())
            .limit(limit)
        )

        query = self._apply_default_relationships(query)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_games_by_metacritic_score(
        self, min_score: int = 80, limit: int = 30
    ) -> List[Game]:
        """Get games with high Metacritic scores."""
        query = (
            select(Game)
            .where(and_(Game.metacritic_score >= min_score, Game.status == "active"))
            .order_by(Game.metacritic_score.desc(), Game.trending_score.desc())
            .limit(limit)
        )

        query = self._apply_default_relationships(query)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_trending_score(self, game_id: UUID, score: int) -> Optional[Game]:
        """Update a game's trending score."""
        return await self.update(game_id, trending_score=score)

    async def get_game_statistics(self) -> Dict[str, Any]:
        """Get overall game statistics."""
        result = await self.session.execute(
            select(
                func.count(Game.id).label("total_games"),
                func.count(Game.id)
                .filter(Game.status == "active")  # type: ignore
                .label("active_games"),
                func.count(Game.id)
                .filter(Game.featured.is_(True))  # type: ignore
                .label("featured_games"),
                func.count(Game.id)
                .filter(Game.discount_percentage > 0)  # type: ignore
                .label("games_on_sale"),
                func.avg(Game.price).label("average_price"),
                func.avg(Game.metacritic_score).label("average_metacritic"),
            )
        )

        stats = result.first()
        if not stats:
            return {
                "total_games": 0,
                "active_games": 0,
                "featured_games": 0,
                "games_on_sale": 0,
                "average_price": 0.0,
                "average_metacritic": 0.0,
            }
        return {
            "total_games": stats.total_games or 0,
            "active_games": stats.active_games or 0,
            "featured_games": stats.featured_games or 0,
            "games_on_sale": stats.games_on_sale or 0,
            "average_price": float(stats.average_price) if stats.average_price else 0.0,
            "average_metacritic": (
                float(stats.average_metacritic) if stats.average_metacritic else 0.0
            ),
        }
