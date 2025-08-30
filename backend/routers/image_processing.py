from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from core.auth import get_current_user
from core.supabase_client import supabase_client
from services.blog_generation_service import blog_generation_service
from models.blog import BlogStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/image-processing", tags=["image-processing"])

@router.post("/process-blog/{blog_id}")
async def process_blog_images(
    blog_id: str,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """
    Process a blog with image placeholders: generate images and store in S3
    
    This endpoint:
    1. Finds image placeholders in the blog content
    2. Stores them in the images table
    3. Generates images using Fal AI FLUX model
    4. Stores images in S3 bucket
    5. Updates blog content with S3 URLs
    """
    try:
        # Validate blog ownership
        blog_response = supabase_client.table("blogs").select("id, project_id, title, content, status").eq("id", blog_id).execute()
        if not blog_response.data:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        blog_data = blog_response.data[0]
        project_response = supabase_client.table("projects").select("user_id, generate_images").eq("id", blog_data["project_id"]).execute()
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
            raise HTTPException(status_code=400, detail="Fal AI API key not found.")
        
        fal_api_key = api_key_response.data[0]["api_key"]
        
        # Update blog status to image processing
        supabase_client.table("blogs").update({
            "status": BlogStatus.IMAGE_GENERATING.value,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", blog_id).execute()
        
        # Process blog with images
        result = await blog_generation_service.process_blog_with_images(
            blog_id=blog_id,
            project_id=blog_data["project_id"],
            content=blog_data["content"],
            title=blog_data["title"],
            fal_api_key=fal_api_key,
            s3_bucket_name="images"
        )
        
        if result["success"]:
            # Update blog status based on results
            if result["images_processed"] > 0:
                if result["content_updated"]:
                    status = BlogStatus.READY.value
                    message = f"✅ {result['message']} and content updated with S3 images"
                else:
                    status = BlogStatus.IMAGE_GENERATING.value
                    message = f"⚠️ {result['message']} but content update failed"
            else:
                status = BlogStatus.READY.value
                message = result["message"]
            
            # Update blog status
            supabase_client.table("blogs").update({
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", blog_id).execute()
            
            # Log the successful processing
            supabase_client.table("logs").insert({
                "user_id": current_user["id"],
                "project_id": blog_data["project_id"],
                "blog_id": blog_id,
                "level": "info",
                "category": "image_processing",
                "message": message,
                "metadata": {
                    "images_processed": result["images_processed"],
                    "content_updated": result["content_updated"]
                }
            }).execute()
            
            return {
                "success": True,
                "message": message,
                "blog_id": blog_id,
                "images_processed": result["images_processed"],
                "content_updated": result["content_updated"],
                "status": status
            }
        else:
            # Update blog status to failed
            supabase_client.table("blogs").update({
                "status": BlogStatus.FAILED.value,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", blog_id).execute()
            
            # Log the failure
            supabase_client.table("logs").insert({
                "user_id": current_user["id"],
                "project_id": blog_data["project_id"],
                "blog_id": blog_id,
                "level": "error",
                "category": "image_processing",
                "message": f"Image processing failed: {result.get('error', 'Unknown error')}",
                "metadata": {
                    "error": result.get("error", "Unknown error")
                }
            }).execute()
            
            raise HTTPException(status_code=500, detail=f"Image processing failed: {result.get('error', 'Unknown error')}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in image processing endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/blog/{blog_id}/status")
async def get_blog_image_status(
    blog_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get the current status of image processing for a blog"""
    try:
        # Validate blog ownership
        blog_response = supabase_client.table("blogs").select("id, project_id, status").eq("id", blog_id).execute()
        if not blog_response.data:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        blog_data = blog_response.data[0]
        project_response = supabase_client.table("projects").select("user_id").eq("id", blog_data["project_id"]).execute()
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project_data = project_response.data[0]
        if project_data["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get image processing status
        images_response = supabase_client.table("images").select("id, image_number, status, prompt, s3_url, error_message, created_at, updated_at").eq("blog_id", blog_id).order("image_number").execute()
        
        images = []
        if images_response.data:
            for img in images_response.data:
                images.append({
                    "id": img["id"],
                    "image_number": img["image_number"],
                    "status": img["status"],
                    "prompt": img["prompt"],
                    "s3_url": img.get("s3_url"),
                    "error_message": img.get("error_message"),
                    "created_at": img["created_at"],
                    "updated_at": img["updated_at"]
                })
        
        # Calculate processing statistics
        total_images = len(images)
        pending_images = len([img for img in images if img["status"] == "pending"])
        generating_images = len([img for img in images if img["status"] == "generating"])
        generated_images = len([img for img in images if img["status"] == "generated"])
        failed_images = len([img for img in images if img["status"] == "failed"])
        
        # Determine overall status
        if total_images == 0:
            overall_status = "no_images"
        elif failed_images == total_images:
            overall_status = "all_failed"
        elif generated_images == total_images:
            overall_status = "completed"
        elif generating_images > 0 or pending_images > 0:
            overall_status = "in_progress"
        else:
            overall_status = "partial_success"
        
        return {
            "success": True,
            "blog_id": blog_id,
            "blog_status": blog_data["status"],
            "overall_status": overall_status,
            "statistics": {
                "total_images": total_images,
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

@router.post("/retry-failed/{blog_id}")
async def retry_failed_images(
    blog_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Retry processing failed images for a blog"""
    try:
        # Validate blog ownership
        blog_response = supabase_client.table("blogs").select("id, project_id").eq("id", blog_id).execute()
        if not blog_response.data:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        blog_data = blog_response.data[0]
        project_response = supabase_client.table("projects").select("user_id").eq("id", blog_data["project_id"]).execute()
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project_data = project_response.data[0]
        if project_data["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get failed images
        failed_images_response = supabase_client.table("images").select("*").eq("blog_id", blog_id).eq("status", "failed").execute()
        
        if not failed_images_response.data:
            return {
                "success": True,
                "message": "No failed images found to retry",
                "retried_count": 0
            }
        
        # Get user's Fal AI API key
        fal_api_key = None
        try:
            api_key_response = supabase_client.table("api_keys").select("api_key").eq("user_id", current_user["id"]).eq("service", "fal").eq("is_active", True).execute()
            if api_key_response.data:
                fal_api_key = api_key_response.data[0]["api_key"]
                logger.info("Using user-provided Fal AI API key")
            else:
                logger.info("No user Fal AI API key found, will use centralized key")
        except Exception as e:
            logger.warning(f"Could not retrieve user Fal AI API key: {e}, will use centralized key")
        
        # Retry processing failed images
        retried_count = 0
        for failed_image in failed_images_response.data:
            try:
                # Reset status to pending
                supabase_client.table("images").update({
                    "status": "pending",
                    "error_message": None,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", failed_image["id"]).execute()
                
                # Process the image again
                result = await blog_generation_service.image_processor.process_stored_placeholders(
                    blog_id=blog_id,
                    fal_api_key=fal_api_key,
                    s3_bucket_name="images"
                )
                
                if result["success"] and result["images_processed"] > 0:
                    retried_count += 1
                    logger.info(f"✅ Retried image {failed_image['image_number']} successfully")
                else:
                    logger.warning(f"Failed to retry image {failed_image['image_number']}")
                    
            except Exception as e:
                logger.error(f"Error retrying image {failed_image['image_number']}: {e}")
        
        return {
            "success": True,
            "message": f"Retried {retried_count} failed images",
            "retried_count": retried_count,
            "total_failed": len(failed_images_response.data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying failed images: {e}")
        raise HTTPException(status_code=500, detail=str(e))
