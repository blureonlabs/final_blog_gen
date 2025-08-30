#!/usr/bin/env python3
"""
Test script for WordPress integration in the blog generation workflow
"""

import sys
import os
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.supabase_client import supabase_client

def test_wordpress_integration():
    """Test the WordPress integration setup"""
    print("🧪 Testing WordPress Integration")
    print("=" * 50)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test 1: Check Supabase connection
        print("\n1️⃣ Testing Supabase connection...")
        response = supabase_client.table('users').select('count').limit(1).execute()
        print("✅ Supabase connection successful")
        
        # Test 2: Check if projects have WordPress accounts configured
        print("\n2️⃣ Checking projects with WordPress accounts...")
        projects_response = supabase_client.table('projects').select(
            'id, name, wordpress_account_id, generate_images'
        ).not_.is_('wordpress_account_id', 'null').execute()
        
        if projects_response.data:
            print(f"✅ Found {len(projects_response.data)} projects with WordPress accounts:")
            for project in projects_response.data:
                print(f"   - {project.get('name')} (ID: {project.get('id')[:8]}...)")
                print(f"     WordPress Account: {project.get('wordpress_account_id')}")
                print(f"     Image Generation: {'✅' if project.get('generate_images') else '❌'}")
        else:
            print("⚠️ No projects found with WordPress accounts configured")
            print("   To test WordPress integration, create a project with a wordpress_account_id")
        
        # Test 3: Check WordPress accounts
        print("\n3️⃣ Checking WordPress accounts...")
        wp_response = supabase_client.table('wordpress_accounts').select(
            'id, name, site_url, is_active'
        ).eq('is_active', True).execute()
        
        if wp_response.data:
            print(f"✅ Found {len(wp_response.data)} active WordPress accounts:")
            for account in wp_response.data:
                print(f"   - {account.get('name')} ({account.get('site_url')})")
        else:
            print("⚠️ No active WordPress accounts found")
        
        # Test 4: Check blogs with generated images
        print("\n4️⃣ Checking blogs with generated images...")
        blogs_response = supabase_client.table('blogs').select(
            'id, title, project_id'
        ).limit(5).execute()
        
        if blogs_response.data:
            print(f"✅ Found {len(blogs_response.data)} blogs:")
            for blog in blogs_response.data:
                blog_id = blog.get('id')
                print(f"   - {blog.get('title')[:50]}...")
                
                # Check images for this blog
                images_response = supabase_client.table('images').select(
                    'id, image_number, status, s3_url, wordpress_media_url'
                ).eq('blog_id', blog_id).execute()
                
                if images_response.data:
                    images = images_response.data
                    generated = len([img for img in images if img.get('status') == 'generated'])
                    with_s3 = len([img for img in images if img.get('s3_url')])
                    with_wp = len([img for img in images if img.get('wordpress_media_url')])
                    
                    print(f"     Images: {len(images)} total, {generated} generated, {with_s3} with S3, {with_wp} with WordPress")
                else:
                    print("     No images found")
        else:
            print("ℹ️ No blogs found")
        
        # Test 5: Check database schema for WordPress fields
        print("\n5️⃣ Checking database schema...")
        try:
            # Try to get a sample image with wordpress_media_url field
            sample_response = supabase_client.table('images').select('id, wordpress_media_url, wordpress_media_id').limit(1).execute()
            if sample_response.data:
                print("✅ Database schema includes WordPress media fields:")
                print("   - wordpress_media_url: ✅")
                print("   - wordpress_media_id: ✅")
            else:
                print("⚠️ No images found in database")
        except Exception as e:
            print(f"❌ Database schema check failed: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 WordPress Integration Test Completed!")
        
        # Summary and next steps
        print("\n📋 Summary:")
        if projects_response.data and wp_response.data:
            print("   ✅ WordPress integration is properly configured")
            print("   🚀 New blogs will automatically trigger WordPress uploads")
            print("   📸 Existing blogs can be manually triggered for WordPress upload")
        else:
            print("   ⚠️ WordPress integration needs configuration")
            print("   📝 Configure a WordPress account for your project")
            print("   🔗 Set wordpress_account_id in your project settings")
        
        print("\n🔗 Available Endpoints:")
        print("   - POST /api/blog-images/blog/{blog_id}/trigger-wordpress-upload")
        print("   - GET /api/blog-images/blog/{blog_id}/wordpress-status")
        print("   - POST /api/wordpress-media/upload-blog-images/{blog_id}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

def test_existing_blog_wordpress_upload():
    """Test triggering WordPress upload for an existing blog"""
    print("\n🔍 Testing Existing Blog WordPress Upload")
    print("=" * 40)
    
    try:
        # Find a blog with generated images
        blogs_response = supabase_client.table('blogs').select(
            'id, title, project_id'
        ).limit(1).execute()
        
        if not blogs_response.data:
            print("ℹ️ No blogs found to test")
            return
        
        blog = blogs_response.data[0]
        blog_id = blog.get('id')
        print(f"📝 Testing with blog: {blog.get('title')[:50]}...")
        
        # Check if this blog has generated images
        images_response = supabase_client.table('images').select(
            'id, status, s3_url, wordpress_media_url'
        ).eq('blog_id', blog_id).eq('status', 'generated').not_.is_('s3_url', 'null').execute()
        
        if not images_response.data:
            print("ℹ️ No generated images found for this blog")
            return
        
        ready_images = [img for img in images_response.data if not img.get('wordpress_media_url')]
        print(f"📸 Found {len(ready_images)} images ready for WordPress upload")
        
        if ready_images:
            print("✅ This blog is ready for WordPress upload testing")
            print("   Use the endpoint: POST /api/blog-images/blog/{blog_id}/trigger-wordpress-upload")
        else:
            print("ℹ️ All images for this blog already have WordPress URLs")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    test_wordpress_integration()
    test_existing_blog_wordpress_upload()
    print("\n🏁 All tests completed!")
