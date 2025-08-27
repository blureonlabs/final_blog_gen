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
        supabase.table("activity_logs").insert({
            "user_id": str(current_user["id"]),
            "action": f"Started generating {request.num_blogs} blogs using {request.ai_model}",
            "level": "info",
            "category": "generation",
            "timestamp": "now()",
            "metadata": {
                "details": {
                    "project_id": str(request.project_id),
                    "ai_model": request.ai_model,
                    "num_blogs": request.num_blogs
                }
            }
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
        
        # Check if project is already in progress or completed to prevent duplicate requests
        if project.get("status") == "in_progress":
            logger.warning(f"⚠️ Project {request.project_id} is already in progress, rejecting duplicate request")
            raise HTTPException(
                status_code=409,
                detail="Project is already generating content. Please wait for the current generation to complete."
            )
        
        if project.get("status") == "completed":
            logger.warning(f"⚠️ Project {request.project_id} is already completed, rejecting duplicate request")
            raise HTTPException(
                status_code=409,
                detail="Project is already completed. Cannot start new generation."
            )
        
        # Additional check: Look for blogs that are currently being generated
        blogs_response = supabase.table("blogs").select("status").eq("project_id", str(request.project_id)).execute()
        if blogs_response.data:
            generating_blogs = [blog for blog in blogs_response.data if blog.get("status") == "generating"]
            if generating_blogs:
                logger.warning(f"⚠️ Project {request.project_id} has {len(generating_blogs)} blogs currently being generated")
                raise HTTPException(
                    status_code=409,
                    detail=f"Project has {len(generating_blogs)} blogs currently being generated. Please wait for them to complete."
                )
        
        # Get project details for blog generation
        project_description = project.get("description", "Blog content generation")
        user_id = project.get("user_id")
        
        # Use the user's selected AI model from the request
        ai_model = request.ai_model
        
        logger.info(f"🔍 Using user-selected AI model:")
        logger.info(f"  - AI Model: {ai_model}")
        
        # Get project's configured API key IDs
        project_api_key_ids = project.get("api_keys", {})
        logger.info(f"🔍 Project API key IDs: {project_api_key_ids}")
        
        # Fetch actual API key values using the project's API key IDs
        project_api_keys = {}
        if project_api_key_ids:
            for service, api_key_id in project_api_key_ids.items():
                if service in ["openai", "gemini", "serp"]:  # Only fetch for supported services
                    try:
                        api_key_response = supabase.table("api_keys").select("api_key").eq("id", api_key_id).execute()
                        if api_key_response.data:
                            project_api_keys[service] = api_key_response.data[0]["api_key"]
                            logger.info(f"✅ Fetched {service} API key for project")
                        else:
                            logger.warning(f"⚠️ No API key found for {service} with ID {api_key_id}")
                    except Exception as e:
                        logger.error(f"❌ Error fetching {service} API key: {e}")
        
        # Fallback: if no project-specific API keys, try user's global API keys
        if not project_api_keys:
            logger.info(f"🔄 No project-specific API keys found, trying user's global API keys...")
            api_keys_response = supabase.table("api_keys").select("*").eq("user_id", str(user_id)).eq("is_active", True).execute()
            
            if api_keys_response.data:
                for key_record in api_keys_response.data:
                    service = key_record.get("service")
                    api_key = key_record.get("api_key")
                    if service and api_key:
                        project_api_keys[service] = api_key
                logger.info(f"✅ Using user's global API keys: {list(project_api_keys.keys())}")
            else:
                logger.error(f"❌ No API keys found for user {user_id}")
                raise HTTPException(
                    status_code=400, 
                    detail="No API keys found. Please configure your API keys first."
                )
        
        # Add detailed logging for debugging
        logger.info(f"🔍 Project data: {project}")
        logger.info(f"🔍 User ID: {user_id}")
        logger.info(f"🔍 Fetched API keys: {list(project_api_keys.keys())}")
        logger.info(f"🔍 Project description: {project_description}")
        logger.info(f"🔍 AI model requested: {request.ai_model}")
        logger.info(f"🔍 Project AI model: {ai_model}")
        logger.info(f"🔍 Number of blogs requested: {request.num_blogs}")
        
        # Check if user has required API keys for the project's configured model
        if ai_model == "openai" and not project_api_keys.get("openai"):
            logger.error(f"❌ No OpenAI API key found for user {user_id}")
            raise HTTPException(
                status_code=400, 
                detail="OpenAI API key not configured. Please add your OpenAI API key first."
            )
        elif ai_model == "gemini" and not project_api_keys.get("gemini"):
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
        # Use the user's selected AI model
        generated_blogs = await blog_generation_service.generate_blogs_for_project(
            project_id=str(request.project_id),
            project_description=project_description,
            num_blogs=request.num_blogs,
            ai_model=ai_model,  # Use user's selected AI model
            project_api_keys=project_api_keys,
            max_concurrent_blogs=getattr(request, 'max_concurrent_blogs', 5)
        )
        
        logger.info(f"✅ Blog generation completed: {len(generated_blogs)} blogs generated")
        
        # Update project status and completed blogs count
        supabase.table("projects").update({
            "status": "completed",
            "completed_blogs": len(generated_blogs),
            "updated_at": "now()"
        }).eq("id", str(request.project_id)).execute()
        
        # Log the generation completion
        generation_method = "multi-threaded" if request.num_blogs > 1 else "sequential"
        supabase.table("activity_logs").insert({
            "user_id": str(user_id),
            "action": f"Generated {len(generated_blogs)} blogs successfully using {request.ai_model} ({generation_method})",
            "level": "info",
            "category": "generation",
            "timestamp": "now()",
            "metadata": {
                "details": {
                    "project_id": str(request.project_id),
                    "ai_model": request.ai_model,
                    "blogs_generated": len(generated_blogs),
                    "project_description": project_description,
                    "generation_method": generation_method,
                    "max_concurrent_blogs": getattr(request, 'max_concurrent_blogs', 5)
                }
            }
        }).execute()
        
        return BlogGenerationResponse(
            project_id=request.project_id,
            task_id=f"direct_gen_{request.project_id}",
            message=f"Successfully generated {len(generated_blogs)} blogs using {generation_method} generation",
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
        blogs_response = supabase.table("blogs").select("*").eq("project_id", str(project_id)).range(offset, offset + per_page).order("created_at", desc=True).execute()
        
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
    Get a specific blog by ID with content from storage (requires authentication)
    """
    try:
        # Get blog with project info to validate access
        blog_response = supabase.table("blogs").select("*, projects!inner(*)").eq("id", str(blog_id)).eq("projects.user_id", str(current_user["id"])).execute()
        
        if not blog_response.data:
            raise HTTPException(status_code=404, detail="Blog not found or access denied")
        
        blog = blog_response.data[0]
        
        # Retrieve content from storage
        try:
            content_data = blog_generation_service.get_blog_content(
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

@router.get("/blog/{blog_id}/public", response_model=BlogResponse)
async def get_blog_public(
    blog_id: UUID,
    supabase = Depends(lambda: supabase_client)
):
    """
    Get a specific blog by ID with content from storage (public access, no authentication required)
    """
    try:
        logger.info(f"🔍 Fetching blog {blog_id} from database...")
        
        # Get blog without user validation (public access)
        blog_response = supabase.table("blogs").select("*").eq("id", str(blog_id)).execute()
        
        logger.info(f"📊 Database response: {blog_response.data}")
        
        if not blog_response.data:
            logger.warning(f"❌ Blog {blog_id} not found in database")
            raise HTTPException(status_code=404, detail="Blog not found")
        
        blog = blog_response.data[0]
        logger.info(f"📝 Found blog: {blog.get('title', 'No title')}")
        logger.info(f"📝 Blog keys: {list(blog.keys())}")
        
        # Retrieve content from storage
        try:
            storage_path = blog.get("storage_path")
            bucket_name = blog.get("storage_bucket", "blog-content")
            
            logger.info(f"🔍 Attempting to retrieve from storage: {bucket_name}/{storage_path}")
            
            if storage_path and bucket_name:
                content_data = blog_generation_service.get_blog_content(
                    storage_path=storage_path,
                    bucket_name=bucket_name
                )
                
                # Extract content from storage data
                content = content_data.get("content", "")
                prompt = content_data.get("prompt", blog.get("prompt", ""))
                ai_model = content_data.get("ai_model", blog.get("ai_model", ""))
                
                logger.info(f"📝 Retrieved content from storage, length: {len(content)}")
                
            else:
                logger.warning(f"⚠️ No storage path or bucket for blog {blog_id}")
                content = blog.get("content", "")  # Fallback to database content
                prompt = blog.get("prompt", "")
                ai_model = blog.get("ai_model", "")
                
        except Exception as storage_error:
            logger.warning(f"Could not retrieve content from storage: {storage_error}")
            # Fallback to database content if available
            content = blog.get("content", "")
            prompt = blog.get("prompt", "")
            ai_model = blog.get("ai_model", "")
            logger.info(f"🔄 Using database fallback content, length: {len(content) if content else 0}")
        
        # Log what we found for debugging
        logger.info(f"📝 Blog {blog_id} final content length: {len(content) if content else 0}")
        logger.info(f"📝 Blog {blog_id} has content: {bool(content)}")
        logger.info(f"📝 Blog {blog_id} content preview: {content[:100] if content else 'No content'}...")
        
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
