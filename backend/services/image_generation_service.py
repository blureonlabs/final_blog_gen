import os
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

from .fal_ai_service import FalAIService

logger = logging.getLogger(__name__)

class ImageGenerationService:
    """Service for generating images for blog posts using Fal AI FLUX.1 [dev] model"""
    
    def __init__(self):
        """Initialize the image generation service"""
        self.fal_service = None
        self.fal_api_key = None
        
    def set_fal_api_key(self, api_key: str):
        """Set the Fal AI API key for this service instance"""
        self.fal_api_key = api_key
        self.fal_service = FalAIService(api_key)
        
    def get_available_styles(self) -> List[str]:
        """Get available image generation styles"""
        return [
            "photographic",
            "cinematic", 
            "anime",
            "digital-art",
            "oil-painting",
            "watercolor",
            "sketch",
            "cartoon",
            "3d-render",
            "minimalist",
            "vintage",
            "modern",
            "abstract",
            "realistic",
            "fantasy"
        ]
        
    def get_available_aspect_ratios(self) -> List[str]:
        """Get available image aspect ratios"""
        return [
            "16:9",    # Landscape widescreen
            "4:3",     # Landscape standard
            "1:1",     # Square
            "3:4",     # Portrait standard
            "9:16"     # Portrait mobile
        ]
        
    def get_available_qualities(self) -> List[str]:
        """Get available image quality levels"""
        return [
            "standard",  # 28 inference steps
            "high",      # 35 inference steps
            "ultra"      # 50 inference steps
        ]
        
    def _extract_keywords_from_content(self, content: str, max_keywords: int = 5) -> List[str]:
        """Extract relevant keywords from blog content for image generation"""
        # Remove HTML tags and special characters
        clean_content = re.sub(r'<[^>]+>', '', content)
        clean_content = re.sub(r'[^\w\s]', ' ', clean_content)
        
        # Split into words and filter
        words = clean_content.lower().split()
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        
        # Count word frequency
        word_freq = {}
        for word in words:
            if word not in stop_words and len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
                
        # Get top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_keywords]]
        
    def _generate_image_prompt(self, title: str, content: str, seo_meta: Dict = None, style: str = "photographic") -> str:
        """Generate an optimized prompt for image generation based on blog content"""
        # Extract keywords from content
        keywords = self._extract_keywords_from_content(content, max_keywords=3)
        
        # Use SEO meta if available
        if seo_meta and seo_meta.get('keywords'):
            seo_keywords = seo_meta['keywords'][:3] if isinstance(seo_meta['keywords'], list) else [seo_meta['keywords']]
            keywords.extend(seo_keywords)
            
        # Create a descriptive prompt
        prompt_parts = [
            f"A professional blog header image for '{title}'",
            f"featuring {', '.join(keywords[:3])}",
            f"in {style} style",
            "high quality, detailed, professional",
            "suitable for blog articles and digital content"
        ]
        
        return ", ".join(prompt_parts)
        
    def _map_aspect_ratio_to_size(self, aspect_ratio: str) -> Dict[str, int]:
        """Map aspect ratio string to width and height dimensions"""
        size_mapping = {
            "16:9": {"width": 1280, "height": 720},
            "4:3": {"width": 1280, "height": 960},
            "1:1": {"width": 1024, "height": 1024},
            "3:4": {"width": 960, "height": 1280},
            "9:16": {"width": 720, "height": 1280}
        }
        return size_mapping.get(aspect_ratio, size_mapping["16:9"])
        
    def _map_quality_to_steps(self, quality: str) -> int:
        """Map quality level to number of inference steps"""
        quality_mapping = {
            "standard": 28,
            "high": 35,
            "ultra": 50
        }
        return quality_mapping.get(quality, 28)
        
    async def generate_blog_images(
        self,
        blog_id: str,
        title: str,
        content: str,
        seo_meta: Dict = None,
        num_images: int = 1,
        style: str = "photographic",
        aspect_ratio: str = "16:9",
        quality: str = "standard"
    ) -> Dict[str, Any]:
        """
        Generate images for a blog post
        
        Args:
            blog_id: ID of the blog post
            title: Blog post title
            content: Blog post content
            seo_meta: SEO metadata including keywords
            num_images: Number of images to generate (1-4)
            style: Image style
            aspect_ratio: Image aspect ratio
            quality: Image quality level
            
        Returns:
            Dict containing generated images and metadata
        """
        try:
            if not self.fal_service:
                raise Exception("Fal AI service not initialized. Please set API key first.")
                
            logger.info(f"Generating {num_images} images for blog {blog_id}")
            
            # Generate optimized prompt
            prompt = self._generate_image_prompt(title, content, seo_meta, style)
            logger.info(f"Generated prompt: {prompt}")
            
            # Map parameters
            image_size = self._map_aspect_ratio_to_size(aspect_ratio)
            num_inference_steps = self._map_quality_to_steps(quality)
            
            # Generate images
            if num_images == 1:
                result = await self.fal_service.generate_image(
                    prompt=prompt,
                    style=style,
                    aspect_ratio=aspect_ratio,
                    quality=quality
                )
                
                if result["success"]:
                    return {
                        "success": True,
                        "blog_id": blog_id,
                        "images": [{
                            "url": result["image_url"],
                            "prompt": prompt,
                            "style": style,
                            "aspect_ratio": aspect_ratio,
                            "quality": quality,
                            "generated_at": datetime.utcnow().isoformat()
                        }],
                        "total_generated": 1,
                        "requested_count": 1,
                        "metadata": result.get("metadata", {})
                    }
                else:
                    return result
            else:
                # Generate multiple images
                result = await self.fal_service.generate_multiple_images(
                    prompt=prompt,
                    count=num_images,
                    style=style,
                    aspect_ratio=aspect_ratio,
                    quality=quality
                )
                
                if result["success"]:
                    return {
                        "success": True,
                        "blog_id": blog_id,
                        "images": result["images"],
                        "total_generated": result["total_generated"],
                        "requested_count": result["requested_count"],
                        "metadata": result.get("metadata", {})
                    }
                else:
                    return result
                    
        except Exception as e:
            logger.error(f"Error generating images for blog {blog_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "blog_id": blog_id,
                "generated_at": datetime.utcnow().isoformat()
            }
            
    async def generate_placeholder_image(self, title: str, style: str = "photographic") -> str:
        """Generate a placeholder image URL for testing purposes"""
        # This would typically use a placeholder service or generate a simple image
        # For now, return a placeholder URL
        return f"https://via.placeholder.com/1280x720/4F46E5/FFFFFF?text={title.replace(' ', '+')}"
        
    def validate_api_key(self, api_key: str) -> bool:
        """Validate if the provided API key is valid"""
        try:
            test_service = FalAIService(api_key)
            return test_service.validate_api_key()
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
