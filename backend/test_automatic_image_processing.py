#!/usr/bin/env python3
"""
Test script for automatic image processing integration in blog generation service
"""

import asyncio
import logging
from services.blog_generation_service import BlogGenerationService
from core.supabase_client import supabase_client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_automatic_image_processing():
    """Test the automatic image processing integration"""
    
    try:
        logger.info("🚀 Testing automatic image processing integration...")
        
        # Initialize the service
        service = BlogGenerationService()
        
        # Test project details (use your actual project)
        project_id = "0fb81663-ea3b-4318-bcdc-ecb95d46d44c"  # Replace with actual project ID
        project_description = "Arun Icecreams brand analysis and marketing insights"
        
        # Test with image generation enabled
        logger.info("📝 Testing blog generation with automatic image processing...")
        
        # Generate a single blog with images enabled
        blog_data = await service.generate_blog_content(
            project_description=project_description,
            blog_number=1,
            ai_model="openai",  # or "gemini"
            project_api_keys={
                "openai": "your-openai-key-here",  # Replace with actual key
                "gemini": "your-gemini-key-here"   # Replace with actual key
            },
            generate_images=True,
            num_images_per_blog=2
        )
        
        logger.info(f"✅ Blog generated successfully: {blog_data['title']}")
        logger.info(f"📊 Word count: {blog_data['word_count']}")
        logger.info(f"🎨 Image placeholders: {blog_data['content'].count('[image:')}")
        
        # Check if image placeholders are present
        if '[image:' in blog_data['content']:
            logger.info("🎯 Image placeholders detected in content!")
            
            # Extract and display image placeholders
            import re
            pattern = r'\[image:([^\]\n]+)\]'
            matches = re.findall(pattern, blog_data['content'])
            
            logger.info(f"📸 Found {len(matches)} image placeholders:")
            for i, match in enumerate(matches, 1):
                logger.info(f"   {i}. {match.strip()}")
        else:
            logger.warning("⚠️ No image placeholders found in content")
        
        logger.info("🎉 Test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_automatic_image_processing())
