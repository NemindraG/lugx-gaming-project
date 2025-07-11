"""
User service for Order Service.
Handles user business logic operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.security import get_password_hash, verify_password, generate_password_reset_token
from app.models.user import User, UserAddress
from app.repositories.user_repository import UserRepository, UserAddressRepository
from app.schemas.user import UserCreate, UserUpdate, AddressCreate, AddressUpdate

logger = structlog.get_logger()


class UserService:
    """Service for user business logic."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.address_repo = UserAddressRepository(session)
    
    async def create_user(self, user_create: UserCreate) -> User:
        """Create a new user."""
        # Check if email or username already exists
        existing_user = await self.user_repo.find_by_email_or_username(
            user_create.email, user_create.username
        )
        
        if existing_user:
            if existing_user.email == user_create.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        # Hash password
        password_hash = get_password_hash(user_create.password)
        
        # Create user
        user_data = user_create.dict(exclude={"password"})
        user_data["password_hash"] = password_hash
        user_data["id"] = uuid4()
        
        user = await self.user_repo.create(**user_data)
        
        logger.info("User created", user_id=str(user.id), email=user.email)
        return user
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password."""
        user = await self.user_repo.find_by_email(email)
        
        if not user:
            logger.warning("Authentication failed - user not found", email=email)
            return None
        
        if user.is_locked:
            logger.warning("Authentication failed - account locked", 
                          user_id=str(user.id), email=email)
            return None
        
        if not user.is_active:
            logger.warning("Authentication failed - account inactive", 
                          user_id=str(user.id), email=email)
            return None
        
        if not verify_password(password, user.password_hash):
            # Increment failed login attempts
            await self.user_repo.increment_failed_login(user.id)
            
            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 4:  # Will be 5 after increment
                lock_until = datetime.now(timezone.utc) + timedelta(minutes=30)
                await self.user_repo.lock_account(user.id, lock_until)
                logger.warning("Account locked due to failed login attempts",
                              user_id=str(user.id), email=email)
            
            logger.warning("Authentication failed - invalid password", 
                          user_id=str(user.id), email=email)
            return None
        
        # Reset failed login attempts on successful login
        await self.user_repo.reset_failed_login(user.id)
        await self.user_repo.update_last_login(user.id)
        
        logger.info("User authenticated successfully", 
                   user_id=str(user.id), email=email)
        return user
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        return await self.user_repo.find_by_id(user_id)
    
    async def update_user(self, user_id: UUID, user_update: UserUpdate) -> Optional[User]:
        """Update user information."""
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if email/username is being changed and already exists
        if user_update.email and user_update.email != user.email:
            existing_user = await self.user_repo.find_by_email(user_update.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        if user_update.username and user_update.username != user.username:
            existing_user = await self.user_repo.find_by_username(user_update.username)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        # Update user
        update_data = user_update.dict(exclude_unset=True)
        updated_user = await self.user_repo.update(user_id, **update_data)
        
        logger.info("User updated", user_id=str(user_id))
        return updated_user
    
    async def change_password(self, user_id: UUID, current_password: str, new_password: str) -> bool:
        """Change user password."""
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        new_password_hash = get_password_hash(new_password)
        await self.user_repo.update_password(user_id, new_password_hash)
        
        logger.info("Password changed", user_id=str(user_id))
        return True
    
    async def initiate_password_reset(self, email: str) -> bool:
        """Initiate password reset process."""
        user = await self.user_repo.find_by_email(email)
        if not user:
            # Don't reveal if email exists
            logger.warning("Password reset requested for non-existent email", email=email)
            return True
        
        # Generate reset token
        reset_token = generate_password_reset_token(user.id)
        expires = datetime.now(timezone.utc) + timedelta(hours=2)
        
        await self.user_repo.set_password_reset_token(user.id, reset_token, expires)
        
        # TODO: Send email with reset token
        logger.info("Password reset initiated", user_id=str(user.id), email=email)
        return True
    
    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password with token."""
        user = await self.user_repo.find_by_reset_token(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Update password
        new_password_hash = get_password_hash(new_password)
        await self.user_repo.update_password(user.id, new_password_hash)
        
        logger.info("Password reset completed", user_id=str(user.id))
        return True
    
    async def get_user_addresses(self, user_id: UUID) -> List[UserAddress]:
        """Get all addresses for a user."""
        return await self.address_repo.find_by_user(user_id)
    
    async def create_address(self, user_id: UUID, address_create: AddressCreate) -> UserAddress:
        """Create a new address for user."""
        address_data = address_create.dict()
        address_data["user_id"] = user_id
        address_data["id"] = uuid4()
        
        address = await self.address_repo.create(**address_data)
        
        # Set as default if it's the first address
        user_addresses = await self.address_repo.find_by_user(user_id)
        if len(user_addresses) == 1:
            if address_create.address_type in ["shipping", "both"]:
                await self.address_repo.set_default_shipping(user_id, address.id)
            if address_create.address_type in ["billing", "both"]:
                await self.address_repo.set_default_billing(user_id, address.id)
        
        logger.info("Address created", user_id=str(user_id), address_id=str(address.id))
        return address
    
    async def update_address(self, user_id: UUID, address_id: UUID, address_update: AddressUpdate) -> Optional[UserAddress]:
        """Update user address."""
        # Verify address belongs to user
        address = await self.address_repo.find_by_id(address_id)
        if not address or address.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found"
            )
        
        # Update address
        update_data = address_update.dict(exclude_unset=True)
        updated_address = await self.address_repo.update(address_id, **update_data)
        
        logger.info("Address updated", user_id=str(user_id), address_id=str(address_id))
        return updated_address
    
    async def delete_address(self, user_id: UUID, address_id: UUID) -> bool:
        """Delete user address."""
        # Verify address belongs to user
        address = await self.address_repo.find_by_id(address_id)
        if not address or address.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found"
            )
        
        # Delete address
        deleted = await self.address_repo.delete(address_id)
        
        if deleted:
            logger.info("Address deleted", user_id=str(user_id), address_id=str(address_id))
        
        return deleted
    
    async def set_default_address(self, user_id: UUID, address_id: UUID, address_type: str) -> bool:
        """Set address as default shipping or billing."""
        # Verify address belongs to user
        address = await self.address_repo.find_by_id(address_id)
        if not address or address.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found"
            )
        
        if address_type == "shipping":
            await self.address_repo.set_default_shipping(user_id, address_id)
        elif address_type == "billing":
            await self.address_repo.set_default_billing(user_id, address_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid address type. Must be 'shipping' or 'billing'"
            )
        
        logger.info("Default address set", 
                   user_id=str(user_id), address_id=str(address_id), type=address_type)
        return True