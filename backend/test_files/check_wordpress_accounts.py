#!/usr/bin/env python3
"""
Script to check what wordpress accounts exist in the database
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.supabase_client import supabase_client
from core.config import settings

def check_wordpress_accounts():
    """Check what wordpress accounts exist in the database"""
    print("🔍 Checking wordpress accounts in database...")
    
    if not supabase_client:
        print("❌ Supabase client not initialized")
        return False
    
    try:
        # Check wordpress_accounts table
        response = supabase_client.table("wordpress_accounts").select("*").execute()
        print(f"📊 Found {len(response.data)} wordpress accounts in database")
        
        if response.data:
            print("\n📋 WordPress Accounts found:")
            for i, account in enumerate(response.data):
                print(f"  {i+1}. ID: {account.get('id', 'N/A')}")
                print(f"     User ID: {account.get('user_id', 'N/A')}")
                print(f"     Site URL: {account.get('site_url', 'N/A')}")
                print(f"     Username: {account.get('username', 'N/A')}")
                print(f"     Created: {account.get('created_at', 'N/A')}")
                print()
        else:
            print("   No wordpress accounts found - table might be empty")
        
        return True
    except Exception as e:
        print(f"❌ Error checking wordpress accounts: {e}")
        return False

def main():
    """Main function"""
    print("🚀 WordPress Accounts Check")
    print("=" * 50)
    
    # Check wordpress accounts
    check_wordpress_accounts()
    
    print("\n✅ Check completed!")

if __name__ == "__main__":
    main()
