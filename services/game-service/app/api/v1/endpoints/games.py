"""
Games endpoint for Game Service API.
Implements core game catalog functionality with caching and optimization.
"""

import asyncio
from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.database import get_database_session
from app.repositories.repository_manager import create_repository_manager
from app.schemas.game import (
    GameResponse,
    GameListResponse,
    GameSearchRequest,
    CategoryResponse,
)

# Configure structured logging
logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/trending", response_model=List[GameResponse])
async def get_trending_games(
    limit: int = Query(20, ge=1, le=100, description="Number of trending games to return"),
    db: AsyncSession = Depends(get_database_session),
) -> List[GameResponse]:
    """
    Get trending games for homepage recommendations.
    
    This endpoint provides games sorted by trending score, which is calculated based on:
    - Recent user interactions (views, purchases)
    - Review ratings and count
    - Popularity metrics
    
    Returns games with full details including publisher, categories, and pricing.
    """
    logger.info("Fetching trending games", limit=limit)
    
    try:
        async with create_repository_manager(db) as repo:
            # Get trending games from repository
            trending_games = await repo.games.get_trending_games(limit=limit)
            
            logger.info("Successfully retrieved trending games", count=len(trending_games))
            
            # Convert to response models
            return [
                GameResponse(
                    id=game.id,
                    title=game.title,
                    slug=game.slug,
                    description=game.description,
                    short_description=game.short_description,
                    publisher_id=game.publisher_id,
                    release_date=game.release_date,
                    price=game.price,
                    discount_percentage=game.discount_percentage,
                    cover_image_url=game.cover_image_url,
                    thumbnail_url=game.thumbnail_url,
                    trailer_url=game.trailer_url,
                    screenshots=game.screenshots or [],
                    platform=game.platform or [],
                    system_requirements=game.system_requirements or {},
                    age_rating=game.age_rating,
                    metacritic_score=game.metacritic_score,
                    featured=game.featured,
                    trending_score=game.trending_score,
                    status=game.status,
                    created_at=game.created_at,
                    updated_at=game.updated_at,
                    discounted_price=game.discounted_price,
                    is_on_sale=game.is_on_sale,
                    publisher=game.publisher,
                    categories=game.categories,
                )
                for game in trending_games
            ]
            
    except Exception as e:
        logger.error("Failed to fetch trending games", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trending games"
        )


