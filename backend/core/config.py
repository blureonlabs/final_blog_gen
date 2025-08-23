from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "Bulk Blog Generator API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Supabase settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    
    # CORS settings
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    
    # API settings
    API_V1_STR: str = "/api"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # External APIs
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    SERP_API_KEY: Optional[str] = os.getenv("SERP_API_KEY")
    
    # Redis settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Validate required settings
if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
    print("⚠️  Warning: SUPABASE_URL and SUPABASE_ANON_KEY are not set. Some features may not work.")
    # Set default placeholder values to allow the server to start
    settings.SUPABASE_URL = "https://placeholder.supabase.co"
    settings.SUPABASE_ANON_KEY = "placeholder_key_here"
