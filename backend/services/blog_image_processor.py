import os
import logging
import re
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import uuid4

from core.supabase_client import supabase_client
from .image_generation_service import ImageGenerationService
from .fal_ai_service import FalAIService

logger = logging.getLogger(__name__)

class BlogImageProcessor:
    """Service for processing blog content and extracting image placeholders for generation"""
    
    def __init__(self):
        """Initialize the blog image processor"""
        self.image_service = ImageGenerationService()
        
    def extract_image_placeholders(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract image placeholders from blog content
        
        Args:
            content: Blog content with [image:description] placeholders
            
        Returns:
            List of image placeholder dictionaries with prompt and metadata
        """
        try:
            # Regex pattern to match [image:description] format - must have content and proper closing
            pattern = r'\[image:([^\]\n]+)\]'
            matches = re.findall(pattern, content)
            
            image_placeholders = []
            for i, match in enumerate(matches, 1):
                # Clean up the description
                description = match.strip()
                
                # Generate alt text for accessibility
                alt_text = f"Image {i}: {description}"
                
                image_placeholders.append({
                    "image_number": i,
                    "prompt": description,
                    "alt_text": alt_text,
                    "raw_match": match
                })
                
            logger.info(f"📸 Extracted {len(image_placeholders)} image placeholders from blog content")
            return image_placeholders
            
        except Exception as e:
            logger.error(f"❌ Error extracting image placeholders: {e}")
            return []
    
    async def process_blog_for_images(
        self, 
        blog_id: str, 
        project_id: str, 
        title: str, 
        content: str,
        user_id: str,
        fal_api_key: str
    ) -> Dict[str, Any]:
        """
        Process a blog post and extract image placeholders for generation
        
        Args:
            blog_id: ID of the blog post
            project_id: ID of the project
            title: Blog title
            content: Blog content
            user_id: ID of the user
            fal_api_key: Fal AI API key for image generation
            
        Returns:
            Dict containing processing results and image placeholders
        """
        try:
            logger.info(f"🔍 Processing blog {blog_id} for image placeholders")
            
            # Extract image placeholders from content
            image_placeholders = self.extract_image_placeholders(content)
            
            if not image_placeholders:
                logger.info(f"📝 No image placeholders found in blog {blog_id}")
                return {
                    "success": True,
                    "message": "No image placeholders found",
                    "blog_id": blog_id,
                    "images_processed": 0
                }
            
            # Set Fal AI API key for image generation
            self.image_service.set_fal_api_key(fal_api_key)
            
            # Store image placeholders in the images table
            stored_images = []
            for placeholder in image_placeholders:
                try:
                    # Create image record
                    image_data = {
                        "id": str(uuid4()),
                        "project_id": project_id,
                        "blog_id": blog_id,
                        "prompt": placeholder["prompt"],
                        "alt_text": placeholder["alt_text"],
                        "image_number": placeholder["image_number"],
                        "status": "pending",
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    
                    # Insert into images table
                    response = supabase_client.table("images").insert(image_data).execute()
                    
                    if response.data:
                        stored_images.append({
                            "id": image_data["id"],
                            "prompt": placeholder["prompt"],
                            "alt_text": placeholder["alt_text"],
                            "image_number": placeholder["image_number"]
                        })
                        logger.info(f"✅ Stored image placeholder {placeholder['image_number']} for blog {blog_id}")
                    else:
                        logger.error(f"❌ Failed to store image placeholder {placeholder['image_number']} for blog {blog_id}")
                        
                except Exception as e:
                    logger.error(f"❌ Error storing image placeholder {placeholder['image_number']}: {e}")
                    continue
            
            logger.info(f"📸 Successfully processed {len(stored_images)} image placeholders for blog {blog_id}")
            
            return {
                "success": True,
                "message": f"Processed {len(stored_images)} image placeholders",
                "blog_id": blog_id,
                "project_id": project_id,
                "images_processed": len(stored_images),
                "stored_images": stored_images
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing blog {blog_id} for images: {e}")
            return {
                "success": False,
                "error": str(e),
                "blog_id": blog_id
            }
    
    async def generate_images_for_blog(
        self, 
        blog_id: str, 
        project_id: str,
        user_id: str,
        fal_api_key: str,
        style: str = "photographic",
        aspect_ratio: str = "16:9",
        quality: str = "standard"
    ) -> Dict[str, Any]:
        """
        Generate images for all pending image placeholders in a blog
        
        Args:
            blog_id: ID of the blog post
            project_id: ID of the project
            user_id: ID of the user
            fal_api_key: Fal AI API key
            style: Image style
            aspect_ratio: Image aspect ratio
            quality: Image quality
            
        Returns:
            Dict containing generation results
        """
        try:
            logger.info(f"🎨 Starting image generation for blog {blog_id}")
            
            # Get pending images for this blog
            response = supabase_client.table("images").select("*").eq("blog_id", blog_id).eq("status", "pending").order("image_number").execute()
            
            if not response.data:
                logger.info(f"📝 No pending images found for blog {blog_id}")
                return {
                    "success": True,
                    "message": "No pending images found",
                    "blog_id": blog_id,
                    "images_generated": 0
                }
            
            pending_images = response.data
            logger.info(f"📸 Found {len(pending_images)} pending images for blog {blog_id}")
            
            # Set Fal AI API key
            self.image_service.set_fal_api_key(fal_api_key)
            
            # Generate images for each placeholder
            generated_images = []
            failed_images = []
            
            for image_record in pending_images:
                try:
                    logger.info(f"🎨 Generating image {image_record['image_number']} for blog {blog_id}")
                    
                    # Update status to generating
                    supabase_client.table("images").update({
                        "status": "generating",
                        "updated_at": datetime.utcnow().isoformat()
                    }).eq("id", image_record["id"]).execute()
                    
                    # Generate image using Fal AI
                    result = await self.image_service.generate_blog_images(
                        blog_id=blog_id,
                        project_id=project_id,
                        title=image_record["prompt"],  # Use prompt as title for context
                        content=image_record["prompt"],  # Use prompt as content
                        seo_meta={},
                        num_images=1,
                        style=style,
                        aspect_ratio=aspect_ratio,
                        quality=quality
                    )
                    
                    if result["success"] and result["images"]:
                        # Get the generated image
                        generated_image = result["images"][0]
                        
                        # Check if we got a URL or base64 data
                        if "url" in generated_image and generated_image["url"]:
                            # We have a URL, download and upload to Supabase Storage
                            fal_image_url = generated_image["url"]
                            
                            # Debug: Check what we're getting from Fal AI
                            logger.info(f"🔍 Fal AI response - generated_image: {generated_image}")
                            logger.info(f"🔍 Fal AI response - fal_image_url type: {type(fal_image_url)}")
                            logger.info(f"🔍 Fal AI response - fal_image_url length: {len(str(fal_image_url))}")
                            logger.info(f"🔍 Fal AI response - fal_image_url starts with 'data:': {str(fal_image_url).startswith('data:')}")
                            
                            # Now we should always get actual URLs from Fal AI
                            if str(fal_image_url).startswith('data:'):
                                logger.warning(f"⚠️ Unexpected base64 data received from Fal AI for image {image_record['image_number']}")
                                continue
                            
                            # Download image from Fal AI and upload to Supabase Storage (now we should always get real HTTP URLs)
                            try:
                                logger.info(f"📥 Downloading image from Fal AI and uploading to Supabase Storage...")
                                async with aiohttp.ClientSession() as session:
                                    async with session.get(fal_image_url) as response:
                                        if response.status == 200:
                                            image_data = await response.read()
                                            logger.info(f"✅ Downloaded {len(image_data)} bytes from Fal AI")
                                            
                                            # Upload to Supabase Storage bucket "images"
                                            try:
                                                storage_path = f"{blog_id}_{image_record['image_number']}_image.jpg"
                                                storage_response = supabase_client.storage.from_("images").upload(
                                                    path=storage_path,
                                                    file=image_data,
                                                    file_options={"content-type": "image/jpeg"}
                                                )
                                                if storage_response:
                                                    storage_url = supabase_client.storage.from_("images").get_public_url(storage_path)
                                                    logger.info(f"✅ Image uploaded to Supabase Storage: {storage_path}")
                                                    logger.info(f"🖼️ Storage URL: {storage_url}")
                                                    update_data = {
                                                        "s3_url": storage_url,
                                                        "status": "generated",
                                                        "updated_at": datetime.utcnow().isoformat()
                                                    }
                                                    supabase_client.table("images").update(update_data).eq("id", image_record["id"]).execute()
                                                    generated_images.append({
                                                        "id": image_record["id"],
                                                        "image_number": image_record["image_number"],
                                                        "url": storage_url,
                                                        "prompt": image_record["prompt"]
                                                    })
                                                    logger.info(f"✅ Successfully generated and uploaded image {image_record['image_number']} for blog {blog_id} to Supabase Storage")
                                                else:
                                                    error_msg = "Failed to upload image to Supabase Storage"
                                                    supabase_client.table("images").update({
                                                        "status": "failed",
                                                        "error_message": error_msg,
                                                        "updated_at": datetime.utcnow().isoformat()
                                                    }).eq("id", image_record["id"]).execute()
                                                    logger.error(f"❌ {error_msg} for image {image_record['image_number']}")
                                            except Exception as storage_error:
                                                error_msg = f"Supabase Storage upload failed: {str(storage_error)}"
                                                supabase_client.table("images").update({
                                                    "status": "failed",
                                                    "error_message": error_msg,
                                                    "updated_at": datetime.utcnow().isoformat()
                                                }).eq("id", image_record["id"]).execute()
                                                logger.error(f"❌ {error_msg} for image {image_record['image_number']}")
                                        else:
                                            error_msg = f"Failed to download image from Fal AI: {response.status}"
                                            supabase_client.table("images").update({
                                                "status": "failed",
                                                "error_message": error_msg,
                                                "updated_at": datetime.utcnow().isoformat()
                                            }).eq("id", image_record["id"]).execute()
                                            logger.error(f"❌ {error_msg} for image {image_record['image_number']}")
                            except Exception as e:
                                error_msg = f"Error during image processing: {str(e)}"
                                supabase_client.table("images").update({
                                    "status": "failed",
                                    "error_message": error_msg,
                                    "updated_at": datetime.utcnow().isoformat()
                                }).eq("id", image_record["id"]).execute()
                                logger.error(f"❌ {error_msg} for image {image_record['image_number']}")
                        
                        elif "image_data" in generated_image and generated_image["image_data"]:
                            # We have base64 data, decode and upload directly to Supabase Storage
                            base64_data = generated_image["image_data"]
                            logger.info(f"🖼️ Processing base64 image data for image {image_record['image_number']}")
                            
                            try:
                                # Decode base64 data
                                import base64
                                if base64_data.startswith('data:image/'):
                                    # Remove data URL prefix
                                    base64_data = base64_data.split(',', 1)[1]
                                
                                image_data = base64.b64decode(base64_data)
                                logger.info(f"✅ Decoded {len(image_data)} bytes from base64 data")
                                
                                # Upload to Supabase Storage bucket "images"
                                try:
                                    storage_path = f"{blog_id}_{image_record['image_number']}_image.jpg"
                                    storage_response = supabase_client.storage.from_("images").upload(
                                        path=storage_path,
                                        file=image_data,
                                        file_options={"content-type": "image/jpeg"}
                                    )
                                    if storage_response:
                                        storage_url = supabase_client.storage.from_("images").get_public_url(storage_path)
                                        logger.info(f"✅ Image uploaded to Supabase Storage: {storage_path}")
                                        logger.info(f"🖼️ Storage URL: {storage_url}")
                                        update_data = {
                                            "s3_url": storage_url,
                                            "status": "generated",
                                            "updated_at": datetime.utcnow().isoformat()
                                        }
                                        supabase_client.table("images").update(update_data).eq("id", image_record["id"]).execute()
                                        generated_images.append({
                                            "id": image_record["id"],
                                            "image_number": image_record["image_number"],
                                            "url": storage_url,
                                            "prompt": image_record["prompt"]
                                        })
                                        logger.info(f"✅ Successfully generated and uploaded image {image_record['image_number']} for blog {blog_id} to Supabase Storage")
                                    else:
                                        error_msg = "Failed to upload image to Supabase Storage"
                                        supabase_client.table("images").update({
                                            "status": "failed",
                                            "error_message": error_msg,
                                            "updated_at": datetime.utcnow().isoformat()
                                        }).eq("id", image_record["id"]).execute()
                                        logger.error(f"❌ {error_msg} for image {image_record['image_number']}")
                                except Exception as storage_error:
                                    error_msg = f"Supabase Storage upload failed: {str(storage_error)}"
                                    supabase_client.table("images").update({
                                        "status": "failed",
                                        "error_message": error_msg,
                                        "updated_at": datetime.utcnow().isoformat()
                                    }).eq("id", image_record["id"]).execute()
                                    logger.error(f"❌ {error_msg} for image {image_record['image_number']}")
                            except Exception as e:
                                error_msg = f"Error processing base64 image data: {str(e)}"
                                supabase_client.table("images").update({
                                    "status": "failed",
                                    "error_message": error_msg,
                                    "updated_at": datetime.utcnow().isoformat()
                                }).eq("id", image_record["id"]).execute()
                                logger.error(f"❌ {error_msg} for image {image_record['image_number']}")
                        
                        else:
                            # No valid image data
                            error_msg = "No valid image data returned from Fal AI"
                            supabase_client.table("images").update({
                                "status": "failed",
                                "error_message": error_msg,
                                "updated_at": datetime.utcnow().isoformat()
                            }).eq("id", image_record["id"]).execute()
                            logger.error(f"❌ {error_msg} for image {image_record['image_number']}")
                        
                    else:
                        # Update status to failed
                        error_msg = result.get("error", "Unknown error during generation")
                        supabase_client.table("images").update({
                            "status": "failed",
                            "error_message": error_msg,
                            "updated_at": datetime.utcnow().isoformat()
                        }).eq("id", image_record["id"]).execute()
                        
                        failed_images.append({
                            "id": image_record["id"],
                            "image_number": image_record["image_number"],
                            "error": error_msg
                        })
                        
                        logger.error(f"❌ Failed to generate image {image_record['image_number']} for blog {blog_id}: {error_msg}")
                        
                except Exception as e:
                    logger.error(f"❌ Error generating image {image_record['image_number']} for blog {blog_id}: {e}")
                    
                    # Update status to failed
                    supabase_client.table("images").update({
                        "status": "failed",
                        "error_message": str(e),
                        "updated_at": datetime.utcnow().isoformat()
                    }).eq("id", image_record["id"]).execute()
                    
                    failed_images.append({
                        "id": image_record["id"],
                        "image_number": image_record["image_number"],
                        "error": str(e)
                    })
                    
                    continue
            
            # Log summary
            logger.info(f"🎉 Image generation completed for blog {blog_id}: {len(generated_images)} successful, {len(failed_images)} failed")
            
            return {
                "success": True,
                "message": f"Generated {len(generated_images)} images, {len(failed_images)} failed",
                "blog_id": blog_id,
                "project_id": project_id,
                "images_generated": len(generated_images),
                "images_failed": len(failed_images),
                "generated_images": generated_images,
                "failed_images": failed_images
            }
            
        except Exception as e:
            logger.error(f"❌ Error in image generation for blog {blog_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "blog_id": blog_id
            }
    
    async def process_and_generate_images(
        self, 
        blog_id: str, 
        project_id: str, 
        title: str, 
        content: str,
        user_id: str,
        fal_api_key: str,
        style: str = "photographic",
        aspect_ratio: str = "16:9",
        quality: str = "standard"
    ) -> Dict[str, Any]:
        """
        Complete workflow: process blog content and generate images
        
        Args:
            blog_id: ID of the blog post
            project_id: ID of the project
            title: Blog title
            content: Blog content
            user_id: ID of the user
            fal_api_key: Fal AI API key
            style: Image style
            aspect_ratio: Image aspect ratio
            quality: Image quality
            
        Returns:
            Dict containing complete workflow results
        """
        try:
            logger.info(f"🚀 Starting complete image workflow for blog {blog_id}")
            
            # Step 1: Process blog content and extract image placeholders
            process_result = await self.process_blog_for_images(
                blog_id, project_id, title, content, user_id, fal_api_key
            )
            
            if not process_result["success"]:
                return process_result
            
            if process_result["images_processed"] == 0:
                return process_result
            
            # Step 2: Generate images for the extracted placeholders
            generation_result = await self.generate_images_for_blog(
                blog_id, project_id, user_id, fal_api_key, style, aspect_ratio, quality
            )
            
            if not generation_result["success"]:
                return generation_result
            
            # Combine results
            return {
                "success": True,
                "message": f"Complete workflow completed: {process_result['images_processed']} processed, {generation_result['images_generated']} generated",
                "blog_id": blog_id,
                "project_id": project_id,
                "workflow_steps": {
                    "processing": process_result,
                    "generation": generation_result
                },
                "total_images_processed": process_result["images_processed"],
                "total_images_generated": generation_result["images_generated"],
                "total_images_failed": generation_result["images_failed"]
            }
            
        except Exception as e:
            logger.error(f"❌ Error in complete image workflow for blog {blog_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "blog_id": blog_id
            }
