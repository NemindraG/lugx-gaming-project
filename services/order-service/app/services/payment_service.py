"""
Payment service for Order Service.
Handles payment processing simulation with multiple payment methods.
"""

import asyncio
import random
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException, status
import structlog

logger = structlog.get_logger()


class PaymentService:
    """Service for payment processing operations."""
    
    def __init__(self):
        # Simulated payment gateway configurations
        self.payment_gateways = {
            'card': {
                'name': 'Stripe Simulator',
                'success_rate': 0.95,  # 95% success rate
                'processing_time': (0.5, 2.0)  # 0.5-2.0 seconds
            },
            'paypal': {
                'name': 'PayPal Simulator',
                'success_rate': 0.98,  # 98% success rate
                'processing_time': (1.0, 3.0)  # 1.0-3.0 seconds
            },
            'wallet': {
                'name': 'Digital Wallet Simulator',
                'success_rate': 0.99,  # 99% success rate
                'processing_time': (0.2, 1.0)  # 0.2-1.0 seconds
            }
        }
    
    async def process_payment(
        self,
        amount: Decimal,
        currency: str,
        payment_method: str,
        payment_token: str,
        order_id: str,
        billing_address: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a payment with the specified method."""
        
        # Validate payment method
        if payment_method not in self.payment_gateways:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported payment method: {payment_method}"
            )
        
        # Validate amount
        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment amount must be greater than zero"
            )
        
        # Validate currency
        if currency not in ['USD', 'EUR', 'GBP']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported currency: {currency}"
            )
        
        gateway_config = self.payment_gateways[payment_method]
        
        logger.info("Processing payment", 
                   order_id=order_id,
                   amount=str(amount),
                   currency=currency,
                   payment_method=payment_method,
                   gateway=gateway_config['name'])
        
        try:
            # Simulate payment processing time
            processing_time = random.uniform(*gateway_config['processing_time'])
            await asyncio.sleep(processing_time)
            
            # Simulate payment success/failure based on gateway success rate
            success = random.random() < gateway_config['success_rate']
            
            if success:
                transaction_id = f"txn_{payment_method}_{uuid4().hex[:12]}"
                
                result = {
                    'status': 'success',
                    'transaction_id': transaction_id,
                    'amount': amount,
                    'currency': currency,
                    'payment_method': payment_method,
                    'gateway': gateway_config['name'],
                    'processed_at': datetime.now(timezone.utc).isoformat(),
                    'fees': self._calculate_processing_fees(amount, payment_method)
                }
                
                logger.info("Payment processed successfully",
                           order_id=order_id,
                           transaction_id=transaction_id,
                           amount=str(amount))
                
                return result
            else:
                # Simulate different types of payment failures
                failure_reasons = [
                    "insufficient_funds",
                    "card_declined", 
                    "expired_card",
                    "invalid_cvv",
                    "network_error",
                    "fraud_detection"
                ]
                failure_reason = random.choice(failure_reasons)
                
                logger.warning("Payment failed",
                              order_id=order_id,
                              reason=failure_reason,
                              amount=str(amount))
                
                return {
                    'status': 'failed',
                    'error': failure_reason,
                    'message': self._get_failure_message(failure_reason),
                    'amount': amount,
                    'currency': currency,
                    'payment_method': payment_method,
                    'gateway': gateway_config['name'],
                    'processed_at': datetime.now(timezone.utc).isoformat()
                }
                
        except Exception as e:
            logger.error("Payment processing error",
                        order_id=order_id,
                        error=str(e),
                        amount=str(amount))
            
            return {
                'status': 'error',
                'error': 'processing_error',
                'message': 'An error occurred while processing the payment',
                'amount': amount,
                'currency': currency,
                'payment_method': payment_method,
                'gateway': gateway_config['name'],
                'processed_at': datetime.now(timezone.utc).isoformat()
            }
    
    async def authorize_payment(
        self,
        amount: Decimal,
        currency: str,
        payment_method: str,
        payment_token: str,
        order_id: str
    ) -> Dict[str, Any]:
        """Authorize a payment without capturing it."""
        
        # For simulation, authorization has higher success rate than capture
        gateway_config = self.payment_gateways.get(payment_method, {})
        success_rate = gateway_config.get('success_rate', 0.95) * 1.05  # Slightly higher
        
        processing_time = random.uniform(0.2, 1.0)  # Faster than full processing
        await asyncio.sleep(processing_time)
        
        success = random.random() < min(success_rate, 1.0)
        
        if success:
            authorization_id = f"auth_{payment_method}_{uuid4().hex[:12]}"
            
            logger.info("Payment authorized successfully",
                       order_id=order_id,
                       authorization_id=authorization_id,
                       amount=str(amount))
            
            return {
                'status': 'authorized',
                'authorization_id': authorization_id,
                'amount': amount,
                'currency': currency,
                'payment_method': payment_method,
                'expires_at': datetime.now(timezone.utc).isoformat(),
                'authorized_at': datetime.now(timezone.utc).isoformat()
            }
        else:
            return {
                'status': 'failed',
                'error': 'authorization_failed',
                'message': 'Payment authorization failed',
                'amount': amount,
                'currency': currency,
                'payment_method': payment_method
            }
    
    async def capture_payment(
        self,
        authorization_id: str,
        amount: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """Capture a previously authorized payment."""
        
        # Simulate capture processing
        processing_time = random.uniform(0.1, 0.5)
        await asyncio.sleep(processing_time)
        
        # High success rate for captures of valid authorizations
        success = random.random() < 0.98
        
        if success:
            transaction_id = f"cap_{authorization_id[-12:]}"
            
            logger.info("Payment captured successfully",
                       authorization_id=authorization_id,
                       transaction_id=transaction_id)
            
            return {
                'status': 'captured',
                'transaction_id': transaction_id,
                'authorization_id': authorization_id,
                'captured_at': datetime.now(timezone.utc).isoformat()
            }
        else:
            return {
                'status': 'failed',
                'error': 'capture_failed',
                'message': 'Payment capture failed',
                'authorization_id': authorization_id
            }
    
    async def refund_payment(
        self,
        transaction_id: str,
        amount: Decimal,
        reason: str = "customer_request"
    ) -> Dict[str, Any]:
        """Process a refund for a captured payment."""
        
        # Simulate refund processing
        processing_time = random.uniform(0.5, 2.0)
        await asyncio.sleep(processing_time)
        
        # High success rate for refunds
        success = random.random() < 0.95
        
        if success:
            refund_id = f"ref_{uuid4().hex[:12]}"
            
            logger.info("Refund processed successfully",
                       transaction_id=transaction_id,
                       refund_id=refund_id,
                       amount=str(amount),
                       reason=reason)
            
            return {
                'status': 'refunded',
                'refund_id': refund_id,
                'transaction_id': transaction_id,
                'amount': amount,
                'reason': reason,
                'refunded_at': datetime.now(timezone.utc).isoformat()
            }
        else:
            return {
                'status': 'failed',
                'error': 'refund_failed',
                'message': 'Refund processing failed',
                'transaction_id': transaction_id,
                'amount': amount
            }
    
    async def get_payment_status(self, transaction_id: str) -> Dict[str, Any]:
        """Get the status of a payment transaction."""
        
        # Simulate API call to payment gateway
        await asyncio.sleep(0.1)
        
        # For simulation, return a mock status
        return {
            'transaction_id': transaction_id,
            'status': 'captured',
            'amount': Decimal("99.99"),
            'currency': 'USD',
            'processed_at': datetime.now(timezone.utc).isoformat()
        }
    
    def _calculate_processing_fees(self, amount: Decimal, payment_method: str) -> Decimal:
        """Calculate processing fees based on payment method."""
        fee_rates = {
            'card': Decimal("0.029"),      # 2.9%
            'paypal': Decimal("0.035"),    # 3.5%
            'wallet': Decimal("0.015")     # 1.5%
        }
        
        rate = fee_rates.get(payment_method, Decimal("0.029"))
        fee = amount * rate
        
        # Minimum fee of $0.30
        return max(fee, Decimal("0.30"))
    
    def _get_failure_message(self, failure_reason: str) -> str:
        """Get user-friendly failure message."""
        messages = {
            "insufficient_funds": "Insufficient funds in account",
            "card_declined": "Your card was declined by the bank",
            "expired_card": "Your card has expired",
            "invalid_cvv": "Invalid security code (CVV)",
            "network_error": "Network error occurred, please try again",
            "fraud_detection": "Transaction flagged for security review"
        }
        
        return messages.get(failure_reason, "Payment processing failed")
    
    async def validate_payment_token(self, payment_token: str, payment_method: str) -> bool:
        """Validate a payment token (simulation)."""
        
        # Simulate token validation
        await asyncio.sleep(0.1)
        
        # Simple validation logic for simulation
        if not payment_token or len(payment_token) < 10:
            return False
        
        # Different validation rules per payment method
        if payment_method == 'card':
            return payment_token.startswith('tok_card_')
        elif payment_method == 'paypal':
            return payment_token.startswith('tok_paypal_')
        elif payment_method == 'wallet':
            return payment_token.startswith('tok_wallet_')
        
        return False