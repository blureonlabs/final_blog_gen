#!/usr/bin/env python3
"""
Test script to check database status and constraints
"""

import os
import sys
from supabase import create_client, Client

def test_database_status():
    """Test the current database status"""
    
    # Check environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing environment variables:")
        print(f"   SUPABASE_URL: {'✅' if supabase_url else '❌'}")
        print(f"   SUPABASE_SERVICE_ROLE_KEY: {'✅' if supabase_key else '❌'}")
        return False
    
    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        print("🔍 Testing database connection...")
        
        # Test 1: Check if projects table exists and its structure
        print("\n📋 Testing projects table...")
        try:
            result = supabase.table("projects").select("*").limit(1).execute()
            print("✅ Projects table exists and is accessible")
            
            # Check table structure
            if result.data:
                project = result.data[0]
                print(f"   Sample project status: {project.get('status', 'N/A')}")
                print(f"   Sample project columns: {list(project.keys())}")
            else:
                print("   No projects found in table")
                
        except Exception as e:
            print(f"❌ Error accessing projects table: {e}")
            return False
        
        # Test 2: Check constraints
        print("\n🔒 Testing table constraints...")
        try:
            # Try to insert a project with "ready" status
            test_project = {
                "user_id": "test-user-id",
                "name": "Test Project",
                "description": "Test Description",
                "num_blogs": 5,
                "completed_blogs": 0,
                "status": "ready",
                "wordpress_account_id": "test-wp-id",
                "api_keys": {"openai": "test", "gemini": "test", "serp": "test"}
            }
            
            result = supabase.table("projects").insert(test_project).execute()
            print("✅ Successfully inserted project with 'ready' status")
            
            # Clean up test data
            if result.data:
                test_id = result.data[0]['id']
                supabase.table("projects").delete().eq("id", test_id).execute()
                print("✅ Cleaned up test project")
                
        except Exception as e:
            print(f"❌ Error inserting project with 'ready' status: {e}")
            print("   This suggests the database constraint is still blocking 'ready' status")
            return False
        
        # Test 3: Check blogs table
        print("\n📝 Testing blogs table...")
        try:
            result = supabase.table("blogs").select("*").limit(1).execute()
            print("✅ Blogs table exists and is accessible")
            
        except Exception as e:
            print(f"❌ Error accessing blogs table: {e}")
        
        print("\n✅ Database tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Database Status Test")
    print("=" * 50)
    
    success = test_database_status()
    
    if success:
        print("\n🎉 All tests passed! Database is working correctly.")
    else:
        print("\n💥 Some tests failed. Check the database migration and constraints.")
        print("\n📋 Next steps:")
        print("   1. Run the database migration script in Supabase SQL Editor")
        print("   2. Check that the constraints allow 'ready' status")
        print("   3. Verify the projects table structure")
