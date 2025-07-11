"""
User management endpoints for Order Service.
Handles user addresses and profile operations.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_async_session
from app.core.security import get_current_user_id
from app.services.user_service import UserService
from app.schemas.user import (
    AddressCreate, AddressUpdate, AddressResponse, 
    UserResponse, UserUpdate
)

logger = structlog.get_logger()

router = APIRouter()


@router.get("/addresses", response_model=List[AddressResponse])
async def get_user_addresses(
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_async_session)
) -> List[AddressResponse]:
    """Get user's addresses."""
    user_service = UserService(session)
    addresses = await user_service.get_user_addresses(current_user_id)
    
    return [AddressResponse.from_orm(addr) for addr in addresses]


@router.post("/addresses", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address(
    address_create: AddressCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_async_session)
) -> AddressResponse:
    """Create new address."""
    user_service = UserService(session)
    address = await user_service.create_address(current_user_id, address_create)
    
    logger.info("Address created", user_id=str(current_user_id), address_id=str(address.id))
    return AddressResponse.from_orm(address)


@router.put("/addresses/{address_id}", response_model=AddressResponse)
async def update_address(
    address_id: UUID,
    address_update: AddressUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_async_session)
) -> AddressResponse:
    """Update user address."""
    user_service = UserService(session)
    address = await user_service.update_address(current_user_id, address_id, address_update)
    
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    logger.info("Address updated", user_id=str(current_user_id), address_id=str(address_id))
    return AddressResponse.from_orm(address)


@router.delete("/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
    address_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_async_session)
) -> None:
    """Delete user address."""
    user_service = UserService(session)
    deleted = await user_service.delete_address(current_user_id, address_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    logger.info("Address deleted", user_id=str(current_user_id), address_id=str(address_id))


@router.post("/addresses/{address_id}/set-default/{address_type}", status_code=status.HTTP_204_NO_CONTENT)
async def set_default_address(
    address_id: UUID,
    address_type: str,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_async_session)
) -> None:
    """Set address as default shipping or billing."""
    if address_type not in ["shipping", "billing"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Address type must be 'shipping' or 'billing'"
        )
    
    user_service = UserService(session)
    await user_service.set_default_address(current_user_id, address_id, address_type)
    
    logger.info("Default address set", 
               user_id=str(current_user_id), 
               address_id=str(address_id), 
               type=address_type)