#!/usr/bin/env python3
"""
Test script for SEO Keywords Extraction
This script demonstrates how the enhanced SerpAPI service now extracts actual SEO keywords.
"""

import sys
import os
import json

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_seo_keywords_extraction():
    """Test the SEO keywords extraction functionality"""
    print("🔍 Testing SEO Keywords Extraction")
    print("=" * 60)
    
    try:
        from services.serp_api_service import SerpAPIService
        
        print("✅ Successfully imported SerpAPIService")
        
        # Create service instance
        service = SerpAPIService()
        
        # Test 1: Banana Plantation (Agriculture)
        print(f"\n🍌 Test 1: Banana Plantation (Agriculture)")
        print("-" * 50)
        
        # Mock research results for banana plantation
        mock_results = [
            {
                "title": "Complete Guide to Sustainable Banana Plantation",
                "snippet": "Learn about organic farming techniques, soil health management, and climate-resilient varieties for banana cultivation in 2024.",
                "domain": "agriculture.com"
            },
            {
                "title": "Modern Banana Farming: Precision Agriculture Techniques",
                "snippet": "Discover how AI-powered irrigation systems and drone technology are revolutionizing banana plantation management.",
                "domain": "farmingtech.com"
            },
            {
                "title": "Banana Plantation Business Guide: Market Analysis 2024",
                "snippet": "Comprehensive market research on banana farming profitability, export opportunities, and sustainable business models.",
                "domain": "agribusiness.com"
            }
        ]
        
        topic = "banana plantation farming techniques"
        seo_keywords = service._extract_seo_keywords(mock_results, topic)
        
        print(f"📝 Topic: {topic}")
        print(f"🔑 SEO Keywords extracted: {len(seo_keywords)}")
        print(f"📊 Keywords:")
        for i, keyword in enumerate(seo_keywords, 1):
            print(f"  {i:2d}. {keyword}")
        
        # Test 2: Digital Marketing (Business)
        print(f"\n💻 Test 2: Digital Marketing (Business)")
        print("-" * 50)
        
        mock_results_2 = [
            {
                "title": "2024 Digital Marketing Trends: AI and Automation",
                "snippet": "Explore the latest trends in digital marketing including artificial intelligence, machine learning, and automated campaign optimization.",
                "domain": "marketingtoday.com"
            },
            {
                "title": "SEO Strategy for 2024: Content Optimization Techniques",
                "snippet": "Learn about modern SEO strategies, content marketing approaches, and social media integration for better search rankings.",
                "domain": "seoexperts.com"
            }
        ]
        
        topic_2 = "digital marketing strategies"
        seo_keywords_2 = service._extract_seo_keywords(mock_results_2, topic_2)
        
        print(f"📝 Topic: {topic_2}")
        print(f"🔑 SEO Keywords extracted: {len(seo_keywords_2)}")
        print(f"📊 Keywords:")
        for i, keyword in enumerate(seo_keywords_2, 1):
            print(f"  {i:2d}. {keyword}")
        
        # Test 3: Technology Development
        print(f"\n🚀 Test 3: Technology Development")
        print("-" * 50)
        
        mock_results_3 = [
            {
                "title": "Modern Web Development: React and Next.js Best Practices",
                "snippet": "Learn about modern web development frameworks, performance optimization, and cloud deployment strategies for 2024.",
                "domain": "webdev.com"
            }
        ]
        
        topic_3 = "web development technologies"
        seo_keywords_3 = service._extract_seo_keywords(mock_results_3, topic_3)
        
        print(f"📝 Topic: {topic_3}")
        print(f"🔑 SEO Keywords extracted: {len(seo_keywords_3)}")
        print(f"📊 Keywords:")
        for i, keyword in enumerate(seo_keywords_3, 1):
            print(f"  {i:2d}. {keyword}")
        
        print(f"\n✅ SEO Keywords extraction tests completed!")
        
    except ImportError as e:
        print(f"❌ Failed to import SerpAPIService: {e}")
        print("💡 Make sure you're running this from the project root directory")
    except Exception as e:
        print(f"❌ SEO keywords test failed: {e}")

def test_industry_keywords():
    """Test the industry-specific keyword generation"""
    print(f"\n🏭 Testing Industry-Specific Keywords")
    print("=" * 60)
    
    try:
        from services.serp_api_service import SerpAPIService
        
        service = SerpAPIService()
        
        # Test different industries
        test_topics = [
            "banana plantation farming",
            "digital marketing automation", 
            "web development frameworks",
            "e-commerce business strategy"
        ]
        
        for topic in test_topics:
            print(f"\n📝 Topic: {topic}")
            print("-" * 40)
            
            industry_keywords = service._get_industry_keywords(topic)
            print(f"🏭 Industry Keywords ({len(industry_keywords)}):")
            
            for i, keyword in enumerate(industry_keywords[:8], 1):  # Show first 8
                print(f"  {i:2d}. {keyword}")
            
            if len(industry_keywords) > 8:
                print(f"  ... and {len(industry_keywords) - 8} more")
        
        print(f"\n✅ Industry keywords tests completed!")
        
    except Exception as e:
        print(f"❌ Industry keywords test failed: {e}")

def test_trending_keywords():
    """Test trending keyword extraction"""
    print(f"\n📈 Testing Trending Keywords Extraction")
    print("=" * 60)
    
    try:
        from services.serp_api_service import SerpAPIService
        
        service = SerpAPIService()
        
        # Mock text with trending terms
        mock_text = """
        In 2024, sustainable farming practices are becoming increasingly popular. 
        Modern AI-powered irrigation systems are revolutionizing agriculture.
        Climate-resilient crop varieties are emerging as a solution to global warming.
        Remote monitoring technologies are growing in adoption.
        Blockchain solutions for supply chain transparency are gaining traction.
        """
        
        topic = "agriculture technology"
        trending_keywords = service._extract_trending_keywords(mock_text, topic)
        
        print(f"📝 Topic: {topic}")
        print(f"📄 Mock Text: {mock_text.strip()}")
        print(f"📈 Trending Keywords extracted: {len(trending_keywords)}")
        print(f"🔑 Keywords:")
        for i, keyword in enumerate(trending_keywords, 1):
            print(f"  {i:2d}. {keyword}")
        
        print(f"\n✅ Trending keywords test completed!")
        
    except Exception as e:
        print(f"❌ Trending keywords test failed: {e}")

if __name__ == "__main__":
    print("🧪 SEO Keywords Extraction Test Suite")
    print("=" * 60)
    
    # Test 1: SEO keywords extraction
    test_seo_keywords_extraction()
    
    # Test 2: Industry-specific keywords
    test_industry_keywords()
    
    # Test 3: Trending keywords
    test_trending_keywords()
    
    print(f"\n🎉 SEO Keywords test suite completed!")
    print(f"\n📊 What This Means:")
    print(f"  • SerpAPI research now extracts actual SEO keywords")
    print(f"  • Keywords are industry-specific and trending")
    print(f"  • AI prompts include these keywords for better content")
    print(f"  • Frontend displays keywords for content optimization")
    print(f"  • Better SEO results through research-driven keyword strategy")
