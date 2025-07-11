"""
Categories endpoint for Game Service API.
Provides hierarchical category browsing for shop navigation.
"""

from typing import List, Optional, Dict, Any# type: ignore
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.database import get_database_session
from app.repositories.repository_manager import create_repository_manager
from app.schemas.game import CategoryResponse

# Configure structured logging
logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=List[CategoryResponse])
async def get_categories(
    include_children: bool = Query(True, description="Include subcategories in response"),
    active_only: bool = Query(True, description="Only return active categories"),
    with_games: bool = Query(False, description="Only categories that have games"),
    limit: int = Query(100, ge=1, le=500, description="Maximum categories to return"),
    db: AsyncSession = Depends(get_database_session),
) -> List[CategoryResponse]:
    """
    Get all categories for shop navigation and filtering.
    
    This endpoint provides the complete category hierarchy used for:
    - Shop sidebar navigation
    - Category filtering in search
    - Product categorization display
    - Admin category management
    
    Returns categories with optional subcategory inclusion and game count filtering.
    """
    logger.info(
        "Fetching categories",
        include_children=include_children,
        active_only=active_only,
        with_games=with_games,
        limit=limit,
    )
    
    try:
        async with create_repository_manager(db) as repo:
            if with_games:
                # Get only categories that have active games
                categories = await repo.categories.get_categories_with_games(min_games=1)
                # Limit the results
                categories = categories[:limit]
            else:
                # Get all categories (root categories if not including children)
                if include_children:
                    categories = await repo.categories.get_all(# type: ignore
                        limit=limit,
                        order_by="display_order",
                        active_only=active_only,# type: ignore
                    )
                else:
                    # Get only root categories
                    categories = await repo.categories.get_root_categories()
                    categories = categories[:limit]
            
            logger.info("Successfully retrieved categories", count=len(categories))# type: ignore
            
            # Convert to response models
            category_responses = []
            for category in categories:# type: ignore
                # Handle children based on include_children flag
                children = []
                if include_children and hasattr(category, 'children'):# type: ignore
                    children = [
                        CategoryResponse(
                            id=child.id,# type: ignore
                            name=child.name,# type: ignore
                            slug=child.slug,# type: ignore
                            description=child.description,# type: ignore
                            icon_url=child.icon_url,# type: ignore
                            parent_id=child.parent_id,# type: ignore
                            display_order=child.display_order,# type: ignore
                            is_active=child.is_active,# type: ignore
                            created_at=child.created_at,# type: ignore
                            updated_at=child.updated_at,# type: ignore
                            children=[],  # Don't include grandchildren for performance
                        )
                        for child in category.children# type: ignore
                        if not active_only or child.is_active# type: ignore
                    ]
                
                category_responses.append(# type: ignore
                    CategoryResponse(
                        id=category.id,# type: ignore
                        name=category.name,# type: ignore
                        slug=category.slug,# type: ignore
                        description=category.description,# type: ignore
                        icon_url=category.icon_url,# type: ignore
                        parent_id=category.parent_id,# type: ignore
                        display_order=category.display_order,# type: ignore
                        is_active=category.is_active,# type: ignore
                        created_at=category.created_at,# type: ignore
                        updated_at=category.updated_at, # type: ignore
                        children=children,
                    )
                )# type: ignore
            
            return category_responses # type: ignore
            
    except Exception as e:
        logger.error("Failed to fetch categories", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve categories"
        )


@router.get("/hierarchy", response_model=List[Dict[str, Any]])
async def get_category_hierarchy(
    db: AsyncSession = Depends(get_database_session),
) -> List[Dict[str, Any]]:
    """
    Get complete category hierarchy as nested structure.
    
    Returns a tree-like structure perfect for:
    - Frontend navigation menus
    - Category selection dropdowns
    - Hierarchical displays
    - Admin category management interfaces
    
    The hierarchy includes all parent-child relationships with proper nesting.
    """
    logger.info("Fetching category hierarchy")
    
    try:
        async with create_repository_manager(db) as repo:
            # Get the complete hierarchy from repository
            hierarchy = await repo.categories.get_category_hierarchy()
            
            logger.info("Successfully retrieved category hierarchy", levels=len(hierarchy))
            
            return hierarchy
            
    except Exception as e:
        logger.error("Failed to fetch category hierarchy", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve category hierarchy"
        )


