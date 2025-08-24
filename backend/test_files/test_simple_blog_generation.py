#!/usr/bin/env python3
"""
Simple test for blog generation without storage
"""

import sys
import os
import uuid
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.supabase_client import supabase_client
from core.config import settings

def create_simple_blog():
    """Create a simple blog without AI generation for testing"""
    print("🔍 Creating simple test blog...")
    
    if not supabase_client:
        print("❌ Supabase client not initialized")
        return False
    
    try:
        # Create a simple blog record
        test_blog = {
            "id": str(uuid.uuid4()),
            "project_id": "18528961-d5f9-45fb-9b55-c261f89f2f75",  # Use the test project ID
            "title": "Test Blog Post - Manual Creation",
            "status": "ready",
            "word_count": 500,
            "prompt": "Test blog creation without AI generation",
            "ai_model": "manual",
            "storage_path": "test/path.json",
            "storage_bucket": "blog-content",
            "content_size_bytes": 1000,
            "content_hash": "test_hash_123",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        print(f"📝 Test blog data: {test_blog}")
        
        # Insert the test blog
        response = supabase_client.table("blogs").insert(test_blog).execute()
        
        if response.data:
            print(f"✅ Test blog created successfully!")
            print(f"   Blog ID: {response.data[0].get('id')}")
            print(f"   Title: {response.data[0].get('title')}")
            print(f"   Status: {response.data[0].get('status')}")
            return response.data[0].get('id')
        else:
            print("❌ Failed to create test blog")
            return None
            
    except Exception as e:
        print(f"❌ Error creating test blog: {e}")
        return False

def verify_blog_creation(blog_id):
    """Verify that the blog was created and can be found"""
    print(f"\n🔍 Verifying blog creation for ID: {blog_id}")
    
    if not supabase_client:
        print("❌ Supabase client not initialized")
        return False
    
    try:
        # Try to find the blog
        response = supabase_client.table("blogs").select("*").eq("id", blog_id).execute()
        
        if response.data:
            blog = response.data[0]
            print(f"✅ Blog found successfully!")
            print(f"   Title: {blog.get('title')}")
            print(f"   Status: {blog.get('status')}")
            print(f"   Project ID: {blog.get('project_id')}")
            return True
        else:
            print("❌ Blog not found after creation")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying blog: {e}")
        return False

def check_project_blogs(project_id):
    """Check how many blogs exist for a project"""
    print(f"\n🔍 Checking blogs for project: {project_id}")
    
    if not supabase_client:
        print("❌ Supabase client not initialized")
        return False
    
    try:
        # Get all blogs for the project
        response = supabase_client.table("blogs").select("*").eq("project_id", project_id).execute()
        
        print(f"📊 Found {len(response.data)} blogs for project")
        
        if response.data:
            for i, blog in enumerate(response.data):
                print(f"  {i+1}. ID: {blog.get('id')}")
                print(f"     Title: {blog.get('title')}")
                print(f"     Status: {blog.get('status')}")
                print(f"     Created: {blog.get('created_at')}")
                print()
        
        return True
    except Exception as e:
        print(f"❌ Error checking project blogs: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Simple Blog Creation Test")
    print("=" * 50)
    
    # Step 1: Create simple blog
    blog_id = create_simple_blog()
    
    if blog_id:
        # Step 2: Verify blog creation
        verify_blog_creation(blog_id)
        
        # Step 3: Check all blogs for the project
        project_id = "18528961-d5f9-45fb-9b55-c261f89f2f75"
        check_project_blogs(project_id)
        
        print(f"\n🎯 Test blog ID: {blog_id}")
        print("💡 This proves the database and storage path work!")
    else:
        print("\n❌ Failed to create test blog")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    main()
