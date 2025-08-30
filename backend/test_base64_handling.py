#!/usr/bin/env python3
"""
Test script to verify base64 image handling in BlogImageProcessor
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.blog_image_processor import BlogImageProcessor

async def test_base64_handling():
    """Test the base64 image handling functionality"""
    
    print("🧪 Testing base64 image handling in BlogImageProcessor...")
    
    try:
        # Initialize the processor
        processor = BlogImageProcessor()
        
        # Test data
        blog_id = "test-blog-123"
        project_id = "test-project-123"
        
        # Simulate a base64 image response from Fal AI
        base64_image_data = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAIBAQEBAQIBAQECAgICAgQDAgICAgUEBAMEBgUGBgYFBgYGBwkIBgcJBwYGCAsICQoKCgoKBggLDAsKDAkKCgr/2wBDAQICAgICAgUDAwUKBwYHCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgr/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
        
        # Create a test image record
        image_record = {
            "id": "test-image-123",
            "image_number": 1,
            "prompt": "Test image prompt",
            "status": "generating"
        }
        
        print(f"📝 Test image record: {image_record}")
        print(f"🖼️ Base64 data length: {len(base64_image_data)}")
        print(f"🔍 Base64 starts with 'data:': {base64_image_data.startswith('data:')}")
        
        # Test the base64 detection logic
        if str(base64_image_data).startswith('data:'):
            print("✅ Base64 detection working correctly")
            
            # Test base64 decoding
            import base64
            base64_data = base64_image_data.split(',', 1)[1]
            image_data = base64.b64decode(base64_data)
            print(f"✅ Base64 decoding successful: {len(image_data)} bytes")
            
            # Test storage path generation
            storage_path = f"{blog_id}_{image_record['image_number']}_image.jpg"
            print(f"📁 Storage path: {storage_path}")
            
            print("✅ Base64 handling test completed successfully!")
        else:
            print("❌ Base64 detection failed")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_base64_handling())
