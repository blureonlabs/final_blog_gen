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
from services.blog_generation_service import blog_generation_service

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
        project_response = supabase.table("projects").select("*").eq("id", str(request.project_id)).eq("user_id", str(current_user["id"])).execute()
        
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
        supabase.table("projects").update({
            "status": "in_progress",
            "updated_at": "now()"
        }).eq("id", str(request.project_id)).execute()
        
        # Log the generation request
        supabase.table("logs").insert({
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

@router.post("/generate-direct", response_model=BlogGenerationResponse)
async def generate_blogs_direct(
    request: BlogGenerationRequest,
    supabase = Depends(lambda: supabase_client)
):
    """
    Generate blogs directly using the blog generation service
    
    This endpoint generates blogs immediately without background tasks.
    Useful for testing and small batches.
    """
    try:
        # Validate project exists (no user authentication required for demo)
        project_response = supabase.table("projects").select("*").eq("id", str(request.project_id)).execute()
        
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = project_response.data[0]
        
        # Get project details for blog generation
        project_description = project.get("description", "Blog content generation")
        user_id = project.get("user_id")
        
        # Fetch API keys from the api_keys table for the user
        api_keys_response = supabase.table("api_keys").select("*").eq("user_id", str(user_id)).eq("is_active", True).execute()
        
        if not api_keys_response.data:
            logger.error(f"❌ No active API keys found for user {user_id}")
            raise HTTPException(
                status_code=400, 
                detail="No active API keys found. Please configure your API keys first."
            )
        
        # Organize API keys by service
        project_api_keys = {}
        for key_record in api_keys_response.data:
            service = key_record.get("service")
            api_key = key_record.get("api_key")
            if service and api_key:
                project_api_keys[service] = api_key
        
        # Add detailed logging for debugging
        logger.info(f"🔍 Project data: {project}")
        logger.info(f"🔍 User ID: {user_id}")
        logger.info(f"🔍 Fetched API keys: {list(project_api_keys.keys())}")
        logger.info(f"🔍 Project description: {project_description}")
        logger.info(f"🔍 AI model requested: {request.ai_model}")
        logger.info(f"🔍 Number of blogs requested: {request.num_blogs}")
        
        # Check if user has required API keys for the requested model
        if request.ai_model == "openai" and not project_api_keys.get("openai"):
            logger.error(f"❌ No OpenAI API key found for user {user_id}")
            raise HTTPException(
                status_code=400, 
                detail="OpenAI API key not configured. Please add your OpenAI API key first."
            )
        elif request.ai_model == "gemini" and not project_api_keys.get("gemini"):
            logger.error(f"❌ No Gemini API key found for user {user_id}")
            raise HTTPException(
                status_code=400, 
                detail="Gemini API key not configured. Please add your Gemini API key first."
            )
        
        logger.info(f"✅ API keys found: OpenAI={bool(project_api_keys.get('openai'))}, Gemini={bool(project_api_keys.get('gemini'))}")
        
        # Update project status to in_progress
        supabase.table("projects").update({
            "status": "in_progress",
            "updated_at": "now()"
        }).eq("id", str(request.project_id)).execute()
        
        logger.info(f"🚀 Starting blog generation with service...")
        
        # Generate blogs using the service with project details and API keys
        generated_blogs = await blog_generation_service.generate_blogs_for_project(
            project_id=str(request.project_id),
            project_description=project_description,
            num_blogs=request.num_blogs,
            ai_model=request.ai_model,
            project_api_keys=project_api_keys
        )
        
        logger.info(f"✅ Blog generation completed: {len(generated_blogs)} blogs generated")
        
        # Update project status and completed blogs count
        supabase.table("projects").update({
            "status": "completed",
            "completed_blogs": len(generated_blogs),
            "updated_at": "now()"
        }).eq("id", str(request.project_id)).execute()
        
        # Log the generation completion
        # TODO: Create logs table or use alternative logging
        # supabase.table("logs").insert({
        #     "project_id": str(request.project_id),
        #     "level": "info",
        #     "category": "generation",
        #     "message": f"Generated {len(generated_blogs)} blogs successfully using {request.ai_model}",
        #     "metadata": {
        #         "ai_model": request.ai_model,
        #         "blogs_generated": len(generated_blogs),
        #         "project_description": project_description
        #     }
        # }).execute()
        
        return BlogGenerationResponse(
            project_id=request.project_id,
            task_id=f"direct_gen_{request.project_id}",
            message=f"Successfully generated {len(generated_blogs)} blogs",
            estimated_time=0,  # Already completed
            blogs_requested=request.num_blogs,
            batch_size=request.num_blogs
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in direct blog generation: {e}")
        logger.error(f"❌ Error type: {type(e)}")
        logger.error(f"❌ Error details: {str(e)}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Blog generation failed: {str(e)}")

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
        project_response = supabase.table("projects").select("*").eq("id", str(project_id)).eq("user_id", str(current_user["id"])).execute()
        
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found or access denied")
        
        # Calculate offset for pagination
        offset = (page - 1) * per_page
        
        # Get blogs with pagination
        blogs_response = supabase.table("blogs").select("*").eq("project_id", str(project_id)).range(offset, offset + per_page - 1).order("created_at", desc=True).execute()
        
        # Get total count
        count_response = supabase.table("blogs").select("id", count="exact").eq("project_id", str(project_id)).execute()
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
    Get a specific blog by ID with content from storage
    """
    try:
        # Get blog with project info to validate access
        blog_response = supabase.table("blogs").select("*, projects!inner(*)").eq("id", str(blog_id)).eq("projects.user_id", str(current_user["id"])).execute()
        
        if not blog_response.data:
            raise HTTPException(status_code=404, detail="Blog not found or access denied")
        
        blog = blog_response.data[0]
        
        # Retrieve content from storage
        try:
            content_data = await blog_generation_service.get_blog_content(
                storage_path=blog["storage_path"],
                bucket_name=blog.get("storage_bucket", "blog-content")
            )
            
            # Extract content from storage data
            content = content_data.get("content", "")
            prompt = content_data.get("prompt", blog.get("prompt", ""))
            ai_model = content_data.get("ai_model", blog.get("ai_model", ""))
            
        except Exception as storage_error:
            logger.warning(f"Could not retrieve content from storage: {storage_error}")
            # Fallback to metadata only
            content = ""
            prompt = blog.get("prompt", "")
            ai_model = blog.get("ai_model", "")
        
        return BlogResponse(
            id=blog["id"],
            project_id=blog["project_id"],
            title=blog.get("title"),
            content=content,
            prompt=prompt,
            ai_model=ai_model,
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
        blog_response = supabase.table("blogs").select("*, projects!inner(*)").eq("id", str(blog_id)).eq("projects.user_id", str(current_user["id"])).execute()
        
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
        project_response = supabase.table("projects").select("*").eq("id", str(project_id)).eq("user_id", str(current_user["id"])).execute()
        
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found or access denied")
        
        project = project_response.data[0]
        
        # Get blog counts by status
        blogs_response = supabase.table("blogs").select("status").eq("project_id", str(project_id)).execute()
        
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
            "num_blogs_requested": project["num_blogs"],
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
