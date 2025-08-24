#!/usr/bin/env python3
"""
Test script to verify Supabase connection and project lookup
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.supabase_client import supabase_client
from core.config import settings

def test_supabase_connection():
    """Test basic Supabase connection"""
    print("🔍 Testing Supabase connection...")
    print(f"📊 Supabase URL: {settings.SUPABASE_URL}")
    print(f"🔑 Supabase Anon Key: {settings.SUPABASE_ANON_KEY[:20]}...")
    
    if not supabase_client:
        print("❌ Supabase client not initialized")
        return False
    
    try:
        # Test basic connection
        response = supabase_client.table('users').select('count').limit(1).execute()
        print("✅ Basic connection successful")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_project_lookup():
    """Test project lookup in the database"""
    print("\n🔍 Testing project lookup...")
    
    if not supabase_client:
        print("❌ Supabase client not initialized")
        return False
    
    try:
        # List all projects
        response = supabase_client.table('projects').select('*').execute()
        print(f"📊 Found {len(response.data)} projects in database")
        
        if response.data:
            print("\n📋 Projects found:")
            for i, project in enumerate(response.data):
                print(f"  {i+1}. ID: {project.get('id', 'N/A')}")
                print(f"     Name: {project.get('name', 'N/A')}")
                print(f"     Status: {project.get('status', 'N/A')}")
                print(f"     Num Blogs: {project.get('num_blogs', 'N/A')}")
                print()
        
        return True
    except Exception as e:
        print(f"❌ Project lookup failed: {e}")
        return False

def test_specific_project(project_id):
    """Test looking up a specific project by ID"""
    print(f"\n🔍 Testing lookup for project ID: {project_id}")
    
    if not supabase_client:
        print("❌ Supabase client not initialized")
        return False
    
    try:
        response = supabase_client.table('projects').select('*').eq('id', project_id).execute()
        
        if response.data:
            project = response.data[0]
            print(f"✅ Project found:")
            print(f"   ID: {project.get('id')}")
            print(f"   Name: {project.get('name')}")
            print(f"   Status: {project.get('status')}")
            print(f"   Num Blogs: {project.get('num_blogs')}")
            print(f"   API Keys: {project.get('api_keys')}")
        else:
            print(f"❌ No project found with ID: {project_id}")
        
        return len(response.data) > 0
    except Exception as e:
        print(f"❌ Specific project lookup failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Supabase Connection Test")
    print("=" * 50)
    
    # Test 1: Basic connection
    if not test_supabase_connection():
        print("\n❌ Cannot proceed without basic connection")
        return
    
    # Test 2: Project listing
    if not test_project_lookup():
        print("\n❌ Cannot list projects")
        return
    
    # Test 3: Specific project (use the ID from your data)
    project_id = "442f3722-3427-4a2f-8a85-04d38ebf27d1"  # From your data
    test_specific_project(project_id)
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    main()
