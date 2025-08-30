import logging
import requests
import base64
from typing import Dict, Any, Optional, List
from datetime import datetime
import aiohttp
import asyncio
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class WordPressMediaService:
    """Service for uploading media to WordPress sites"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def upload_image_to_wordpress(
        self,
        image_url: str,
        wordpress_account: Dict[str, Any],
        filename: str,
        alt_text: str = ""
    ) -> Dict[str, Any]:
        """
        Upload an image to WordPress using the REST API
        
        Args:
            image_url: URL of the image to upload (from Supabase Storage)
            wordpress_account: WordPress account configuration
            filename: Name for the uploaded file
            alt_text: Alt text for the image
            
        Returns:
            Dict containing upload result and WordPress media data
        """
        try:
            logger.info(f"🚀 Starting WordPress media upload for image: {filename}")
            
            # Get WordPress credentials
            site_url = wordpress_account["site_url"]
            username = wordpress_account["username"]
            password = wordpress_account["password"]
            
            # Download the image from Supabase Storage
            logger.info(f"📥 Downloading image from: {image_url}")
            image_data = await self._download_image(image_url)
            if not image_data:
                return {
                    "success": False,
                    "error": "Failed to download image from storage"
                }
            
            # Prepare the upload request - try modern endpoint first, fallback to legacy
            modern_url = urljoin(site_url, "/wp-json/wp/v2/media")
            legacy_url = urljoin(site_url, "/index.php?rest_route=/wp/v2/media")
            
            # Use modern endpoint by default, but we'll handle fallback in the upload logic
            upload_url = modern_url
            
            # Use WordPress REST API authentication with application password
            headers = {
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
            
            # Prepare form data for upload
            data = aiohttp.FormData()
            data.add_field('file', image_data, filename=filename, content_type='image/jpeg')
            data.add_field('alt_text', alt_text)
            data.add_field('title', filename.replace('.jpg', '').replace('_', ' '))
            
            logger.info(f"📤 Uploading to WordPress: {upload_url}")
            
            # Upload to WordPress using application password authentication
            # aiohttp expects BasicAuth object for authentication
            from aiohttp import BasicAuth
            auth = BasicAuth(username, password)
            
            # Try modern endpoint first
            logger.info(f"📤 Trying modern WordPress endpoint: {upload_url}")
            async with self.session.post(upload_url, data=data, headers=headers, auth=auth) as response:
                if response.status == 201:
                    # Success - WordPress returns the media object
                    media_data = await response.json()
                    
                    logger.info(f"✅ Image uploaded successfully to WordPress (ID: {media_data.get('id')})")
                    
                    return {
                        "success": True,
                        "wordpress_media_id": media_data.get("id"),
                        "wordpress_media_url": media_data.get("source_url"),
                        "wordpress_media_data": media_data,
                        "filename": filename
                    }
                elif response.status == 404:
                    # Modern endpoint failed, try legacy endpoint
                    logger.info(f"⚠️ Modern endpoint failed (404), trying legacy endpoint: {legacy_url}")
                    async with self.session.post(legacy_url, data=data, headers=headers, auth=auth) as legacy_response:
                        if legacy_response.status == 201:
                            # Success with legacy endpoint
                            media_data = await legacy_response.json()
                            
                            logger.info(f"✅ Image uploaded successfully to WordPress via legacy endpoint (ID: {media_data.get('id')})")
                            
                            return {
                                "success": True,
                                "wordpress_media_id": media_data.get("id"),
                                "wordpress_media_url": media_data.get("source_url"),
                                "wordpress_media_data": media_data,
                                "filename": filename
                            }
                        else:
                            # Legacy endpoint also failed
                            error_text = await legacy_response.text()
                            logger.error(f"❌ WordPress upload failed on both endpoints. Legacy: {legacy_response.status} - {error_text}")
                            
                            return {
                                "success": False,
                                "error": f"WordPress upload failed on both endpoints. Modern: {response.status}, Legacy: {legacy_response.status}",
                                "details": f"Modern: {await response.text()}, Legacy: {error_text}"
                            }
                else:
                    # Handle other errors from modern endpoint
                    error_text = await response.text()
                    logger.error(f"❌ WordPress upload failed: {response.status} - {error_text}")
                    
                    return {
                        "success": False,
                        "error": f"WordPress upload failed: {response.status}",
                        "details": error_text
                    }
                    
        except Exception as e:
            logger.error(f"❌ Error uploading image to WordPress: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _download_image(self, image_url: str) -> Optional[bytes]:
        """
        Download image data from URL
        
        Args:
            image_url: URL of the image to download
            
        Returns:
            Image data as bytes or None if failed
        """
        try:
            async with self.session.get(image_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    logger.info(f"✅ Downloaded {len(image_data)} bytes from {image_url}")
                    return image_data
                else:
                    logger.error(f"❌ Failed to download image: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"❌ Error downloading image: {e}")
            return None
    
    async def upload_multiple_images(
        self,
        images: List[Dict[str, Any]],
        wordpress_account: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Upload multiple images to WordPress
        
        Args:
            images: List of image records from database
            wordpress_account: WordPress account configuration
            
        Returns:
            Dict containing results for all uploads
        """
        logger.info(f"🚀 Starting batch upload of {len(images)} images to WordPress")
        
        results = []
        successful_count = 0
        failed_count = 0
        
        for image_record in images:
            try:
                # Get image data
                image_id = image_record["id"]
                s3_url = image_record.get("s3_url")
                prompt = image_record.get("prompt", "")
                
                if not s3_url:
                    logger.warning(f"⚠️ Image {image_id} has no S3 URL, skipping")
                    results.append({
                        "image_id": image_id,
                        "success": False,
                        "error": "No S3 URL available"
                    })
                    failed_count += 1
                    continue
                
                # Generate filename
                filename = f"blog_image_{image_id}_{image_record.get('image_number', 1)}.jpg"
                
                # Upload to WordPress
                upload_result = await self.upload_image_to_wordpress(
                    image_url=s3_url,
                    wordpress_account=wordpress_account,
                    filename=filename,
                    alt_text=prompt[:100] if prompt else filename  # Use prompt as alt text
                )
                
                # Add image ID to result
                upload_result["image_id"] = image_id
                results.append(upload_result)
                
                if upload_result["success"]:
                    successful_count += 1
                    logger.info(f"✅ Image {image_id} uploaded successfully to WordPress")
                else:
                    failed_count += 1
                    logger.error(f"❌ Image {image_id} failed to upload: {upload_result.get('error')}")
                
                # Small delay to avoid overwhelming WordPress
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"❌ Error processing image {image_record.get('id')}: {e}")
                results.append({
                    "image_id": image_record.get("id"),
                    "success": False,
                    "error": str(e)
                })
                failed_count += 1
        
        logger.info(f"🎉 Batch upload completed: {successful_count} successful, {failed_count} failed")
        
        return {
            "success": failed_count == 0,
            "total_images": len(images),
            "successful_count": successful_count,
            "failed_count": failed_count,
            "results": results
        }
