from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

class ProjectBase(BaseModel):
    """Base project model"""
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    num_blogs: int = Field(..., gt=0, le=1000, description="Number of blogs to generate")
    ai_model: Optional[str] = Field(None, description="AI model to use for generation")
    wordpress_account_id: Optional[UUID] = Field(None, description="WordPress account ID")
    api_keys: Optional[Dict[str, Any]] = Field(None, description="API keys configuration")

class ProjectCreate(ProjectBase):
    """Model for creating a new project"""
    pass

class ProjectUpdate(BaseModel):
    """Model for updating a project"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    num_blogs: Optional[int] = Field(None, gt=0, le=1000)
    ai_model: Optional[str] = None
    wordpress_account_id: Optional[UUID] = None
    api_keys: Optional[Dict[str, Any]] = None
    status: Optional[str] = Field(None, description="Project status")

class ProjectResponse(ProjectBase):
    """Model for project response"""
    id: UUID
    user_id: UUID
    status: str = Field(default="pending", description="Project status")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ProjectListResponse(BaseModel):
    """Model for project list response"""
    projects: List[ProjectResponse]
    total: int
    page: int
    per_page: int

class ProjectStatus(BaseModel):
    """Model for project status"""
    id: UUID
    name: str
    status: str
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    blogs_generated: int = Field(default=0, description="Number of blogs generated")
    num_blogs: int = Field(..., description="Number of blogs to generate")
    created_at: datetime
    updated_at: datetime
