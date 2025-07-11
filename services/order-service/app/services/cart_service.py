"""
Shopping cart service for Order Service.
Handles cart operations with Redis backend and game service integration.
"""

import json
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from fastapi import HTTPException, status
import structlog

from app.core.redis import RedisClient
from app.schemas.cart import (
    CartItemCreate, CartItemUpdate, CartItemResponse, 
    CartResponse, CartSummary, BulkCartUpdate,
    PromoCode, CartTransfer, CartStats
)
from app.core.service_client import ServiceClient

logger = structlog.get_logger()


class CartService:
    """Service for shopping cart operations."""
    
    def __init__(self, redis_client: RedisClient, user_id: Optional[UUID] = None, session_id: Optional[str] = None):
        self.redis = redis_client
        self.user_id = user_id
        self.session_id = session_id or str(uuid4())
        self.service_client = ServiceClient()
        
        # Set cart key based on user or session
        if user_id:
            self.cart_key = f"cart:user:{user_id}"
        else:
            self.cart_key = f"cart:session:{self.session_id}"
    
    async def add_item(self, item_create: CartItemCreate) -> CartItemResponse:
        """Add item to cart."""
        # Validate game exists and get details
        game_data = await self._get_game_details(item_create.game_id)
        if not game_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game not found"
            )
        
        # Check inventory availability
        if not await self._check_inventory(item_create.game_id, item_create.quantity):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient inventory"
            )
        
        cart = await self._get_cart()
        
        # Create cart item
        item_id = str(uuid4())
        cart_item = {
            'id': item_id,
            'game_id': str(item_create.game_id),
            'quantity': item_create.quantity,
            'price': str(item_create.price),
            'game_title': game_data['title'],
            'game_image': game_data.get('image_url'),
            'game_platform': game_data.get('platform', 'PC'),
            'discounted_price': str(game_data.get('discounted_price')) if game_data.get('discounted_price') else None,
            'is_available': True,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Check if item already exists in cart
        existing_item_key = None
        for key, item in cart.get('items', {}).items():
            if item['game_id'] == str(item_create.game_id):
                existing_item_key = key
                break
        
        if existing_item_key:
            # Update existing item quantity
            existing_item = cart['items'][existing_item_key]
            new_quantity = existing_item['quantity'] + item_create.quantity
            
            # Cap at maximum quantity
            if new_quantity > 100:
                new_quantity = 100
            
            existing_item['quantity'] = new_quantity
            existing_item['updated_at'] = datetime.now(timezone.utc).isoformat()
            cart_item = existing_item
        else:
            # Add new item
            cart['items'][item_id] = cart_item
        
        # Update cart metadata
        cart['updated_at'] = datetime.now(timezone.utc).isoformat()
        await self._save_cart(cart)
        
        # Update cart expiry
        await self._update_cart_expiry()
        
        logger.info("Item added to cart", 
                   cart_key=self.cart_key, 
                   game_id=str(item_create.game_id),
                   quantity=item_create.quantity)
        
        return CartItemResponse(**cart_item, subtotal=self._calculate_item_subtotal(cart_item))
    
    async def update_item(self, game_id: UUID, item_update: CartItemUpdate) -> Optional[CartItemResponse]:
        """Update cart item quantity."""
        cart = await self._get_cart()
        
        # Find item in cart
        item_key = None
        for key, item in cart.get('items', {}).items():
            if item['game_id'] == str(game_id):
                item_key = key
                break
        
        if not item_key:
            return None
        
        # Check inventory for new quantity
        if not await self._check_inventory(game_id, item_update.quantity):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient inventory"
            )
        
        # Update item
        cart_item = cart['items'][item_key]
        cart_item['quantity'] = item_update.quantity
        cart_item['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        # Update cart metadata
        cart['updated_at'] = datetime.now(timezone.utc).isoformat()
        await self._save_cart(cart)
        
        logger.info("Cart item updated", 
                   cart_key=self.cart_key, 
                   game_id=str(game_id),
                   new_quantity=item_update.quantity)
        
        return CartItemResponse(**cart_item, subtotal=self._calculate_item_subtotal(cart_item))
    
    async def remove_item(self, game_id: UUID) -> bool:
        """Remove item from cart."""
        cart = await self._get_cart()
        
        # Find and remove item
        item_key = None
        for key, item in cart.get('items', {}).items():
            if item['game_id'] == str(game_id):
                item_key = key
                break
        
        if not item_key:
            return False
        
        del cart['items'][item_key]
        
        # Update cart metadata
        cart['updated_at'] = datetime.now(timezone.utc).isoformat()
        await self._save_cart(cart)
        
        logger.info("Item removed from cart", 
                   cart_key=self.cart_key, 
                   game_id=str(game_id))
        
        return True
    
    async def get_cart(self) -> CartResponse:
        """Get complete cart with items and summary."""
        cart = await self._get_cart()
        
        # Convert items to response format
        cart_items = []
        for item_data in cart.get('items', {}).values():
            cart_items.append(
                CartItemResponse(**item_data, subtotal=self._calculate_item_subtotal(item_data))
            )
        
        # Calculate summary
        summary = await self._calculate_cart_summary(cart)
        
        return CartResponse(
            user_id=self.user_id,
            items=cart_items,
            summary=summary,
            created_at=datetime.fromisoformat(cart['created_at']),
            updated_at=datetime.fromisoformat(cart['updated_at']),
            expires_at=datetime.fromisoformat(cart['expires_at']) if cart.get('expires_at') else None
        )
    
    async def clear_cart(self) -> bool:
        """Clear all items from cart."""
        cart = await self._get_cart()
        cart['items'] = {}
        cart['promo_code'] = None
        cart['discount_amount'] = "0.00"
        cart['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        await self._save_cart(cart)
        
        logger.info("Cart cleared", cart_key=self.cart_key)
        return True
    
    async def apply_promo_code(self, promo_data: PromoCode) -> CartResponse:
        """Apply promo code to cart."""
        cart = await self._get_cart()
        
        # Validate promo code (this would call a promo service in production)
        discount_amount = await self._validate_promo_code(promo_data.code, cart)
        
        cart['promo_code'] = promo_data.code
        cart['discount_amount'] = str(discount_amount)
        cart['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        await self._save_cart(cart)
        
        logger.info("Promo code applied", 
                   cart_key=self.cart_key, 
                   code=promo_data.code,
                   discount=str(discount_amount))
        
        return await self.get_cart()
    
    async def remove_promo_code(self) -> CartResponse:
        """Remove promo code from cart."""
        cart = await self._get_cart()
        cart['promo_code'] = None
        cart['discount_amount'] = "0.00"
        cart['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        await self._save_cart(cart)
        
        logger.info("Promo code removed", cart_key=self.cart_key)
        return await self.get_cart()
    
    async def bulk_update(self, bulk_update: BulkCartUpdate) -> CartResponse:
        """Bulk update cart items."""
        cart = await self._get_cart()
        
        # Clear existing items
        cart['items'] = {}
        
        # Add all items
        for item_create in bulk_update.items:
            await self.add_item(item_create)
        
        logger.info("Cart bulk updated", 
                   cart_key=self.cart_key, 
                   item_count=len(bulk_update.items))
        
        return await self.get_cart()
    
    async def transfer_cart(self, target_user_id: UUID) -> bool:
        """Transfer anonymous cart to user account."""
        if self.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot transfer user cart"
            )
        
        # Get current cart
        cart = await self._get_cart()
        
        # Create new cart key for user
        user_cart_key = f"cart:user:{target_user_id}"
        
        # Check if user already has a cart
        existing_cart = await self.redis.get(user_cart_key)
        if existing_cart:
            # Merge carts (this is simplified - in production you'd handle conflicts better)
            for item_id, item_data in cart.get('items', {}).items():
                existing_cart['items'][item_id] = item_data
            
            existing_cart['updated_at'] = datetime.now(timezone.utc).isoformat()
            await self.redis.set(user_cart_key, existing_cart, expires=86400 * 7)  # 7 days
        else:
            # Transfer cart directly
            await self.redis.set(user_cart_key, cart, expires=86400 * 7)  # 7 days
        
        # Remove old cart
        await self.redis.delete(self.cart_key)
        
        logger.info("Cart transferred to user", 
                   from_key=self.cart_key, 
                   to_user=str(target_user_id))
        
        return True
    
    async def get_cart_stats(self) -> CartStats:
        """Get cart statistics (admin function)."""
        # This would aggregate stats from multiple carts
        # For now, return dummy data
        return CartStats(
            total_active_carts=0,
            total_items_in_carts=0,
            average_cart_value=Decimal("0.00"),
            abandoned_carts_count=0,
            conversion_rate=Decimal("0.0000")
        )
    
    async def _get_cart(self) -> Dict[str, Any]:
        """Get cart data from Redis."""
        cart = await self.redis.get(self.cart_key)
        
        if not cart:
            # Create new cart
            cart = {
                'user_id': str(self.user_id) if self.user_id else None,
                'session_id': self.session_id,
                'items': {},
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'expires_at': None,
                'promo_code': None,
                'discount_amount': "0.00"
            }
        
        return cart
    
    async def _save_cart(self, cart: Dict[str, Any]) -> None:
        """Save cart data to Redis."""
        # Set expiry: 24 hours for guest carts, 7 days for user carts
        expires = 86400 if not self.user_id else 86400 * 7
        await self.redis.set(self.cart_key, cart, expires=expires)
    
    async def _update_cart_expiry(self) -> None:
        """Update cart expiry time."""
        expires = 86400 if not self.user_id else 86400 * 7
        await self.redis.expire(self.cart_key, expires)
    
    async def _get_game_details(self, game_id: UUID) -> Optional[Dict[str, Any]]:
        """Get game details from Game Service."""
        try:
            response = await self.service_client.get(f"game-service/api/v1/games/{game_id}")
            return response
        except Exception as e:
            logger.error("Failed to get game details", game_id=str(game_id), error=str(e))
            return None
    
    async def _check_inventory(self, game_id: UUID, quantity: int) -> bool:
        """Check if sufficient inventory is available."""
        try:
            response = await self.service_client.get(f"game-service/api/v1/games/{game_id}/inventory")
            available_quantity = response.get('available_quantity', 0)
            return available_quantity >= quantity
        except Exception as e:
            logger.error("Failed to check inventory", game_id=str(game_id), error=str(e))
            return False
    
    async def _validate_promo_code(self, code: str, cart: Dict[str, Any]) -> Decimal:
        """Validate promo code and return discount amount."""
        # This would call a promo/discount service in production
        # For now, return a dummy discount
        if code.upper() == "SAVE10":
            subtotal = self._calculate_cart_subtotal(cart)
            return subtotal * Decimal("0.10")  # 10% discount
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid promo code"
        )
    
    def _calculate_item_subtotal(self, item_data: Dict[str, Any]) -> Decimal:
        """Calculate subtotal for a cart item."""
        price = Decimal(item_data.get('discounted_price') or item_data['price'])
        quantity = item_data['quantity']
        return price * quantity
    
    def _calculate_cart_subtotal(self, cart: Dict[str, Any]) -> Decimal:
        """Calculate cart subtotal."""
        subtotal = Decimal("0.00")
        for item_data in cart.get('items', {}).values():
            subtotal += self._calculate_item_subtotal(item_data)
        return subtotal
    
    async def _calculate_cart_summary(self, cart: Dict[str, Any]) -> CartSummary:
        """Calculate cart summary."""
        total_items = sum(item['quantity'] for item in cart.get('items', {}).values())
        total_amount = self._calculate_cart_subtotal(cart)
        discount_amount = Decimal(cart.get('discount_amount', '0.00'))
        
        # Calculate tax (this would be based on user location in production)
        tax_rate = Decimal("0.08")  # 8% tax
        tax_amount = (total_amount - discount_amount) * tax_rate
        
        final_amount = total_amount - discount_amount + tax_amount
        
        return CartSummary(
            total_items=total_items,
            total_amount=total_amount,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            final_amount=final_amount
        )