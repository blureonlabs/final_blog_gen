from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from core.auth import get_current_user
from core.supabase_client import supabase_client
from services.blog_image_processor import BlogImageProcessor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/blog-images", tags=["blog-image-processing"])

# Initialize blog image processor
blog_image_processor = BlogImageProcessor()

@router.post("/process-blog")
async def process_blog_for_images(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """
    Process a blog post and extract image placeholders for generation
    
    Request body:
    - blog_id: UUID of the blog
    - project_id: UUID of the project
    - title: Blog title
    - content: Blog content
    - style: Image style (optional, default: photographic)
    - aspect_ratio: Image aspect ratio (optional, default: 16:9)
    - quality: Image quality (optional, default: standard)
    """
    try:
        # Validate required fields
        required_fields = ["blog_id", "project_id", "title", "content"]
        for field in required_fields:
            if field not in request:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        blog_id = request["blog_id"]
        project_id = request["project_id"]
        title = request["title"]
        content = request["content"]
        style = request.get("style", "photographic")
        aspect_ratio = request.get("aspect_ratio", "16:9")
        quality = request.get("quality", "standard")
        
        # Validate blog ownership
        blog_response = supabase_client.table("blogs").select("id, project_id").eq("id", blog_id).execute()
        if not blog_response.data:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        blog_data = blog_response.data[0]
        if blog_data["project_id"] != project_id:
            raise HTTPException(status_code=400, detail="Blog project_id mismatch")
        
        project_response = supabase_client.table("projects").select("user_id, generate_images, num_images_per_blog").eq("id", project_id).execute()
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project_data = project_response.data[0]
        if project_data["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if image generation is enabled for this project
        if not project_data.get("generate_images", False):
            raise HTTPException(status_code=400, detail="Image generation is not enabled for this project")
        
        # Get user's Fal AI API key
        api_key_response = supabase_client.table("api_keys").select("api_key").eq("user_id", current_user["id"]).eq("service", "fal").eq("is_active", True).execute()
        
        if not api_key_response.data:
            raise HTTPException(status_code=400, detail="Fal AI API key not found. Please add your Fal AI API key in settings.")
        
        fal_api_key = api_key_response.data[0]["api_key"]
        
        # Process blog content and extract image placeholders
        result = await blog_image_processor.process_blog_for_images(
            blog_id=blog_id,
            project_id=project_id,
            title=title,
            content=content,
            user_id=current_user["id"],
            fal_api_key=fal_api_key
        )
        
        if result["success"]:
            # Log the processing
            supabase_client.table("logs").insert({
                "user_id": current_user["id"],
                "project_id": project_id,
                "blog_id": blog_id,
                "level": "info",
                "category": "image_processing",
                "message": f"Processed {result['images_processed']} image placeholders",
                "metadata": {
                    "images_processed": result["images_processed"],
                    "style": style,
                    "aspect_ratio": aspect_ratio,
                    "quality": quality
                }
            }).execute()
            
            return {
                "success": True,
                "message": result["message"],
                "blog_id": blog_id,
                "project_id": project_id,
                "images_processed": result["images_processed"],
                "stored_images": result.get("stored_images", [])
            }
        else:
            raise HTTPException(status_code=500, detail=f"Image processing failed: {result.get('error', 'Unknown error')}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in blog image processing endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-images")
async def generate_images_for_blog(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """
    Generate images for all pending image placeholders in a blog
    
    Request body:
    - blog_id: UUID of the blog
    - project_id: UUID of the project
    - style: Image style (optional, default: photographic)
    - aspect_ratio: Image aspect ratio (optional, default: 16:9)
    - quality: Image quality (optional, default: standard)
    """
    try:
        # Validate required fields
        required_fields = ["blog_id", "project_id"]
        for field in required_fields:
            if field not in request:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        blog_id = request["blog_id"]
        project_id = request["project_id"]
        style = request.get("style", "photographic")
        aspect_ratio = request.get("aspect_ratio", "16:9")
        quality = request.get("quality", "standard")
        
        # Validate blog ownership
        blog_response = supabase_client.table("blogs").select("id, project_id").eq("id", blog_id).execute()
        if not blog_response.data:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        blog_data = blog_response.data[0]
        if blog_data["project_id"] != project_id:
            raise HTTPException(status_code=400, detail="Blog project_id mismatch")
        
        project_response = supabase_client.table("projects").select("user_id").eq("id", project_id).execute()
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project_data = project_response.data[0]
        if project_data["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get user's Fal AI API key
        api_key_response = supabase_client.table("api_keys").select("api_key").eq("user_id", current_user["id"]).eq("service", "fal").eq("is_active", True).execute()
        
        if not api_key_response.data:
            raise HTTPException(status_code=400, detail="Fal AI API key not found. Please add your Fal AI API key in settings.")
        
        fal_api_key = api_key_response.data[0]["api_key"]
        
        # Generate images for the blog
        result = await blog_image_processor.generate_images_for_blog(
            blog_id=blog_id,
            project_id=project_id,
            user_id=current_user["id"],
            fal_api_key=fal_api_key,
            style=style,
            aspect_ratio=aspect_ratio,
            quality=quality
        )
        
        if result["success"]:
            # Log the generation
            supabase_client.table("logs").insert({
                "user_id": current_user["id"],
                "project_id": project_id,
                "blog_id": blog_id,
                "level": "info",
                "category": "image_generation",
                "message": f"Generated {result['images_generated']} images, {result['images_failed']} failed",
                "metadata": {
                    "images_generated": result["images_generated"],
                    "images_failed": result["images_failed"],
                    "style": style,
                    "aspect_ratio": aspect_ratio,
                    "quality": quality
                }
            }).execute()
            
            return {
                "success": True,
                "message": result["message"],
                "blog_id": blog_id,
                "project_id": project_id,
                "images_generated": result["images_generated"],
                "images_failed": result["images_failed"],
                "generated_images": result.get("generated_images", []),
                "failed_images": result.get("failed_images", [])
            }
        else:
            raise HTTPException(status_code=500, detail=f"Image generation failed: {result.get('error', 'Unknown error')}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in image generation endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-and-generate")
async def process_and_generate_images(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """
    Complete workflow: process blog content and generate images
    
    Request body:
    - blog_id: UUID of the blog
    - project_id: UUID of the project
    - title: Blog title
    - content: Blog content
    - style: Image style (optional, default: photographic)
    - aspect_ratio: Image aspect ratio (optional, default: 16:9)
    - quality: Image quality (optional, default: standard)
    """
    try:
        # Validate required fields
        required_fields = ["blog_id", "project_id", "title", "content"]
        for field in required_fields:
            if field not in request:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        blog_id = request["blog_id"]
        project_id = request["project_id"]
        title = request["title"]
        content = request["content"]
        style = request.get("style", "photographic")
        aspect_ratio = request.get("aspect_ratio", "16:9")
        quality = request.get("quality", "standard")
        
        # Validate blog ownership
        blog_response = supabase_client.table("blogs").select("id, project_id").eq("id", blog_id).execute()
        if not blog_response.data:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        blog_data = blog_response.data[0]
        if blog_data["project_id"] != project_id:
            raise HTTPException(status_code=400, detail="Blog project_id mismatch")
        
        project_response = supabase_client.table("projects").select("user_id, generate_images, num_images_per_blog").eq("id", project_id).execute()
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project_data = project_response.data[0]
        if project_data["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if image generation is enabled for this project
        if not project_data.get("generate_images", False):
            raise HTTPException(status_code=400, detail="Image generation is not enabled for this project")
        
        # Get user's Fal AI API key
        api_key_response = supabase_client.table("api_keys").select("api_key").eq("user_id", current_user["id"]).eq("service", "fal").eq("is_active", True).execute()
        
        if not api_key_response.data:
            raise HTTPException(status_code=400, detail="Fal AI API key not found. Please add your Fal AI API key in settings.")
        
        fal_api_key = api_key_response.data[0]["api_key"]
        
        # Run complete workflow
        result = await blog_image_processor.process_and_generate_images(
            blog_id=blog_id,
            project_id=project_id,
            title=title,
            content=content,
            user_id=current_user["id"],
            fal_api_key=fal_api_key,
            style=style,
            aspect_ratio=aspect_ratio,
            quality=quality
        )
        
        if result["success"]:
            # Log the complete workflow
            supabase_client.table("logs").insert({
                "user_id": current_user["id"],
                "project_id": project_id,
                "blog_id": blog_id,
                "level": "info",
                "category": "complete_image_workflow",
                "message": f"Complete workflow: {result['total_images_processed']} processed, {result['total_images_generated']} generated",
                "metadata": {
                    "total_images_processed": result["total_images_processed"],
                    "total_images_generated": result["total_images_generated"],
                    "total_images_failed": result["total_images_failed"],
                    "style": style,
                    "aspect_ratio": aspect_ratio,
                    "quality": quality
                }
            }).execute()
            
            return {
                "success": True,
                "message": result["message"],
                "blog_id": blog_id,
                "project_id": project_id,
                "workflow_summary": {
                    "total_images_processed": result["total_images_processed"],
                    "total_images_generated": result["total_images_generated"],
                    "total_images_failed": result["total_images_failed"]
                },
                "workflow_details": result.get("workflow_steps", {})
            }
        else:
            raise HTTPException(status_code=500, detail=f"Complete workflow failed: {result.get('error', 'Unknown error')}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in complete workflow endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/blog/{blog_id}/status")
async def get_blog_image_status(
    blog_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get the status of image generation for a specific blog"""
    try:
        # Validate blog ownership
        blog_response = supabase_client.table("blogs").select("id, project_id, title").eq("id", blog_id).execute()
        if not blog_response.data:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        blog_data = blog_response.data[0]
        project_response = supabase_client.table("projects").select("user_id").eq("id", blog_data["project_id"]).execute()
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project_data = project_response.data[0]
        if project_data["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get image status for this blog
        images_response = supabase_client.table("images").select("*").eq("blog_id", blog_id).order("image_number").execute()
        
        images = []
        if images_response.data:
            for img in images_response.data:
                images.append({
                    "id": img["id"],
                    "image_number": img["image_number"],
                    "prompt": img["prompt"],
                    "alt_text": img["alt_text"],
                    "status": img["status"],
                    "s3_url": img.get("s3_url"),
                    "error_message": img.get("error_message"),
                    "created_at": img["created_at"],
                    "updated_at": img["updated_at"]
                })
        
        # Calculate status summary
        total_images = len(images)
        pending_images = len([img for img in images if img["status"] == "pending"])
        generating_images = len([img for img in images if img["status"] == "generating"])
        generated_images = len([img for img in images if img["status"] == "generated"])
        failed_images = len([img for img in images if img["status"] == "failed"])
        
        return {
            "success": True,
            "blog_id": blog_id,
            "blog_title": blog_data["title"],
            "total_images": total_images,
            "status_summary": {
                "pending": pending_images,
                "generating": generating_images,
                "generated": generated_images,
                "failed": failed_images
            },
            "images": images
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting blog image status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
