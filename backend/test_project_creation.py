#!/usr/bin/env python3
"""
Test script for project creation and database storage
This script helps verify that projects are being created correctly in the database
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from core.supabase_client import supabase_client
from models.project import ProjectCreate, ProjectResponse

def load_environment():
    """Load environment variables"""
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv()
        print("✅ Environment variables loaded")
    else:
        print("⚠️  No .env file found, using system environment variables")

def test_supabase_connection():
    """Test Supabase connection"""
    try:
        # Test basic connection
        response = supabase_client.table('projects').select('count').limit(1).execute()
        print("✅ Supabase connection successful")
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

def check_database_schema():
    """Check if the projects table has the expected structure"""
    try:
        # Get table information
        response = supabase_client.rpc('get_table_info', {'table_name': 'projects'}).execute()
        print("✅ Database schema check completed")
        
        # Alternative: Check columns directly
        response = supabase_client.table('projects').select('*').limit(0).execute()
        if hasattr(response, 'columns'):
            print(f"📊 Table columns: {response.columns}")
        
        return True
    except Exception as e:
        print(f"⚠️  Schema check failed (this is normal if RPC doesn't exist): {e}")
        return True

def create_test_project():
    """Create a test project to verify the creation process"""
    try:
        # Test project data
        test_project_data = {
            "name": "Test Project - API Debug",
            "description": "This is a test project to verify API functionality",
            "num_blogs": 5,
            "ai_model": "gpt-4",
            "wordpress_account_id": None,
            "api_keys": {
                "openai": "sk-test-key-for-debugging"
            }
        }
        
        print(f"📝 Creating test project: {test_project_data['name']}")
        
        # Insert project directly into database
        response = supabase_client.table("projects").insert({
            "user_id": "00000000-0000-0000-0000-000000000000",  # Test user ID
            "name": test_project_data["name"],
            "description": test_project_data["description"],
            "num_blogs": test_project_data["num_blogs"],
            "completed_blogs": 0,
            "status": "ready",
            "wordpress_account_id": None,
            "api_keys": test_project_data["api_keys"],
            "settings": None,
            "draft_creation_model": test_project_data["ai_model"],
            "content_vetting_model": test_project_data["ai_model"],
            "model_settings": None,
            "workflow_preferences": None
        }).execute()
        
        if response.data:
            created_project = response.data[0]
            print(f"✅ Project created successfully!")
            print(f"   ID: {created_project['id']}")
            print(f"   Status: {created_project['status']}")
            print(f"   Created at: {created_project['created_at']}")
            
            # Verify the project was stored correctly
            verify_project_storage(created_project['id'])
            
            return created_project
        else:
            print("❌ Failed to create project - no data returned")
            return None
            
    except Exception as e:
        print(f"❌ Error creating test project: {e}")
        return None

def verify_project_storage(project_id):
    """Verify that the project was stored correctly in the database"""
    try:
        print(f"🔍 Verifying project storage for ID: {project_id}")
        
        # Fetch the project from database
        response = supabase_client.table("projects").select("*").eq("id", project_id).execute()
        
        if response.data:
            stored_project = response.data[0]
            print(f"✅ Project retrieved from database:")
            print(f"   Name: {stored_project['name']}")
            print(f"   Status: {stored_project['status']}")
            print(f"   Num blogs: {stored_project['num_blogs']}")
            print(f"   Completed blogs: {stored_project['completed_blogs']}")
            print(f"   Draft model: {stored_project['draft_creation_model']}")
            print(f"   Vetting model: {stored_project['content_vetting_model']}")
            print(f"   API keys: {stored_project['api_keys']}")
            
            # Check if all expected fields are present
            expected_fields = [
                'idx', 'id', 'user_id', 'name', 'description', 'num_blogs', 
                'completed_blogs', 'status', 'wordpress_account_id', 'api_keys',
                'settings', 'draft_creation_model', 'content_vetting_model',
                'model_settings', 'workflow_preferences', 'created_at', 'updated_at'
            ]
            
            missing_fields = []
            for field in expected_fields:
                if field not in stored_project:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"⚠️  Missing fields: {missing_fields}")
            else:
                print("✅ All expected fields are present")
                
        else:
            print("❌ Project not found in database")
            
    except Exception as e:
        print(f"❌ Error verifying project storage: {e}")

def list_all_projects():
    """List all projects in the database for debugging"""
    try:
        print("📋 Listing all projects in database:")
        
        response = supabase_client.table("projects").select("*").order("created_at", desc=True).execute()
        
        if response.data:
            for i, project in enumerate(response.data):
                print(f"   {i+1}. {project['name']} (ID: {project['id']})")
                print(f"      Status: {project['status']}, Blogs: {project['num_blogs']}")
                print(f"      Created: {project['created_at']}")
                print()
        else:
            print("   No projects found in database")
            
    except Exception as e:
        print(f"❌ Error listing projects: {e}")

def main():
    """Main test function"""
    print("🧪 Project Creation Test Script")
    print("=" * 50)
    
    # Load environment
    load_environment()
    
    # Test connection
    if not test_supabase_connection():
        print("❌ Cannot proceed without database connection")
        return
    
    # Check schema
    check_database_schema()
    
    # List existing projects
    list_all_projects()
    
    # Create test project
    test_project = create_test_project()
    
    if test_project:
        print("\n🎉 Test completed successfully!")
        print("The project creation is working correctly.")
    else:
        print("\n❌ Test failed!")
        print("There are issues with project creation.")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
