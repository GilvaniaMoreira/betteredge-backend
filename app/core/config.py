from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Banco de dados
    database_url: str = Field(
        default="postgresql+asyncpg://invest:investpw@localhost/investdb",
        alias="DATABASE_URL"
    )
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        alias="REDIS_URL"
    )
    
    # JWT
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        alias="SECRET_KEY"
    )
    algorithm: str = Field(
        default="HS256",
        alias="ALGORITHM"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    
    # API Yahoo Finance
    yahoo_finance_base_url: str = Field(
        default="https://query1.finance.yahoo.com/v8/finance/chart",
        alias="YAHOO_FINANCE_BASE_URL"
    )
    
    # CORS
    allowed_origins: List[str] = Field(
        default=[
            "http://localhost:3000", 
            "http://localhost:3001",
            "http://frontend:3000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://0.0.0.0:3000",
            "http://0.0.0.0:3001"
        ],
        alias="ALLOWED_ORIGINS"
    )
    
settings = Settings()

