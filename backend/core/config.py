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
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    # Database settings
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    # CORS settings
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001"
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
    FAL_AI_API_KEY: Optional[str] = os.getenv("FAL_AI_API_KEY")
    
    # Storage Configuration
    STORAGE_BUCKET_NAME: str = os.getenv("STORAGE_BUCKET_NAME", "blog-content")
    STORAGE_REGION: str = os.getenv("STORAGE_REGION", "auto")
    
    # Redis settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        # Allow extra fields to prevent validation errors
        extra = "allow"

# Create settings instance
settings = Settings()

# Validate required settings
if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
    print("⚠️  Warning: SUPABASE_URL and SUPABASE_ANON_KEY are not set. Using provided credentials.")
    # Use the user's actual Supabase credentials
    settings.SUPABASE_URL = "https://kjijwycmwjxqurdlnalo.supabase.co"
    settings.SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtqaWp3eWNtd2p4cXVyZGxuYWxvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTU5NzM3MzEsImV4cCI6MjA3MTU0OTczMX0.mf8SqZZLbirhlmu13AZ0ftJrV71L91bTxkWAWyGqA0g"
