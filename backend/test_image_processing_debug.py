#!/usr/bin/env python3
"""
Debug script for image processing flow
"""

import asyncio
import logging
from services.blog_image_processor import BlogImageProcessor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_image_processing():
    """Test the image processing flow"""
    try:
        logger.info("🧪 Testing image processing flow...")
        
        # Initialize the processor
        processor = BlogImageProcessor()
        
        # Test data
        blog_id = "test-blog-123"
        project_id = "test-project-123"
        user_id = "test-user-123"
        fal_api_key = "test-key-123"
        
        # Test content with image placeholders
        content = """
        This is a test blog post about technology.
        
        [image:A futuristic computer with glowing blue lights]
        
        Technology is amazing and continues to evolve.
        
        [image:A robot working on a circuit board]
        
        The future is bright!
        """
        
        logger.info("📝 Testing blog processing for images...")
        result = await processor.process_blog_for_images(
            blog_id=blog_id,
            project_id=project_id,
            title="Test Blog",
            content=content,
            user_id=user_id,
            fal_api_key=fal_api_key
        )
        
        logger.info(f"✅ Blog processing result: {result}")
        
        if result.get("success"):
            logger.info("🎨 Testing image generation...")
            gen_result = await processor.generate_images_for_blog(
                blog_id=blog_id,
                project_id=project_id,
                user_id=user_id,
                fal_api_key=fal_api_key
            )
            
            logger.info(f"✅ Image generation result: {gen_result}")
        else:
            logger.error(f"❌ Blog processing failed: {result}")
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_image_processing())
