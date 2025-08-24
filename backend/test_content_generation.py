#!/usr/bin/env python3
"""
Test script for Content Generation Service
This script tests the AI client and content generation functionality
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.ai_client import ai_client
from core.config import settings

async def test_ai_client():
    """Test the AI client functionality"""
    print("🧪 Testing AI Client...")
    
    # Test available models
    print("\n📋 Available Models:")
    models = ai_client.get_available_models()
    for provider, model_list in models.items():
        if model_list:
            print(f"  {provider.upper()}: {', '.join(model_list)}")
        else:
            print(f"  {provider.upper()}: No API key configured")
    
    # Test model availability
    print("\n🔍 Model Availability:")
    for provider in ["openai", "gemini"]:
        is_available = ai_client.is_model_available(provider)
        status = "✅ Available" if is_available else "❌ Not Available"
        print(f"  {provider.upper()}: {status}")
    
    # Test blog generation if any model is available
    print("\n🚀 Testing Blog Generation...")
    
    test_prompt = "The benefits of remote work for productivity and work-life balance"
    
    # Try OpenAI first
    if ai_client.is_model_available("openai"):
        print("  Testing OpenAI...")
        try:
            result = await ai_client.generate_blog_draft(
                prompt=test_prompt,
                ai_model="openai",
                ai_model_version="gpt-3.5-turbo"
            )
            print(f"    ✅ Success! Generated blog with title: {result['title'][:50]}...")
            print(f"    📝 Content length: {len(result['content'])} characters")
            print(f"    🤖 Model: {result['model']}")
            print(f"    🔢 Tokens used: {result['tokens_used']}")
        except Exception as e:
            print(f"    ❌ OpenAI generation failed: {e}")
    
    # Try Gemini
    if ai_client.is_model_available("gemini"):
        print("  Testing Gemini...")
        try:
            result = await ai_client.generate_blog_draft(
                prompt=test_prompt,
                ai_model="gemini"
            )
            print(f"    ✅ Success! Generated blog with title: {result['title'][:50]}...")
            print(f"    📝 Content length: {len(result['content'])} characters")
            print(f"    🤖 Model: {result['model']}")
            print(f"    🔢 Tokens used: {result['tokens_used']}")
        except Exception as e:
            print(f"    ❌ Gemini generation failed: {e}")
    
    # Test multiple blog generation
    print("\n📚 Testing Multiple Blog Generation...")
    if ai_client.is_model_available("openai") or ai_client.is_model_available("gemini"):
        try:
            # Use whichever model is available
            available_model = "openai" if ai_client.is_model_available("openai") else "gemini"
            
            blogs = await ai_client.generate_multiple_blogs(
                prompt=test_prompt,
                num_blogs=2,
                ai_model=available_model
            )
            
            print(f"    ✅ Successfully generated {len(blogs)} blogs using {available_model}")
            for i, blog in enumerate(blogs):
                print(f"      Blog {i+1}: {blog['title'][:40]}... ({len(blog['content'])} chars)")
                
        except Exception as e:
            print(f"    ❌ Multiple blog generation failed: {e}")

async def test_config():
    """Test configuration loading"""
    print("⚙️  Testing Configuration...")
    
    print(f"  Environment: {settings.ENVIRONMENT}")
    print(f"  Debug mode: {settings.DEBUG}")
    print(f"  Supabase URL: {settings.SUPABASE_URL[:50]}..." if settings.SUPABASE_URL else "  Supabase URL: Not set")
    print(f"  OpenAI API Key: {'✅ Set' if settings.OPENAI_API_KEY else '❌ Not set'}")
    print(f"  Gemini API Key: {'✅ Set' if settings.GEMINI_API_KEY else '❌ Not set'}")

async def main():
    """Main test function"""
    print("🚀 Content Generation Service Test")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Test configuration
    await test_config()
    
    print("\n" + "=" * 50)
    
    # Test AI client
    await test_ai_client()
    
    print("\n" + "=" * 50)
    print("✅ Testing completed!")

if __name__ == "__main__":
    asyncio.run(main())
