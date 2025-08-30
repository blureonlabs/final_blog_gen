#!/usr/bin/env python3
"""
Test script for WordPress Media Upload Service
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.wordpress_media_service import WordPressMediaService
from core.supabase_client import supabase_client

async def test_wordpress_media_upload():
    """Test the WordPress Media Upload Service"""
    print("🧪 Testing WordPress Media Upload Service")
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
        
        # Test 4: Test WordPress Media Service
        print("\n4️⃣ Testing WordPress Media Service...")
        async with WordPressMediaService() as wp_service:
            # Test single image upload
            result = await wp_service.upload_image_to_wordpress(
                image_url=image.get('s3_url'),
                wordpress_account=wp_account,
                filename=f"test_image_{image.get('id')[:8]}.jpg",
                alt_text="Test image for WordPress upload"
            )
            
            if result.get('success'):
                print("🎉 WordPress upload successful!")
                print(f"   Media ID: {result.get('wordpress_media_id')}")
                print(f"   Media URL: {result.get('wordpress_media_url')}")
                print(f"   Filename: {result.get('filename')}")
                
                # Update the image record with WordPress data
                print("\n5️⃣ Updating image record with WordPress data...")
                update_response = supabase_client.table('images').update({
                    'wordpress_media_url': result.get('wordpress_media_url'),
                    'wordpress_media_id': result.get('wordpress_media_id'),
                    'status': 'wordpress_uploaded'
                }).eq('id', image.get('id')).execute()
                
                if update_response.data:
                    print("✅ Image record updated successfully")
                else:
                    print("⚠️ Failed to update image record")
                    
            else:
                print("❌ WordPress upload failed")
                print(f"   Error: {result.get('error')}")
                if result.get('details'):
                    print(f"   Details: {result.get('details')}")
        
        print("\n" + "=" * 50)
        print("🎉 WordPress Media Upload Test Completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_wordpress_media_upload())
