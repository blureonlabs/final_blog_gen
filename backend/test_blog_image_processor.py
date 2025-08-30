#!/usr/bin/env python3
"""
Test script for the BlogImageProcessor service
"""

import asyncio
import logging
from services.blog_image_processor import BlogImageProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_image_placeholder_extraction():
    """Test extracting image placeholders from blog content"""
    
    # Test content with image placeholders
    test_content = """
    # Introduction to AI
    
    [image:Modern AI laboratory with glowing neural network visualizations and researchers working on computers]
    
    Artificial Intelligence is transforming the world as we know it. From machine learning algorithms to neural networks, the technology continues to evolve rapidly.
    
    ## Machine Learning Basics
    
    Machine learning is a subset of AI that focuses on algorithms and statistical models.
    
    [image:Data visualization dashboard showing machine learning metrics and performance charts]
    
    ## Deep Learning
    
    Deep learning uses neural networks with multiple layers to process complex patterns.
    
    ## Conclusion
    
    AI is the future of technology and will continue to shape our world.
    """
    
    processor = BlogImageProcessor()
    
    # Test extraction
    placeholders = processor.extract_image_placeholders(test_content)
    
    logger.info(f"📸 Extracted {len(placeholders)} image placeholders:")
    for i, placeholder in enumerate(placeholders, 1):
        logger.info(f"  {i}. Image {placeholder['image_number']}: {placeholder['prompt']}")
        logger.info(f"     Alt text: {placeholder['alt_text']}")
    
    # Verify extraction
    assert len(placeholders) == 2, f"Expected 2 placeholders, got {len(placeholders)}"
    assert placeholders[0]["prompt"] == "Modern AI laboratory with glowing neural network visualizations and researchers working on computers"
    assert placeholders[1]["prompt"] == "Data visualization dashboard showing machine learning metrics and performance charts"
    
    logger.info("✅ Image placeholder extraction test passed!")

async def test_content_without_images():
    """Test content without image placeholders"""
    
    test_content = """
    # Introduction to AI
    
    Artificial Intelligence is transforming the world as we know it. From machine learning algorithms to neural networks, the technology continues to evolve rapidly.
    
    ## Machine Learning Basics
    
    Machine learning is a subset of AI that focuses on algorithms and statistical models.
    
    ## Deep Learning
    
    Deep learning uses neural networks with multiple layers to process complex patterns.
    
    ## Conclusion
    
    AI is the future of technology and will continue to shape our world.
    """
    
    processor = BlogImageProcessor()
    
    # Test extraction
    placeholders = processor.extract_image_placeholders(test_content)
    
    logger.info(f"📸 Extracted {len(placeholders)} image placeholders from content without images")
    
    # Verify no placeholders found
    assert len(placeholders) == 0, f"Expected 0 placeholders, got {len(placeholders)}"
    
    logger.info("✅ No image placeholders test passed!")

async def test_malformed_content():
    """Test content with malformed image placeholders"""
    
    test_content = """
    # Introduction to AI
    
    [image:Incomplete
    [image:Complete image description]
    [image]
    [image:]
    
    Artificial Intelligence is transforming the world.
    """
    
    processor = BlogImageProcessor()
    
    # Test extraction
    placeholders = processor.extract_image_placeholders(test_content)
    
    logger.info(f"📸 Extracted {len(placeholders)} image placeholders from malformed content")
    
    # Should only extract the complete one
    assert len(placeholders) == 1, f"Expected 1 placeholder, got {len(placeholders)}"
    assert placeholders[0]["prompt"] == "Complete image description"
    
    logger.info("✅ Malformed content test passed!")

async def main():
    """Run all tests"""
    logger.info("🚀 Starting BlogImageProcessor tests...")
    
    try:
        # Test 1: Normal content with image placeholders
        await test_image_placeholder_extraction()
        
        # Test 2: Content without images
        await test_content_without_images()
        
        # Test 3: Malformed content
        await test_malformed_content()
        
        logger.info("🎉 All tests passed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
