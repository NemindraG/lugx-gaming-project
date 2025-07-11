"""
Analytics Service Configuration
Environment-based configuration for the Analytics Service.
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
    
    # ClickHouse Configuration
    CLICKHOUSE_HOST: str = Field(default="localhost", env="CLICKHOUSE_HOST")
    CLICKHOUSE_PORT: int = Field(default=8123, env="CLICKHOUSE_PORT")
    CLICKHOUSE_DATABASE: str = Field(default="lugx_analytics", env="CLICKHOUSE_DATABASE")
    CLICKHOUSE_USERNAME: str = Field(default="default", env="CLICKHOUSE_USERNAME")
    CLICKHOUSE_PASSWORD: str = Field(default="", env="CLICKHOUSE_PASSWORD")
    
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
    ORDER_SERVICE_URL: str = Field(
        default="http://localhost:8002",
        env="ORDER_SERVICE_URL"
    )
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=1000, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # seconds
    
    # Analytics Configuration
    BATCH_SIZE: int = Field(default=1000, env="ANALYTICS_BATCH_SIZE")
    BATCH_TIMEOUT: int = Field(default=30, env="ANALYTICS_BATCH_TIMEOUT")  # seconds
    MAX_QUEUE_SIZE: int = Field(default=10000, env="ANALYTICS_MAX_QUEUE_SIZE")
    
    # Event Processing
    PROCESS_HISTORICAL_EVENTS: bool = Field(default=True, env="PROCESS_HISTORICAL_EVENTS")
    RETENTION_DAYS: int = Field(default=365, env="ANALYTICS_RETENTION_DAYS")
    
    # Performance Settings
    ENABLE_SAMPLING: bool = Field(default=False, env="ENABLE_SAMPLING")
    SAMPLE_RATE: float = Field(default=0.1, env="SAMPLE_RATE")  # 10% by default
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()