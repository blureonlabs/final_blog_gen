import os
import logging
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class FalAIService:
    """Service for generating images using Fal AI FLUX.1 [dev] model"""
    
    def __init__(self, api_key: str):
        """Initialize the Fal AI service with API key"""
        self.api_key = api_key
        self.base_url = "https://fal.run/fal-ai/flux"
        self.headers = {
            "Authorization": f"Key {api_key}",
            "Content-Type": "application/json"
        }
        
    async def generate_image(
        self,
        prompt: str,
        style: str = "photographic",
        aspect_ratio: str = "16:9",
        quality: str = "standard"
    ) -> Dict[str, Any]:
        """
        Generate a single image using Fal AI FLUX.1
        
        Args:
            prompt: Text description of the image to generate
            style: Image style (photographic, cinematic, anime, etc.)
            aspect_ratio: Image aspect ratio (16:9, 4:3, 1:1, etc.)
            quality: Image quality (standard, high, ultra)
            
        Returns:
            Dict containing the generated image URL and metadata
        """
        try:
            # Map quality to inference steps
            quality_steps = {
                "standard": 28,
                "high": 35,
                "ultra": 50
            }
            
            # Map aspect ratio to dimensions
            dimensions = self._get_dimensions(aspect_ratio)
            
            # Prepare the request payload
            payload = {
                "prompt": f"{prompt}, {style} style, high quality, detailed",
                "image_dimensions": f"{dimensions['width']}x{dimensions['height']}",
                "num_inference_steps": quality_steps.get(quality, 28),
                "guidance_scale": 7.5,
                "scheduler": "euler_a",
                "seed": None,  # Random seed for variety
                "sync_mode": True
            }
            
            logger.info(f"Generating image with prompt: {prompt[:100]}...")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        if "images" in result and len(result["images"]) > 0:
                            image_url = result["images"][0]["url"]
                            
                            logger.info(f"✅ Image generated successfully: {image_url}")
                            
                            return {
                                "success": True,
                                "image_url": image_url,
                                "metadata": {
                                    "prompt": prompt,
                                    "style": style,
                                    "aspect_ratio": aspect_ratio,
                                    "quality": quality,
                                    "dimensions": dimensions,
                                    "inference_steps": quality_steps.get(quality, 28),
                                    "generated_at": datetime.utcnow().isoformat(),
                                    "fal_response": result
                                }
                            }
                        else:
                            logger.error("No images returned from Fal AI")
                            return {
                                "success": False,
                                "error": "No images returned from Fal AI",
                                "response": result
                            }
                    else:
                        error_text = await response.text()
                        logger.error(f"Fal AI API error: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"API error {response.status}: {error_text}"
                        }
                        
        except asyncio.TimeoutError:
            logger.error("Image generation timed out")
            return {
                "success": False,
                "error": "Image generation timed out"
            }
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_multiple_images(
        self,
        prompt: str,
        count: int = 2,
        style: str = "photographic",
        aspect_ratio: str = "16:9",
        quality: str = "standard"
    ) -> Dict[str, Any]:
        """
        Generate multiple images using Fal AI
        
        Args:
            prompt: Text description of the image to generate
            count: Number of images to generate (1-4)
            style: Image style
            aspect_ratio: Image aspect ratio
            quality: Image quality
            
        Returns:
            Dict containing generated images and metadata
        """
        try:
            # Limit count to 4 for cost control
            count = min(count, 4)
            
            # Generate images sequentially to avoid rate limits
            images = []
            successful_count = 0
            
            for i in range(count):
                logger.info(f"Generating image {i+1}/{count}")
                
                # Add variation to prompt for diversity
                varied_prompt = f"{prompt}, variation {i+1}"
                
                result = await self.generate_image(
                    prompt=varied_prompt,
                    style=style,
                    aspect_ratio=aspect_ratio,
                    quality=quality
                )
                
                if result["success"]:
                    images.append({
                        "url": result["image_url"],
                        "prompt": varied_prompt,
                        "style": style,
                        "aspect_ratio": aspect_ratio,
                        "quality": quality,
                        "generated_at": datetime.utcnow().isoformat(),
                        "variation": i + 1
                    })
                    successful_count += 1
                else:
                    logger.warning(f"Failed to generate image {i+1}: {result.get('error', 'Unknown error')}")
                
                # Small delay between requests
                if i < count - 1:
                    await asyncio.sleep(1)
            
            return {
                "success": successful_count > 0,
                "images": images,
                "total_generated": successful_count,
                "requested_count": count,
                "metadata": {
                    "style": style,
                    "aspect_ratio": aspect_ratio,
                    "quality": quality,
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating multiple images: {e}")
            return {
                "success": False,
                "error": str(e),
                "images": [],
                "total_generated": 0,
                "requested_count": count
            }
    
    def _get_dimensions(self, aspect_ratio: str) -> Dict[str, int]:
        """Get width and height dimensions for given aspect ratio"""
        dimensions = {
            "16:9": {"width": 1280, "height": 720},
            "4:3": {"width": 1280, "height": 960},
            "1:1": {"width": 1024, "height": 1024},
            "3:4": {"width": 960, "height": 1280},
            "9:16": {"width": 720, "height": 1280}
        }
        return dimensions.get(aspect_ratio, dimensions["16:9"])
    
    async def validate_api_key(self) -> bool:
        """Validate if the API key is valid by making a test request"""
        try:
            # Make a simple test request
            test_payload = {
                "prompt": "test image, simple",
                "image_dimensions": "512x512",
                "num_inference_steps": 10,
                "guidance_scale": 7.5,
                "scheduler": "euler_a",
                "sync_mode": True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    headers=self.headers,
                    json=test_payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
    
    async def get_usage_info(self) -> Dict[str, Any]:
        """Get current usage information from Fal AI"""
        try:
            # Note: This would require Fal AI to provide usage endpoints
            # For now, return placeholder information
            return {
                "success": True,
                "usage": {
                    "images_generated": "Unknown",
                    "credits_remaining": "Unknown",
                    "rate_limit": "Unknown"
                },
                "note": "Usage information not available from Fal AI API"
            }
        except Exception as e:
            logger.error(f"Error getting usage info: {e}")
            return {
                "success": False,
                "error": str(e)
            }
