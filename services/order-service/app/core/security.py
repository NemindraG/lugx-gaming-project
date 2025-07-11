"""
Security utilities for Order Service.
Handles JWT token generation, validation, and password hashing.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for required authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# HTTP Bearer for optional authentication
security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    
    expire = datetime.now(timezone.utc) + timedelta(days=7)  # Refresh tokens last 7 days
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> UUID:
    """Extract user ID from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "access":
            raise credentials_exception
            
        return UUID(user_id)
        
    except (JWTError, ValueError) as e:
        logger.error("JWT validation failed", error=str(e))
        raise credentials_exception


async def get_optional_user_id(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[UUID]:
    """Extract user ID from JWT token if provided, otherwise return None."""
    if not token:
        return None
        
    try:
        return await get_current_user_id(token)
    except HTTPException:
        return None


def generate_password_reset_token(user_id: UUID) -> str:
    """Generate a password reset token."""
    data = {
        "sub": str(user_id),
        "type": "password_reset",
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.PASSWORD_RESET_EXPIRATION_HOURS)
    }
    
    return jwt.encode(
        data,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def verify_password_reset_token(token: str) -> Optional[UUID]:
    """Verify a password reset token and return user ID."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        token_type = payload.get("type")
        user_id = payload.get("sub")
        
        if token_type != "password_reset" or not user_id:
            return None
            
        return UUID(user_id)
        
    except (JWTError, ValueError):
        return None