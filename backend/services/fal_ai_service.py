import os
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

# Import the official fal-client package
try:
    import fal_client
    FAL_CLIENT_AVAILABLE = True
except ImportError:
    FAL_CLIENT_AVAILABLE = False
    fal_client = None

logger = logging.getLogger(__name__)

class FalAIService:
    """Service for generating images using Fal AI FLUX.1 [dev] model with official client"""
    
    def __init__(self, api_key: str):
        """Initialize the Fal AI service with API key"""
        self.api_key = api_key
        
        # Set the API key for fal-client
        if FAL_CLIENT_AVAILABLE:
            os.environ["FAL_KEY"] = api_key
            logger.info("✅ Fal AI client initialized with API key")
        else:
            logger.error("❌ fal-client package not available. Please install with: pip install fal-client")
            raise ImportError("fal-client package not available")
        
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
            
            # Map aspect ratio to official Fal AI format
            image_size = self._map_aspect_ratio_to_fal_format(aspect_ratio)
            
            # Prepare the request arguments
            arguments = {
                "prompt": f"{prompt}, {style} style, high quality, detailed, professional",
                "image_size": image_size,
                "num_inference_steps": quality_steps.get(quality, 28),
                "guidance_scale": 3.5,  # Using default from docs
                "sync_mode": True,  # Wait for completion
                "num_images": 1,
                "enable_safety_checker": True,
                "output_format": "jpeg",
                "acceleration": "none"
            }
            
            logger.info(f"🎨 Generating image with Fal AI FLUX.1 [dev]")
            logger.info(f"📝 Prompt: {prompt[:100]}...")
            logger.info(f"🔧 Arguments: {arguments}")
            
            # Use the official fal-client to submit the request
            result = fal_client.submit(
                "fal-ai/flux/dev",
                arguments=arguments
            )
            
            logger.info(f"📤 Request submitted to Fal AI with ID: {result.request_id}")
            
            # Wait for the result (since sync_mode=True)
            final_result = fal_client.result("fal-ai/flux/dev", result.request_id)
            
            if final_result and "images" in final_result and len(final_result["images"]) > 0:
                image_url = final_result["images"][0]["url"]
                
                logger.info(f"✅ Image generated successfully by Fal AI!")
                logger.info(f"🖼️ Image URL: {image_url[:100]}...")
                
                return {
                    "success": True,
                    "image_url": image_url,
                    "metadata": {
                        "prompt": prompt,
                        "style": style,
                        "aspect_ratio": aspect_ratio,
                        "quality": quality,
                        "inference_steps": quality_steps.get(quality, 28),
                        "generated_at": datetime.utcnow().isoformat(),
                        "fal_request_id": result.request_id,
                        "fal_response": final_result
                    }
                }
            else:
                logger.error("❌ No images returned from Fal AI")
                return {
                    "success": False,
                    "error": "No images returned from Fal AI",
                    "metadata": {
                        "prompt": prompt,
                        "fal_response": final_result
                    }
                }
                        
        except Exception as e:
            logger.error(f"❌ Error generating image with Fal AI: {e}")
            return {
                "success": False,
                "error": str(e),
                "metadata": {
                    "prompt": prompt,
                    "error": str(e)
                }
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
    
    def _map_aspect_ratio_to_fal_format(self, aspect_ratio: str) -> str:
        """Map aspect ratio string to Fal AI official format"""
        fal_format_map = {
            "16:9": "landscape_16_9",
            "4:3": "landscape_4_3", 
            "1:1": "square",
            "3:4": "portrait_4_3",
            "9:16": "portrait_16_9"
        }
        return fal_format_map.get(aspect_ratio, "landscape_4_3")
    
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
