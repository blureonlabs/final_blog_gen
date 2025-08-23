from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class APIKeyBase(BaseModel):
    """Base API key model"""
    name: str = Field(..., min_length=1, max_length=255, description="API key name")
    service: str = Field(..., description="Service name (e.g., openai, gemini, serp)")
    api_key: str = Field(..., min_length=1, description="The actual API key")
    is_default: bool = Field(default=False, description="Whether this is the default key for the service")
    is_active: bool = Field(default=True, description="Whether the API key is active")

class APIKeyCreate(APIKeyBase):
    """Model for creating a new API key"""
    pass

class APIKeyUpdate(BaseModel):
    """Model for updating an API key"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    service: Optional[str] = None
    api_key: Optional[str] = Field(None, min_length=1)
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None

class APIKeyResponse(APIKeyBase):
    """Model for API key response"""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class APIKeyListResponse(BaseModel):
    """Model for API key list response"""
    api_keys: List[APIKeyResponse]
    total: int

class ServiceAPIKeys(BaseModel):
    """Model for grouping API keys by service"""
    openai: Optional[APIKeyResponse] = None
    gemini: Optional[APIKeyResponse] = None
    serp: Optional[APIKeyResponse] = None
