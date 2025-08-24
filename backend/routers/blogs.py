from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from uuid import UUID
import logging
from datetime import datetime

from models.blog import (
    BlogCreate, 
    BlogUpdate, 
    BlogResponse, 
    BlogListResponse,
    BlogGenerationRequest,
    BlogGenerationResponse,
    BlogPreview,
    BlogPublishRequest,
    BlogPublishResponse
)
from core.supabase_client import supabase_client, verify_user_exists
from core.auth import get_current_user
from tasks.content_generation import generate_blogs_for_project
from tasks.wordpress_publishing import bulk_publish_to_wordpress_task

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/generate", response_model=BlogGenerationResponse, summary="Generate blogs for a project")
async def generate_blogs(
    request: BlogGenerationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Start blog generation for a project
    """
    try:
        user_id = current_user["id"]
        
        # Verify user exists in database
        if not await verify_user_exists(user_id):
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify project exists and belongs to user
        project_response = supabase_client.table("projects").select("*").eq("id", str(request.project_id)).eq("user_id", user_id).execute()
        
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = project_response.data[0]
        
        # Check if project is already running
        if project["status"] in ["running", "generating"]:
            raise HTTPException(status_code=400, detail="Project is already running")
        
        # Start blog generation task
        task = generate_blogs_for_project.delay(
            str(request.project_id),
            request.prompt,
            request.num_blogs,
            request.ai_model,
            request.batch_size
        )
        
        # Update project status
        supabase_client.table("projects").update({
            "status": "running",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", str(request.project_id)).execute()
        
        logger.info(f"Blog generation started for project {request.project_id}: {request.num_blogs} blogs")
        
        return BlogGenerationResponse(
            project_id=request.project_id,
            task_id=task.id,
            message=f"Started generating {request.num_blogs} blogs",
            estimated_time=max(1, request.num_blogs // 5),  # Rough estimate: 5 blogs per minute
            blogs_requested=request.num_blogs,
            batch_size=request.batch_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting blog generation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start blog generation: {str(e)}")

@router.get("/project/{project_id}", response_model=BlogListResponse, summary="Get blogs for a project")
async def get_project_blogs(
    project_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get paginated list of blogs for a project
    """
    try:
        user_id = current_user["id"]
        
        # Verify project belongs to user
        project_response = supabase_client.table("projects").select("id").eq("id", str(project_id)).eq("user_id", user_id).execute()
        
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Build query
        query = supabase_client.table("blogs").select("*").eq("project_id", str(project_id))
        
        # Add status filter if provided
        if status:
            query = query.eq("status", status)
        
        # Get total count
        count_response = query.execute()
        total = len(count_response.data)
        
        # Get paginated results
        offset = (page - 1) * per_page
        response = query.range(offset, offset + per_page - 1).order("created_at", desc=True).execute()
        
        blogs = [BlogResponse(**blog) for blog in response.data]
        
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
        raise HTTPException(status_code=500, detail=f"Failed to fetch project blogs: {str(e)}")

@router.get("/{blog_id}", response_model=BlogResponse, summary="Get blog by ID")
async def get_blog(
    blog_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific blog by ID
    """
    try:
        user_id = current_user["id"]
        
        # Get blog from database
        response = supabase_client.table("blogs").select("*, projects!inner(*)").eq("blogs.id", str(blog_id)).eq("projects.user_id", user_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        blog = response.data[0]
        return BlogResponse(**blog)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching blog: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch blog: {str(e)}")

@router.put("/{blog_id}", response_model=BlogResponse, summary="Update blog")
async def update_blog(
    blog_id: UUID,
    blog_update: BlogUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a blog
    """
    try:
        user_id = current_user["id"]
        
        # Check if blog exists and belongs to user
        existing_response = supabase_client.table("blogs").select("*, projects!inner(*)").eq("blogs.id", str(blog_id)).eq("projects.user_id", user_id).execute()
        
        if not existing_response.data:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        # Prepare update data
        update_data = blog_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Update blog
        response = supabase_client.table("blogs").update(update_data).eq("id", str(blog_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to update blog")
        
        updated_blog = response.data[0]
        logger.info(f"Blog updated successfully: {blog_id}")
        
        return BlogResponse(**updated_blog)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating blog: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update blog: {str(e)}")

@router.post("/{blog_id}/publish", response_model=BlogPublishResponse, summary="Publish blog to WordPress")
async def publish_blog(
    blog_id: UUID,
    publish_request: BlogPublishRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Publish a blog to WordPress
    """
    try:
        user_id = current_user["id"]
        
        # Check if blog exists and belongs to user
        existing_response = supabase_client.table("blogs").select("*, projects!inner(*)").eq("blogs.id", str(blog_id)).eq("projects.user_id", user_id).execute()
        
        if not existing_response.data:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        blog = existing_response.data[0]
        
        # Check if blog is ready for publishing
        if blog["status"] != "ready":
            raise HTTPException(status_code=400, detail="Blog is not ready for publishing. Current status: " + blog["status"])
        
        # Start publishing task
        task = bulk_publish_to_wordpress_task.delay(
            str(blog["project_id"]),
            str(publish_request.wordpress_account_id),
            publish_request.publish_status
        )
        
        logger.info(f"Blog publishing started for blog {blog_id}")
        
        return BlogPublishResponse(
            blog_id=blog_id,
            wordpress_url="",  # Will be updated when task completes
            wordpress_post_id="",  # Will be updated when task completes
            publish_status=publish_request.publish_status,
            message="Blog publishing started",
            published_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting blog publishing: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start blog publishing: {str(e)}")

@router.get("/{blog_id}/preview", response_model=BlogPreview, summary="Get blog preview")
async def get_blog_preview(
    blog_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get blog preview for publishing
    """
    try:
        user_id = current_user["id"]
        
        # Get blog from database
        response = supabase_client.table("blogs").select("*, projects!inner(*)").eq("blogs.id", str(blog_id)).eq("projects.user_id", user_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        blog = response.data[0]
        
        # Create preview
        content_preview = blog.get("content", "")[:200] + "..." if len(blog.get("content", "")) > 200 else blog.get("content", "")
        
        return BlogPreview(
            id=blog["id"],
            title=blog.get("title", "Untitled"),
            content_preview=content_preview,
            seo_meta=blog.get("seo_meta"),
            status=blog["status"],
            created_at=blog["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching blog preview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch blog preview: {str(e)}")

@router.delete("/{blog_id}", summary="Delete blog")
async def delete_blog(
    blog_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a blog
    """
    try:
        user_id = current_user["id"]
        
        # Check if blog exists and belongs to user
        existing_response = supabase_client.table("blogs").select("*, projects!inner(*)").eq("blogs.id", str(blog_id)).eq("projects.user_id", user_id).execute()
        
        if not existing_response.data:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        # Delete blog
        response = supabase_client.table("blogs").delete().eq("id", str(blog_id)).execute()
        
        logger.info(f"Blog deleted successfully: {blog_id}")
        
        return {"message": "Blog deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting blog: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete blog: {str(e)}")
