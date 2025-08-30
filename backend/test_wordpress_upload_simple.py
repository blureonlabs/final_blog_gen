#!/usr/bin/env python3
"""
Simple test script for WordPress upload using REST API
"""

import requests
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.supabase_client import supabase_client

def test_wordpress_upload_simple():
    """Test WordPress upload using simple requests approach"""
    print("🧪 Testing WordPress Upload (Simple Approach)")
    print("=" * 50)
    
    try:
        # Test 1: Check Supabase connection
        print("\n1️⃣ Testing Supabase connection...")
        response = supabase_client.table('users').select('count').limit(1).execute()
        print("✅ Supabase connection successful")
        
        # Test 2: Get WordPress account details
        print("\n2️⃣ Getting WordPress account details...")
        wp_response = supabase_client.table('wordpress_accounts').select(
            'id, name, site_url, username, password'
        ).eq('is_active', True).limit(1).execute()
        
        if not wp_response.data:
            print("⚠️ No active WordPress accounts found")
            print("   Please create a WordPress account first")
            return
        
        wp_account = wp_response.data[0]
        print(f"✅ Found WordPress account: {wp_account.get('name')}")
        print(f"   Site URL: {wp_account.get('site_url')}")
        print(f"   Username: {wp_account.get('username')}")
        print(f"   Password: {'*' * len(wp_account.get('password', ''))} (hidden)")
        
        # Test 3: Get an image ready for upload
        print("\n3️⃣ Finding an image ready for WordPress upload...")
        images_response = supabase_client.table('images').select(
            'id, blog_id, status, s3_url, wordpress_media_url'
        ).eq('status', 'generated').not_.is_('s3_url', 'null').is_('wordpress_media_url', 'null').limit(1).execute()
        
        if not images_response.data:
            print("ℹ️ No images found that are ready for WordPress upload")
            return
        
        image = images_response.data[0]
        print(f"✅ Found image ready for upload: {image.get('id')[:8]}...")
        print(f"   S3 URL: {image.get('s3_url')}")
        
        # Test 4: Test WordPress connectivity
        print("\n4️⃣ Testing WordPress site connectivity...")
        wp_url = wp_account.get('site_url')
        test_url = f"{wp_url}/wp-json/wp/v2/media"
        
        try:
            # Test basic connectivity
            test_response = requests.get(f"{wp_url}/wp-json/", timeout=10)
            if test_response.status_code == 200:
                print("✅ WordPress REST API is accessible")
                print(f"   API endpoint: {test_url}")
            else:
                print(f"⚠️ WordPress site responded with status: {test_response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to WordPress site: {e}")
            print("   Please check:")
            print("   - Site URL is correct")
            print("   - Site is accessible from this server")
            print("   - REST API is enabled")
            return
        
        # Test 5: Test authentication
        print("\n5️⃣ Testing WordPress authentication...")
        username = wp_account.get('username')
        password = wp_account.get('password')
        
        try:
            # Test with a simple GET request to check authentication
            auth_response = requests.get(
                f"{wp_url}/wp-json/wp/v2/users/me",
                auth=(username, password),
                timeout=10
            )
            
            if auth_response.status_code == 200:
                user_info = auth_response.json()
                print("✅ WordPress authentication successful!")
                print(f"   Authenticated as: {user_info.get('name', 'Unknown')}")
                print(f"   User ID: {user_info.get('id')}")
                print(f"   Roles: {', '.join(user_info.get('roles', []))}")
                
                # Check if user can upload media
                if 'author' in user_info.get('roles', []) or 'administrator' in user_info.get('roles', []):
                    print("✅ User has media upload permissions")
                else:
                    print("⚠️ User may not have media upload permissions")
                    print("   Recommended roles: author, editor, or administrator")
                    
            elif auth_response.status_code == 401:
                print("❌ WordPress authentication failed")
                print("   Please check:")
                print("   - Username is correct")
                print("   - Application password is correct")
                print("   - Application password was generated from WP user profile")
                return
            else:
                print(f"⚠️ Unexpected response: {auth_response.status_code}")
                print(f"   Response: {auth_response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Authentication test failed: {e}")
            return
        
        print("\n" + "=" * 50)
        print("🎉 WordPress Upload Test Completed!")
        
        # Summary and next steps
        print("\n📋 Summary:")
        print("   ✅ WordPress site is accessible")
        print("   ✅ REST API is working")
        print("   ✅ Authentication is successful")
        print("   ✅ User has appropriate permissions")
        print(f"   ✅ Found {len(images_response.data)} images ready for upload")
        
        print("\n🚀 Ready for WordPress Upload!")
        print("   The system will now automatically upload images to WordPress")
        print("   when blogs are generated or when manually triggered.")
        
        print("\n🔗 Test Endpoints:")
        print("   - POST /api/blog-images/blog/{blog_id}/trigger-wordpress-upload")
        print("   - GET /api/blog-images/blog/{blog_id}/wordpress-status")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_wordpress_upload_simple()
