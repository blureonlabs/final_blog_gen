#!/usr/bin/env python3
"""
Test script to debug project lookup issue
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.supabase_client import supabase_client
from core.config import settings

def test_specific_project_lookup():
    """Test looking up the specific project that exists"""
    print("🔍 Testing specific project lookup...")
    
    if not supabase_client:
        print("❌ Supabase client not initialized")
        return False
    
    # The project ID from your data
    project_id = "d34471b5-71fc-4daa-aea0-15060b7bf600"
    
    print(f"🔍 Looking for project ID: {project_id}")
    print(f"🔍 Project ID type: {type(project_id)}")
    print(f"🔍 Project ID length: {len(project_id)}")
    
    try:
        # Test 1: Direct lookup
        response = supabase_client.table("projects").select("*").eq("id", project_id).execute()
        print(f"✅ Direct lookup result: {len(response.data)} projects found")
        
        if response.data:
            project = response.data[0]
            print(f"   Found project: {project.get('name')} - {project.get('status')}")
        
        # Test 2: Lookup with str() conversion
        response2 = supabase_client.table("projects").select("*").eq("id", str(project_id)).execute()
        print(f"✅ Str conversion lookup result: {len(response2.data)} projects found")
        
        if response2.data:
            project2 = response2.data[0]
            print(f"   Found project: {project2.get('name')} - {project2.get('status')}")
        
        # Test 3: List all projects to see what's actually there
        print("\n🔍 Listing all projects in database:")
        all_projects = supabase_client.table("projects").select("*").execute()
        print(f"   Total projects found: {len(all_projects.data)}")
        
        for i, proj in enumerate(all_projects.data):
            print(f"   {i+1}. ID: {proj.get('id')}")
            print(f"      Name: {proj.get('name')}")
            print(f"      Status: {proj.get('status')}")
            print(f"      Num Blogs: {proj.get('num_blogs')}")
            print()
        
        return True
    except Exception as e:
        print(f"❌ Project lookup failed: {e}")
        return False

def test_uuid_handling():
    """Test UUID handling in Supabase"""
    print("\n🔍 Testing UUID handling...")
    
    if not supabase_client:
        print("❌ Supabase client not initialized")
        return False
    
    try:
        # Test with different UUID formats
        test_ids = [
            "d34471b5-71fc-4daa-aea0-15060b7bf600",
            "d34471b5-71fc-4daa-aea0-15060b7bf600",
            "d34471b5-71fc-4daa-aea0-15060b7bf600"
        ]
        
        for test_id in test_ids:
            print(f"🔍 Testing ID: {test_id}")
            try:
                response = supabase_client.table("projects").select("id").eq("id", test_id).execute()
                print(f"   Result: {len(response.data)} found")
            except Exception as e:
                print(f"   Error: {e}")
        
        return True
    except Exception as e:
        print(f"❌ UUID handling test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Project Lookup Debug Test")
    print("=" * 50)
    
    # Test 1: Specific project lookup
    test_specific_project_lookup()
    
    # Test 2: UUID handling
    test_uuid_handling()
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    main()
