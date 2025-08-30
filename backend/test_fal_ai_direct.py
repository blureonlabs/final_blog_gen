#!/usr/bin/env python3
"""
Direct test of Fal AI FLUX.1 model to see what's being returned
"""

import os
import asyncio
import logging
from core.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_fal_ai_direct():
    """Test Fal AI directly to see the response format"""
    try:
        logger.info("🧪 Testing Fal AI FLUX.1 directly...")
        
        # Check if we have the API key
        fal_key = os.getenv("FAL_KEY") or settings.FAL_AI_API_KEY
        if not fal_key:
            logger.error("❌ No Fal AI API key found")
            return
        
        logger.info(f"🔑 Using Fal AI API key: {fal_key[:10]}...")
        
        # Import fal_client
        try:
            import fal_client
            logger.info("✅ fal-client imported successfully")
        except ImportError:
            logger.error("❌ fal-client not installed. Run: pip install fal-client")
            return
        
        # Set the API key
        os.environ["FAL_KEY"] = fal_key
        
        # Test the model directly
        logger.info("🎨 Submitting request to Fal AI FLUX.1...")
        
        # Submit request
        result = fal_client.submit(
            "fal-ai/flux/dev",
            arguments={
                "prompt": "A simple test image of a red apple on a white background",
                "image_size": "landscape_16_9",
                "num_inference_steps": 28,
                "guidance_scale": 3.5,
                "sync_mode": True,
                "num_images": 1,
                "enable_safety_checker": True,
                "output_format": "jpeg",
                "acceleration": "none"
            }
        )
        
        logger.info(f"📤 Request submitted with ID: {result.request_id}")
        
        # Get the result
        logger.info("⏳ Waiting for result...")
        final_result = fal_client.result("fal-ai/flux/dev", result.request_id)
        
        logger.info("🔍 Raw Fal AI response:")
        logger.info(f"Type: {type(final_result)}")
        logger.info(f"Content: {final_result}")
        
        if final_result and "images" in final_result:
            logger.info("✅ Images found in response")
            for i, img in enumerate(final_result["images"]):
                logger.info(f"Image {i+1}:")
                logger.info(f"  Keys: {list(img.keys())}")
                logger.info(f"  URL: {img.get('url', 'NOT_FOUND')}")
                logger.info(f"  Content type: {img.get('content_type', 'NOT_FOUND')}")
                if 'image' in img:
                    logger.info(f"  Has base64 data: {bool(img['image'])}")
                    if img['image']:
                        logger.info(f"  Base64 data length: {len(str(img['image']))}")
                        logger.info(f"  Base64 starts with 'data:': {str(img['image']).startswith('data:')}")
        else:
            logger.error("❌ No images in response")
            logger.error(f"Response keys: {list(final_result.keys()) if final_result else 'None'}")
        
    except Exception as e:
        logger.error(f"❌ Error testing Fal AI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fal_ai_direct())
