#!/usr/bin/env python3
"""
Script to check what users exist in the database
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.supabase_client import supabase_client
from core.config import settings

def check_users():
    """Check what users exist in the database"""
    print("🔍 Checking users in database...")
    
    if not supabase_client:
        print("❌ Supabase client not initialized")
        return False
    
    try:
        # Check users table
        response = supabase_client.table("users").select("*").execute()
        print(f"📊 Found {len(response.data)} users in database")
        
        if response.data:
            print("\n📋 Users found:")
            for i, user in enumerate(response.data):
                print(f"  {i+1}. ID: {user.get('id', 'N/A')}")
                print(f"     Email: {user.get('email', 'N/A')}")
                print(f"     Name: {user.get('full_name', 'N/A')}")
                print(f"     Created: {user.get('created_at', 'N/A')}")
                print()
        else:
            print("   No users found - table might be empty")
        
        return True
    except Exception as e:
        print(f"❌ Error checking users: {e}")
        return False

def check_api_keys():
    """Check what API keys exist in the database"""
    print("\n🔍 Checking API keys in database...")
    
    if not supabase_client:
        print("❌ Supabase client not initialized")
        return False
    
    try:
        # Check api_keys table
        response = supabase_client.table("api_keys").select("*").execute()
        print(f"📊 Found {len(response.data)} API key records in database")
        
        if response.data:
            print("\n📋 API Keys found:")
            for i, key in enumerate(response.data):
                print(f"  {i+1}. ID: {key.get('id', 'N/A')}")
                print(f"     User ID: {key.get('user_id', 'N/A')}")
                print(f"     Type: {key.get('key_type', 'N/A')}")
                print(f"     Created: {key.get('created_at', 'N/A')}")
                print()
        
        return True
    except Exception as e:
        print(f"❌ Error checking API keys: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Database Users Check")
    print("=" * 50)
    
    # Check users
    check_users()
    
    # Check API keys
    check_api_keys()
    
    print("\n✅ Check completed!")

if __name__ == "__main__":
    main()
