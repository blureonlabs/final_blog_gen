from celery import shared_task
from typing import Dict, List, Any
import logging
from datetime import datetime
import asyncio

from core.supabase_client import supabase_client
from services.wordpress_media_service import WordPressMediaService

logger = logging.getLogger(__name__)

@shared_task(bind=True, name="upload_images_to_wordpress")
def upload_images_to_wordpress_task(
    self, 
    blog_id: str, 
    wordpress_account_id: str
):
    """
    Upload blog images to WordPress and update database with media URLs
    
    Args:
        blog_id: Blog UUID as string
        wordpress_account_id: WordPress account UUID as string
        
    Returns:
        Dict containing upload results
    """
    try:
        logger.info(f"🚀 Starting WordPress media upload for blog {blog_id}")
        
        # Get blog images that have been generated but not yet uploaded to WordPress
        images = get_blog_images_for_wordpress_upload(blog_id)
        if not images:
            logger.info(f"ℹ️ No images found for blog {blog_id} that need WordPress upload")
            return {
                "blog_id": blog_id,
                "status": "no_images",
                "message": "No images found that need WordPress upload"
            }
        
        logger.info(f"📸 Found {len(images)} images to upload to WordPress for blog {blog_id}")
        
        # Get WordPress account details
        wordpress_account = get_wordpress_account(wordpress_account_id)
        if not wordpress_account:
            logger.error(f"❌ WordPress account {wordpress_account_id} not found")
            return {
                "blog_id": blog_id,
                "status": "failed",
                "error": "WordPress account not found"
            }
        
        # Run the async upload process
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            upload_result = loop.run_until_complete(
                upload_images_async(images, wordpress_account)
            )
        finally:
            loop.close()
        
        if upload_result["success"]:
            # Update database with WordPress media URLs
            update_result = update_images_with_wordpress_urls(upload_result["results"])
            
            logger.info(f"✅ WordPress media upload completed for blog {blog_id}")
            logger.info(f"   📊 {upload_result['successful_count']} successful, {upload_result['failed_count']} failed")
            
            return {
                "blog_id": blog_id,
                "status": "completed",
                "total_images": upload_result["total_images"],
                "successful_count": upload_result["successful_count"],
                "failed_count": upload_result["failed_count"],
                "database_updated": update_result
            }
        else:
            logger.error(f"❌ WordPress media upload failed for blog {blog_id}")
            return {
                "blog_id": blog_id,
                "status": "failed",
                "error": "Media upload process failed",
                "details": upload_result
            }
            
    except Exception as e:
        logger.error(f"❌ Error in WordPress media upload task: {e}")
        return {
            "blog_id": blog_id,
            "status": "failed",
            "error": str(e)
        }

async def upload_images_async(images: List[Dict[str, Any]], wordpress_account: Dict[str, Any]):
    """
    Async function to upload images to WordPress
    
    Args:
        images: List of image records
        wordpress_account: WordPress account configuration
        
    Returns:
        Upload results
    """
    async with WordPressMediaService() as wp_media_service:
        return await wp_media_service.upload_multiple_images(images, wordpress_account)

async def upload_single_image_async(image: Dict[str, Any], wordpress_account: Dict[str, Any]):
    """
    Async function to upload a single image to WordPress
    
    Args:
        image: Image record
        wordpress_account: WordPress account configuration
        
    Returns:
        Upload result
    """
    async with WordPressMediaService() as wp_media_service:
        return await wp_media_service.upload_image_to_wordpress(
            image_url=image["s3_url"],
            wordpress_account=wordpress_account,
            filename=f"blog_image_{image['id']}_{image.get('image_number', 1)}.jpg",
            alt_text=image.get("prompt", "")[:100]
        )

def get_blog_images_for_wordpress_upload(blog_id: str) -> List[Dict[str, Any]]:
    """
    Get blog images that need WordPress upload
    
    Args:
        blog_id: Blog UUID
        
    Returns:
        List of image records
    """
    try:
        # Get images that have been generated (have S3 URLs) but no WordPress media URL
        response = supabase_client.table("images").select("*").eq("blog_id", blog_id).eq("status", "generated").is_("wordpress_media_url", "null").execute()
        
        if response.data:
            logger.info(f"📸 Found {len(response.data)} images ready for WordPress upload")
            return response.data
        else:
            logger.info(f"ℹ️ No images found for blog {blog_id} that need WordPress upload")
            return []
            
    except Exception as e:
        logger.error(f"❌ Error getting blog images: {e}")
        return []