@router.get("/popular", response_model=List[Dict[str, Any]])
async def get_popular_categories(
    limit: int = Query(10, ge=1, le=50, description="Number of popular categories to return"),
    db: AsyncSession = Depends(get_database_session),
) -> List[Dict[str, Any]]:
    """
    Get most popular categories based on game count.
    
    Popular categories are determined by the number of active games in each category.
    This is useful for:
    - Homepage category highlights
    - Trending category sections
    - Category recommendations
    - Analytics and reporting
    """
    logger.info("Fetching popular categories", limit=limit)
    
    try:
        async with create_repository_manager(db) as repo:
            # Get popular categories from repository
            popular_categories = await repo.categories.get_popular_categories(limit=limit)
            
            logger.info("Successfully retrieved popular categories", count=len(popular_categories))
            
            return popular_categories
            
    except Exception as e:
        logger.error("Failed to fetch popular categories", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve popular categories"
        )


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category_details(
    category_id: UUID = Path(..., description="Category ID"),
    include_children: bool = Query(True, description="Include subcategories"),
    db: AsyncSession = Depends(get_database_session),
) -> CategoryResponse:
    """
    Get detailed information for a specific category.
    
    Returns complete category details including:
    - Basic category information (name, description, display order)
    - Parent category relationship
    - Child categories (if requested)
    - Category statistics and metadata
    """
    logger.info("Fetching category details", category_id=category_id)
    
    try:
        async with create_repository_manager(db) as repo:
            # Get category by ID with relationships
            category = await repo.categories.get_by_id(category_id)
            
            if not category:
                logger.warning("Category not found", category_id=category_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with ID {category_id} not found"
                )
            
            logger.info("Successfully retrieved category details", category_id=category_id, name=category.name)
            
            # Handle children if requested
            children = []
            if include_children and hasattr(category, 'children'):
                children = [
                    CategoryResponse(
                        id=child.id,
                        name=child.name,
                        slug=child.slug,
                        description=child.description,
                        icon_url=child.icon_url,
                        parent_id=child.parent_id,
                        display_order=child.display_order,
                        is_active=child.is_active,
                        created_at=child.created_at,
                        updated_at=child.updated_at,
                        children=[],  # Don't include grandchildren
                    )
                    for child in category.children
                    if child.is_active
                ]
            
            return CategoryResponse(
                id=category.id,
                name=category.name,
                slug=category.slug,
                description=category.description,
                icon_url=category.icon_url,
                parent_id=category.parent_id,
                display_order=category.display_order,
                is_active=category.is_active,
                created_at=category.created_at,
                updated_at=category.updated_at,
                children=children,
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error("Failed to fetch category details", category_id=category_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve category details"
        )


@router.get("/{category_id}/subcategories", response_model=List[CategoryResponse])
async def get_subcategories(
    category_id: UUID = Path(..., description="Parent category ID"),
    db: AsyncSession = Depends(get_database_session),
) -> List[CategoryResponse]:
    """
    Get all subcategories of a specific parent category.
    
    This endpoint is useful for:
    - Dynamic loading of subcategories
    - Category drill-down navigation
    - Lazy loading of category trees
    - Category management interfaces
    """
    logger.info("Fetching subcategories", parent_category_id=category_id)
    
    try:
        async with create_repository_manager(db) as repo:
            # First verify parent category exists
            parent_category = await repo.categories.get_by_id(category_id)
            if not parent_category:
                logger.warning("Parent category not found", category_id=category_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Parent category with ID {category_id} not found"
                )
            
            # Get subcategories
            subcategories = await repo.categories.get_subcategories(category_id)
            
            logger.info(
                "Successfully retrieved subcategories",
                parent_category_id=category_id,
                parent_name=parent_category.name,
                subcategory_count=len(subcategories),
            )
            
            # Convert to response models
            return [
                CategoryResponse(
                    id=subcategory.id,
                    name=subcategory.name,
                    slug=subcategory.slug,
                    description=subcategory.description,
                    icon_url=subcategory.icon_url,
                    parent_id=subcategory.parent_id,
                    display_order=subcategory.display_order,
                    is_active=subcategory.is_active,
                    created_at=subcategory.created_at,
                    updated_at=subcategory.updated_at,
                    children=[],  # Don't include grandchildren for performance
                )
                for subcategory in subcategories
            ]
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error("Failed to fetch subcategories", parent_category_id=category_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subcategories"
        )


@router.get("/{category_id}/statistics", response_model=Dict[str, Any])
async def get_category_statistics(
    category_id: UUID = Path(..., description="Category ID"),
    db: AsyncSession = Depends(get_database_session),
) -> Dict[str, Any]:
    """
    Get statistics for a specific category.
    
    Returns useful metrics including:
    - Total number of games in category
    - Number of active games
    - Number of featured games
    - Average game price
    - Category performance metrics
    
    This data is useful for analytics, reporting, and category management.
    """
    logger.info("Fetching category statistics", category_id=category_id)
    
    try:
        async with create_repository_manager(db) as repo:
            # First verify category exists
            category = await repo.categories.get_by_id(category_id)
            if not category:
                logger.warning("Category not found for statistics", category_id=category_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with ID {category_id} not found"
                )
            
            # Get category statistics
            statistics = await repo.categories.get_category_statistics(category_id)
            
            logger.info(
                "Successfully retrieved category statistics",
                category_id=category_id,
                category_name=category.name,
                total_games=statistics.get("total_games", 0),
            )
            
            # Add category information to statistics
            statistics["category"] = {
                "id": category.id,
                "name": category.name,
                "slug": category.slug,
                "is_active": category.is_active,
            }
            
            return statistics
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error("Failed to fetch category statistics", category_id=category_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve category statistics"
        )


@router.get("/search/{query}", response_model=List[CategoryResponse])
async def search_categories(
    query: str = Path(..., description="Search query for category names"),
    limit: int = Query(20, ge=1, le=100, description="Maximum categories to return"),
    db: AsyncSession = Depends(get_database_session),
) -> List[CategoryResponse]:
    """
    Search categories by name or description.
    
    This endpoint enables:
    - Category search functionality
    - Auto-complete for category selection
    - Category discovery
    - Admin category management search
    
    Searches across category names and descriptions using text matching.
    """
    logger.info("Searching categories", query=query, limit=limit)
    
    try:
        async with create_repository_manager(db) as repo:
            # Perform category search
            categories = await repo.categories.search(query_text=query, limit=limit)
            
            logger.info("Category search completed", query=query, results_count=len(categories))
            
            # Convert to response models
            return [
                CategoryResponse(
                    id=category.id,
                    name=category.name,
                    slug=category.slug,
                    description=category.description,
                    icon_url=category.icon_url,
                    parent_id=category.parent_id,
                    display_order=category.display_order,
                    is_active=category.is_active,
                    created_at=category.created_at,
                    updated_at=category.updated_at,
                    children=[],  # Don't include children in search results for performance
                )
                for category in categories
            ]
            
    except Exception as e:
        logger.error("Category search failed", query=query, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Category search operation failed"
        )
