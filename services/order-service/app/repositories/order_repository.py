"""
Order repository for Order Service.
Handles order and order item data access operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog

from app.models.order import Order, OrderItem
from app.repositories.base_repository import BaseRepository

logger = structlog.get_logger()


class OrderRepository(BaseRepository[Order]):
    """Repository for order data access."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Order)
    
    async def find_by_id_and_user(self, order_id: UUID, user_id: UUID) -> Optional[Order]:
        """Find order by ID and user ID."""
        query = select(Order).where(
            and_(Order.id == order_id, Order.user_id == user_id)
        ).options(selectinload(Order.items))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def find_by_user(
        self, 
        user_id: UUID, 
        limit: int = 20, 
        offset: int = 0,
        status: Optional[str] = None,
        payment_status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Order]:
        """Find orders for user with filtering and pagination."""
        query = select(Order).where(Order.user_id == user_id)
        
        # Apply filters
        if status:
            query = query.where(Order.status == status)
        
        if payment_status:
            query = query.where(Order.payment_status == payment_status)
        
        if start_date:
            query = query.where(Order.created_at >= start_date)
        
        if end_date:
            query = query.where(Order.created_at <= end_date)
        
        # Order by most recent first
        query = query.order_by(desc(Order.created_at))
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        # Include order items
        query = query.options(selectinload(Order.items))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def find_by_order_number(self, order_number: str) -> Optional[Order]:
        """Find order by order number."""
        query = select(Order).where(Order.order_number == order_number).options(
            selectinload(Order.items)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_order_count(self, user_id: UUID) -> int:
        """Get total order count for user."""
        query = select(func.count()).select_from(Order).where(Order.user_id == user_id)
        result = await self.session.scalar(query)
        return result or 0
    
    async def get_user_order_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Get order statistics for user."""
        # Total orders
        total_orders = await self.session.scalar(
            select(func.count()).select_from(Order).where(Order.user_id == user_id)
        )
        
        # Orders by status
        pending_orders = await self.session.scalar(
            select(func.count()).select_from(Order).where(
                and_(Order.user_id == user_id, Order.status == 'pending')
            )
        )
        
        completed_orders = await self.session.scalar(
            select(func.count()).select_from(Order).where(
                and_(Order.user_id == user_id, Order.status.in_(['delivered', 'completed']))
            )
        )
        
        cancelled_orders = await self.session.scalar(
            select(func.count()).select_from(Order).where(
                and_(Order.user_id == user_id, Order.status == 'cancelled')
            )
        )
        
        # Total spent
        total_spent = await self.session.scalar(
            select(func.sum(Order.total_amount)).where(
                and_(
                    Order.user_id == user_id,
                    Order.payment_status == 'captured'
                )
            )
        )
        
        return {
            "total_orders": total_orders or 0,
            "pending_orders": pending_orders or 0,
            "completed_orders": completed_orders or 0,
            "cancelled_orders": cancelled_orders or 0,
            "total_spent": float(total_spent or 0)
        }
    
    async def search_orders(
        self,
        search_term: Optional[str] = None,
        status: Optional[str] = None,
        payment_status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Order]:
        """Search orders with filters (admin function)."""
        query = select(Order)
        
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.where(
                or_(
                    Order.order_number.ilike(search_pattern),
                    Order.notes.ilike(search_pattern)
                )
            )
        
        if status:
            query = query.where(Order.status == status)
        
        if payment_status:
            query = query.where(Order.payment_status == payment_status)
        
        if start_date:
            query = query.where(Order.created_at >= start_date)
        
        if end_date:
            query = query.where(Order.created_at <= end_date)
        
        query = query.order_by(desc(Order.created_at))
        query = query.limit(limit).offset(offset)
        query = query.options(selectinload(Order.items))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_order_items(self, order_id: UUID) -> List[OrderItem]:
        """Get all items for an order."""
        query = select(OrderItem).where(OrderItem.order_id == order_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create_order_item(self, **kwargs) -> OrderItem:
        """Create a new order item."""
        item = OrderItem(**kwargs)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item


class OrderItemRepository(BaseRepository[OrderItem]):
    """Repository for order item data access."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, OrderItem)
    
    async def find_by_order(self, order_id: UUID) -> List[OrderItem]:
        """Find all items for an order."""
        query = select(OrderItem).where(OrderItem.order_id == order_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def find_by_game(self, game_id: UUID) -> List[OrderItem]:
        """Find all order items for a specific game."""
        query = select(OrderItem).where(OrderItem.game_id == game_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_item_sales_stats(self, game_id: UUID) -> Dict[str, Any]:
        """Get sales statistics for a game."""
        # Total quantity sold
        total_sold = await self.session.scalar(
            select(func.sum(OrderItem.quantity)).where(OrderItem.game_id == game_id)
        )
        
        # Total revenue
        total_revenue = await self.session.scalar(
            select(func.sum(OrderItem.unit_price * OrderItem.quantity)).where(
                OrderItem.game_id == game_id
            )
        )
        
        # Number of orders containing this item
        order_count = await self.session.scalar(
            select(func.count(func.distinct(OrderItem.order_id))).where(
                OrderItem.game_id == game_id
            )
        )
        
        return {
            "total_sold": int(total_sold or 0),
            "total_revenue": float(total_revenue or 0),
            "order_count": int(order_count or 0)
        }