"""
User repository for Order Service.
Handles user data access operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog

from app.models.user import User, UserAddress
from app.repositories.base_repository import BaseRepository

logger = structlog.get_logger()


class UserRepository(BaseRepository[User]):
    """Repository for user data access."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email address."""
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username."""
        query = select(User).where(User.username == username)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def find_by_email_or_username(self, email: str, username: str) -> Optional[User]:
        """Find user by email or username."""
        query = select(User).where(
            or_(User.email == email, User.username == username)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update_last_login(self, user_id: UUID) -> None:
        """Update user's last login timestamp."""
        query = (
            self.model.__table__.update()
            .where(self.model.id == user_id)
            .values(last_login_at=datetime.now(timezone.utc))
        )
        await self.session.execute(query)
    
    async def increment_failed_login(self, user_id: UUID) -> int:
        """Increment failed login attempts and return new count."""
        user = await self.find_by_id(user_id)
        if user:
            user.failed_login_attempts += 1
            await self.session.commit()
            return user.failed_login_attempts
        return 0
    
    async def reset_failed_login(self, user_id: UUID) -> None:
        """Reset failed login attempts."""
        query = (
            self.model.__table__.update()
            .where(self.model.id == user_id)
            .values(failed_login_attempts=0, locked_until=None)
        )
        await self.session.execute(query)
    
    async def lock_account(self, user_id: UUID, until: datetime) -> None:
        """Lock user account until specified time."""
        query = (
            self.model.__table__.update()
            .where(self.model.id == user_id)
            .values(locked_until=until)
        )
        await self.session.execute(query)
    
    async def set_password_reset_token(self, user_id: UUID, token: str, expires: datetime) -> None:
        """Set password reset token for user."""
        query = (
            self.model.__table__.update()
            .where(self.model.id == user_id)
            .values(
                password_reset_token=token,
                password_reset_expires=expires
            )
        )
        await self.session.execute(query)
    
    async def clear_password_reset_token(self, user_id: UUID) -> None:
        """Clear password reset token."""
        query = (
            self.model.__table__.update()
            .where(self.model.id == user_id)
            .values(
                password_reset_token=None,
                password_reset_expires=None
            )
        )
        await self.session.execute(query)
    
    async def find_by_reset_token(self, token: str) -> Optional[User]:
        """Find user by password reset token."""
        query = select(User).where(
            and_(
                User.password_reset_token == token,
                User.password_reset_expires > datetime.now(timezone.utc)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update_password(self, user_id: UUID, password_hash: str) -> None:
        """Update user password."""
        query = (
            self.model.__table__.update()
            .where(self.model.id == user_id)
            .values(password_hash=password_hash)
        )
        await self.session.execute(query)
        await self.clear_password_reset_token(user_id)
        await self.reset_failed_login(user_id)
    
    async def verify_email(self, user_id: UUID) -> None:
        """Mark user email as verified."""
        query = (
            self.model.__table__.update()
            .where(self.model.id == user_id)
            .values(
                is_verified=True,
                email_verification_token=None,
                email_verification_expires=None
            )
        )
        await self.session.execute(query)
    
    async def search_users(
        self,
        search_term: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[User]:
        """Search users with filters."""
        query = select(User)
        
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.where(
                or_(
                    User.email.ilike(search_pattern),
                    User.username.ilike(search_pattern),
                    User.first_name.ilike(search_pattern),
                    User.last_name.ilike(search_pattern)
                )
            )
        
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        if is_verified is not None:
            query = query.where(User.is_verified == is_verified)
        
        query = query.order_by(User.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics."""
        total_users = await self.session.scalar(
            select(func.count()).select_from(User)
        )
        
        active_users = await self.session.scalar(
            select(func.count()).select_from(User).where(User.is_active == True)
        )
        
        verified_users = await self.session.scalar(
            select(func.count()).select_from(User).where(User.is_verified == True)
        )
        
        return {
            "total_users": total_users or 0,
            "active_users": active_users or 0,
            "verified_users": verified_users or 0,
            "unverified_users": (total_users or 0) - (verified_users or 0)
        }


class UserAddressRepository(BaseRepository[UserAddress]):
    """Repository for user address data access."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserAddress)
    
    async def find_by_user(self, user_id: UUID) -> List[UserAddress]:
        """Find all addresses for a user."""
        query = select(UserAddress).where(UserAddress.user_id == user_id)
        query = query.order_by(
            UserAddress.is_default_shipping.desc(),
            UserAddress.is_default_billing.desc(),
            UserAddress.created_at.desc()
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def find_default_shipping(self, user_id: UUID) -> Optional[UserAddress]:
        """Find user's default shipping address."""
        query = select(UserAddress).where(
            and_(
                UserAddress.user_id == user_id,
                UserAddress.is_default_shipping == True
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def find_default_billing(self, user_id: UUID) -> Optional[UserAddress]:
        """Find user's default billing address."""
        query = select(UserAddress).where(
            and_(
                UserAddress.user_id == user_id,
                UserAddress.is_default_billing == True
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def set_default_shipping(self, user_id: UUID, address_id: UUID) -> None:
        """Set address as default shipping address."""
        # Clear existing default
        await self.session.execute(
            self.model.__table__.update()
            .where(
                and_(
                    UserAddress.user_id == user_id,
                    UserAddress.is_default_shipping == True
                )
            )
            .values(is_default_shipping=False)
        )
        
        # Set new default
        await self.session.execute(
            self.model.__table__.update()
            .where(UserAddress.id == address_id)
            .values(is_default_shipping=True)
        )
    
    async def set_default_billing(self, user_id: UUID, address_id: UUID) -> None:
        """Set address as default billing address."""
        # Clear existing default
        await self.session.execute(
            self.model.__table__.update()
            .where(
                and_(
                    UserAddress.user_id == user_id,
                    UserAddress.is_default_billing == True
                )
            )
            .values(is_default_billing=False)
        )
        
        # Set new default
        await self.session.execute(
            self.model.__table__.update()
            .where(UserAddress.id == address_id)
            .values(is_default_billing=True)
        )