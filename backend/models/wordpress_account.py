from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class WordPressAccountBase(BaseModel):
    """Base WordPress account model"""
    name: str = Field(..., min_length=1, max_length=255, description="Account name")
    site_url: HttpUrl = Field(..., description="WordPress site URL")
    username: str = Field(..., min_length=1, max_length=255, description="WordPress username")
    password: str = Field(..., min_length=1, description="WordPress password or API token")
    is_active: bool = Field(default=True, description="Whether the account is active")

class WordPressAccountCreate(WordPressAccountBase):
    """Model for creating a new WordPress account"""
    pass

class WordPressAccountUpdate(BaseModel):
    """Model for updating a WordPress account"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    site_url: Optional[HttpUrl] = None
    username: Optional[str] = Field(None, min_length=1, max_length=255)
    password: Optional[str] = Field(None, min_length=1)
    is_active: Optional[bool] = None

class WordPressAccountResponse(WordPressAccountBase):
    """Model for WordPress account response"""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class WordPressAccountListResponse(BaseModel):
    """Model for WordPress account list response"""
    accounts: List[WordPressAccountResponse]
    total: int
