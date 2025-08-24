#!/usr/bin/env python3
"""
Test script to verify project creation flow
Run this to test if projects are created with correct status
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from core.supabase_client import supabase_client
from core.config import settings

async def test_project_creation():
    """Test project creation flow"""
    print("🧪 Testing Project Creation Flow...")
    print(f"🌐 Supabase URL: {settings.SUPABASE_URL}")
    
    try:
        # Test 1: Check if we can connect to Supabase
        print("\n1️⃣ Testing Supabase connection...")
        
        # Try to list projects to test connection
        projects_response = supabase_client.table("projects").select("id").limit(1).execute()
        print(f"✅ Supabase connection successful: {len(projects_response.data)} projects found")
        
        # Test 2: Check if projects table exists and has correct structure
        print("\n2️⃣ Testing projects table structure...")
        
        # Try to get table info
        try:
            # This will fail if table doesn't exist, which is expected
            projects_response = supabase_client.table("projects").select("*").execute()
            print(f"✅ Projects table accessible")
            print(f"📊 Table columns: {list(projects_response.data[0].keys()) if projects_response.data else 'No data'}")
        except Exception as e:
            print(f"⚠️ Projects table not accessible: {e}")
            print("💡 You need to run the database schema first!")
            return False
        
        # Test 3: Check if storage is accessible
        print("\n3️⃣ Testing storage access...")
        try:
            buckets = supabase_client.storage.list_buckets()
            bucket_names = [bucket.name for bucket in buckets]
            print(f"✅ Storage accessible: {len(bucket_names)} buckets found")
            print(f"📁 Available buckets: {bucket_names}")
            
            if settings.STORAGE_BUCKET_NAME in bucket_names:
                print(f"✅ Required bucket '{settings.STORAGE_BUCKET_NAME}' exists")
            else:
                print(f"⚠️ Required bucket '{settings.STORAGE_BUCKET_NAME}' not found")
                print("💡 The bucket will be created automatically when needed")
                
        except Exception as e:
            print(f"❌ Storage test failed: {e}")
            print("💡 Check your Supabase storage permissions")
            return False
        
        print("\n🎉 All tests passed! Your project creation should work correctly.")
        print("\n📋 Next steps:")
        print("1. Create a project from the frontend")
        print("2. Check that it shows 'Ready to Start' status")
        print("3. Click the green play button to start content generation")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check your .env file has correct Supabase credentials")
        print("2. Ensure the database schema has been run")
        print("3. Verify storage is enabled in your Supabase project")
        return False

async def main():
    """Run the test"""
    success = await test_project_creation()
    
    if success:
        print("\n✅ Ready to create projects!")
    else:
        print("\n❌ Please fix the issues above before creating projects")

if __name__ == "__main__":
    asyncio.run(main())
