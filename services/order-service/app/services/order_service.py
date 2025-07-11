"""
Order service for Order Service.
Handles order processing, payment integration, and order management.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.order import Order, OrderItem
from app.repositories.order_repository import OrderRepository
from app.services.cart_service import CartService
from app.services.user_service import UserService
from app.services.payment_service import PaymentService
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse, PaymentRequest
from app.core.redis import RedisClient

logger = structlog.get_logger()


class OrderService:
    """Service for order operations."""
    
    def __init__(self, session: AsyncSession, redis_client: RedisClient):
        self.session = session
        self.redis = redis_client
        self.order_repo = OrderRepository(session)
        self.user_service = UserService(session)
        self.payment_service = PaymentService()
    
    async def create_order_from_cart(self, user_id: UUID, order_create: OrderCreate) -> OrderResponse:
        """Create order from user's cart."""
        # Get user's cart
        cart_service = CartService(self.redis, user_id)
        cart = await cart_service.get_cart()
        
        if not cart.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty"
            )
        
        # Validate addresses belong to user
        addresses = await self.user_service.get_user_addresses(user_id)
        shipping_address = next((addr for addr in addresses if addr.id == order_create.shipping_address_id), None)
        if not shipping_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid shipping address"
            )
        
        billing_address = shipping_address
        if order_create.billing_address_id:
            billing_address = next((addr for addr in addresses if addr.id == order_create.billing_address_id), None)
            if not billing_address:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid billing address"
                )
        
        # Generate order number
        order_number = await self._generate_order_number()
        
        # Calculate order totals
        subtotal = cart.summary.total_amount
        discount_amount = cart.summary.discount_amount
        tax_amount = cart.summary.tax_amount
        shipping_amount = await self._calculate_shipping(shipping_address.country)
        total_amount = subtotal - discount_amount + tax_amount + shipping_amount
        
        # Create order
        order_data = {
            'id': uuid4(),
            'order_number': order_number,
            'user_id': user_id,
            'status': 'pending',
            'payment_status': 'pending',
            'payment_method': order_create.payment_method.value,
            'subtotal': subtotal,
            'discount_amount': discount_amount,
            'tax_amount': tax_amount,
            'shipping_amount': shipping_amount,
            'total_amount': total_amount,
            'promo_code': getattr(cart, 'promo_code', None),
            'shipping_address': shipping_address.to_dict() if hasattr(shipping_address, 'to_dict') else shipping_address.__dict__,
            'billing_address': billing_address.to_dict() if hasattr(billing_address, 'to_dict') else billing_address.__dict__,
            'notes': order_create.notes
        }
        
        order = await self.order_repo.create(**order_data)
        
        # Create order items
        for cart_item in cart.items:
            item_data = {
                'id': uuid4(),
                'order_id': order.id,
                'game_id': cart_item.game_id,
                'quantity': cart_item.quantity,
                'unit_price': cart_item.price,
                'discount_amount': Decimal("0.00"),  # Individual item discounts
                'game_title': cart_item.game_title,
                'game_platform': cart_item.game_platform,
                'game_image_url': cart_item.game_image
            }
            await self.order_repo.create_order_item(**item_data)
        
        # Clear cart after successful order creation
        await cart_service.clear_cart()
        
        logger.info("Order created from cart", 
                   order_id=str(order.id), 
                   user_id=str(user_id),
                   order_number=order_number)
        
        return await self.get_order(order.id, user_id)
    
    async def get_order(self, order_id: UUID, user_id: UUID) -> OrderResponse:
        """Get order by ID for user."""
        order = await self.order_repo.find_by_id_and_user(order_id, user_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        return await self._build_order_response(order)
    
    async def get_user_orders(self, user_id: UUID, limit: int = 20, offset: int = 0) -> List[OrderResponse]:
        """Get orders for user with pagination."""
        orders = await self.order_repo.find_by_user(user_id, limit, offset)
        return [await self._build_order_response(order) for order in orders]
    
    async def update_order(self, order_id: UUID, user_id: UUID, order_update: OrderUpdate) -> OrderResponse:
        """Update order (limited fields for users)."""
        order = await self.order_repo.find_by_id_and_user(order_id, user_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Users can only cancel pending orders
        if order_update.status and order_update.status != 'cancelled':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update order status"
            )
        
        if order_update.status == 'cancelled' and order.status != 'pending':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only cancel pending orders"
            )
        
        # Update order
        update_data = order_update.dict(exclude_unset=True)
        updated_order = await self.order_repo.update(order_id, **update_data)
        
        logger.info("Order updated", 
                   order_id=str(order_id), 
                   user_id=str(user_id),
                   updates=update_data)
        
        return await self._build_order_response(updated_order)
    
    async def cancel_order(self, order_id: UUID, user_id: UUID) -> OrderResponse:
        """Cancel an order."""
        order = await self.order_repo.find_by_id_and_user(order_id, user_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        if order.status not in ['pending', 'confirmed']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel order in current status"
            )
        
        # Cancel order
        updated_order = await self.order_repo.update(order_id, status='cancelled')
        
        # If payment was captured, initiate refund
        if order.payment_status == 'captured':
            await self.payment_service.refund_payment(order.payment_id, order.total_amount)
            await self.order_repo.update(order_id, payment_status='refunded')
        
        logger.info("Order cancelled", 
                   order_id=str(order_id), 
                   user_id=str(user_id))
        
        return await self._build_order_response(updated_order)
    
    async def process_payment(self, order_id: UUID, user_id: UUID, payment_request: PaymentRequest) -> Dict[str, Any]:
        """Process payment for an order."""
        order = await self.order_repo.find_by_id_and_user(order_id, user_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        if order.status != 'pending':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order is not in pending status"
            )
        
        try:
            # Process payment
            payment_result = await self.payment_service.process_payment(
                amount=order.total_amount,
                currency="USD",
                payment_method=payment_request.payment_method,
                payment_token=payment_request.payment_token,
                order_id=str(order_id)
            )
            
            if payment_result['status'] == 'success':
                # Update order status
                await self.order_repo.update(
                    order_id,
                    status='confirmed',
                    payment_status='captured',
                    payment_id=payment_result['transaction_id']
                )
                
                logger.info("Payment processed successfully", 
                           order_id=str(order_id),
                           transaction_id=payment_result['transaction_id'])
                
                return {
                    'status': 'success',
                    'message': 'Payment processed successfully',
                    'transaction_id': payment_result['transaction_id']
                }
            else:
                # Update payment status to failed
                await self.order_repo.update(order_id, payment_status='failed')
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Payment failed: {payment_result.get('error', 'Unknown error')}"
                )
                
        except Exception as e:
            logger.error("Payment processing failed", 
                        order_id=str(order_id), 
                        error=str(e))
            
            await self.order_repo.update(order_id, payment_status='failed')
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Payment processing failed"
            )
    
    async def _generate_order_number(self) -> str:
        """Generate unique order number."""
        # Simple implementation - in production you might want more sophisticated numbering
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        random_suffix = str(uuid4())[:8].upper()
        return f"LGX-{timestamp}-{random_suffix}"
    
    async def _calculate_shipping(self, country: str) -> Decimal:
        """Calculate shipping cost based on destination."""
        # Simple shipping calculation - in production this would be more complex
        if country.upper() == "US":
            return Decimal("9.99")
        elif country.upper() in ["CA", "MX"]:
            return Decimal("14.99")
        else:
            return Decimal("24.99")
    
    async def _build_order_response(self, order: Order) -> OrderResponse:
        """Build order response with items."""
        # Get order items
        items = await self.order_repo.get_order_items(order.id)
        
        order_items = []
        for item in items:
            order_items.append({
                'id': item.id,
                'game_id': item.game_id,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'discount_amount': item.discount_amount,
                'game_title': item.game_title,
                'game_platform': item.game_platform,
                'game_image': item.game_image_url,
                'subtotal': item.unit_price * item.quantity - item.discount_amount
            })
        
        summary = {
            'subtotal': order.subtotal,
            'discount_amount': order.discount_amount,
            'tax_amount': order.tax_amount,
            'shipping_amount': order.shipping_amount,
            'total_amount': order.total_amount
        }
        
        return OrderResponse(
            id=order.id,
            order_number=order.order_number,
            user_id=order.user_id,
            status=order.status,
            payment_status=order.payment_status,
            items=order_items,
            summary=summary,
            shipping_address=order.shipping_address,
            billing_address=order.billing_address,
            payment_method=order.payment_method,
            promo_code=order.promo_code,
            tracking_number=order.tracking_number,
            notes=order.notes,
            created_at=order.created_at,
            updated_at=order.updated_at,
            estimated_delivery=order.estimated_delivery
        )