def get_wordpress_account(wordpress_account_id: str) -> Dict[str, Any]:
    """
    Get WordPress account details
    
    Args:
        wordpress_account_id: WordPress account UUID
        
    Returns:
        WordPress account data
    """
    try:
        response = supabase_client.table("wordpress_accounts").select("*").eq("id", wordpress_account_id).eq("is_active", True).execute()
        
        if response.data:
            account = response.data[0]
            logger.info(f"✅ Found WordPress account: {account.get('name')}")
            return account
        else:
            logger.error(f"❌ WordPress account {wordpress_account_id} not found or inactive")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error getting WordPress account: {e}")
        return None

def update_images_with_wordpress_urls(upload_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Update image records with WordPress media URLs
    
    Args:
        upload_results: List of upload results from WordPress
        
    Returns:
        Update results
    """
    try:
        updated_count = 0
        failed_count = 0
        
        for result in upload_results:
            if result["success"]:
                try:
                    # Update the image record with WordPress media URL
                    update_data = {
                        "wordpress_media_url": result["wordpress_media_url"],
                        "wordpress_media_id": result["wordpress_media_id"],
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    
                    supabase_client.table("images").update(update_data).eq("id", result["image_id"]).execute()
                    updated_count += 1
                    
                    logger.info(f"✅ Updated image {result['image_id']} with WordPress media URL")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to update image {result['image_id']}: {e}")
                    failed_count += 1
            else:
                logger.warning(f"⚠️ Image {result['image_id']} upload failed, not updating database")
        
        logger.info(f"📊 Database update completed: {updated_count} updated, {failed_count} failed")
        
        return {
            "success": failed_count == 0,
            "updated_count": updated_count,
            "failed_count": failed_count
        }
        
    except Exception as e:
        logger.error(f"❌ Error updating images with WordPress URLs: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@shared_task(bind=True, name="upload_single_image_to_wordpress")
def upload_single_image_to_wordpress_task(
    self,
    image_id: str,
    wordpress_account_id: str
):
    """
    Upload a single image to WordPress
    
    Args:
        image_id: Image UUID as string
        wordpress_account_id: WordPress account UUID as string
        
    Returns:
        Dict containing upload result
    """
    try:
        logger.info(f"🚀 Starting single image WordPress upload for image {image_id}")
        
        # Get image details
        image = get_image_by_id(image_id)
        if not image:
            logger.error(f"❌ Image {image_id} not found")
            return {
                "image_id": image_id,
                "status": "failed",
                "error": "Image not found"
            }
        
        # Get WordPress account
        wordpress_account = get_wordpress_account(wordpress_account_id)
        if not wordpress_account:
            logger.error(f"❌ WordPress account {wordpress_account_id} not found")
            return {
                "image_id": image_id,
                "status": "failed",
                "error": "WordPress account not found"
            }
        
        # Run async upload
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            upload_result = loop.run_until_complete(
                upload_single_image_async(image, wordpress_account)
            )
        finally:
            loop.close()
        
        if upload_result["success"]:
            # Update database
            update_data = {
                "wordpress_media_url": upload_result["wordpress_media_url"],
                "wordpress_media_id": upload_result["wordpress_media_id"],
                "updated_at": datetime.utcnow().isoformat()
            }
            
            supabase_client.table("images").update(update_data).eq("id", image_id).execute()
            
            logger.info(f"✅ Single image upload completed for image {image_id}")
            
            return {
                "image_id": image_id,
                "status": "completed",
                "wordpress_media_url": upload_result["wordpress_media_url"],
                "wordpress_media_id": upload_result["wordpress_media_id"]
            }
        else:
            logger.error(f"❌ Single image upload failed for image {image_id}: {upload_result.get('error')}")
            return {
                "image_id": image_id,
                "status": "failed",
                "error": upload_result.get("error")
            }
            
    except Exception as e:
        logger.error(f"❌ Error in single image WordPress upload task: {e}")
        return {
            "image_id": image_id,
            "status": "failed",
            "error": str(e)
        }

def get_image_by_id(image_id: str) -> Dict[str, Any]:
    """
    Get image by ID
    
    Args:
        image_id: Image UUID
        
    Returns:
        Image data
    """
    try:
        response = supabase_client.table("images").select("*").eq("id", image_id).execute()
        
        if response.data:
            return response.data[0]
        else:
            return None
            
    except Exception as e:
        logger.error(f"❌ Error getting image by ID: {e}")
        return None
