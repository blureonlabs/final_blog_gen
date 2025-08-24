#!/usr/bin/env python3
"""
Test script to verify Supabase Storage setup
Run this after setting up your .env file
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from core.supabase_client import supabase_client
from core.config import settings

async def test_storage_setup():
    """Test if storage bucket exists and can be accessed"""
    print("🧪 Testing Supabase Storage Setup...")
    print(f"📁 Bucket name: {settings.STORAGE_BUCKET_NAME}")
    print(f"🌐 Supabase URL: {settings.SUPABASE_URL}")
    
    try:
        # Test 1: List buckets
        print("\n1️⃣ Testing bucket listing...")
        buckets = supabase_client.storage.list_buckets()
        bucket_names = [bucket.name for bucket in buckets]
        print(f"✅ Found {len(bucket_names)} buckets: {bucket_names}")
        
        # Test 2: Check if our bucket exists
        if settings.STORAGE_BUCKET_NAME in bucket_names:
            print(f"✅ Bucket '{settings.STORAGE_BUCKET_NAME}' exists!")
        else:
            print(f"❌ Bucket '{settings.STORAGE_BUCKET_NAME}' not found!")
            print("Creating bucket...")
            
            # Create bucket
            result = supabase_client.storage.create_bucket(
                name=settings.STORAGE_BUCKET_NAME,
                public=True,
                file_size_limit=52428800,  # 50MB
                allowed_mime_types=["application/json", "text/plain", "text/markdown"]
            )
            print(f"✅ Bucket created: {result}")
        
        # Test 3: Test file upload
        print("\n2️⃣ Testing file upload...")
        test_content = "Hello from Supabase Storage! 🚀"
        test_file_path = "test/hello.txt"
        
        upload_result = supabase_client.storage.from_(settings.STORAGE_BUCKET_NAME).upload(
            path=test_file_path,
            file=test_content.encode('utf-8'),
            file_options={"content-type": "text/plain"}
        )
        print(f"✅ File uploaded: {upload_result}")
        
        # Test 4: Test file download
        print("\n3️⃣ Testing file download...")
        download_result = supabase_client.storage.from_(settings.STORAGE_BUCKET_NAME).download(test_file_path)
        downloaded_content = download_result.decode('utf-8')
        print(f"✅ File downloaded: {downloaded_content}")
        
        # Test 5: Test file listing
        print("\n4️⃣ Testing file listing...")
        files = supabase_client.storage.from_(settings.STORAGE_BUCKET_NAME).list()
        print(f"✅ Files in bucket: {[f.name for f in files]}")
        
        # Test 6: Clean up test file
        print("\n5️⃣ Cleaning up test file...")
        delete_result = supabase_client.storage.from_(settings.STORAGE_BUCKET_NAME).remove([test_file_path])
        print(f"✅ Test file removed: {delete_result}")
        
        print("\n🎉 All storage tests passed! Your Supabase Storage is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Storage test failed: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check your .env file has correct Supabase credentials")
        print("2. Ensure Storage is enabled in your Supabase project")
        print("3. Verify your service role key has storage permissions")
        print("4. Check if your project has storage quota available")
        return False
    
    return True

async def test_blog_generation_service():
    """Test the blog generation service with storage"""
    print("\n🧪 Testing Blog Generation Service...")
    
    try:
        from services.blog_generation_service import blog_generation_service
        
        # Test storage bucket creation
        await blog_generation_service._ensure_bucket_exists(settings.STORAGE_BUCKET_NAME)
        print("✅ Blog generation service storage test passed!")
        
    except Exception as e:
        print(f"❌ Blog generation service test failed: {e}")
        return False
    
    return True

async def main():
    """Run all tests"""
    print("🚀 Starting Supabase Storage Tests...\n")
    
    # Test 1: Basic storage setup
    storage_ok = await test_storage_setup()
    
    if storage_ok:
        # Test 2: Blog generation service
        service_ok = await test_blog_generation_service()
        
        if service_ok:
            print("\n🎉 All tests passed! You're ready to generate blogs with storage.")
        else:
            print("\n⚠️  Storage works but blog service has issues.")
    else:
        print("\n❌ Storage setup failed. Please fix the issues above.")

if __name__ == "__main__":
    asyncio.run(main())
