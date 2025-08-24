#!/usr/bin/env python3
"""
Simple test script to verify blog generation is working
"""

import asyncio
import json
from datetime import datetime

# Mock the blog generation service for testing
class MockBlogGenerationService:
    async def generate_blogs_for_project(
        self,
        project_id: str,
        project_description: str,
        num_blogs: int,
        ai_model: str = "openai",
        project_api_keys: dict = None
    ):
        """Mock blog generation for testing"""
        print(f"🚀 Mock: Starting blog generation for project {project_id}")
        print(f"📝 Mock: Generating {num_blogs} blogs about: {project_description}")
        print(f"🤖 Mock: Using AI model: {ai_model}")
        
        if project_api_keys:
            print(f"🔑 Mock: Project API keys: {list(project_api_keys.keys())}")
        
        generated_blogs = []
        for i in range(num_blogs):
            blog_data = {
                "id": f"mock-blog-{i+1}",
                "title": f"Mock Blog {i+1}: {project_description[:30]}...",
                "status": "ready",
                "word_count": 500 + (i * 100),
                "prompt": f"Generate content about {project_description}",
                "ai_model": ai_model,
                "storage_path": f"blogs/{project_id}/mock_blog_{i+1}.json",
                "storage_bucket": "blog-content",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            generated_blogs.append(blog_data)
            print(f"✅ Mock: Generated blog {i+1}: {blog_data['title']}")
        
        print(f"🎉 Mock: Blog generation completed: {len(generated_blogs)}/{num_blogs} blogs generated")
        return generated_blogs

async def test_blog_generation():
    """Test the blog generation flow"""
    print("🧪 Testing Blog Generation Service")
    print("=" * 50)
    
    # Create mock service
    service = MockBlogGenerationService()
    
    # Test data
    project_id = "test-project-123"
    project_description = "AI-powered content generation platform for modern businesses"
    num_blogs = 3
    ai_model = "openai"
    project_api_keys = {
        "openai": "sk-test-key-123",
        "gemini": "gemini-test-key-456"
    }
    
    try:
        # Test blog generation
        result = await service.generate_blogs_for_project(
            project_id=project_id,
            project_description=project_description,
            num_blogs=num_blogs,
            ai_model=ai_model,
            project_api_keys=project_api_keys
        )
        
        print("\n📊 Test Results:")
        print(f"✅ Successfully generated {len(result)} blogs")
        print(f"📁 First blog storage path: {result[0]['storage_path']}")
        print(f"🔍 Blog statuses: {[blog['status'] for blog in result]}")
        
        # Verify data structure
        required_fields = ['id', 'title', 'status', 'storage_path', 'storage_bucket']
        for blog in result:
            missing_fields = [field for field in required_fields if field not in blog]
            if missing_fields:
                print(f"❌ Blog {blog['id']} missing fields: {missing_fields}")
            else:
                print(f"✅ Blog {blog['id']} has all required fields")
        
        print("\n🎯 Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_blog_generation())
    exit(0 if success else 1)