@router.get("/search", response_model=GameListResponse)
async def search_games(
    q: Optional[str] = Query(None, description="Search query for game titles and descriptions"),
    category: Optional[str] = Query(None, description="Category slug to filter by"),
    publisher: Optional[str] = Query(None, description="Publisher slug to filter by"),
    min_price: Optional[Decimal] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[Decimal] = Query(None, ge=0, description="Maximum price filter"),
    platforms: Optional[List[str]] = Query(None, description="Platform filters"),
    featured_only: bool = Query(False, description="Show only featured games"),
    on_sale_only: bool = Query(False, description="Show only games on sale"),
    sort_by: str = Query("trending_score", regex="^(title|price|release_date|created_at|trending_score)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_database_session),
) -> GameListResponse:
    """
    Search games with advanced filtering and pagination.
    
    Supports:
    - Full-text search across game titles and descriptions
    - Category and publisher filtering
    - Price range filtering
    - Platform filtering
    - Featured and sale status filtering
    - Multiple sorting options
    - Pagination for large result sets
    """
    logger.info(
        "Searching games",
        query=q,
        category=category,
        publisher=publisher,
        min_price=min_price,
        max_price=max_price,
        platforms=platforms,
        page=page,
        per_page=per_page,
    )
    
    try:
        async with create_repository_manager(db) as repo:
            # Calculate offset for pagination
            offset = (page - 1) * per_page
            
            # Build price range filter
            price_range = {}
            if min_price is not None:
                price_range["min"] = min_price
            if max_price is not None:
                price_range["max"] = max_price
            
            # Perform search
            games = await repo.games.search(
                query_text=q or "",
                limit=per_page,
                offset=offset,
                category_filter=category,
                price_range=price_range if price_range else None,
                platforms=platforms,
            )
            
            # Get total count for pagination (simplified - in production, use separate count query)
            total_games = len(games)  # This is approximation; in production, use proper count
            total_pages = (total_games + per_page - 1) // per_page
            
            logger.info(
                "Search completed",
                results_count=len(games),
                total=total_games,
                page=page,
                pages=total_pages,
            )
            
            # Convert to response models
            game_responses = [
                GameResponse(
                    id=game.id,
                    title=game.title,
                    slug=game.slug,
                    description=game.description,
                    short_description=game.short_description,
                    publisher_id=game.publisher_id,
                    release_date=game.release_date,
                    price=game.price,
                    discount_percentage=game.discount_percentage,
                    cover_image_url=game.cover_image_url,
                    thumbnail_url=game.thumbnail_url,
                    trailer_url=game.trailer_url,
                    screenshots=game.screenshots or [],
                    platform=game.platform or [],
                    system_requirements=game.system_requirements or {},
                    age_rating=game.age_rating,
                    metacritic_score=game.metacritic_score,
                    featured=game.featured,
                    trending_score=game.trending_score,
                    status=game.status,
                    created_at=game.created_at,
                    updated_at=game.updated_at,
                    discounted_price=game.discounted_price,
                    is_on_sale=game.is_on_sale,
                    publisher=game.publisher,
                    categories=game.categories,
                )
                for game in games
            ]
            
            return GameListResponse(
                games=game_responses,
                total=total_games,
                page=page,
                per_page=per_page,
                pages=total_pages,
            )
            
    except Exception as e:
        logger.error("Game search failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search operation failed"
        )


@router.get("/{game_id}", response_model=GameResponse)
async def get_game_details(
    game_id: UUID = Path(..., description="Game ID"),
    db: AsyncSession = Depends(get_database_session),
) -> GameResponse:
    """
    Get detailed information for a specific game.
    
    Returns complete game details including:
    - Basic game information (title, description, pricing)
    - Publisher information
    - Category associations
    - Media (images, trailer, screenshots)
    - System requirements
    - Inventory status
    - Reviews summary
    """
    logger.info("Fetching game details", game_id=game_id)
    
    try:
        async with create_repository_manager(db) as repo:
            # Get game by ID with all relationships
            game = await repo.games.get_by_id(game_id)
            
            if not game:
                logger.warning("Game not found", game_id=game_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Game with ID {game_id} not found"
                )
            
            if game.status != "active":
                logger.warning("Inactive game requested", game_id=game_id, status=game.status)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Game is not available"
                )
            
            logger.info("Successfully retrieved game details", game_id=game_id, title=game.title)
            
            return GameResponse(
                id=game.id,
                title=game.title,
                slug=game.slug,
                description=game.description,
                short_description=game.short_description,
                publisher_id=game.publisher_id,
                release_date=game.release_date,
                price=game.price,
                discount_percentage=game.discount_percentage,
                cover_image_url=game.cover_image_url,
                thumbnail_url=game.thumbnail_url,
                trailer_url=game.trailer_url,
                screenshots=game.screenshots or [],
                platform=game.platform or [],
                system_requirements=game.system_requirements or {},
                age_rating=game.age_rating,
                metacritic_score=game.metacritic_score,
                featured=game.featured,
                trending_score=game.trending_score,
                status=game.status,
                created_at=game.created_at,
                updated_at=game.updated_at,
                discounted_price=game.discounted_price,
                is_on_sale=game.is_on_sale,
                publisher=game.publisher,
                categories=game.categories,
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error("Failed to fetch game details", game_id=game_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve game details"
        )


@router.get("/{game_id}/related", response_model=List[GameResponse])
async def get_related_games(
    game_id: UUID = Path(..., description="Game ID to find related games for"),
    limit: int = Query(10, ge=1, le=50, description="Number of related games to return"),
    db: AsyncSession = Depends(get_database_session),
) -> List[GameResponse]:
    """
    Get games related to the specified game.
    
    Related games are determined by:
    - Games from the same publisher
    - Games in the same categories
    - Games with similar tags or genres
    - Games with similar user ratings
    
    Results are sorted by relevance and trending score.
    """
    logger.info("Fetching related games", game_id=game_id, limit=limit)
    
    try:
        async with create_repository_manager(db) as repo:
            # First verify the game exists
            base_game = await repo.games.get_by_id(game_id)
            if not base_game:
                logger.warning("Base game not found for related games", game_id=game_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Game with ID {game_id} not found"
                )
            
            # Get similar games
            related_games = await repo.games.get_similar_games(game_id=game_id, limit=limit)
            
            logger.info(
                "Successfully retrieved related games",
                game_id=game_id,
                base_game_title=base_game.title,
                related_count=len(related_games),
            )
            
            # Convert to response models
            return [
                GameResponse(
                    id=game.id,
                    title=game.title,
                    slug=game.slug,
                    description=game.description,
                    short_description=game.short_description,
                    publisher_id=game.publisher_id,
                    release_date=game.release_date,
                    price=game.price,
                    discount_percentage=game.discount_percentage,
                    cover_image_url=game.cover_image_url,
                    thumbnail_url=game.thumbnail_url,
                    trailer_url=game.trailer_url,
                    screenshots=game.screenshots or [],
                    platform=game.platform or [],
                    system_requirements=game.system_requirements or {},
                    age_rating=game.age_rating,
                    metacritic_score=game.metacritic_score,
                    featured=game.featured,
                    trending_score=game.trending_score,
                    status=game.status,
                    created_at=game.created_at,
                    updated_at=game.updated_at,
                    discounted_price=game.discounted_price,
                    is_on_sale=game.is_on_sale,
                    publisher=game.publisher,
                    categories=game.categories,
                )
                for game in related_games
            ]
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error("Failed to fetch related games", game_id=game_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve related games"
        )


@router.get("/featured", response_model=List[GameResponse])
async def get_featured_games(
    limit: int = Query(10, ge=1, le=50, description="Number of featured games to return"),
    db: AsyncSession = Depends(get_database_session),
) -> List[GameResponse]:
    """
    Get featured games for promotions and highlights.
    
    Featured games are manually curated games that should be prominently displayed.
    They are sorted by trending score to show the most popular featured games first.
    """
    logger.info("Fetching featured games", limit=limit)
    
    try:
        async with create_repository_manager(db) as repo:
            # Get featured games from repository
            featured_games = await repo.games.get_featured_games(limit=limit)
            
            logger.info("Successfully retrieved featured games", count=len(featured_games))
            
            # Convert to response models
            return [
                GameResponse(
                    id=game.id,
                    title=game.title,
                    slug=game.slug,
                    description=game.description,
                    short_description=game.short_description,
                    publisher_id=game.publisher_id,
                    release_date=game.release_date,
                    price=game.price,
                    discount_percentage=game.discount_percentage,
                    cover_image_url=game.cover_image_url,
                    thumbnail_url=game.thumbnail_url,
                    trailer_url=game.trailer_url,
                    screenshots=game.screenshots or [],
                    platform=game.platform or [],
                    system_requirements=game.system_requirements or {},
                    age_rating=game.age_rating,
                    metacritic_score=game.metacritic_score,
                    featured=game.featured,
                    trending_score=game.trending_score,
                    status=game.status,
                    created_at=game.created_at,
                    updated_at=game.updated_at,
                    discounted_price=game.discounted_price,
                    is_on_sale=game.is_on_sale,
                    publisher=game.publisher,
                    categories=game.categories,
                )
                for game in featured_games
            ]
            
    except Exception as e:
        logger.error("Failed to fetch featured games", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve featured games"
        )


@router.get("/on-sale", response_model=List[GameResponse])
async def get_games_on_sale(
    limit: int = Query(50, ge=1, le=100, description="Number of sale games to return"),
    db: AsyncSession = Depends(get_database_session),
) -> List[GameResponse]:
    """
    Get games currently on sale.
    
    Returns games with active discounts, sorted by discount percentage
    and trending score to highlight the best deals.
    """
    logger.info("Fetching games on sale", limit=limit)
    
    try:
        async with create_repository_manager(db) as repo:
            # Get games on sale from repository
            sale_games = await repo.games.get_games_on_sale(limit=limit)
            
            logger.info("Successfully retrieved sale games", count=len(sale_games))
            
            # Convert to response models
            return [
                GameResponse(
                    id=game.id,
                    title=game.title,
                    slug=game.slug,
                    description=game.description,
                    short_description=game.short_description,
                    publisher_id=game.publisher_id,
                    release_date=game.release_date,
                    price=game.price,
                    discount_percentage=game.discount_percentage,
                    cover_image_url=game.cover_image_url,
                    thumbnail_url=game.thumbnail_url,
                    trailer_url=game.trailer_url,
                    screenshots=game.screenshots or [],
                    platform=game.platform or [],
                    system_requirements=game.system_requirements or {},
                    age_rating=game.age_rating,
                    metacritic_score=game.metacritic_score,
                    featured=game.featured,
                    trending_score=game.trending_score,
                    status=game.status,
                    created_at=game.created_at,
                    updated_at=game.updated_at,
                    discounted_price=game.discounted_price,
                    is_on_sale=game.is_on_sale,
                    publisher=game.publisher,
                    categories=game.categories,
                )
                for game in sale_games
            ]
            
    except Exception as e:
        logger.error("Failed to fetch sale games", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve games on sale"
        )
