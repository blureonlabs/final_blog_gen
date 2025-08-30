import re
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime

from .image_generation_service import ImageGenerationService
from core.supabase_client import supabase_client
from core.config import settings

logger = logging.getLogger(__name__)

class ImagePlaceholderProcessor:
    """Service for processing image placeholders in blog content and generating actual images"""
    
    def __init__(self):
        self.image_service = ImageGenerationService()
    
    def extract_image_placeholders(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract image placeholders from blog content
        
        Args:
            content: Blog content with [image:description] placeholders
            
        Returns:
            List of image placeholder data
        """
        try:
            # Find all [image:description] patterns
            pattern = r'\[image:(.*?)\]'
            matches = re.findall(pattern, content, re.IGNORECASE)
            
            image_placeholders = []
            for i, description in enumerate(matches, 1):
                image_placeholders.append({
                    "placeholder": f"[image:{description}]",
                    "description": description.strip(),
                    "image_number": i,
                    "position": content.find(f"[image:{description}]")
                })
            
            logger.info(f"Found {len(image_placeholders)} image placeholders in content")
            return image_placeholders
            
        except Exception as e:
            logger.error(f"Error extracting image placeholders: {e}")
            return []
    
    def replace_placeholders_with_images(self, content: str, generated_images: List[Dict[str, Any]]) -> str:
        """
        Replace image placeholders with actual image HTML
        
        Args:
            content: Original blog content with placeholders
            generated_images: List of generated image data
            
        Returns:
            Content with placeholders replaced by image HTML
        """
        try:
            # Extract placeholders
            placeholders = self.extract_image_placeholders(content)
            
            if not placeholders:
                logger.info("No image placeholders found to replace")
                return content
            
            # Replace each placeholder with image HTML
            modified_content = content
            for placeholder_data in placeholders:
                placeholder = placeholder_data["placeholder"]
                image_number = placeholder_data["image_number"]
                
                # Find corresponding generated image
                image_data = next((img for img in generated_images if img.get("image_number") == image_number), None)
                
                if image_data:
                    # Create image HTML
                    image_html = self._create_image_html(image_data, placeholder_data)
                    modified_content = modified_content.replace(placeholder, image_html)
                    logger.info(f"Replaced placeholder {image_number} with image HTML")
                else:
                    logger.warning(f"No generated image found for placeholder {image_number}")
                    # Replace with a fallback image or keep placeholder
                    fallback_html = f'<div class="image-placeholder">[Image {image_number}: {placeholder_data["description"]}]</div>'
                    modified_content = modified_content.replace(placeholder, fallback_html)
            
            return modified_content
            
        except Exception as e:
            logger.error(f"Error replacing image placeholders: {e}")
            return content
    
    def _create_image_html(self, image_data: Dict[str, Any], placeholder_data: Dict[str, Any]) -> str:
        """
        Create HTML for an image based on generated data
        
        Args:
            image_data: Generated image information
            placeholder_data: Original placeholder information
            
        Returns:
            HTML string for the image
        """
        try:
            image_url = image_data.get("url", "")
            alt_text = image_data.get("alt_text", placeholder_data["description"])
            prompt = image_data.get("prompt", placeholder_data["description"])
            
            # Create responsive image HTML
            html = f'''
            <div class="blog-image image-{image_data.get('image_number', 1)}">
                <img src="{image_url}" 
                     alt="{alt_text}" 
                     class="img-fluid" 
                     style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"
                     loading="lazy">
                <div class="image-caption" style="text-align: center; margin-top: 8px; font-style: italic; color: #666; font-size: 0.9em;">
                    {placeholder_data["description"]}
                </div>
            </div>
            '''
            
            return html.strip()
            
        except Exception as e:
            logger.error(f"Error creating image HTML: {e}")
            return f'<div class="image-error">[Image generation failed: {placeholder_data["description"]}]</div>'
    
    async def process_blog_content(
        self,
        blog_id: str,
        project_id: str,
        content: str,
        title: str,
        seo_meta: Dict = None,
        fal_api_key: str = None
    ) -> Dict[str, Any]:
        """
        Process blog content to generate images for placeholders and replace them
        
        Args:
            blog_id: Blog ID
            project_id: Project ID
            content: Blog content with image placeholders
            title: Blog title
            seo_meta: SEO metadata
            fal_api_key: Fal AI API key
            
        Returns:
            Dict with processed content and image information
        """
        try:
            logger.info(f"Processing image placeholders for blog {blog_id}")
            
            # Extract image placeholders
            placeholders = self.extract_image_placeholders(content)
            
            if not placeholders:
                logger.info("No image placeholders found in content")
                return {
                    "success": True,
                    "content": content,
                    "images_generated": 0,
                    "message": "No image placeholders found"
                }
            
            # Set API key for image generation
            if fal_api_key:
                self.image_service.set_fal_api_key(fal_api_key)
            else:
                logger.error("No Fal AI API key provided for image generation")
                return {
                    "success": False,
                    "error": "No Fal AI API key provided",
                    "images_generated": 0
                }
            
            # Generate images for each placeholder
            generated_images = []
            for placeholder in placeholders:
                try:
                    logger.info(f"Generating image for placeholder {placeholder['image_number']}: {placeholder['description']}")
                    
                    # Generate image using the description as prompt
                    result = await self.image_service.generate_blog_images(
                        blog_id=blog_id,
                        project_id=project_id,
                        title=title,
                        content=content,
                        seo_meta=seo_meta,
                        num_images=1,
                        style="photographic",  # Default style
                        aspect_ratio="16:9",   # Default aspect ratio
                        quality="standard"     # Default quality
                    )
                    
                    if result["success"] and result["images"]:
                        # Add image number to the result
                        image_data = result["images"][0]
                        image_data["image_number"] = placeholder["image_number"]
                        image_data["alt_text"] = placeholder["description"]
                        generated_images.append(image_data)
                        
                        logger.info(f"✅ Generated image {placeholder['image_number']} successfully")
                    else:
                        logger.warning(f"Failed to generate image for placeholder {placeholder['image_number']}: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    logger.error(f"Error generating image for placeholder {placeholder['image_number']}: {e}")
            
            # Replace placeholders with generated images
            if generated_images:
                processed_content = self.replace_placeholders_with_images(content, generated_images)
                
                return {
                    "success": True,
                    "content": processed_content,
                    "images_generated": len(generated_images),
                    "total_placeholders": len(placeholders),
                    "generated_images": generated_images,
                    "message": f"Generated {len(generated_images)} images successfully"
                }
            else:
                logger.warning("No images were generated successfully")
                return {
                    "success": False,
                    "error": "Failed to generate any images",
                    "content": content,
                    "total_placeholders": len(placeholders)
                }
                
        except Exception as e:
            logger.error(f"Error processing blog content for images: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": content
            }
    
    def validate_image_placeholders(self, content: str, expected_count: int) -> Dict[str, Any]:
        """
        Validate that the content has the expected number of image placeholders
        
        Args:
            content: Blog content to validate
            expected_count: Expected number of image placeholders
            
        Returns:
            Validation result
        """
        try:
            placeholders = self.extract_image_placeholders(content)
            actual_count = len(placeholders)
            
            is_valid = actual_count == expected_count
            message = f"Found {actual_count} image placeholders, expected {expected_count}"
            
            if is_valid:
                message = f"✅ {message}"
            else:
                message = f"⚠️ {message}"
            
            return {
                "valid": is_valid,
                "actual_count": actual_count,
                "expected_count": expected_count,
                "message": message,
                "placeholders": placeholders
            }
            
        except Exception as e:
            logger.error(f"Error validating image placeholders: {e}")
            return {
                "valid": False,
                "error": str(e),
                "actual_count": 0,
                "expected_count": expected_count
            }
    
    async def store_image_placeholders(
        self,
        blog_id: str,
        project_id: str,
        content: str,
        title: str
    ) -> Dict[str, Any]:
        """
        Store image placeholders in the database for later processing
        
        Args:
            blog_id: Blog ID
            project_id: Project ID
            content: Blog content with image placeholders
            title: Blog title
            
        Returns:
            Dict with stored placeholder information
        """
        try:
            logger.info(f"Storing image placeholders for blog {blog_id}")
            
            # Extract image placeholders
            placeholders = self.extract_image_placeholders(content)
            
            if not placeholders:
                logger.info("No image placeholders found to store")
                return {
                    "success": True,
                    "placeholders_stored": 0,
                    "message": "No image placeholders found"
                }
            
            # Store each placeholder in the images table
            stored_placeholders = []
            for placeholder in placeholders:
                try:
                    # Create image record
                    image_data = {
                        "project_id": project_id,
                        "blog_id": blog_id,
                        "prompt": placeholder["description"],
                        "alt_text": placeholder["description"],
                        "image_number": placeholder["image_number"],
                        "status": "pending",  # Will be updated to 'generating' then 'generated'
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    
                    # Insert into images table
                    response = supabase_client.table("images").insert(image_data).execute()
                    
                    if response.data:
                        stored_placeholder = response.data[0]
                        stored_placeholders.append(stored_placeholder)
                        logger.info(f"✅ Stored placeholder {placeholder['image_number']} with ID: {stored_placeholder['id']}")
                    else:
                        logger.error(f"Failed to store placeholder {placeholder['image_number']}")
                        
                except Exception as e:
                    logger.error(f"Error storing placeholder {placeholder['image_number']}: {e}")
            
            return {
                "success": True,
                "placeholders_stored": len(stored_placeholders),
                "total_placeholders": len(placeholders),
                "stored_placeholders": stored_placeholders,
                "message": f"Stored {len(stored_placeholders)} image placeholders successfully"
            }
            
        except Exception as e:
            logger.error(f"Error storing image placeholders: {e}")
            return {
                "success": False,
                "error": str(e),
                "placeholders_stored": 0
            }
    
    async def process_stored_placeholders(
        self,
        blog_id: str,
        fal_api_key: str,
        s3_bucket_name: str = "images"
    ) -> Dict[str, Any]:
        """
        Process stored image placeholders: generate images and store in S3
        
        Args:
            blog_id: Blog ID
            fal_api_key: Fal AI API key
            s3_bucket_name: S3 bucket name for storing images
            
        Returns:
            Dict with processing results
        """
        try:
            logger.info(f"Processing stored image placeholders for blog {blog_id}")
            
            # Get stored placeholders for this blog
            response = supabase_client.table("images").select("*").eq("blog_id", blog_id).order("image_number").execute()
            
            if not response.data:
                logger.info("No stored placeholders found for this blog")
                return {
                    "success": True,
                    "images_processed": 0,
                    "message": "No stored placeholders found"
                }
            
            placeholders = response.data
            logger.info(f"Found {len(placeholders)} stored placeholders to process")
            
            # Set API key for image generation
            if fal_api_key:
                self.image_service.set_fal_api_key(fal_api_key)
            else:
                logger.error("No Fal AI API key provided for image generation")
                return {
                    "success": False,
                    "error": "No Fal AI API key provided",
                    "images_processed": 0
                }
            
            # Process each placeholder
            processed_images = []
            for placeholder in placeholders:
                try:
                    logger.info(f"Processing placeholder {placeholder['image_number']}: {placeholder['prompt']}")
                    
                    # Update status to generating
                    supabase_client.table("images").update({
                        "status": "generating",
                        "updated_at": datetime.utcnow().isoformat()
                    }).eq("id", placeholder["id"]).execute()
                    
                    # Generate image using Fal AI
                    result = await self.image_service.generate_blog_images(
                        blog_id=blog_id,
                        project_id=placeholder["project_id"],
                        title="",  # Not needed for image generation
                        content="",  # Not needed for image generation
                        seo_meta={},
                        num_images=1,
                        style="photographic",
                        aspect_ratio="16:9",
                        quality="standard"
                    )
                    
                    if result["success"] and result["images"]:
                        image_data = result["images"][0]
                        
                        # Store image in S3 bucket
                        s3_url = await self._store_image_in_s3(
                            image_data["url"],
                            blog_id,
                            placeholder["image_number"],
                            s3_bucket_name
                        )
                        
                        if s3_url:
                            # Update image record with S3 URL and status
                            update_data = {
                                "s3_url": s3_url,
                                "status": "generated",
                                "updated_at": datetime.utcnow().isoformat()
                            }
                            
                            supabase_client.table("images").update(update_data).eq("id", placeholder["id"]).execute()
                            
                            # Add to processed images
                            processed_images.append({
                                "id": placeholder["id"],
                                "image_number": placeholder["image_number"],
                                "s3_url": s3_url,
                                "original_url": image_data["url"],
                                "prompt": placeholder["prompt"]
                            })
                            
                            logger.info(f"✅ Processed placeholder {placeholder['image_number']} successfully")
                        else:
                            # Update status to failed
                            supabase_client.table("images").update({
                                "status": "failed",
                                "error_message": "Failed to store image in S3",
                                "updated_at": datetime.utcnow().isoformat()
                            }).eq("id", placeholder["id"]).execute()
                            
                    else:
                        # Update status to failed
                        error_msg = result.get("error", "Unknown error")
                        supabase_client.table("images").update({
                            "status": "failed",
                            "error_message": error_msg,
                            "updated_at": datetime.utcnow().isoformat()
                        }).eq("id", placeholder["id"]).execute()
                        
                        logger.warning(f"Failed to generate image for placeholder {placeholder['image_number']}: {error_msg}")
                        
                except Exception as e:
                    logger.error(f"Error processing placeholder {placeholder['image_number']}: {e}")
                    
                    # Update status to failed
                    supabase_client.table("images").update({
                        "status": "failed",
                        "error_message": str(e),
                        "updated_at": datetime.utcnow().isoformat()
                    }).eq("id", placeholder["id"]).execute()
            
            return {
                "success": True,
                "images_processed": len(processed_images),
                "total_placeholders": len(placeholders),
                "processed_images": processed_images,
                "message": f"Processed {len(processed_images)} images successfully"
            }
            
        except Exception as e:
            logger.error(f"Error processing stored placeholders: {e}")
            return {
                "success": False,
                "error": str(e),
                "images_processed": 0
            }
    
    async def _store_image_in_s3(
        self,
        image_url: str,
        blog_id: str,
        image_number: int,
        bucket_name: str
    ) -> str:
        """
        Store generated image in S3 bucket
        
        Args:
            image_url: URL of the generated image
            blog_id: Blog ID
            image_number: Image number
            bucket_name: S3 bucket name
            
        Returns:
            S3 URL of the stored image
        """
        try:
            # Import S3 service here to avoid circular imports
            from .s3_storage_service import S3StorageService
            
            s3_service = S3StorageService()
            
            # Download image from URL
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        
                        # Generate S3 key
                        s3_key = f"blog-images/{blog_id}/image_{image_number}.jpg"
                        
                        # Store in S3
                        s3_url = await s3_service.upload_file(
                            file_data=image_data,
                            bucket_name=bucket_name,
                            key=s3_key,
                            content_type="image/jpeg"
                        )
                        
                        if s3_url:
                            logger.info(f"✅ Image stored in S3: {s3_url}")
                            return s3_url
                        else:
                            logger.error("Failed to upload image to S3")
                            return None
                    else:
                        logger.error(f"Failed to download image from {image_url}: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error storing image in S3: {e}")
            return None
