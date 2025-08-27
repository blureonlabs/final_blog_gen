#!/usr/bin/env python3
"""
Database Schema Update Script for WordPress Publishing
This script adds the missing columns needed for WordPress publishing functionality.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from core.supabase_client import supabase_client

def update_database_schema():
    """Update the database schema to add missing WordPress publishing columns"""
    
    print("🔄 Updating database schema for WordPress publishing...")
    
    try:
        # Step 1: Add missing fields to blogs table
        print("📝 Adding missing fields to blogs table...")
        
        # Add wordpress_post_id column
        supabase_client.rpc('exec_sql', {
            'sql': 'ALTER TABLE blogs ADD COLUMN IF NOT EXISTS wordpress_post_id VARCHAR(255);'
        }).execute()
        print("✅ Added wordpress_post_id column")
        
        # Add wordpress_url column (if not already exists)
        supabase_client.rpc('exec_sql', {
            'sql': 'ALTER TABLE blogs ADD COLUMN IF NOT EXISTS wordpress_url VARCHAR(500);'
        }).execute()
        print("✅ Added wordpress_url column")
        
        # Add other missing columns
        columns_to_add = [
            ('storage_path', 'VARCHAR(500)'),
            ('storage_bucket', 'VARCHAR(100) DEFAULT \'blog-content\''),
            ('content_size_bytes', 'INTEGER'),
            ('content_hash', 'VARCHAR(64)'),
            ('error_message', 'TEXT'),
            ('generation_logs', 'JSONB'),
            ('seo_score', 'INTEGER DEFAULT 0')
        ]
        
        for column_name, column_type in columns_to_add:
            try:
                supabase_client.rpc('exec_sql', {
                    'sql': f'ALTER TABLE blogs ADD COLUMN IF NOT EXISTS {column_name} {column_type};'
                }).execute()
                print(f"✅ Added {column_name} column")
            except Exception as e:
                print(f"⚠️  Column {column_name} might already exist: {e}")
        
        # Step 2: Update status constraints
        print("🔧 Updating status constraints...")
        try:
            # Drop existing constraint if it exists
            supabase_client.rpc('exec_sql', {
                'sql': 'ALTER TABLE blogs DROP CONSTRAINT IF EXISTS blogs_status_check;'
            }).execute()
            
            # Add new constraint with all required statuses
            supabase_client.rpc('exec_sql', {
                'sql': '''
                ALTER TABLE blogs ADD CONSTRAINT blogs_status_check 
                CHECK (status IN ('draft', 'generating', 'seo_optimizing', 'formatting', 
                                'image_generating', 'ready', 'needs_revision', 'publishing', 
                                'published', 'failed'));
                '''
            }).execute()
            print("✅ Updated status constraints")
        except Exception as e:
            print(f"⚠️  Status constraint update: {e}")
        
        # Step 3: Create indexes
        print("📊 Creating performance indexes...")
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_blogs_wordpress_post_id ON blogs(wordpress_post_id);',
            'CREATE INDEX IF NOT EXISTS idx_blogs_storage_path ON blogs(storage_path);',
            'CREATE INDEX IF NOT EXISTS idx_blogs_content_hash ON blogs(content_hash);',
            'CREATE INDEX IF NOT EXISTS idx_blogs_seo_score ON blogs(seo_score);'
        ]
        
        for index_sql in indexes:
            try:
                supabase_client.rpc('exec_sql', {'sql': index_sql}).execute()
                print("✅ Created index")
            except Exception as e:
                print(f"⚠️  Index creation: {e}")
        
        print("\n🎉 Database schema update completed successfully!")
        print("📋 The following columns are now available:")
        print("   - wordpress_post_id: To store WordPress post ID")
        print("   - wordpress_url: To store WordPress post URL")
        print("   - storage_path: For file storage paths")
        print("   - generation_logs: For tracking publishing steps")
        print("   - seo_score: For SEO optimization tracking")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating database schema: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

def verify_schema():
    """Verify that the required columns exist"""
    print("\n🔍 Verifying database schema...")
    
    try:
        # Check if wordpress_post_id column exists
        response = supabase_client.table("blogs").select("wordpress_post_id").limit(1).execute()
        print("✅ wordpress_post_id column exists")
        
        # Check if wordpress_url column exists
        response = supabase_client.table("blogs").select("wordpress_url").limit(1).execute()
        print("✅ wordpress_url column exists")
        
        # Check if generation_logs column exists
        response = supabase_client.table("blogs").select("generation_logs").limit(1).execute()
        print("✅ generation_logs column exists")
        
        print("✅ All required columns are present!")
        return True
        
    except Exception as e:
        print(f"❌ Schema verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 WordPress Publishing Database Schema Update")
    print("=" * 50)
    
    success = update_database_schema()
    
    if success:
        verify_schema()
        print("\n✨ Your database is now ready for WordPress publishing!")
        print("📝 You can now publish blogs and they will store the WordPress post ID and URL.")
    else:
        print("\n❌ Schema update failed. Please check the error messages above.")
        sys.exit(1)
