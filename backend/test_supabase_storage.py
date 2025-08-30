#!/usr/bin/env python3
"""
Test script for Supabase Storage integration
"""

import asyncio
import logging
from core.supabase_client import supabase_client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_supabase_storage():
    """Test Supabase Storage functionality"""
    
    try:
        logger.info("🚀 Testing Supabase Storage integration...")
        
        # Test bucket access
        try:
            buckets = supabase_client.storage.list_buckets()
            logger.info(f"✅ Available buckets: {[b.name for b in buckets]}")
            
            # Check if 'images' bucket exists
            images_bucket = None
            for bucket in buckets:
                if bucket.name == "images":
                    images_bucket = bucket
                    break
            
            if images_bucket:
                logger.info("✅ 'images' bucket found")
                logger.info(f"📊 Bucket details: {images_bucket}")
            else:
                logger.warning("⚠️ 'images' bucket not found - you may need to create it")
                
        except Exception as e:
            logger.error(f"❌ Error accessing storage buckets: {e}")
            return
        
        # Test file upload (if bucket exists)
        if images_bucket:
            try:
                # Create a simple test image (1x1 pixel JPEG)
                test_image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
                
                test_path = "test_image.jpg"
                
                logger.info(f"📤 Testing file upload to path: {test_path}")
                
                # Upload test file
                upload_response = supabase_client.storage.from_("images").upload(
                    path=test_path,
                    file=test_image_data,
                    file_options={"content-type": "image/jpeg"}
                )
                
                if upload_response:
                    logger.info("✅ Test file uploaded successfully")
                    
                    # Get public URL
                    public_url = supabase_client.storage.from_("images").get_public_url(test_path)
                    logger.info(f"🖼️ Public URL: {public_url}")
                    
                    # Clean up - delete test file
                    try:
                        supabase_client.storage.from_("images").remove([test_path])
                        logger.info("🧹 Test file cleaned up")
                    except Exception as cleanup_error:
                        logger.warning(f"⚠️ Could not clean up test file: {cleanup_error}")
                        
                else:
                    logger.error("❌ Test file upload failed")
                    
            except Exception as e:
                logger.error(f"❌ Error during file upload test: {e}")
        
        logger.info("🎉 Supabase Storage test completed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_supabase_storage())
