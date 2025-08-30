#!/usr/bin/env python3
"""
Test script for SerpAPI integration
This script tests the SerpAPI research endpoint to ensure it's working correctly.
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
SERPAPI_RESEARCH_ENDPOINT = f"{BASE_URL}/api/content-generation/research-topic"

def test_serpapi_research_endpoint():
    """Test the SerpAPI research endpoint"""
    print("🧪 Testing SerpAPI Research Endpoint")
    print("=" * 50)
    
    # Test data - using your real SerpAPI key and proper UUID format
    project_id = "550e8400-e29b-41d4-a716-446655440000"  # Valid UUID format
    topic = "how sofa's grew"
    api_key = "f11475cee488362fe8791331e507a99af25ef721e2f08ada96d0af406d93fd89"
    num_results = 5
    
    try:
        print(f"📡 Making request to: {SERPAPI_RESEARCH_ENDPOINT}")
        print(f"📝 Test data:")
        print(f"  - Project ID: {project_id}")
        print(f"  - Topic: {topic}")
        print(f"  - API Key: {api_key[:10]}...{api_key[-10:]}")
        print(f"  - Num Results: {num_results}")
        
        # Make the request with query parameters
        params = {
            "project_id": project_id,
            "topic": topic,
            "api_key": api_key,
            "num_results": num_results
        }
        
        response = requests.post(
            SERPAPI_RESEARCH_ENDPOINT,
            params=params,  # Use params instead of json
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Request successful!")
            try:
                response_data = response.json()
                print(f"📄 Response Data: {json.dumps(response_data, indent=2)}")
                
                # Validate response structure
                if "success" in response_data:
                    print(f"✅ Success field present: {response_data['success']}")
                else:
                    print("⚠️ Missing 'success' field in response")
                
                if "research_summary" in response_data:
                    print(f"✅ Research summary present: {len(response_data['research_summary'])} characters")
                else:
                    print("⚠️ Missing 'research_summary' field in response")
                
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON response: {e}")
                print(f"📄 Raw response: {response.text}")
        else:
            print(f"❌ Request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"📄 Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"📄 Raw error response: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the backend server running?")
        print("💡 Make sure to run: cd backend && python start_server.py")
    except requests.exceptions.Timeout:
        print("❌ Request timed out - SerpAPI research is taking too long")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"🔍 Error type: {type(e)}")

def test_serpapi_service_directly():
    """Test the SerpAPI service directly (without HTTP endpoint)"""
    print("\n🧪 Testing SerpAPI Service Directly")
    print("=" * 50)
    
    try:
        # Import the service
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
        
        from services.serp_api_service import SerpAPIService
        import asyncio
        
        print("✅ Successfully imported SerpAPIService")
        
        async def test_service():
            """Test the service asynchronously"""
            async with SerpAPIService() as service:
                print("🔍 Testing research_topic method...")
                
                # Test with real SerpAPI key and sofa topic
                result = await service.research_topic(
                    topic="how sofa's grew",
                    api_key="f11475cee488362fe8791331e507a99af25ef721e2f08ada96d0af406d93fd89",
                    num_results=5
                )
                
                print(f"📊 Research result: {json.dumps(result, indent=2)}")
                
                if result.get("success"):
                    print("✅ Service test successful!")
                    if result.get("total_results", 0) > 0:
                        print(f"🎯 Found {result['total_results']} relevant sources!")
                        if result.get("external_links"):
                            print(f"🔗 External links: {len(result['external_links'])}")
                        if result.get("key_insights"):
                            print(f"💡 Key insights: {len(result['key_insights'])}")
                    else:
                        print("⚠️ No research results found (this might be expected with test data)")
                else:
                    print(f"⚠️ Service test failed: {result.get('error', 'Unknown error')}")
        
        # Run the async test
        asyncio.run(test_service())
        
    except ImportError as e:
        print(f"❌ Failed to import SerpAPIService: {e}")
        print("💡 Make sure you're in the project root directory")
    except Exception as e:
        print(f"❌ Service test failed: {e}")

def main():
    """Main test function"""
    print("🚀 Starting SerpAPI Integration Tests")
    print("=" * 60)
    
    # Test 1: HTTP endpoint
    test_serpapi_research_endpoint()
    
    # Test 2: Service directly
    test_serpapi_service_directly()
    
    print("\n" + "=" * 60)
    print("🏁 SerpAPI Integration Tests Complete")
    print("\n📋 Summary:")
    print("• If you see connection errors, make sure the backend server is running")
    print("• If you see import errors, make sure you're in the project root directory")
    print("• The SerpAPI service should work even with invalid API keys (it will return empty results)")

if __name__ == "__main__":
    main()
