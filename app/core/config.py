from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra fields (e.g., VITE_* frontend vars)
    )
    
    APP_NAME: str = "credit-risk-backend"
    APP_VERSION: str = "0.1.0"
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"
    
    # Phase 3B-1: Backend URL discovery for frontend integration
    BACKEND_URL: str = "http://localhost:8000"
    
    # Phase 3B-1: CORS configuration for local frontend access
    # Safe mode: Only localhost origins, only GET/POST methods
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",  # Vite default
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    CORS_METHODS: List[str] = ["GET", "POST"]
    CORS_ALLOW_CREDENTIALS: bool = True


settings = Settings()
