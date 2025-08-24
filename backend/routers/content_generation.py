from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional
from uuid import UUID
import logging

from models.blog import (
    BlogGenerationRequest, 
    BlogGenerationResponse, 
    BlogResponse,
    BlogListResponse,
    BlogPreview
)
from models.project import ProjectResponse
from core.ai_client import ai_client
from core.supabase_client import supabase_client
from core.auth import get_current_user
from tasks.content_generation import generate_blogs_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content-generation", tags=["Content Generation"])

@router.post("/generate", response_model=BlogGenerationResponse)
async def generate_blogs(
    request: BlogGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(lambda: supabase_client)
):
    """
    Generate multiple blogs for a project
    
    This endpoint starts the blog generation process in the background.
    The actual generation happens asynchronously via Celery tasks.
    """
    try:
        # Validate project exists and belongs to user
        project_response = await supabase.table("projects").select("*").eq("id", str(request.project_id)).eq("user_id", str(current_user["id"])).execute()
        
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found or access denied")
        
        project = project_response.data[0]
        
        # Validate AI model availability
        if not ai_client.is_model_available(request.ai_model, request.ai_model_version):
            raise HTTPException(
                status_code=400, 
                detail=f"AI model {request.ai_model} is not available. Please check your API keys."
            )
        
        # Start background task for blog generation
        task_id = f"blog_gen_{request.project_id}_{current_user['id']}"
        
        # Add to background tasks (this will be replaced by Celery in production)
        background_tasks.add_task(
            generate_blogs_task,
            project_id=str(request.project_id),
            prompt=request.prompt,
            num_blogs=request.num_blogs,
            ai_model=request.ai_model,
            ai_model_version=request.ai_model_version,
            user_id=str(current_user["id"])
        )
        
        # Update project status
        await supabase.table("projects").update({
            "status": "generating",
            "updated_at": "now()"
        }).eq("id", str(request.project_id)).execute()
        
        # Log the generation request
        await supabase.table("logs").insert({
            "project_id": str(request.project_id),
            "message": f"Started generating {request.num_blogs} blogs using {request.ai_model}",
            "timestamp": "now()"
        }).execute()
        
        return BlogGenerationResponse(
            project_id=request.project_id,
            task_id=task_id,
            message=f"Blog generation started for {request.num_blogs} blogs",
            estimated_time=request.num_blogs * 2,  # Rough estimate: 2 minutes per blog
            blogs_requested=request.num_blogs,
            batch_size=request.batch_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting blog generation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/blogs/{project_id}", response_model=BlogListResponse)
async def get_project_blogs(
    project_id: UUID,
    page: int = 1,
    per_page: int = 20,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(lambda: supabase_client)
):
    """
    Get all blogs for a specific project with pagination
    """
    try:
        # Validate project access
        project_response = await supabase.table("projects").select("*").eq("id", str(project_id)).eq("user_id", str(current_user["id"])).execute()
        
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found or access denied")
        
        # Calculate offset for pagination
        offset = (page - 1) * per_page
        
        # Get blogs with pagination
        blogs_response = await supabase.table("blogs").select("*").eq("project_id", str(project_id)).range(offset, offset + per_page - 1).order("created_at", desc=True).execute()
        
        # Get total count
        count_response = await supabase.table("blogs").select("id", count="exact").eq("project_id", str(project_id)).execute()
        total = count_response.count or 0
        
        blogs = []
        for blog in blogs_response.data:
            blogs.append(BlogResponse(
                id=blog["id"],
                project_id=blog["project_id"],
                title=blog.get("title"),
                content=blog.get("content"),
                prompt=blog["prompt"],
                ai_model=blog["ai_model"],
                ai_model_version=blog.get("ai_model_version"),
                seo_meta=blog.get("seo_meta"),
                status=blog["status"],
                wordpress_url=blog.get("wordpress_url"),
                wordpress_post_id=blog.get("wordpress_post_id"),
                error_message=blog.get("error_message"),
                generation_logs=blog.get("generation_logs"),
                created_at=blog["created_at"],
                updated_at=blog["updated_at"]
            ))
        
        return BlogListResponse(
            blogs=blogs,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project blogs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/blog/{blog_id}", response_model=BlogResponse)
async def get_blog(
    blog_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(lambda: supabase_client)
):
    """
    Get a specific blog by ID
    """
    try:
        # Get blog with project info to validate access
        blog_response = await supabase.table("blogs").select("*, projects!inner(*)").eq("id", str(blog_id)).eq("projects.user_id", str(current_user["id"])).execute()
        
        if not blog_response.data:
            raise HTTPException(status_code=404, detail="Blog not found or access denied")
        
        blog = blog_response.data[0]
        
        return BlogResponse(
            id=blog["id"],
            project_id=blog["project_id"],
            title=blog.get("title"),
            content=blog.get("content"),
            prompt=blog["prompt"],
            ai_model=blog["ai_model"],
            ai_model_version=blog.get("ai_model_version"),
            seo_meta=blog.get("seo_meta"),
            status=blog["status"],
            wordpress_url=blog.get("wordpress_url"),
            wordpress_post_id=blog.get("wordpress_post_id"),
            error_message=blog.get("error_message"),
            generation_logs=blog.get("generation_logs"),
            created_at=blog["created_at"],
            updated_at=blog["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching blog: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/preview/{blog_id}", response_model=BlogPreview)
async def get_blog_preview(
    blog_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(lambda: supabase_client)
):
    """
    Get a blog preview (title and first 200 characters) for listing
    """
    try:
        # Get blog with project info to validate access
        blog_response = await supabase.table("blogs").select("*, projects!inner(*)").eq("id", str(blog_id)).eq("projects.user_id", str(current_user["id"])).execute()
        
        if not blog_response.data:
            raise HTTPException(status_code=404, detail="Blog not found or access denied")
        
        blog = blog_response.data[0]
        
        # Create content preview (first 200 characters)
        content_preview = ""
        if blog.get("content"):
            content_preview = blog["content"][:200]
            if len(blog["content"]) > 200:
                content_preview += "..."
        
        return BlogPreview(
            id=blog["id"],
            title=blog.get("title") or "Untitled Blog",
            content_preview=content_preview,
            seo_meta=blog.get("seo_meta"),
            status=blog["status"],
            created_at=blog["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching blog preview: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/available-models")
async def get_available_models():
    """
    Get available AI models for content generation
    """
    try:
        models = ai_client.get_available_models()
        return {
            "models": models,
            "message": "Available AI models for content generation"
        }
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/generation-status/{project_id}")
async def get_generation_status(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(lambda: supabase_client)
):
    """
    Get the current status of blog generation for a project
    """
    try:
        # Validate project access
        project_response = await supabase.table("projects").select("*").eq("id", str(project_id)).eq("user_id", str(current_user["id"])).execute()
        
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found or access denied")
        
        project = project_response.data[0]
        
        # Get blog counts by status
        blogs_response = await supabase.table("blogs").select("status").eq("project_id", str(project_id)).execute()
        
        status_counts = {}
        total_blogs = 0
        
        for blog in blogs_response.data:
            status = blog["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
            total_blogs += 1
        
        # Calculate progress percentage
        progress = 0
        if project["num_blogs"] > 0:
            completed = status_counts.get("ready", 0) + status_counts.get("published", 0)
            progress = int((completed / project["num_blogs"]) * 100)
        
        return {
            "project_id": str(project_id),
            "project_name": project["name"],
            "total_blogs_requested": project["num_blogs"],
            "blogs_generated": total_blogs,
            "progress_percentage": progress,
            "status_breakdown": status_counts,
            "project_status": project["status"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting generation status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
