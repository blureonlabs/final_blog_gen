from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, List
import logging
from datetime import datetime

from core.supabase_client import supabase_client
from tasks.wordpress_media_upload import (
    upload_images_to_wordpress_task,
    upload_single_image_to_wordpress_task
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/wordpress-media", tags=["WordPress Media"])

@router.post("/upload-blog-images/{blog_id}")
async def upload_blog_images_to_wordpress(
    blog_id: str,
    wordpress_account_id: str,
    background_tasks: BackgroundTasks
):
    """
    Upload all images for a blog to WordPress
    
    Args:
        blog_id: Blog UUID
        wordpress_account_id: WordPress account UUID
        
    Returns:
        Upload task information
    """
    try:
        logger.info(f"🚀 Received request to upload blog {blog_id} images to WordPress")
        
        # Validate blog exists
        blog_response = supabase_client.table("blogs").select("id, title").eq("id", blog_id).execute()
        if not blog_response.data:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        blog = blog_response.data[0]
        logger.info(f"📝 Blog found: {blog.get('title')}")
        
        # Validate WordPress account exists
        wp_response = supabase_client.table("wordpress_accounts").select("id, name, site_url").eq("id", wordpress_account_id).eq("is_active", True).execute()
        if not wp_response.data:
            raise HTTPException(status_code=404, detail="WordPress account not found or inactive")
        
        wp_account = wp_response.data[0]
        logger.info(f"🌐 WordPress account found: {wp_account.get('name')} ({wp_account.get('site_url')})")
        
        # Check if images exist and are ready for upload
        images_response = supabase_client.table("images").select("id, status, s3_url, wordpress_media_url").eq("blog_id", blog_id).execute()
        
        if not images_response.data:
            raise HTTPException(status_code=404, detail="No images found for this blog")
        
        images = images_response.data
        ready_images = [img for img in images if img.get("status") == "generated" and img.get("s3_url") and not img.get("wordpress_media_url")]
        
        if not ready_images:
            raise HTTPException(status_code=400, detail="No images ready for WordPress upload. Images must be generated and have S3 URLs.")
        
        logger.info(f"📸 Found {len(ready_images)} images ready for WordPress upload")
        
        # Start background task
        task = upload_images_to_wordpress_task.delay(blog_id, wordpress_account_id)
        
        logger.info(f"✅ WordPress media upload task started: {task.id}")
        
        return {
            "success": True,
            "message": f"WordPress media upload started for {len(ready_images)} images",
            "task_id": task.id,
            "blog_id": blog_id,
            "wordpress_account": wp_account.get("name"),
            "images_count": len(ready_images),
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error starting WordPress media upload: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/upload-single-image/{image_id}")
async def upload_single_image_to_wordpress(
    image_id: str,
    wordpress_account_id: str,
    background_tasks: BackgroundTasks
):
    """
    Upload a single image to WordPress
    
    Args:
        image_id: Image UUID
        wordpress_account_id: WordPress account UUID
        
    Returns:
        Upload task information
    """
    try:
        logger.info(f"🚀 Received request to upload single image {image_id} to WordPress")
        
        # Validate image exists and is ready
        image_response = supabase_client.table("images").select("id, blog_id, status, s3_url, wordpress_media_url").eq("id", image_id).execute()
        if not image_response.data:
            raise HTTPException(status_code=404, detail="Image not found")
        
        image = image_response.data[0]
        
        if image.get("status") != "generated":
            raise HTTPException(status_code=400, detail="Image is not ready for upload. Status must be 'generated'.")
        
        if not image.get("s3_url"):
            raise HTTPException(status_code=400, detail="Image has no S3 URL. Cannot upload to WordPress.")
        
        if image.get("wordpress_media_url"):
            raise HTTPException(status_code=400, detail="Image already has a WordPress media URL.")
        
        # Validate WordPress account
        wp_response = supabase_client.table("wordpress_accounts").select("id, name, site_url").eq("id", wordpress_account_id).eq("is_active", True).execute()
        if not wp_response.data:
            raise HTTPException(status_code=404, detail="WordPress account not found or inactive")
        
        wp_account = wp_response.data[0]
        logger.info(f"🌐 WordPress account found: {wp_account.get('name')}")
        
        # Start background task
        task = upload_single_image_to_wordpress_task.delay(image_id, wordpress_account_id)
        
        logger.info(f"✅ Single image WordPress upload task started: {task.id}")
        
        return {
            "success": True,
            "message": "Single image WordPress upload started",
            "task_id": task.id,
            "image_id": image_id,
            "blog_id": image.get("blog_id"),
            "wordpress_account": wp_account.get("name"),
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error starting single image WordPress upload: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/blog-images/{blog_id}")
async def get_blog_images_status(blog_id: str):
    """
    Get the status of all images for a blog, including WordPress upload status
    
    Args:
        blog_id: Blog UUID
        
    Returns:
        List of images with their status
    """
    try:
        logger.info(f"📊 Getting image status for blog {blog_id}")
        
        # Get all images for the blog
        response = supabase_client.table("images").select(
            "id, image_number, status, s3_url, wordpress_media_url, wordpress_media_id, prompt, created_at, updated_at"
        ).eq("blog_id", blog_id).order("image_number").execute()
        
        if not response.data:
            return {
                "blog_id": blog_id,
                "images": [],
                "total_count": 0,
                "ready_for_wordpress": 0,
                "uploaded_to_wordpress": 0
            }
        
        images = response.data
        
        # Calculate statistics
        total_count = len(images)
        ready_for_wordpress = len([img for img in images if img.get("status") == "generated" and img.get("s3_url") and not img.get("wordpress_media_url")])
        uploaded_to_wordpress = len([img for img in images if img.get("wordpress_media_url")])
        
        return {
            "blog_id": blog_id,
            "images": images,
            "total_count": total_count,
            "ready_for_wordpress": ready_for_wordpress,
            "uploaded_to_wordpress": uploaded_to_wordpress,
            "summary": {
                "total_images": total_count,
                "generated": len([img for img in images if img.get("status") == "generated"]),
                "pending": len([img for img in images if img.get("status") == "pending"]),
                "failed": len([img for img in images if img.get("status") == "failed"]),
                "wordpress_ready": ready_for_wordpress,
                "wordpress_uploaded": uploaded_to_wordpress
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting blog images status: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/wordpress-accounts")
async def get_wordpress_accounts():
    """
    Get all active WordPress accounts
    
    Returns:
        List of active WordPress accounts
    """
    try:
        logger.info("🌐 Getting active WordPress accounts")
        
        response = supabase_client.table("wordpress_accounts").select(
            "id, name, site_url, username, is_active, created_at"
        ).eq("is_active", True).execute()
        
        return {
            "success": True,
            "accounts": response.data or [],
            "total_count": len(response.data or [])
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting WordPress accounts: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/retry-failed-uploads/{blog_id}")
async def retry_failed_wordpress_uploads(
    blog_id: str,
    wordpress_account_id: str,
    background_tasks: BackgroundTasks
):
    """
    Retry failed WordPress uploads for a blog
    
    Args:
        blog_id: Blog UUID
        wordpress_account_id: WordPress account UUID
        
    Returns:
        Retry task information
    """
    try:
        logger.info(f"🔄 Received request to retry failed WordPress uploads for blog {blog_id}")
        
        # Get failed uploads
        failed_response = supabase_client.table("images").select(
            "id, status, error_message"
        ).eq("blog_id", blog_id).eq("status", "failed").execute()
        
        if not failed_response.data:
            return {
                "success": True,
                "message": "No failed uploads found for this blog",
                "failed_count": 0
            }
        
        failed_images = failed_response.data
        logger.info(f"📸 Found {len(failed_images)} failed uploads to retry")
        
        # Reset failed images to pending status
        for image in failed_images:
            supabase_client.table("images").update({
                "status": "pending",
                "error_message": None,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", image["id"]).execute()
        
        # Start WordPress upload task
        task = upload_images_to_wordpress_task.delay(blog_id, wordpress_account_id)
        
        logger.info(f"✅ Retry task started: {task.id}")
        
        return {
            "success": True,
            "message": f"Retry task started for {len(failed_images)} failed uploads",
            "task_id": task.id,
            "blog_id": blog_id,
            "failed_count": len(failed_images),
            "status": "retrying"
        }
        
    except Exception as e:
        logger.error(f"❌ Error starting retry task: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
