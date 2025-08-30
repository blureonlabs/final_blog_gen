#!/usr/bin/env python3
"""
Test script for the image generation backend
Run this to verify that the image generation service is working correctly
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.fal_ai_service import FalAIService
from services.image_generation_service import ImageGenerationService

# Load environment variables
load_dotenv()

async def test_fal_ai_service():
    """Test the Fal AI service directly"""
    print("🧪 Testing Fal AI Service...")
    
    # Get API key from environment
    api_key = os.getenv("FAL_AI_API_KEY")
    if not api_key:
        print("❌ FAL_AI_API_KEY not found in environment variables")
        print("Please set FAL_AI_API_KEY in your .env file")
        return False
    
    try:
        # Initialize service
        fal_service = FalAIService(api_key)
        print("✅ Fal AI service initialized")
        
        # Test API key validation
        print("🔑 Validating API key...")
        is_valid = await fal_service.validate_api_key()
        if is_valid:
            print("✅ API key is valid")
        else:
            print("❌ API key is invalid")
            return False
        
        # Test single image generation
        print("🎨 Testing single image generation...")
        result = await fal_service.generate_image(
            prompt="A beautiful sunset over mountains, photographic style",
            style="photographic",
            aspect_ratio="16:9",
            quality="standard"
        )
        
        if result["success"]:
            print("✅ Single image generated successfully")
            print(f"   Image URL: {result['image_url']}")
            print(f"   Metadata: {result['metadata']}")
        else:
            print(f"❌ Single image generation failed: {result.get('error')}")
            return False
        
        # Test multiple image generation
        print("🎨 Testing multiple image generation...")
        multi_result = await fal_service.generate_multiple_images(
            prompt="A modern office workspace, clean design",
            count=2,
            style="modern",
            aspect_ratio="16:9",
            quality="standard"
        )
        
        if multi_result["success"]:
            print("✅ Multiple images generated successfully")
            print(f"   Generated: {multi_result['total_generated']}/{multi_result['requested_count']}")
            for i, img in enumerate(multi_result["images"]):
                print(f"   Image {i+1}: {img['url']}")
        else:
            print(f"❌ Multiple image generation failed: {multi_result.get('error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Fal AI service: {e}")
        return False

async def test_image_generation_service():
    """Test the main image generation service"""
    print("\n🧪 Testing Image Generation Service...")
    
    try:
        # Initialize service
        image_service = ImageGenerationService()
        print("✅ Image generation service initialized")
        
        # Test available options
        styles = image_service.get_available_styles()
        ratios = image_service.get_available_aspect_ratios()
        qualities = image_service.get_available_qualities()
        
        print(f"✅ Available styles: {len(styles)}")
        print(f"✅ Available aspect ratios: {len(ratios)}")
        print(f"✅ Available qualities: {len(qualities)}")
        
        # Test prompt generation
        title = "10 Tips for Better Productivity"
        content = "Productivity is essential for success in today's fast-paced world. Here are some key strategies..."
        seo_meta = {"keywords": ["productivity", "tips", "success"]}
        
        prompt = image_service._generate_image_prompt(title, content, seo_meta, "modern")
        print(f"✅ Generated prompt: {prompt[:100]}...")
        
        # Test placeholder image generation
        placeholder_url = image_service.generate_placeholder_image(title, "modern")
        print(f"✅ Placeholder image URL: {placeholder_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing image generation service: {e}")
        return False

async def test_integration():
    """Test the integration between services"""
    print("\n🧪 Testing Service Integration...")
    
    try:
        # Get API key
        api_key = os.getenv("FAL_AI_API_KEY")
        if not api_key:
            print("❌ FAL_AI_API_KEY not found")
            return False
        
        # Initialize integrated service
        image_service = ImageGenerationService()
        image_service.set_fal_api_key(api_key)
        print("✅ Integrated service initialized")
        
        # Test blog image generation
        blog_id = "test-blog-123"
        title = "The Future of Artificial Intelligence"
        content = "Artificial intelligence is transforming every industry..."
        seo_meta = {"keywords": ["AI", "technology", "future"]}
        
        print("🎨 Testing integrated blog image generation...")
        result = await image_service.generate_blog_images(
            blog_id=blog_id,
            title=title,
            content=content,
            seo_meta=seo_meta,
            num_images=1,
            style="digital-art",
            aspect_ratio="16:9",
            quality="standard"
        )
        
        if result["success"]:
            print("✅ Integrated blog image generation successful")
            print(f"   Generated: {result['total_generated']} images")
            for i, img in enumerate(result["images"]):
                print(f"   Image {i+1}: {img['url']}")
        else:
            print(f"❌ Integrated generation failed: {result.get('error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing integration: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting Image Generation Backend Tests...")
    print("=" * 50)
    
    # Test individual services
    fal_test = await test_fal_ai_service()
    service_test = await test_image_generation_service()
    integration_test = await test_integration()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Fal AI Service: {'✅ PASS' if fal_test else '❌ FAIL'}")
    print(f"   Image Generation Service: {'✅ PASS' if service_test else '❌ PASS'}")
    print(f"   Service Integration: {'✅ PASS' if integration_test else '❌ FAIL'}")
    
    if fal_test and service_test and integration_test:
        print("\n🎉 All tests passed! Image generation backend is working correctly.")
        return True
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
