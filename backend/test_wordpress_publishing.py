#!/usr/bin/env python3
"""
Test script for WordPress publishing service
This script tests the fixed WordPress publishing functionality
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tasks.wordpress_publishing import (
    get_blog_data, 
    prepare_wordpress_post, 
    get_wordpress_account,
    update_blog_status
)
from models.blog import BlogStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_wordpress_publishing():
    """Test the WordPress publishing functionality"""
    
    print("🧪 Testing WordPress Publishing Service")
    print("=" * 50)
    
    # Test 1: Get blog data
    print("\n1️⃣ Testing blog data retrieval...")
    test_blog_id = "test-blog-id"  # Replace with actual blog ID for testing
    
    try:
        blog_data = get_blog_data(test_blog_id)
        if blog_data:
            print(f"✅ Blog data retrieved successfully")
            print(f"   Title: {blog_data.get('title', 'N/A')}")
            print(f"   Content length: {len(blog_data.get('content', ''))} characters")
            print(f"   Storage bucket: {blog_data.get('storage_bucket', 'N/A')}")
            print(f"   Storage path: {blog_data.get('storage_path', 'N/A')}")
        else:
            print(f"❌ Blog data retrieval failed (expected for test ID)")
    except Exception as e:
        print(f"❌ Error testing blog data retrieval: {e}")
    
    # Test 2: Test WordPress post preparation with mock data
    print("\n2️⃣ Testing WordPress post preparation...")
    
    mock_blog_data = {
        "title": "Test Blog Post",
        "content": "This is a test blog post content for testing WordPress publishing.",
        "seo_meta": {
            "meta_description": "A test blog post for testing purposes",
            "tags": ["test", "wordpress", "publishing"],
            "main_keyword": "test publishing"
        }
    }
    
    try:
        post_data = prepare_wordpress_post(mock_blog_data, "draft")
        if post_data:
            print(f"✅ WordPress post data prepared successfully")
            print(f"   Title: {post_data.get('title')}")
            print(f"   Content length: {len(post_data.get('content', ''))} characters")
            print(f"   Status: {post_data.get('status')}")
            print(f"   Excerpt: {post_data.get('excerpt', 'N/A')}")
            print(f"   Tags: {post_data.get('tags', 'N/A')}")
            print(f"   Featured media: {post_data.get('featured_media', 'N/A')}")
        else:
            print(f"❌ WordPress post data preparation failed")
    except Exception as e:
        print(f"❌ Error testing WordPress post preparation: {e}")
    
    # Test 3: Test without SEO metadata
    print("\n3️⃣ Testing WordPress post preparation without SEO metadata...")
    
    minimal_blog_data = {
        "title": "Minimal Blog Post",
        "content": "This is a minimal blog post without SEO metadata."
    }
    
    try:
        post_data = prepare_wordpress_post(minimal_blog_data, "draft")
        if post_data:
            print(f"✅ Minimal WordPress post data prepared successfully")
            print(f"   Title: {post_data.get('title')}")
            print(f"   Content length: {len(post_data.get('content', ''))} characters")
            print(f"   Status: {post_data.get('status')}")
            print(f"   Has excerpt: {bool(post_data.get('excerpt'))}")
            print(f"   Has tags: {bool(post_data.get('tags'))}")
            print(f"   Has featured media: {bool(post_data.get('featured_media'))}")
        else:
            print(f"❌ Minimal WordPress post data preparation failed")
    except Exception as e:
        print(f"❌ Error testing minimal WordPress post preparation: {e}")
    
    # Test 4: Test error handling
    print("\n4️⃣ Testing error handling...")
    
    invalid_blog_data = {
        "title": "",  # Empty title
        "content": ""  # Empty content
    }
    
    try:
        post_data = prepare_wordpress_post(invalid_blog_data, "draft")
        if post_data:
            print(f"⚠️ Unexpected success with invalid data")
        else:
            print(f"✅ Error handling working correctly - invalid data rejected")
    except Exception as e:
        print(f"✅ Error handling working correctly - exception raised: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 WordPress Publishing Service Test Complete!")
    print("\nNext steps:")
    print("1. Test with actual blog IDs from your database")
    print("2. Test with actual WordPress account credentials")
    print("3. Verify S3 content retrieval works correctly")
    print("4. Test the full publishing workflow")

if __name__ == "__main__":
    asyncio.run(test_wordpress_publishing())
