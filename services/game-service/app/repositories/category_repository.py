"""
Category Repository
Repository for category entities with hierarchical support.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select

from app.models.game import Category, Game, GameCategory
from app.repositories.base_repository import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    """Repository for category entities with hierarchical queries."""
    
    def __init__(self, session):
        super().__init__(session, Category)
    
    def _apply_default_relationships(self, query: Select) -> Select:
        """Load default relationships for categories."""
        return query.options(
            selectinload(Category.parent),
            selectinload(Category.children)
        )
    
    async def search(
        self, 
        query_text: str, 
        limit: int = 50,
        offset: int = 0
    ) -> List[Category]:
        """Search categories by name or description."""
        query = select(Category).where(
            and_(
                Category.is_active == True,
                Category.name.ilike(f'%{query_text}%') |
                Category.description.ilike(f'%{query_text}%')
            )
        ).order_by(
            Category.display_order,
            Category.name
        ).limit(limit).offset(offset)
        
        query = self._apply_default_relationships(query)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_root_categories(self) -> List[Category]:
        """Get all root categories (no parent)."""
        query = select(Category).where(
            and_(
                Category.parent_id.is_(None),
                Category.is_active == True
            )
        ).order_by(
            Category.display_order,
            Category.name
        )
        
        query = self._apply_default_relationships(query)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_subcategories(self, parent_id: UUID) -> List[Category]:
        """Get subcategories of a specific parent category."""
        query = select(Category).where(
            and_(
                Category.parent_id == parent_id,
                Category.is_active == True
            )
        ).order_by(
            Category.display_order,
            Category.name
        )
        
        query = self._apply_default_relationships(query)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_category_hierarchy(self) -> List[Dict[str, Any]]:
        """Get complete category hierarchy as nested structure."""
        # Get all categories
        categories = await self.get_all(
            limit=1000,  # Assume we don't have more than 1000 categories
            order_by='display_order'
        )
        
        # Build hierarchy
        category_map = {cat.id: cat for cat in categories}
        hierarchy = []
        
        for category in categories:
            if category.parent_id is None:
                # Root category
                cat_dict = {
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                    'description': category.description,
                    'display_order': category.display_order,
                    'children': []
                }
                
                # Add children
                for child in categories:
                    if child.parent_id == category.id:
                        cat_dict['children'].append({
                            'id': child.id,
                            'name': child.name,
                            'slug': child.slug,
                            'description': child.description,
                            'display_order': child.display_order
                        })
                
                # Sort children by display_order
                cat_dict['children'].sort(key=lambda x: x['display_order'])
                hierarchy.append(cat_dict)
        
        return hierarchy
    
    async def get_categories_with_games(self, min_games: int = 1) -> List[Category]:
        """Get categories that have at least min_games games."""
        query = select(Category).join(
            GameCategory, Category.id == GameCategory.category_id
        ).join(
            Game, GameCategory.game_id == Game.id
        ).where(
            and_(
                Category.is_active == True,
                Game.status == 'active'
            )
        ).group_by(Category.id).having(
            func.count(Game.id) >= min_games
        ).order_by(
            func.count(Game.id).desc(),
            Category.display_order
        )
        
        query = self._apply_default_relationships(query)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_category_statistics(self, category_id: UUID) -> Dict[str, Any]:
        """Get statistics for a specific category."""
        result = await self.session.execute(
            select(
                func.count(Game.id).label('total_games'),
                func.count(Game.id).filter(Game.status == 'active').label('active_games'),
                func.count(Game.id).filter(Game.featured == True).label('featured_games'),
                func.avg(Game.price).label('average_price')
            ).select_from(
                Game
            ).join(
                GameCategory, Game.id == GameCategory.game_id
            ).where(
                GameCategory.category_id == category_id
            )
        )
        
        stats = result.first()
        return {
            'total_games': stats.total_games,
            'active_games': stats.active_games,
            'featured_games': stats.featured_games,
            'average_price': float(stats.average_price) if stats.average_price else 0
        }
    
    async def get_popular_categories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular categories based on game count."""
        result = await self.session.execute(
            select(
                Category.id,
                Category.name,
                Category.slug,
                func.count(Game.id).label('game_count')
            ).select_from(
                Category
            ).join(
                GameCategory, Category.id == GameCategory.category_id
            ).join(
                Game, GameCategory.game_id == Game.id
            ).where(
                and_(
                    Category.is_active == True,
                    Game.status == 'active'
                )
            ).group_by(
                Category.id, Category.name, Category.slug
            ).order_by(
                func.count(Game.id).desc()
            ).limit(limit)
        )
        
        return [
            {
                'id': row.id,
                'name': row.name,
                'slug': row.slug,
                'game_count': row.game_count
            }
            for row in result.fetchall()
        ]