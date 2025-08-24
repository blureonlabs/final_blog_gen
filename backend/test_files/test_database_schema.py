#!/usr/bin/env python3
"""
Test script to check database schema and table structure
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.supabase_client import supabase_client
from core.config import settings

def test_table_structure():
    """Test the structure of the projects table"""
    print("🔍 Testing table structure...")
    
    if not supabase_client:
        print("❌ Supabase client not initialized")
        return False
    
    try:
        # Test 1: Try to get a single row to see the structure
        print("🔍 Testing table structure by selecting one row...")
        response = supabase_client.table("projects").select("*").limit(1).execute()
        print(f"   Result: {len(response.data)} rows returned")
        
        if response.data:
            project = response.data[0]
            print(f"   Project data: {project}")
            print(f"   Keys in project: {list(project.keys())}")
        else:
            print("   No data returned - table might be empty")
        
        # Test 2: Try to insert a test record to see if table exists
        print("\n🔍 Testing table write access...")
        try:
            test_project = {
                "name": "TEST_PROJECT",
                "description": "Test project for debugging",
                "num_blogs": 1,
                "status": "ready",
                "user_id": "test-user-id"
            }
            
            # Try to insert (this will fail if table doesn't exist or has wrong structure)
            insert_response = supabase_client.table("projects").insert(test_project).execute()
            print(f"   Insert test: {len(insert_response.data)} rows inserted")
            
            # Clean up - delete the test record
            if insert_response.data:
                test_id = insert_response.data[0].get('id')
                delete_response = supabase_client.table("projects").delete().eq("id", test_id).execute()
                print(f"   Cleanup: Test record deleted")
                
        except Exception as e:
            print(f"   Insert test failed: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Table structure test failed: {e}")
        return False

def test_different_table_names():
    """Test if the table might have a different name"""
    print("\n🔍 Testing different possible table names...")
    
    if not supabase_client:
        print("❌ Supabase client not initialized")
        return False
    
    possible_names = [
        'project',
        'Project',
        'PROJECTS',
        'Projects',
        'blog_projects',
        'content_projects'
    ]
    
    for table_name in possible_names:
        try:
            response = supabase_client.table(table_name).select("count").limit(1).execute()
            print(f"   Table '{table_name}': {response.data[0]['count'] if response.data else 'N/A'} rows")
        except Exception as e:
            print(f"   Table '{table_name}': Does not exist")
    
    return True

def test_raw_sql_access():
    """Test if we can access the database with raw SQL"""
    print("\n🔍 Testing raw SQL access...")
    
    if not supabase_client:
        print("❌ Supabase client not initialized")
        return False
    
    try:
        # Try to use RPC to get table info
        response = supabase_client.rpc('get_table_info', {'table_name': 'projects'}).execute()
        print(f"   RPC result: {response.data}")
        return True
    except Exception as e:
        print(f"   RPC failed: {e}")
        
        # Try alternative approach
        try:
            # Try to get column information
            response = supabase_client.table("projects").select("*").limit(0).execute()
            print(f"   Column test: Success (table exists)")
            return True
        except Exception as e2:
            print(f"   Column test failed: {e2}")
            return False

def main():
    """Main test function"""
    print("🚀 Database Schema Debug Test")
    print("=" * 50)
    
    # Test 1: Table structure
    test_table_structure()
    
    # Test 2: Different table names
    test_different_table_names()
    
    # Test 3: Raw SQL access
    test_raw_sql_access()
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    main()
