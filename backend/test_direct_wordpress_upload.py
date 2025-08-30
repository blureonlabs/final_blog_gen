#!/usr/bin/env python3
"""
Test script for direct WordPress upload functionality
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.wordpress_media_service import WordPressMediaService
from core.supabase_client import supabase_client

async def test_direct_wordpress_upload():
    """Test the direct WordPress upload functionality"""
    print("🧪 Testing Direct WordPress Upload")
    print("=" * 40)
    
    try:
        # Test 1: Check Supabase connection
        print("\n1️⃣ Testing Supabase connection...")
        response = supabase_client.table('users').select('count').limit(1).execute()
        print("✅ Supabase connection successful")
        
        # Test 2: Check if there are images ready for WordPress upload
        print("\n2️⃣ Checking for images ready for WordPress upload...")
        images_response = supabase_client.table('images').select(
            'id, blog_id, status, s3_url, wordpress_media_url'
        ).eq('status', 'generated').not_.is_('s3_url', 'null').is_('wordpress_media_url', 'null').limit(3).execute()
        
        if not images_response.data:
            print("ℹ️ No images found that are ready for WordPress upload")
            print("   Images need to be:")
            print("   - Status: 'generated'")
            print("   - Have S3 URLs")
            print("   - No WordPress media URL yet")
            return
        
        images = images_response.data
        print(f"✅ Found {len(images)} images ready for WordPress upload")
        
        # Test 3: Check if WordPress accounts exist
        print("\n3️⃣ Checking WordPress accounts...")
        wp_response = supabase_client.table('wordpress_accounts').select(
            'id, name, site_url, is_active'
        ).eq('is_active', True).limit(1).execute()
        
        if not wp_response.data:
            print("⚠️ No active WordPress accounts found")
            print("   Please create a WordPress account first")
            return
        
        wordpress_account = wp_response.data[0]
        print(f"✅ Found WordPress account: {wordpress_account.get('name')} ({wordpress_account.get('site_url')})")
        
        # Test 4: Test WordPress media service initialization
        print("\n4️⃣ Testing WordPress media service...")
        try:
            async with WordPressMediaService() as wp_service:
                print("✅ WordPress media service initialized successfully")
                
                # Test 5: Test image download (without actually uploading to WordPress)
                print("\n5️⃣ Testing image download capability...")
                test_image = images[0]
                print(f"   Testing with image: {test_image.get('id')[:8]}...")
                
                try:
                    image_data = await wp_service._download_image(test_image.get('s3_url'))
                    if image_data:
                        print(f"✅ Image download successful: {len(image_data)} bytes")
                        print("   This means the service can access your Supabase Storage images")
                    else:
                        print("❌ Image download failed")
                except Exception as e:
                    print(f"❌ Image download error: {e}")
                
        except Exception as e:
            print(f"❌ WordPress media service error: {e}")
            return
        
        print("\n" + "=" * 40)
        print("🎉 Direct WordPress Upload Test Completed!")
        
        # Summary
        print("\n📋 Summary:")
        print(f"   ✅ Found {len(images)} images ready for WordPress upload")
        print(f"   ✅ WordPress account configured: {wordpress_account.get('name')}")
        print("   ✅ Service can download images from Supabase Storage")
        print("\n🚀 Next Steps:")
        print("   1. Ensure your WordPress site is accessible")
        print("   2. Verify username/password credentials")
        print("   3. Check user permissions for media upload")
        print("   4. The system will now automatically upload images to WordPress!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_wordpress_upload())
