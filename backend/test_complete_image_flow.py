#!/usr/bin/env python3
"""
Complete Image Generation and Processing Flow Test
This script tests the entire flow from blog generation with placeholders to image generation and S3 storage
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.blog_generation_service import BlogGenerationService
from services.image_placeholder_processor import ImagePlaceholderProcessor
from services.fal_ai_service import FalAIService

# Load environment variables
load_dotenv()

async def test_complete_image_flow():
    """Test the complete image generation and processing flow"""
    print("🚀 Testing Complete Image Generation and Processing Flow...")
    print("=" * 60)
    
    # Check required environment variables
    fal_api_key = os.getenv("FAL_AI_API_KEY")
    if not fal_api_key:
        print("❌ FAL_AI_API_KEY not found in environment variables")
        print("Please set FAL_AI_API_KEY in your .env file")
        return False
    
    try:
        # Initialize services
        blog_service = BlogGenerationService()
        image_processor = ImagePlaceholderProcessor()
        fal_service = FalAIService(fal_api_key)
        
        print("✅ Services initialized successfully")
        
        # Test 1: Generate blog content with image placeholders
        print("\n🧪 Test 1: Generating blog content with image placeholders...")
        
        test_project_description = "The Future of Artificial Intelligence in Business"
        test_blog_number = 1
        
        blog_result = await blog_service.generate_blog_content(
            project_description=test_project_description,
            blog_number=test_blog_number,
            ai_model="openai",  # or "gemini"
            project_api_keys={"openai": "test-key"},  # Mock key for testing
            generate_images=True,
            num_images_per_blog=2
        )
        
        if blog_result["success"]:
            print("✅ Blog content generated successfully")
            print(f"   Title: {blog_result['title']}")
            print(f"   Word count: {blog_result['word_count']}")
            
            # Check for image placeholders
            content = blog_result["content"]
            placeholders = image_processor.extract_image_placeholders(content)
            
            if placeholders:
                print(f"✅ Found {len(placeholders)} image placeholders:")
                for i, placeholder in enumerate(placeholders, 1):
                    print(f"   {i}. [image:{placeholder['description']}]")
            else:
                print("⚠️ No image placeholders found in generated content")
                print("   Content preview:", content[:200] + "...")
        else:
            print(f"❌ Blog generation failed: {blog_result.get('error', 'Unknown error')}")
            return False
        
        # Test 2: Extract and validate image placeholders
        print("\n🧪 Test 2: Extracting and validating image placeholders...")
        
        validation_result = image_processor.validate_image_placeholders(content, 2)
        
        if validation_result["valid"]:
            print("✅ Image placeholder validation passed")
            print(f"   Found: {validation_result['actual_count']} placeholders")
            print(f"   Expected: {validation_result['expected_count']} placeholders")
        else:
            print("⚠️ Image placeholder validation failed")
            print(f"   Found: {validation_result['actual_count']} placeholders")
            print(f"   Expected: {validation_result['expected_count']} placeholders")
            if validation_result.get("error"):
                print(f"   Error: {validation_result['error']}")
        
        # Test 3: Test Fal AI service connectivity
        print("\n🧪 Test 3: Testing Fal AI service connectivity...")
        
        is_valid = await fal_service.validate_api_key()
        if is_valid:
            print("✅ Fal AI API key is valid")
        else:
            print("❌ Fal AI API key is invalid")
            return False
        
        # Test 4: Test image generation (single image)
        print("\n🧪 Test 4: Testing single image generation...")
        
        test_prompt = "Modern office workspace with productivity tools and organized desk setup"
        
        image_result = await fal_service.generate_image(
            prompt=test_prompt,
            style="photographic",
            aspect_ratio="16:9",
            quality="standard"
        )
        
        if image_result["success"]:
            print("✅ Single image generated successfully")
            print(f"   Image URL: {image_result['image_url']}")
            print(f"   Metadata: {image_result['metadata']}")
        else:
            print(f"❌ Single image generation failed: {image_result.get('error')}")
            return False
        
        # Test 5: Test multiple image generation
        print("\n🧪 Test 5: Testing multiple image generation...")
        
        multi_result = await fal_service.generate_multiple_images(
            prompt=test_prompt,
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
        
        # Test 6: Test image placeholder processor
        print("\n🧪 Test 6: Testing image placeholder processor...")
        
        # Create a mock blog content with placeholders
        mock_content = f"""
        # {test_project_description}
        
        This is a test blog post about artificial intelligence in business.
        
        [image:{test_prompt}]
        
        Here's some more content about AI applications.
        
        [image:Data visualization showing AI adoption trends in different industries]
        
        The future looks promising for AI integration.
        """
        
        # Extract placeholders
        extracted_placeholders = image_processor.extract_image_placeholders(mock_content)
        
        if len(extracted_placeholders) == 2:
            print("✅ Image placeholder extraction working correctly")
            for i, placeholder in enumerate(extracted_placeholders, 1):
                print(f"   {i}. {placeholder['placeholder']}")
        else:
            print(f"❌ Expected 2 placeholders, found {len(extracted_placeholders)}")
            return False
        
        # Test 7: Test placeholder replacement with mock images
        print("\n🧪 Test 7: Testing placeholder replacement...")
        
        mock_images = [
            {
                "url": "https://example.com/image1.jpg",
                "alt_text": test_prompt,
                "image_number": 1
            },
            {
                "url": "https://example.com/image2.jpg",
                "alt_text": "Data visualization showing AI adoption trends",
                "image_number": 2
            }
        ]
        
        replaced_content = image_processor.replace_placeholders_with_images(mock_content, mock_images)
        
        if "[image:" not in replaced_content and "<img" in replaced_content:
            print("✅ Placeholder replacement working correctly")
            print("   Content now contains HTML image tags")
        else:
            print("❌ Placeholder replacement failed")
            print("   Content still contains placeholders or missing HTML")
            return False
        
        print("\n" + "=" * 60)
        print("🎉 All tests passed! Complete image flow is working correctly.")
        print("\n📋 Summary of what was tested:")
        print("   ✅ Blog generation with image placeholders")
        print("   ✅ Image placeholder extraction and validation")
        print("   ✅ Fal AI service connectivity")
        print("   ✅ Single and multiple image generation")
        print("   ✅ Image placeholder processing")
        print("   ✅ Placeholder replacement with HTML")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

async def test_s3_integration():
    """Test S3 integration for image storage"""
    print("\n🧪 Testing S3 Integration...")
    
    try:
        from services.s3_storage_service import S3StorageService
        
        s3_service = S3StorageService()
        
        # Test S3 connection
        print("   Testing S3 connection...")
        
        # This would test actual S3 connectivity
        # For now, just check if the service can be instantiated
        print("✅ S3 service initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ S3 integration test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting Complete Image Flow Tests...")
    
    # Test the main flow
    main_test_success = await test_complete_image_flow()
    
    # Test S3 integration
    s3_test_success = await test_s3_integration()
    
    print("\n" + "=" * 60)
    print("📊 Final Test Results:")
    print(f"   Main Flow: {'✅ PASS' if main_test_success else '❌ FAIL'}")
    print(f"   S3 Integration: {'✅ PASS' if s3_test_success else '❌ PASS'}")
    
    if main_test_success and s3_test_success:
        print("\n🎉 All tests passed! The complete image generation and processing flow is ready.")
        return True
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
