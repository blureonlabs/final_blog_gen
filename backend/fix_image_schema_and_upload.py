#!/usr/bin/env python3
"""
Fix image generation issues:
1. Update database schema to handle longer URLs
2. Add S3 upload functionality for generated images
"""

import asyncio
import logging
import aiohttp
import os
from typing import Dict, Any
from core.supabase_client import supabase_client
from services.s3_storage_service import S3StorageService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_database_schema():
    """Fix the images table schema to handle longer URLs"""
    try:
        logger.info("🔧 Fixing database schema for images table...")
        
        # Update s3_url field to handle longer URLs
        sql_commands = [
            "ALTER TABLE images ALTER COLUMN s3_url TYPE VARCHAR(2000);",
            "ALTER TABLE images ALTER COLUMN wordpress_media_url TYPE VARCHAR(2000);"
        ]
        
        for sql in sql_commands:
            try:
                # Execute raw SQL
                response = supabase_client.rpc('exec_sql', {'sql': sql}).execute()
                logger.info(f"✅ Executed: {sql}")
            except Exception as e:
                logger.warning(f"⚠️ SQL execution failed (might already be updated): {e}")
        
        logger.info("✅ Database schema updated successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to update database schema: {e}")

async def download_and_upload_to_s3(image_url: str, blog_id: str, image_number: int) -> str:
    """Download image from Fal AI and upload to S3"""
    try:
        logger.info(f"📥 Downloading image {image_number} for blog {blog_id} from {image_url[:100]}...")
        
        # Download image from Fal AI
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    logger.info(f"✅ Downloaded {len(image_data)} bytes")
                    
                    # Upload to S3
                    s3_service = S3StorageService()
                    
                    # Generate S3 key
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    s3_key = f"blog-images/{blog_id}/image_{image_number}_{timestamp}.jpg"
                    
                    # Upload to S3
                    s3_url = await s3_service.upload_file_from_bytes(
                        file_bytes=image_data,
                        s3_key=s3_key,
                        content_type="image/jpeg"
                    )
                    
                    if s3_url:
                        logger.info(f"✅ Image uploaded to S3: {s3_url}")
                        return s3_url
                    else:
                        logger.error("❌ Failed to upload image to S3")
                        return None
                else:
                    logger.error(f"❌ Failed to download image: {response.status}")
                    return None
                    
    except Exception as e:
        logger.error(f"❌ Error downloading/uploading image: {e}")
        return None

async def fix_existing_failed_images():
    """Fix existing failed images by downloading and uploading to S3"""
    try:
        logger.info("🔧 Fixing existing failed images...")
        
        # Get all failed images
        response = supabase_client.table("images").select("*").eq("status", "failed").execute()
        
        if not response.data:
            logger.info("✅ No failed images to fix")
            return
        
        logger.info(f"📸 Found {len(response.data)} failed images to fix")
        
        fixed_count = 0
        for image in response.data:
            try:
                # Check if it has a Fal AI URL in error_message (temporary storage)
                error_data = image.get("error_message", {})
                if isinstance(error_data, dict) and "fal_url" in error_data:
                    fal_url = error_data["fal_url"]
                    
                    # Download and upload to S3
                    s3_url = await download_and_upload_to_s3(
                        fal_url, 
                        image["blog_id"], 
                        image["image_number"]
                    )
                    
                    if s3_url:
                        # Update image record
                        supabase_client.table("images").update({
                            "s3_url": s3_url,
                            "status": "generated",
                            "error_message": None,
                            "updated_at": datetime.now().isoformat()
                        }).eq("id", image["id"]).execute()
                        
                        fixed_count += 1
                        logger.info(f"✅ Fixed image {image['image_number']} for blog {image['blog_id']}")
                    else:
                        logger.warning(f"⚠️ Could not fix image {image['image_number']} for blog {image['blog_id']}")
                        
            except Exception as e:
                logger.error(f"❌ Error fixing image {image['id']}: {e}")
                continue
        
        logger.info(f"🎉 Fixed {fixed_count}/{len(response.data)} failed images")
        
    except Exception as e:
        logger.error(f"❌ Failed to fix existing images: {e}")

async def main():
    """Main function to fix image generation issues"""
    try:
        logger.info("🚀 Starting image generation fixes...")
        
        # Fix database schema
        await fix_database_schema()
        
        # Fix existing failed images
        await fix_existing_failed_images()
        
        logger.info("🎉 Image generation fixes completed!")
        
    except Exception as e:
        logger.error(f"❌ Main process failed: {e}")

if __name__ == "__main__":
    from datetime import datetime
    asyncio.run(main())
