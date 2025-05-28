from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
     # Application
    APP_NAME: str = "PerplexiQuest"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "https://perplexiquest.com",
        "https://app.perplexiquest.com"
    ]
    
    # Database
    DATABASE_URL: str
    ASYNC_DATABASE_URL: str
    
    # External APIs
    PERPLEXITY_API_KEY: str
    OPENAI_API_KEY: Optional[str] = None
    
    # Vector Store
    WEAVIATE_URL: str = "http://localhost:8080"
    WEAVIATE_API_KEY: Optional[str] = None
    
    # LangSmith
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "perplexi-quest"
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGSMITH_TRACING: bool = True
    
    # Redis (for caching and rate limiting)
    REDIS_URL: str = "redis://localhost:6379"
    
    # Email Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    EMAIL_FROM: str = "noreply@perplexiquest.com"
    EMAIL_FROM_NAME: str = "PerplexiQuest"
    
    # Frontend URL
    FRONTEND_URL: str = "https://app.perplexiquest.com"
    
    # File Storage
    UPLOAD_DIR: Path = Path("uploads")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    DEFAULT_RATE_LIMIT: str = "100/hour"
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    ENABLE_METRICS: bool = True
    
    # Background Tasks
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Current context
    CURRENT_USER: str = "r3tr056"
    CURRENT_TIMESTAMP: str = "2025-05-28 17:20:15"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()