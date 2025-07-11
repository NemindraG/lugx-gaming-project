"""
Payment processing endpoints for Order Service.
Handles payment methods, transactions, and refunds.
"""

from typing import Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_async_session
from app.core.security import get_current_user_id
from app.services.payment_service import PaymentService
from app.schemas.order import PaymentRequest, PaymentResponse

logger = structlog.get_logger()

router = APIRouter()


def get_payment_service() -> PaymentService:
    """Get payment service instance."""
    return PaymentService()


@router.get("/methods")
async def get_payment_methods() -> Dict[str, Any]:
    """Get available payment methods."""
    return {
        "payment_methods": [
            {
                "type": "card",
                "name": "Credit/Debit Card",
                "description": "Visa, Mastercard, American Express",
                "processing_fee": "2.9%",
                "supported": True
            },
            {
                "type": "paypal",
                "name": "PayPal",
                "description": "Pay with your PayPal account",
                "processing_fee": "3.5%",
                "supported": True
            },
            {
                "type": "wallet",
                "name": "Digital Wallet",
                "description": "Apple Pay, Google Pay, Samsung Pay",
                "processing_fee": "1.5%",
                "supported": True
            }
        ]
    }


@router.post("/validate-token")
async def validate_payment_token(
    payment_method: str,
    payment_token: str,
    payment_service: PaymentService = Depends(get_payment_service)
) -> Dict[str, Any]:
    """Validate a payment token."""
    is_valid = await payment_service.validate_payment_token(payment_token, payment_method)
    
    return {
        "valid": is_valid,
        "payment_method": payment_method,
        "message": "Token is valid" if is_valid else "Invalid payment token"
    }


@router.post("/authorize")
async def authorize_payment(
    payment_request: PaymentRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    payment_service: PaymentService = Depends(get_payment_service)
) -> Dict[str, Any]:
    """Authorize a payment without capturing it."""
    
    # Validate payment token
    is_valid = await payment_service.validate_payment_token(
        payment_request.payment_token, 
        payment_request.payment_method
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment token"
        )
    
    # For this endpoint, we need amount from the request
    # In a real implementation, this would be passed in the request
    result = await payment_service.authorize_payment(
        amount=100.00,  # This would come from the request
        currency="USD",
        payment_method=payment_request.payment_method,
        payment_token=payment_request.payment_token,
        order_id=str(payment_request.order_id)
    )
    
    return result


@router.post("/capture/{authorization_id}")
async def capture_payment(
    authorization_id: str,
    amount: float = None,
    current_user_id: UUID = Depends(get_current_user_id),
    payment_service: PaymentService = Depends(get_payment_service)
) -> Dict[str, Any]:
    """Capture a previously authorized payment."""
    
    result = await payment_service.capture_payment(
        authorization_id=authorization_id,
        amount=amount
    )
    
    return result


@router.post("/refund")
async def refund_payment(
    transaction_id: str,
    amount: float,
    reason: str = "customer_request",
    current_user_id: UUID = Depends(get_current_user_id),
    payment_service: PaymentService = Depends(get_payment_service)
) -> Dict[str, Any]:
    """Refund a payment."""
    
    result = await payment_service.refund_payment(
        transaction_id=transaction_id,
        amount=amount,
        reason=reason
    )
    
    return result


@router.get("/transactions/{transaction_id}")
async def get_transaction(
    transaction_id: str,
    current_user_id: UUID = Depends(get_current_user_id),
    payment_service: PaymentService = Depends(get_payment_service)
) -> Dict[str, Any]:
    """Get payment transaction details."""
    
    transaction = await payment_service.get_payment_status(transaction_id)
    
    return transaction


@router.get("/fees/calculate")
async def calculate_fees(
    amount: float,
    payment_method: str,
    payment_service: PaymentService = Depends(get_payment_service)
) -> Dict[str, Any]:
    """Calculate processing fees for a payment."""
    
    fees = payment_service._calculate_processing_fees(amount, payment_method)
    
    return {
        "amount": amount,
        "payment_method": payment_method,
        "processing_fee": float(fees),
        "total_amount": amount + float(fees)
    }