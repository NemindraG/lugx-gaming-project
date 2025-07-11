"""
User schemas for Order Service.
Pydantic models for request/response validation.
"""

from datetime import datetime, date
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, pattern=r"^\+?[\d\s\-\(\)]+$")
    date_of_birth: Optional[date] = None


class UserCreate(UserBase):
    """Schema for user creation."""
    password: str = Field(..., min_length=8, max_length=128)
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('Password must contain uppercase, lowercase, and digit')
        
        return v


class UserUpdate(BaseModel):
    """Schema for user updates."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, pattern=r"^\+?[\d\s\-\(\)]+$")
    date_of_birth: Optional[date] = None
    preferences: Optional[Dict[str, Any]] = None
    notification_settings: Optional[Dict[str, Any]] = None


class UserResponse(UserBase):
    """Schema for user responses."""
    id: UUID
    full_name: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    preferences: Dict[str, Any] = {}
    notification_settings: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    """Schema for password change."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('Password must contain uppercase, lowercase, and digit')
        
        return v


class PasswordReset(BaseModel):
    """Schema for password reset."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('Password must contain uppercase, lowercase, and digit')
        
        return v


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    email: EmailStr


class AddressBase(BaseModel):
    """Base address schema."""
    address_type: str = Field(..., pattern=r"^(shipping|billing|both)$")
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    address_line_1: str = Field(..., max_length=255)
    address_line_2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., max_length=100)
    state_province: str = Field(..., max_length=100)
    postal_code: str = Field(..., max_length=20)
    country: str = Field(..., max_length=100)
    phone: Optional[str] = Field(None, pattern=r"^\+?[\d\s\-\(\)]+$")


class AddressCreate(AddressBase):
    """Schema for address creation."""
    pass


class AddressUpdate(BaseModel):
    """Schema for address updates."""
    address_type: Optional[str] = Field(None, pattern=r"^(shipping|billing|both)$")
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    address_line_1: Optional[str] = Field(None, max_length=255)
    address_line_2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state_province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, pattern=r"^\+?[\d\s\-\(\)]+$")


class AddressResponse(AddressBase):
    """Schema for address responses."""
    id: UUID
    user_id: UUID
    is_default_shipping: bool
    is_default_billing: bool
    full_address: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Schema for login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str


class UserStats(BaseModel):
    """Schema for user statistics."""
    total_users: int
    active_users: int
    verified_users: int
    unverified_users: int