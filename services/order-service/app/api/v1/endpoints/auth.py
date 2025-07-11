"""
Authentication endpoints for Order Service.
Handles user login, registration, and password management.
"""

from datetime import timedelta
from typing import Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.config import settings
from app.core.database import get_async_session
from app.core.security import (
    create_access_token, 
    create_refresh_token,
    get_current_user_id,
    verify_password_reset_token
)
from app.models.user import User
from app.services.user_service import UserService
from app.schemas.user import (
    UserCreate, UserResponse, UserUpdate, PasswordChange, 
    PasswordReset, PasswordResetRequest, LoginRequest, 
    TokenResponse, RefreshTokenRequest
)

logger = structlog.get_logger()

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_create: UserCreate,
    session: AsyncSession = Depends(get_async_session)
) -> UserResponse:
    """Register a new user."""
    user_service = UserService(session)
    
    try:
        user = await user_service.create_user(user_create)
        logger.info("User registered successfully", user_id=str(user.id))
        return UserResponse.from_orm(user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("User registration failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session)
) -> TokenResponse:
    """Authenticate user and return access token."""
    user_service = UserService(session)
    
    user = await user_service.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token_expires = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    token_data = {"sub": str(user.id)}
    
    access_token = create_access_token(
        data=token_data, 
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data=token_data)
    
    logger.info("User logged in successfully", user_id=str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds())
    )


@router.post("/login-json", response_model=TokenResponse)
async def login_json(
    login_data: LoginRequest,
    session: AsyncSession = Depends(get_async_session)
) -> TokenResponse:
    """Authenticate user with JSON payload and return access token."""
    user_service = UserService(session)
    
    user = await user_service.authenticate_user(login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token_expires = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    token_data = {"sub": str(user.id)}
    
    access_token = create_access_token(
        data=token_data, 
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data=token_data)
    
    logger.info("User logged in successfully", user_id=str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds())
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    session: AsyncSession = Depends(get_async_session)
) -> TokenResponse:
    """Refresh access token using refresh token."""
    from jose import JWTError, jwt
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            refresh_data.refresh_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "refresh":
            raise credentials_exception
            
        # Verify user still exists and is active
        user_service = UserService(session)
        user = await user_service.get_user_by_id(UUID(user_id))
        
        if not user or not user.is_active:
            raise credentials_exception
        
        # Create new tokens
        access_token_expires = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        token_data = {"sub": str(user.id)}
        
        access_token = create_access_token(
            data=token_data, 
            expires_delta=access_token_expires
        )
        new_refresh_token = create_refresh_token(data=token_data)
        
        logger.info("Token refreshed successfully", user_id=str(user.id))
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds())
        )
        
    except (JWTError, ValueError) as e:
        logger.error("Token refresh failed", error=str(e))
        raise credentials_exception


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_async_session)
) -> UserResponse:
    """Get current user profile."""
    user_service = UserService(session)
    user = await user_service.get_user_by_id(current_user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.from_orm(user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_async_session)
) -> UserResponse:
    """Update current user profile."""
    user_service = UserService(session)
    user = await user_service.update_user(current_user_id, user_update)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info("User profile updated", user_id=str(current_user_id))
    return UserResponse.from_orm(user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_data: PasswordChange,
    current_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_async_session)
) -> None:
    """Change user password."""
    user_service = UserService(session)
    
    await user_service.change_password(
        current_user_id,
        password_data.current_password,
        password_data.new_password
    )
    
    logger.info("Password changed successfully", user_id=str(current_user_id))


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
async def forgot_password(
    reset_request: PasswordResetRequest,
    session: AsyncSession = Depends(get_async_session)
) -> None:
    """Initiate password reset process."""
    user_service = UserService(session)
    await user_service.initiate_password_reset(reset_request.email)
    
    # Always return success to prevent email enumeration
    logger.info("Password reset requested", email=reset_request.email)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    reset_data: PasswordReset,
    session: AsyncSession = Depends(get_async_session)
) -> None:
    """Reset password with token."""
    # Verify token first
    user_id = verify_password_reset_token(reset_data.token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    user_service = UserService(session)
    await user_service.reset_password(reset_data.token, reset_data.new_password)
    
    logger.info("Password reset completed", user_id=str(user_id))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user_id: UUID = Depends(get_current_user_id)
) -> None:
    """Logout user (token blacklisting would be handled here in production)."""
    # In a production system, you would blacklist the token
    # For now, we just log the logout event
    logger.info("User logged out", user_id=str(current_user_id))