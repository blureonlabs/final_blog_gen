#!/usr/bin/env python3
"""
Test script for the updated Fal AI service using official fal-client
"""

import asyncio
import logging
import os
from services.fal_ai_service import FalAIService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_fal_ai_service():
    """Test the updated Fal AI service"""
    
    try:
        logger.info("🚀 Testing updated Fal AI service...")
        
        # You'll need to set your actual Fal AI API key here
        api_key = "your-fal-ai-api-key-here"  # Replace with actual key
        
        if api_key == "your-fal-ai-api-key-here":
            logger.error("❌ Please set your actual Fal AI API key in the script")
            return
        
        # Initialize the service
        fal_service = FalAIService(api_key)
        logger.info("✅ Fal AI service initialized")
        
        # Test image generation
        logger.info("🎨 Testing image generation...")
        
        result = await fal_service.generate_image(
            prompt="A beautiful sunset over mountains, photographic style",
            style="photographic",
            aspect_ratio="16:9",
            quality="standard"
        )
        
        if result["success"]:
            logger.info("✅ Image generation successful!")
            logger.info(f"🖼️ Image URL: {result['image_url'][:100]}...")
            logger.info(f"📊 Metadata: {result['metadata']}")
        else:
            logger.error(f"❌ Image generation failed: {result.get('error', 'Unknown error')}")
            logger.error(f"📊 Error metadata: {result.get('metadata', {})}")
        
        logger.info("🎉 Test completed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_fal_ai_service())
