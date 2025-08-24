#!/usr/bin/env python3
"""
Script to create a test project in the database
"""

import sys
import os
import uuid
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.supabase_client import supabase_client
from core.config import settings

def create_test_project():
    """Create a test project in the database"""
    print("🔍 Creating test project...")
    
    if not supabase_client:
        print("❌ Supabase client not initialized")
        return False
    
    try:
        # Use the existing user ID from the database
        existing_user_id = "64846101-1a25-4e23-a756-2547d4146308"
        
        # Create a test project
        test_project = {
            "id": str(uuid.uuid4()),
            "user_id": existing_user_id,  # Use the existing user ID
            "name": "Test Project for Debugging",
            "description": "This is a test project to verify the database connection",
            "num_blogs": 5,
            "completed_blogs": 0,
            "status": "ready",
            "wordpress_account_id": str(uuid.uuid4()),
            "api_keys": {
                "openai": "7eb7fa46-b731-48d4-a0fb-33ac1f7207ca",
                "gemini": "6d121ba0-880e-47c3-ba41-4a1ade6653ed",
                "serp": "5146b54d-b1c5-4b74-a749-af56509834ee"
            },
            "draft_creation_model": "openai",
            "content_vetting_model": "openai",
            "model_settings": {
                "gemini": {
                    "temperature": 0.3,
                    "model_version": "gemini-pro",
                    "max_output_tokens": 2000
                },
                "openai": {
                    "max_tokens": 2000,
                    "temperature": 0.7,
                    "model_version": "gpt-4"
                }
            },
            "workflow_preferences": {
                "vetting_threshold": 0.8,
                "auto_vet_after_draft": True,
                "require_human_review": False
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        print(f"📝 Test project data: {test_project}")
        print(f"🔑 Using existing user ID: {existing_user_id}")
        
        # Insert the test project
        response = supabase_client.table("projects").insert(test_project).execute()
        
        if response.data:
            print(f"✅ Test project created successfully!")
            print(f"   Project ID: {response.data[0].get('id')}")
            print(f"   Project Name: {response.data[0].get('name')}")
            print(f"   Status: {response.data[0].get('status')}")
            return response.data[0].get('id')
        else:
            print("❌ Failed to create test project")
            return None
            
    except Exception as e:
        print(f"❌ Error creating test project: {e}")
        return False

def verify_project_creation(project_id):
    """Verify that the project was created and can be found"""
    print(f"\n🔍 Verifying project creation for ID: {project_id}")
    
    if not supabase_client:
        print("❌ Supabase client not initialized")
        return False
    
    try:
        # Try to find the project
        response = supabase_client.table("projects").select("*").eq("id", project_id).execute()
        
        if response.data:
            project = response.data[0]
            print(f"✅ Project found successfully!")
            print(f"   Name: {project.get('name')}")
            print(f"   Status: {project.get('status')}")
            print(f"   Num Blogs: {project.get('num_blogs')}")
            return True
        else:
            print("❌ Project not found after creation")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying project: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Test Project Creation Script")
    print("=" * 50)
    
    # Step 1: Create test project
    project_id = create_test_project()
    
    if project_id:
        # Step 2: Verify project creation
        verify_project_creation(project_id)
        
        print(f"\n🎯 Test project ID: {project_id}")
        print("💡 Use this ID to test the blog generation API!")
    else:
        print("\n❌ Failed to create test project")
    
    print("\n✅ Script completed!")

if __name__ == "__main__":
    main()
