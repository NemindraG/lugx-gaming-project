"""
Repository Manager
Provides unified access to all repositories with transaction management.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.game_repository import GameRepository
from app.repositories.publisher_repository import PublisherRepository
from app.repositories.category_repository import CategoryRepository


class RepositoryManager:
    """
    Manages all repositories and provides transaction context.
    Acts as a Unit of Work pattern implementation.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._games: Optional[GameRepository] = None
        self._publishers: Optional[PublisherRepository] = None
        self._categories: Optional[CategoryRepository] = None

    @property
    def games(self) -> GameRepository:
        """Get games repository."""
        if self._games is None:
            self._games = GameRepository(self.session)
        return self._games

    @property
    def publishers(self) -> PublisherRepository:
        """Get publishers repository."""
        if self._publishers is None:
            self._publishers = PublisherRepository(self.session)
        return self._publishers

    @property
    def categories(self) -> CategoryRepository:
        """Get categories repository."""
        if self._categories is None:
            self._categories = CategoryRepository(self.session)
        return self._categories

    async def commit(self):
        """Commit all changes."""
        await self.session.commit()

    async def rollback(self):
        """Rollback all changes."""
        await self.session.rollback()

    async def flush(self):
        """Flush changes without committing."""
        await self.session.flush()

    async def refresh(self, instance):
        """Refresh an instance from the database."""
        await self.session.refresh(instance)

    async def close(self):
        """Close the session."""
        await self.session.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()
        await self.close()


# Factory function for creating repository managers
def create_repository_manager(session: AsyncSession) -> RepositoryManager:
    """Create a repository manager with the given session."""
    return RepositoryManager(session)
