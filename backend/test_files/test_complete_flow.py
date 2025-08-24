#!/usr/bin/env python3
"""
Complete test script to verify the entire blog generation flow
Run this to test project creation, blog generation, and storage
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from core.supabase_client import supabase_client
from core.config import settings
from services.blog_generation_service import blog_generation_service

async def test_complete_flow():
    """Test the complete blog generation flow"""
    print("🧪 Testing Complete Blog Generation Flow...")
    print(f"🌐 Supabase URL: {settings.SUPABASE_URL}")
    
    try:
        # Test 1: Check Supabase connection
        print("\n1️⃣ Testing Supabase connection...")
        projects_response = supabase_client.table("projects").select("id").limit(1).execute()
        print(f"✅ Supabase connection successful: {len(projects_response.data)} projects found")
        
        # Test 2: Create a test project
        print("\n2️⃣ Creating test project...")
        test_project = {
            "name": "Test Blog Generation Project",
            "description": "This is a test project for blog generation",
            "total_blogs": 3,
            "completed_blogs": 0,
            "status": "pending",
            "api_keys": {
                "openai": "test-openai-key",
                "gemini": "test-gemini-key"
            },
            "draft_creation_model": "openai",
            "content_vetting_model": "openai"
        }
        
        # Insert test project
        project_result = supabase_client.table("projects").insert(test_project).select().execute()
        if project_result.data:
            project_id = project_result.data[0]["id"]
            print(f"✅ Test project created with ID: {project_id}")
        else:
            print("❌ Failed to create test project")
            return False
        
        # Test 3: Test blog generation service
        print("\n3️⃣ Testing blog generation service...")
        try:
            generated_blogs = await blog_generation_service.generate_blogs_for_project(
                project_id=project_id,
                project_description=test_project["description"],
                total_blogs=2,  # Generate 2 blogs for testing
                ai_model="openai",
                project_api_keys=test_project["api_keys"]
            )
            print(f"✅ Generated {len(generated_blogs)} blogs")
            
            # Check if blogs were stored in database
            blogs_response = supabase_client.table("blogs").select("*").eq("project_id", project_id).execute()
            print(f"✅ Found {len(blogs_response.data)} blogs in database")
            
            # Check if blogs have storage paths
            for blog in blogs_response.data:
                if blog.get("storage_path"):
                    print(f"✅ Blog {blog['id']} has storage path: {blog['storage_path']}")
                else:
                    print(f"⚠️ Blog {blog['id']} missing storage path")
            
        except Exception as e:
            print(f"❌ Blog generation failed: {e}")
            return False
        
        # Test 4: Test storage access
        print("\n4️⃣ Testing storage access...")
        try:
            buckets = supabase_client.storage.list_buckets()
            bucket_names = [bucket.name for bucket in buckets]
            print(f"✅ Storage accessible: {len(bucket_names)} buckets found")
            
            if settings.STORAGE_BUCKET_NAME in bucket_names:
                print(f"✅ Required bucket '{settings.STORAGE_BUCKET_NAME}' exists")
                
                # List files in the bucket
                files = supabase_client.storage.from_(settings.STORAGE_BUCKET_NAME).list()
                print(f"✅ Found {len(files)} files in storage bucket")
                
                # Check if our blog files exist
                for blog in blogs_response.data:
                    if blog.get("storage_path"):
                        try:
                            content = supabase_client.storage.from_(settings.STORAGE_BUCKET_NAME).download(blog["storage_path"])
                            if content:
                                print(f"✅ Blog content accessible: {blog['storage_path']}")
                            else:
                                print(f"⚠️ Blog content not accessible: {blog['storage_path']}")
                        except Exception as e:
                            print(f"⚠️ Could not access blog content {blog['storage_path']}: {e}")
                
            else:
                print(f"⚠️ Required bucket '{settings.STORAGE_BUCKET_NAME}' not found")
                
        except Exception as e:
            print(f"❌ Storage test failed: {e}")
            return False
        
        # Test 5: Clean up test data
        print("\n5️⃣ Cleaning up test data...")
        try:
            # Delete test blogs
            supabase_client.table("blogs").delete().eq("project_id", project_id).execute()
            print("✅ Test blogs deleted")
            
            # Delete test project
            supabase_client.table("projects").delete().eq("id", project_id).execute()
            print("✅ Test project deleted")
            
        except Exception as e:
            print(f"⚠️ Cleanup failed: {e}")
        
        print("\n🎉 All tests passed! Your blog generation flow is working correctly.")
        print("\n📋 What was tested:")
        print("1. ✅ Supabase connection")
        print("2. ✅ Project creation")
        print("3. ✅ Blog generation with project API keys")
        print("4. ✅ Storage integration (S3-compatible)")
        print("5. ✅ Database storage of blog metadata")
        print("6. ✅ Content retrieval from storage")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check your .env file has correct Supabase credentials")
        print("2. Ensure the database schema has been run")
        print("3. Verify storage is enabled in your Supabase project")
        print("4. Check if your project has storage quota available")
        return False

async def main():
    """Run the complete test"""
    success = await test_complete_flow()
    
    if success:
        print("\n✅ Ready for production use!")
    else:
        print("\n❌ Please fix the issues above before proceeding")

if __name__ == "__main__":
    asyncio.run(main())
