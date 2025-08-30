#!/usr/bin/env python3
"""
Test script for Enhanced SerpAPI integration
This script tests the enhanced SerpAPI research features including AI queries, external links, and content scraping.
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
ENHANCED_RESEARCH_ENDPOINT = f"{BASE_URL}/api/content-generation/enhanced-research"

def test_enhanced_serpapi_research():
    """Test the enhanced SerpAPI research endpoint"""
    print("🚀 Testing Enhanced SerpAPI Research Endpoint")
    print("=" * 60)
    
    # Test data - using your real SerpAPI key and proper UUID format
    project_id = "550e8400-e29b-41d4-a716-446655440000"  # Valid UUID format
    topic = "artificial intelligence trends 2024"
    api_key = "f11475cee488362fe8791331e507a99af25ef721e2f08ada96d0af406d93fd89"
    num_results = 5
    
    try:
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
        
        print(f"\n🔍 Making enhanced research request...")
        response = requests.post(
            ENHANCED_RESEARCH_ENDPOINT,
            params=params,  # Use params instead of json
            timeout=60  # Increased timeout for enhanced research
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Enhanced research request successful!")
            try:
                response_data = response.json()
                print(f"📄 Response Data: {json.dumps(response_data, indent=2)}")
                
                # Validate enhanced response structure
                if "success" in response_data:
                    print(f"✅ Success field present: {response_data['success']}")
                else:
                    print("⚠️ Missing 'success' field in response")
                
                if "research_results" in response_data:
                    research = response_data["research_results"]
                    print(f"✅ Research results present")
                    
                    if research.get("enhanced_research"):
                        print("🚀 Enhanced research features detected!")
                        
                        if research.get("content_analysis"):
                            print(f"📄 Content analysis available: {len(research['content_analysis'])} items")
                        
                        if research.get("external_links"):
                            print(f"🔗 External links: {len(research['external_links'])} found")
                        
                        if research.get("key_insights"):
                            print(f"💡 Key insights: {len(research['key_insights'])} extracted")
                    else:
                        print("📝 Standard research results (enhanced features not detected)")
                
                else:
                    print("⚠️ Missing 'research_results' field in response")
                
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON response: {e}")
                print(f"📄 Raw response: {response.text}")
        else:
            print(f"❌ Enhanced research request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"📄 Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"📄 Raw error response: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the backend server running?")
        print("💡 Make sure to run: cd backend && python start_server.py")
    except requests.exceptions.Timeout:
        print("❌ Request timed out - Enhanced research is taking too long")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"🔍 Error type: {type(e)}")

def test_enhanced_serpapi_service_directly():
    """Test the enhanced SerpAPI service directly (without HTTP endpoint)"""
    print("\n🧪 Testing Enhanced SerpAPI Service Directly")
    print("=" * 60)
    
    try:
        # Import the service
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
        
        from services.serp_api_service import SerpAPIService
        import asyncio
        
        print("✅ Successfully imported SerpAPIService")
        
        async def test_enhanced_service():
            """Test the enhanced service asynchronously"""
            async with SerpAPIService() as service:
                print("🚀 Testing enhanced research_topic method...")
                
                # Test with real SerpAPI key and enhanced research enabled
                result = await service.research_topic(
                    topic="artificial intelligence trends 2024",
                    api_key="f11475cee488362fe8791331e507a99af25ef721e2f08ada96d0af406d93fd89",
                    num_results=5,
                    enhanced_research=True
                )
                
                print(f"📊 Enhanced research result: {json.dumps(result, indent=2)}")
                
                if result.get("success"):
                    print("✅ Enhanced service test successful!")
                    
                    if result.get("enhanced_research"):
                        print("🚀 Enhanced research features detected!")
                        
                        if result.get("content_analysis"):
                            print(f"📄 Content analysis: {len(result['content_analysis'])} items")
                            for i, item in enumerate(result['content_analysis'][:3]):
                                if item.get("scraped_content"):
                                    print(f"  {i+1}. Content length: {item.get('content_length', 0)} chars")
                        
                        if result.get("total_results", 0) > 0:
                            print(f"🎯 Found {result['total_results']} relevant sources!")
                            if result.get("external_links"):
                                print(f"🔗 External links: {len(result['external_links'])}")
                            if result.get("key_insights"):
                                print(f"💡 Key insights: {len(result['key_insights'])}")
                    else:
                        print("📝 Standard research results (enhanced features not detected)")
                        
                else:
                    print(f"⚠️ Enhanced service test failed: {result.get('error', 'Unknown error')}")
        
        # Run the async test
        asyncio.run(test_enhanced_service())
        
    except ImportError as e:
        print(f"❌ Failed to import SerpAPIService: {e}")
        print("💡 Make sure you're running this from the project root directory")
    except Exception as e:
        print(f"❌ Enhanced service test failed: {e}")
        print(f"🔍 Error type: {type(e)}")

def test_standard_vs_enhanced():
    """Compare standard vs enhanced research modes"""
    print("\n🔄 Testing Standard vs Enhanced Research Modes")
    print("=" * 60)
    
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
        
        from services.serp_api_service import SerpAPIService
        import asyncio
        
        async def compare_modes():
            """Compare standard and enhanced research modes"""
            async with SerpAPIService() as service:
                topic = "digital marketing strategies"
                api_key = "f11475cee488362fe8791331e507a99af25ef721e2f08ada96d0af406d93fd89"
                
                print(f"🔍 Testing topic: {topic}")
                
                # Test standard mode
                print("\n📝 Standard Research Mode:")
                standard_result = await service.research_topic(
                    topic=topic,
                    api_key=api_key,
                    num_results=3,
                    enhanced_research=False
                )
                
                if standard_result.get("success"):
                    print(f"  ✅ Found {standard_result.get('total_results', 0)} results")
                    print(f"  🔗 External links: {len(standard_result.get('external_links', []))}")
                    print(f"  💡 Key insights: {len(standard_result.get('key_insights', []))}")
                else:
                    print(f"  ❌ Standard research failed: {standard_result.get('error')}")
                
                # Test enhanced mode
                print("\n🚀 Enhanced Research Mode:")
                enhanced_result = await service.research_topic(
                    topic=topic,
                    api_key=api_key,
                    num_results=3,
                    enhanced_research=True
                )
                
                if enhanced_result.get("success"):
                    print(f"  ✅ Found {enhanced_result.get('total_results', 0)} results")
                    print(f"  🔗 External links: {len(enhanced_result.get('external_links', []))}")
                    print(f"  💡 Key insights: {len(enhanced_result.get('key_insights', []))}")
                    
                    if enhanced_result.get("enhanced_research"):
                        print(f"  🚀 Enhanced features: AI queries, external links, content scraping")
                        if enhanced_result.get("content_analysis"):
                            print(f"  📄 Content analysis: {len(enhanced_result['content_analysis'])} items")
                    else:
                        print(f"  📝 Standard features only")
                else:
                    print(f"  ❌ Enhanced research failed: {enhanced_result.get('error')}")
        
        # Run the comparison test
        asyncio.run(compare_modes())
        
    except Exception as e:
        print(f"❌ Comparison test failed: {e}")

if __name__ == "__main__":
    print("🧪 Enhanced SerpAPI Integration Test Suite")
    print("=" * 60)
    
    # Test 1: Enhanced research endpoint
    test_enhanced_serpapi_research()
    
    # Test 2: Enhanced service directly
    test_enhanced_serpapi_service_directly()
    
    # Test 3: Compare standard vs enhanced modes
    test_standard_vs_enhanced()
    
    print("\n✅ Enhanced SerpAPI test suite completed!")
