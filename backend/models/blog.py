from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from enum import Enum

class BlogStatus(str, Enum):
    """Blog status enumeration"""
    DRAFT = "draft"
    GENERATING = "generating"
    SEO_OPTIMIZING = "seo_optimizing"
    FORMATTING = "formatting"
    IMAGE_GENERATING = "image_generating"
    READY = "ready"
    NEEDS_REVISION = "needs_revision"  # New status for failed vetting
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"

class BlogCreate(BaseModel):
    """Model for creating a new blog"""
    project_id: UUID
    title: Optional[str] = None
    # content field removed - content is now stored in Supabase Storage
    prompt: str
    ai_model: str = "openai"
    ai_model_version: Optional[str] = None
    seo_meta: Optional[Dict[str, Any]] = None
    status: BlogStatus = BlogStatus.DRAFT
    word_count: Optional[int] = None
    generation_metadata: Optional[Dict[str, Any]] = None  # New field for AI generation metadata

class BlogUpdate(BaseModel):
    """Model for updating a blog"""
    title: Optional[str] = None
    # content field removed - content is now stored in Supabase Storage
    seo_meta: Optional[Dict[str, Any]] = None
    status: Optional[BlogStatus] = None
    wordpress_url: Optional[str] = None
    wordpress_post_id: Optional[str] = None
    error_message: Optional[str] = None
    generation_logs: Optional[List[Dict[str, Any]]] = None

class BlogResponse(BaseModel):
    """Model for blog response"""
    id: UUID
    project_id: UUID
    title: Optional[str] = None
    content: Optional[str] = None  # Content from database
    prompt: str
    ai_model: str
    ai_model_version: Optional[str] = None
    seo_meta: Optional[Dict[str, Any]] = None
    status: BlogStatus
    word_count: Optional[int] = None
    # Storage references
    storage_path: Optional[str] = None
    storage_bucket: Optional[str] = None
    content_size_bytes: Optional[int] = None
    content_hash: Optional[str] = None
    wordpress_url: Optional[str] = None
    wordpress_post_id: Optional[str] = None
    error_message: Optional[str] = None
    generation_logs: Optional[List[Dict[str, Any]]] = None
    # AI Model Configuration and Vetting Metadata
    generation_metadata: Optional[Dict[str, Any]] = None  # New field for AI generation metadata
    created_at: datetime
    updated_at: datetime

class BlogListResponse(BaseModel):
    """Model for blog list response"""
    blogs: List[BlogResponse]
    total: int
    page: int
    per_page: int

class BlogGenerationRequest(BaseModel):
    """Model for requesting blog generation"""
    project_id: UUID
    prompt: str
    ai_model: str = "openai"
    ai_model_version: Optional[str] = None
    num_blogs: int = Field(ge=1, le=100, description="Number of blogs to generate")
    batch_size: int = Field(default=5, ge=1, le=20, description="Batch size for generation")

class BlogGenerationResponse(BaseModel):
    """Model for blog generation response"""
    project_id: UUID
    task_id: str
    message: str
    estimated_time: Optional[int] = None  # in minutes
    blogs_requested: int
    batch_size: int

class BlogPreview(BaseModel):
    """Model for blog preview before publishing"""
    id: UUID
    title: str
    content_preview: str  # First 200 characters
    seo_meta: Optional[Dict[str, Any]] = None
    status: BlogStatus
    created_at: datetime

class BlogPublishRequest(BaseModel):
    """Model for publishing a blog to WordPress"""
    blog_id: UUID
    wordpress_account_id: UUID
    publish_status: str = "draft"  # draft or publish
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    featured_image_url: Optional[str] = None

class BlogPublishResponse(BaseModel):
    """Model for blog publishing response"""
    blog_id: UUID
    wordpress_url: str
    wordpress_post_id: str
    publish_status: str
    message: str
    published_at: datetime
