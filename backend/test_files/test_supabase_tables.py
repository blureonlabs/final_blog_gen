#!/usr/bin/env python3
"""
Test script to check what tables exist in Supabase
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.supabase_client import supabase_client
from core.config import settings

def test_table_existence():
    """Test what tables exist in the database"""
    print("🔍 Testing table existence...")
    print(f"📊 Supabase URL: {settings.SUPABASE_URL}")
    
    if not supabase_client:
        print("❌ Supabase client not initialized")
        return False
    
    try:
        # Try to access different possible table names
        tables_to_test = [
            'projects',
            'blogs', 
            'users',
            'api_keys',
            'wordpress_accounts',
            'logs'
        ]
        
        for table_name in tables_to_test:
            try:
                response = supabase_client.table(table_name).select('count').limit(1).execute()
                print(f"✅ Table '{table_name}' exists - Count: {response.data[0]['count'] if response.data else 'N/A'}")
            except Exception as e:
                print(f"❌ Table '{table_name}' does not exist or error: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Table existence test failed: {e}")
        return False

def test_schema_info():
    """Try to get schema information"""
    print("\n🔍 Testing schema information...")
    
    if not supabase_client:
        print("❌ Supabase client not initialized")
        return False
    
    try:
        # Try to get information about the public schema
        response = supabase_client.rpc('get_schema_info').execute()
        print(f"✅ Schema info: {response.data}")
        return True
    except Exception as e:
        print(f"❌ Schema info failed: {e}")
        return False

def test_direct_sql():
    """Try to run a simple SQL query to see what's available"""
    print("\n🔍 Testing direct SQL access...")
    
    if not supabase_client:
        print("❌ Supabase client not initialized")
        return False
    
    try:
        # Try to get table names using information_schema
        response = supabase_client.rpc('get_table_names').execute()
        print(f"✅ Table names: {response.data}")
        return True
    except Exception as e:
        print(f"❌ Direct SQL failed: {e}")
        
        # Try alternative approach
        try:
            # Try to access a system table
            response = supabase_client.table('information_schema.tables').select('table_name').eq('table_schema', 'public').execute()
            print(f"✅ System tables accessible: {len(response.data)} tables found")
            for table in response.data[:10]:  # Show first 10
                print(f"   - {table.get('table_name')}")
        except Exception as e2:
            print(f"❌ System table access also failed: {e2}")
    
    return False

def main():
    """Main test function"""
    print("🚀 Supabase Table Existence Test")
    print("=" * 50)
    
    # Test 1: Check specific tables
    test_table_existence()
    
    # Test 2: Try to get schema info
    test_schema_info()
    
    # Test 3: Try direct SQL access
    test_direct_sql()
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    main()
