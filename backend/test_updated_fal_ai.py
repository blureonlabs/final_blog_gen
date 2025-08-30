#!/usr/bin/env python3
"""
Test script to verify that the updated Fal AI service returns URLs instead of base64 data
"""

import asyncio
import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.fal_ai_service import FalAIService

async def test_updated_fal_ai():
    """Test the updated Fal AI service"""
    
    print("🧪 Testing updated Fal AI service...")
    
    try:
        # Initialize the service
        api_key = "bf364836-0f46-4a0b-832d-b5e7c8f930ff:c7b3dca20440f13612aebac00867a119"
        fal_service = FalAIService(api_key)
        
        # Test image generation
        prompt = "A simple test image of a red apple on a white background"
        style = "photographic"
        aspect_ratio = "16:9"
        quality = "standard"
        
        print(f"📝 Prompt: {prompt}")
        print(f"🎨 Style: {style}")
        print(f"📐 Aspect Ratio: {aspect_ratio}")
        print(f"⭐ Quality: {quality}")
        
        # Generate image
        result = await fal_service.generate_image(prompt, style, aspect_ratio, quality)
        
        print(f"\n🔍 Result:")
        print(f"  Success: {result.get('success')}")
        
        if result.get('success'):
            if result.get('image_url'):
                print(f"  ✅ Got URL: {result['image_url'][:100]}...")
                if result['image_url'].startswith('data:'):
                    print(f"  ⚠️  Still getting base64 data in URL field")
                else:
                    print(f"  🎉 SUCCESS! Got actual HTTP URL")
            elif result.get('image_data'):
                print(f"  ⚠️  Got base64 data: {len(result['image_data'])} chars")
            else:
                print(f"  ❌ No image data returned")
        else:
            print(f"  ❌ Error: {result.get('error')}")
        
        print(f"\n📊 Metadata: {result.get('metadata', {})}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Set API key
    os.environ['FAL_KEY'] = "bf364836-0f46-4a0b-832d-b5e7c8f930ff:c7b3dca20440f13612aebac00867a119"
    
    # Run test
    asyncio.run(test_updated_fal_ai())
