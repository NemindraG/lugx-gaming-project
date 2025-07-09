"""
Publisher Repository
Repository for publisher entities with gaming-specific queries.
"""

from typing import List, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select

from app.models.game import Publisher, Game
from app.repositories.base_repository import BaseRepository


class PublisherRepository(BaseRepository[Publisher]):
    """Repository for publisher entities."""

    def __init__(self, session):
        super().__init__(session, Publisher)

    def _apply_default_relationships(self, query: Select) -> Select:
        """Load default relationships for publishers."""
        return query.options(selectinload(Publisher.games))

    async def search(
        self, query_text: str, limit: int = 50, offset: int = 0
    ) -> List[Publisher]:
        """Search publishers by name or description."""
        query = (
            select(Publisher)
            .where(
                and_(
                    Publisher.is_active.is_(True),
                    Publisher.name.ilike(f"%{query_text}%")
                    | Publisher.description.ilike(f"%{query_text}%"),
                )
            )
            .order_by(Publisher.name)
            .limit(limit)
            .offset(offset)
        )

        query = self._apply_default_relationships(query)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_active_publishers(self, limit: int = 100) -> List[Publisher]:
        """Get all active publishers."""
        query = (
            select(Publisher)
            .where(Publisher.is_active.is_(True))
            .order_by(Publisher.name)
            .limit(limit)
        )

        query = self._apply_default_relationships(query)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_publishers_by_country(self, country: str) -> List[Publisher]:
        """Get publishers from a specific country."""
        query = (
            select(Publisher)
            .where(and_(Publisher.country == country, Publisher.is_active.is_(True)))
            .order_by(Publisher.name)
        )

        query = self._apply_default_relationships(query)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_publishers_with_games(self, min_games: int = 1) -> List[Publisher]:
        """Get publishers that have published at least min_games games."""
        query = (
            select(Publisher)
            .join(Publisher.games)
            .where(and_(Publisher.is_active.is_(True), Game.status == "active"))
            .group_by(Publisher.id)
            .having(func.count(Game.id) >= min_games)
            .order_by(func.count(Game.id).desc(), Publisher.name)
        )

        query = self._apply_default_relationships(query)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_publisher_statistics(self, publisher_id: UUID) -> Dict[str, Any]:
        """Get statistics for a specific publisher."""
        result = await self.session.execute(
            select(
                func.count(Game.id).label("total_games"),
                func.count(Game.id)
                .filter(Game.status == "active")
                .label("active_games"),
                func.count(Game.id)
                .filter(Game.featured.is_(True))
                .label("featured_games"),
                func.avg(Game.price).label("average_price"),
                func.avg(Game.metacritic_score).label("average_metacritic"),
            )
            .select_from(Game)
            .where(Game.publisher_id == publisher_id)
        )

        stats = result.first()
        return {
            "total_games": stats.total_games,
            "active_games": stats.active_games,
            "featured_games": stats.featured_games,
            "average_price": float(stats.average_price) if stats.average_price else 0,
            "average_metacritic": (
                float(stats.average_metacritic) if stats.average_metacritic else 0
            ),
        }
