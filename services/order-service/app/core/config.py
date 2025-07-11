"""
Order Service Configuration
Environment-based configuration for the Order Service.
"""

import os
from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings, BaseModel):
    """Application settings."""
    
    # Application
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://order_service:order_secure_password_2024@localhost:5433/lugx_orders",
        env="DATABASE_URL"
    )
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/1",
        env="REDIS_URL"
    )
    
    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    JWT_SECRET_KEY: str = Field(
        default="your-jwt-secret-key-change-in-production",
        env="JWT_SECRET_KEY"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    PASSWORD_RESET_EXPIRATION_HOURS: int = 2
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="ALLOWED_ORIGINS"
    )
    ALLOWED_HOSTS: List[str] = Field(
        default=["*"],
        env="ALLOWED_HOSTS"
    )
    
    # External Services
    GAME_SERVICE_URL: str = Field(
        default="http://localhost:8001",
        env="GAME_SERVICE_URL"
    )
    ANALYTICS_SERVICE_URL: str = Field(
        default="http://localhost:8003",
        env="ANALYTICS_SERVICE_URL"
    )
    
    # Email Configuration (for user notifications)
    EMAIL_ENABLED: bool = Field(default=False, env="EMAIL_ENABLED")
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    EMAIL_FROM: str = Field(default="noreply@lugx.com", env="EMAIL_FROM")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # seconds
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Session Management
    SESSION_COOKIE_NAME: str = "lugx_session"
    SESSION_EXPIRATION_HOURS: int = 24
    
    # Cart Configuration
    CART_EXPIRATION_DAYS: int = 7
    MAX_CART_ITEMS: int = 50
    
    # Order Configuration
    ORDER_TIMEOUT_MINUTES: int = 30
    MAX_ORDER_ITEMS: int = 20
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()