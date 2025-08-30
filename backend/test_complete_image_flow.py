#!/usr/bin/env python3
"""
Test the complete image generation flow:
1. Fal AI generates image
2. Download from Fal AI
3. Upload to Supabase Storage
4. Store URL in database
"""

import asyncio
import logging
import os
from services.blog_image_processor import BlogImageProcessor
from core.supabase_client import supabase_client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_complete_image_flow():
    """Test the complete image generation and storage flow"""
    
    try:
        logger.info("🚀 Testing complete image generation flow...")
        
        # Test parameters
        test_blog_id = "test-blog-123"
        test_project_id = "test-project-456"
        test_user_id = "test-user-789"
        
        # You need to set your actual Fal AI API key
        fal_api_key = "your-fal-ai-api-key-here"  # Replace with actual key
        
        if fal_api_key == "your-fal-ai-api-key-here":
            logger.error("❌ Please set your actual Fal AI API key in the script")
            return
        
        # Initialize the blog image processor
        processor = BlogImageProcessor()
        logger.info("✅ BlogImageProcessor initialized")
        
        # Test 1: Process blog for images
        logger.info("📝 Test 1: Processing blog for image placeholders...")
        
        test_content = """
        This is a test blog post with image placeholders.
        
        [image:A beautiful sunset over mountains, photographic style]
        
        [image:A cozy coffee shop interior with warm lighting]
        
        This is the end of the test blog.
        """
        
        process_result = await processor.process_blog_for_images(
            blog_id=test_blog_id,
            project_id=test_project_id,
            title="Test Blog for Image Generation",
            content=test_content,
            user_id=test_user_id,
            fal_api_key=fal_api_key
        )
        
        if process_result["success"]:
            logger.info(f"✅ Blog processing successful: {process_result['images_processed']} images found")
            
            # Test 2: Generate images for the blog
            logger.info("🎨 Test 2: Generating images for the blog...")
            
            generate_result = await processor.generate_images_for_blog(
                blog_id=test_blog_id,
                project_id=test_project_id,
                user_id=test_user_id,
                fal_api_key=fal_api_key,
                style="photographic",
                aspect_ratio="16:9",
                quality="standard"
            )
            
            if generate_result["success"]:
                logger.info(f"✅ Image generation successful: {generate_result['images_generated']} images generated")
                
                # Check the database for results
                logger.info("📊 Checking database results...")
                
                db_response = supabase_client.table("images").select("*").eq("blog_id", test_blog_id).execute()
                
                if db_response.data:
                    logger.info(f"📸 Found {len(db_response.data)} images in database:")
                    
                    for img in db_response.data:
                        logger.info(f"   Image {img['image_number']}:")
                        logger.info(f"     Status: {img['status']}")
                        logger.info(f"     Prompt: {img['prompt']}")
                        logger.info(f"     Storage URL: {img.get('s3_url', 'Not set')[:100] if img.get('s3_url') else 'Not set'}...")
                        
                        if img['status'] == 'generated' and img.get('s3_url'):
                            logger.info(f"     ✅ Successfully stored in Supabase Storage!")
                        elif img['status'] == 'failed':
                            logger.info(f"     ❌ Failed: {img.get('error_message', 'Unknown error')}")
                        else:
                            logger.info(f"     ⏳ Still processing...")
                else:
                    logger.warning("⚠️ No images found in database")
                
                # Test 3: Check Supabase Storage
                logger.info("🪣 Test 3: Checking Supabase Storage...")
                
                try:
                    # List files in the images bucket
                    storage_files = supabase_client.storage.from_("images").list("")
                    logger.info(f"📁 Files in storage bucket: {storage_files}")
                    
                    # Check for our test images
                    test_files = [f for f in storage_files if test_blog_id in f]
                    if test_files:
                        logger.info(f"✅ Found {len(test_files)} test images in storage:")
                        for file in test_files:
                            logger.info(f"   📄 {file}")
                    else:
                        logger.warning("⚠️ No test images found in storage bucket")
                        
                except Exception as storage_error:
                    logger.error(f"❌ Error checking storage: {storage_error}")
                
            else:
                logger.error(f"❌ Image generation failed: {generate_result.get('error', 'Unknown error')}")
                
        else:
            logger.error(f"❌ Blog processing failed: {process_result.get('error', 'Unknown error')}")
        
        logger.info("🎉 Complete image flow test finished!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_complete_image_flow())
