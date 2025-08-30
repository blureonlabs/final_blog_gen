#!/usr/bin/env python3
"""
Test User API Key Requirement
This script verifies that users must provide their own Fal AI API keys for image generation
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.image_generation_service import ImageGenerationService
from services.image_placeholder_processor import ImagePlaceholderProcessor

# Load environment variables
load_dotenv()

async def test_user_api_key_requirement():
    """Test that users must provide their own Fal AI API keys"""
    print("🧪 Testing User API Key Requirement...")
    print("=" * 50)
    
    try:
        # Initialize services
        image_service = ImageGenerationService()
        image_processor = ImagePlaceholderProcessor()
        
        print("✅ Services initialized successfully")
        
        # Test 1: Image Generation Service without API key
        print("\n🧪 Test 1: Image Generation Service without API key...")
        
        if image_service.fal_service is None:
            print("✅ Image service correctly requires API key to be set")
        else:
            print("❌ Image service should not have fal_service initialized without API key")
            return False
        
        # Test 2: Try to generate images without API key
        print("\n🧪 Test 2: Attempting image generation without API key...")
        
        try:
            result = await image_service.generate_blog_images(
                blog_id="test-blog",
                project_id="test-project",
                title="Test Blog",
                content="Test content",
                seo_meta={},
                num_images=1,
                style="photographic",
                aspect_ratio="16:9",
                quality="standard"
            )
            
            if not result["success"] and "not initialized" in result.get("error", "").lower():
                print("✅ Correctly prevented image generation without API key")
            else:
                print("❌ Should have prevented image generation without API key")
                return False
                
        except Exception as e:
            if "not initialized" in str(e).lower():
                print("✅ Correctly threw error for missing API key")
            else:
                print(f"❌ Unexpected error: {e}")
                return False
        
        # Test 3: Set API key and verify it works
        print("\n🧪 Test 3: Setting API key and verifying functionality...")
        
        test_api_key = "test-key-12345"
        image_service.set_fal_api_key(test_api_key)
        
        if image_service.fal_service is not None:
            print("✅ API key successfully set and service initialized")
        else:
            print("❌ Service should be initialized after setting API key")
            return False
        
        # Test 4: Image Placeholder Processor without API key
        print("\n🧪 Test 4: Image Placeholder Processor without API key...")
        
        try:
            result = await image_processor.process_stored_placeholders(
                blog_id="test-blog",
                fal_api_key=None,  # No API key
                s3_bucket_name="images"
            )
            
            if not result["success"] and "no fal ai api key provided" in result.get("error", "").lower():
                print("✅ Correctly prevented processing without API key")
            else:
                print("❌ Should have prevented processing without API key")
                return False
                
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
        
        # Test 5: Image Placeholder Processor with API key
        print("\n🧪 Test 5: Image Placeholder Processor with API key...")
        
        try:
            result = await image_processor.process_stored_placeholders(
                blog_id="test-blog",
                fal_api_key=test_api_key,  # With API key
                s3_bucket_name="images"
            )
            
            # This should fail due to invalid API key, but not due to missing API key
            if "no fal ai api key provided" not in result.get("error", "").lower():
                print("✅ API key requirement satisfied (even if key is invalid)")
            else:
                print("❌ Still complaining about missing API key")
                return False
                
        except Exception as e:
            print(f"✅ API key requirement satisfied (error: {e})")
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! User API key requirement is working correctly.")
        print("\n📋 Summary:")
        print("   ✅ Services require API keys to be set")
        print("   ✅ Image generation blocked without API key")
        print("   ✅ Image processing blocked without API key")
        print("   ✅ API key can be set and service becomes functional")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

async def main():
    """Main test function"""
    print("🚀 Testing User API Key Requirement...")
    
    success = await test_user_api_key_requirement()
    
    if success:
        print("\n🎉 Success! Users must provide their own Fal AI API keys.")
        print("This ensures proper cost tracking and user isolation.")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
    
    return success

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
