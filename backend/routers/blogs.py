from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from uuid import UUID, uuid4
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
from tasks.content_generation import generate_blogs_task, retry_failed_blog
from tasks.wordpress_publishing import publish_to_wordpress_task

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/generate", response_model=BlogGenerationResponse, summary="Generate blogs for a project")
async def generate_blogs(
    request: BlogGenerationRequest,
    # current_user: dict = Depends(get_current_user)  # Temporarily disabled for testing
):
    """
    Start blog generation for a project
    """
    try:
        # Temporarily use a mock user ID for testing
        user_id = str(uuid4())  # Generate a proper UUID instead of "test-user-123"
        
        # Verify user exists in database
        # if not await verify_user_exists(user_id):  # Temporarily disabled
        #     raise HTTPException(status_code=404, detail="User not found")
        
        # Verify project exists and belongs to user
        # project_response = supabase_client.table("projects").select("*").eq("id", str(request.project_id)).eq("user_id", user_id).execute()
        # if not project_response.data:
        #     raise HTTPException(status_code=404, detail="Project not found")
        # project = project_response.data[0]
        
        # For testing, create a mock project
        project = {
            "id": str(request.project_id),
            "status": "pending"
        }
        
        # Check if project is already running
        if project["status"] in ["running", "in_progress"]:
            raise HTTPException(status_code=400, detail="Project is already running")
        
        # Create some test blogs immediately for testing
        try:
            print(f"🔍 Starting to create {request.num_blogs} test blogs...")
            test_blogs = []
            for i in range(request.num_blogs):
                blog_data = {
                    "id": str(uuid4()),
                    "project_id": str(request.project_id),
                    "user_id": None,  # Set to NULL to bypass foreign key constraint
                    "title": f"Test Blog {i+1}: {request.prompt}",
                    "content": f"This is test content for blog {i+1}. The prompt was: {request.prompt}",
                    "status": "ready" if i < 3 else "generating" if i < 7 else "draft",  # Use valid statuses
                    "word_count": 500 + (i * 100),
                    "ai_model": request.ai_model,
                    "prompt": request.prompt,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                test_blogs.append(blog_data)
                print(f"📝 Prepared blog {i+1}: {blog_data['title']}")
            
            # Insert test blogs into database
            print(f"💾 Attempting to insert {len(test_blogs)} blogs into Supabase...")
            for i, blog in enumerate(test_blogs):
                try:
                    print(f"🔄 Inserting blog {i+1} with ID: {blog['id']}")
                    response = supabase_client.table("blogs").insert(blog).execute()
                    print(f"✅ Successfully created blog {i+1}: {blog['title']}")
                    print(f"   Response: {response.data}")
                except Exception as e:
                    print(f"❌ Failed to create blog {i+1}: {e}")
                    print(f"   Blog data: {blog}")
                    
        except Exception as e:
            print(f"❌ Error in test blog creation: {e}")
            import traceback
            traceback.print_exc()
        
        # Start blog generation task (simulated for now)
        # task = generate_blogs_task.delay(
        #     str(request.project_id),
        #     request.prompt,
        #     request.num_blogs,
        #     request.ai_model,
        #     request.batch_size
        # )
        
        # For testing, simulate the task
        task_id = str(uuid4())
        
        # Update project status in Supabase if possible
        try:
            supabase_client.table("projects").update({
                "status": "in_progress",
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", str(request.project_id)).execute()
        except Exception as e:
            print(f"Warning: Could not update project status: {e}")
        
        logger.info(f"Blog generation started for project {request.project_id}: {request.num_blogs} blogs")
        
        return BlogGenerationResponse(
            project_id=request.project_id,
            task_id=task_id,
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
    # current_user: dict = Depends(get_current_user)  # Temporarily disabled for testing
):
    """
    Get paginated list of blogs for a project
    """
    try:
        # Temporarily use a mock user ID for testing
        user_id = "test-user-123"  # This will be replaced with real auth later
        
        # Verify project belongs to user
        # project_response = supabase_client.table("projects").select("id").eq("id", str(project_id)).eq("user_id", user_id).execute()
        # if not project_response.data:
        #     raise HTTPException(status_code=404, detail="Project not found")
        
        # For testing, skip project verification
        
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
    # current_user: dict = Depends(get_current_user)  # Temporarily disabled for testing
):
    """
    Publish a blog to WordPress
    """
    try:
        # Temporarily use a mock user ID for testing
        user_id = "test-user-123"  # Mock user ID for testing
        
        # Check if blog exists (temporarily skip user ownership check)
        existing_response = supabase_client.table("blogs").select("*").eq("id", str(blog_id)).execute()
        
        if not existing_response.data:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        blog = existing_response.data[0]
        
        # Check if blog is ready for publishing
        if blog["status"] == "failed":
            # For failed blogs, try to retry generation first
            logger.info(f"Blog {blog_id} is failed, attempting to retry generation before publishing")
            retry_result = await retry_failed_blog(str(blog_id))
            
            if not retry_result.get("success"):
                raise HTTPException(status_code=400, detail=f"Blog retry failed: {retry_result.get('error', 'Unknown error')}. Cannot publish.")
            
            # Blog is now regenerated as draft, but we need to wait for it to be ready
            # For now, we'll allow draft blogs to be published directly
            logger.info(f"Blog {blog_id} retry successful, proceeding with publishing")
        elif blog["status"] not in ["ready", "published", "draft"]:
            raise HTTPException(status_code=400, detail="Blog is not ready for publishing. Current status: " + blog["status"])
        
        # Call the publishing function directly instead of using Celery
        try:
            logger.info(f"🚀 Starting WordPress publishing for blog {blog_id}")
            
            # Call the function directly
            result = publish_to_wordpress_task(
                str(blog_id),
                str(publish_request.wordpress_account_id),
                publish_request.publish_status
            )
            
            logger.info(f"Blog publishing completed for blog {blog_id}")
            
            if result.get("status") == "published":
                return BlogPublishResponse(
                    blog_id=blog_id,
                    wordpress_url=result.get("wordpress_url", ""),
                    wordpress_post_id=str(result.get("wordpress_post_id", "")),  # Convert to string
                    publish_status=publish_request.publish_status,
                    message="Blog published successfully",
                    published_at=datetime.utcnow()
                )
            else:
                raise HTTPException(status_code=500, detail=f"Publishing failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error in direct publishing: {e}")
            raise HTTPException(status_code=500, detail=f"Publishing failed: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting blog publishing: {e}")
        raise HTTPException(status_code=500, detail="Failed to start blog publishing: {str(e)}")

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

@router.post("/{blog_id}/retry", summary="Retry failed blog generation")
async def retry_blog(
    blog_id: UUID,
    # current_user: dict = Depends(get_current_user)  # Temporarily disabled for testing
):
    """
    Retry generation for a failed blog
    """
    try:
        # Temporarily use a mock user ID for testing
        user_id = "test-user-123"  # Mock user ID for testing
        
        # Check if blog exists
        existing_response = supabase_client.table("blogs").select("*").eq("id", str(blog_id)).execute()
        
        if not existing_response.data:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        blog = existing_response.data[0]
        
        # Check if blog is actually failed
        if blog["status"] != "failed":
            raise HTTPException(status_code=400, detail="Blog is not in failed status. Current status: " + blog["status"])
        
        # Call the retry function
        result = await retry_failed_blog(str(blog_id))
        
        if result.get("success"):
            return {
                "message": "Blog retry initiated successfully",
                "blog_id": blog_id,
                "new_status": "draft"
            }
        else:
            raise HTTPException(status_code=500, detail=f"Retry failed: {result.get('error', 'Unknown error')}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying blog: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retry blog: {str(e)}")
