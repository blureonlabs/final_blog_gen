#!/usr/bin/env python3
"""
Test script to check Fal AI service response format
"""

import asyncio
import logging
from services.fal_ai_service import FalAIService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_fal_ai_response():
    """Test the Fal AI service response format"""
    try:
        logger.info("🧪 Testing Fal AI service response...")
        
        # Initialize the service
        fal_service = FalAIService("test-key-123")
        
        # Test image generation
        logger.info("🎨 Testing image generation...")
        result = await fal_service.generate_image(
            prompt="A simple test image",
            style="photographic",
            aspect_ratio="16:9",
            quality="standard"
        )
        
        logger.info(f"✅ Fal AI response: {result}")
        
        # Check the structure
        if result.get("success"):
            logger.info(f"🖼️ Image URL: {result.get('image_url', 'No image_url field')}")
            logger.info(f"📊 Metadata: {result.get('metadata', 'No metadata field')}")
        else:
            logger.info(f"❌ Error: {result.get('error', 'No error field')}")
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_fal_ai_response())
