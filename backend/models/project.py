from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

class ProjectBase(BaseModel):
    """Base project model"""
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    num_blogs: int = Field(..., gt=0, le=1000, description="Number of blogs to generate")
    draft_creation_model: Optional[str] = Field(None, description="AI model to use for draft creation")
    wordpress_account_id: Optional[UUID] = Field(None, description="WordPress account ID")
    api_keys: Optional[Dict[str, Any]] = Field(None, description="API keys configuration")
    serp_api_on: Optional[bool] = Field(False, description="Enable SerpAPI research for this project")
    enhanced_research: Optional[bool] = Field(False, description="Enable enhanced research features (AI queries, external links, content scraping)")
    generate_images: Optional[bool] = Field(False, description="Enable image generation for blogs")
    num_images_per_blog: Optional[int] = Field(1, ge=1, le=4, description="Number of images per blog (1-4)")

class ProjectCreate(ProjectBase):
    """Model for creating a new project"""
    pass

class ProjectUpdate(BaseModel):
    """Model for updating a project"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    num_blogs: Optional[int] = Field(None, gt=0, le=1000)
    draft_creation_model: Optional[str] = Field(None, description="AI model to use for content generation")
    wordpress_account_id: Optional[UUID] = None
    api_keys: Optional[Dict[str, Any]] = None
    status: Optional[str] = Field(None, description="Project status")
    completed_blogs: Optional[int] = Field(None, ge=0, description="Number of completed blogs")

class ProjectResponse(BaseModel):
    """Model for project response"""
    idx: Optional[int] = Field(None, description="Database index")
    id: UUID = Field(..., description="Project UUID")
    user_id: UUID = Field(..., description="User UUID")
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    num_blogs: int = Field(..., description="Number of blogs to generate")
    completed_blogs: int = Field(default=0, description="Number of completed blogs")
    status: str = Field(default="ready", description="Project status")
    wordpress_account_id: Optional[UUID] = Field(None, description="WordPress account ID")
    api_keys: Optional[Dict[str, Any]] = Field(None, description="API keys configuration")
    settings: Optional[Dict[str, Any]] = Field(None, description="Project settings")
    draft_creation_model: Optional[str] = Field(None, description="AI model to use for content generation")
    serp_api_on: Optional[bool] = Field(False, description="Enable SerpAPI research for this project")
    enhanced_research: Optional[bool] = Field(False, description="Enable enhanced research features (AI queries, external links, content scraping)")
    generate_images: Optional[bool] = Field(False, description="Enable image generation for blogs")
    num_images_per_blog: Optional[int] = Field(1, ge=1, le=4, description="Number of images per blog (1-4)")
    serp_api_contents: Optional[Dict[str, Any]] = Field(None, description="SerpAPI research results and insights")
    extracted_seo_keywords: Optional[List[str]] = Field(None, description="Extracted SEO keywords for easy display")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
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
