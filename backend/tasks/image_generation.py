from celery import shared_task
from typing import Dict, List, Any
import logging
import os
from datetime import datetime

from core.supabase_client import supabase_client
from models.blog import BlogStatus

logger = logging.getLogger(__name__)

@shared_task(bind=True, name="generate_image")
def generate_image_task(self, blog_id: str):
    """
    Generate or fetch featured image for blog
    
    Args:
        blog_id: Blog UUID as string
    """
    try:
        logger.info(f"Starting image generation for blog {blog_id}")
        
        # Get blog data
        blog_data = get_blog_data(blog_id)
        if not blog_data:
            logger.error(f"Blog {blog_id} not found")
            return
        
        # Update status to image generating
        update_blog_status(blog_id, BlogStatus.IMAGE_GENERATING)
        
        # Extract content and title for image generation
        title = blog_data.get("title", "")
        content = blog_data.get("content", "")
        seo_meta = blog_data.get("seo_meta", {})
        
        # Generate image prompt
        image_prompt = generate_image_prompt(title, content, seo_meta)
        
        # For now, we'll use placeholder images
        # In production, this would integrate with DALL-E, Stable Diffusion, or Unsplash API
        image_url = generate_placeholder_image(title, image_prompt)
        
        # Generate alt text for accessibility
        alt_text = generate_alt_text(title, image_prompt)
        
        # Update blog with image data
        update_blog_image(blog_id, image_url, alt_text, image_prompt)
        
        # Update status to ready
        update_blog_status(blog_id, BlogStatus.READY)
        
        logger.info(f"Image generation completed for blog {blog_id}")
        
        return {
            "blog_id": blog_id,
            "status": "image_generated",
            "image_url": image_url,
            "alt_text": alt_text
        }
        
    except Exception as e:
        logger.error(f"Error in image generation for blog {blog_id}: {e}")
        update_blog_status(blog_id, BlogStatus.FAILED, str(e))
        raise

def generate_image_prompt(title: str, content: str, seo_meta: Dict) -> str:
    """Generate image prompt based on blog content"""
    try:
        # Extract main topic and keywords
        main_topic = seo_meta.get("main_keyword", "blog")
        tags = seo_meta.get("tags", [])
        
        # Analyze content type
        content_type = analyze_content_type(title, content)
        
        # Generate contextual image prompt
        if content_type == "how_to":
            prompt = f"Professional illustration showing {main_topic} tutorial or guide, clean design, modern style"
        elif content_type == "tips":
            prompt = f"Infographic style image for {main_topic} tips and advice, organized layout, professional appearance"
        elif content_type == "analysis":
            prompt = f"Data visualization or chart representing {main_topic} analysis, business style, clean design"
        elif content_type == "news":
            prompt = f"News headline style image for {main_topic}, modern typography, professional journalism look"
        else:
            prompt = f"Professional blog header image for {main_topic}, modern design, clean typography"
        
        # Add style modifiers based on tags
        if "technology" in tags:
            prompt += ", tech aesthetic, digital style"
        elif "business" in tags:
            prompt += ", corporate style, professional business look"
        elif "health" in tags:
            prompt += ", wellness aesthetic, clean health style"
        elif "lifestyle" in tags:
            prompt += ", modern lifestyle, contemporary design"
        
        # Ensure the prompt is appropriate for image generation
        prompt += ", high quality, suitable for blog header, no text overlay needed"
        
        return prompt
        
    except Exception as e:
        logger.error(f"Error generating image prompt: {e}")
        return f"Professional blog header image for {title}, modern design, clean style"

def analyze_content_type(title: str, content: str) -> str:
    """Analyze content type to determine appropriate image style"""
    title_lower = title.lower()
    content_lower = content.lower()
    
    if any(word in title_lower for word in ["how to", "guide", "tutorial", "step by step"]):
        return "how_to"
    elif any(word in title_lower for word in ["tips", "advice", "strategies", "best practices"]):
        return "tips"
    elif any(word in title_lower for word in ["analysis", "review", "comparison", "research"]):
        return "analysis"
    elif any(word in title_lower for word in ["news", "update", "announcement", "latest"]):
        return "news"
    else:
        return "general"

def generate_placeholder_image(title: str, image_prompt: str) -> str:
    """Generate placeholder image URL (in production, this would use AI image generation)"""
    try:
        # For development/testing, use placeholder services
        # In production, integrate with DALL-E, Stable Diffusion, or Unsplash API
        
        # Use Unsplash API for relevant images (placeholder implementation)
        # This is a simplified version - in production you'd make actual API calls
        
        # For now, return a placeholder image URL
        # You can replace this with actual AI image generation
        placeholder_url = f"https://via.placeholder.com/1200x630/1f2937/ffffff?text={title.replace(' ', '+')}"
        
        logger.info(f"Generated placeholder image for: {image_prompt}")
        
        return placeholder_url
        
    except Exception as e:
        logger.error(f"Error generating placeholder image: {e}")
        # Fallback to a generic placeholder
        return "https://via.placeholder.com/1200x630/1f2937/ffffff?text=Blog+Image"

def generate_alt_text(title: str, image_prompt: str) -> str:
    """Generate descriptive alt text for accessibility and SEO"""
    try:
        # Extract main topic from title
        main_topic = title.split()[0] if title else "blog"
        
        # Create descriptive alt text
        alt_text = f"Featured image for blog post about {main_topic}. {image_prompt}"
        
        # Ensure alt text is not too long (recommended: under 125 characters)
        if len(alt_text) > 125:
            alt_text = f"Featured image for blog post about {main_topic}"
        
        return alt_text
        
    except Exception as e:
        logger.error(f"Error generating alt text: {e}")
        return f"Featured image for {title}"

def get_blog_data(blog_id: str) -> Dict[str, Any]:
    """Get blog data from database"""
    try:
        response = supabase_client.table("blogs").select("*").eq("id", blog_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Error fetching blog data: {e}")
        return None

def update_blog_status(blog_id: str, status: BlogStatus, error_message: str = None):
    """Update blog status in database"""
    try:
        update_data = {
            "status": status.value,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if error_message:
            update_data["error_message"] = error_message
        
        response = supabase_client.table("blogs").update(update_data).eq("id", blog_id).execute()
        
        if not response.data:
            logger.error(f"Failed to update blog {blog_id} status")
            
    except Exception as e:
        logger.error(f"Error updating blog status: {e}")

def update_blog_image(blog_id: str, image_url: str, alt_text: str, image_prompt: str):
    """Update blog with image data"""
    try:
        # Update generation logs
        current_logs = get_current_generation_logs(blog_id)
        current_logs.append({
            "step": "image_generation",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
            "image_url": image_url,
            "alt_text": alt_text,
            "image_prompt": image_prompt
        })
        
        # Update SEO meta with image information
        seo_meta = get_current_seo_meta(blog_id)
        seo_meta["featured_image"] = {
            "url": image_url,
            "alt_text": alt_text,
            "prompt": image_prompt,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        update_data = {
            "seo_meta": seo_meta,
            "generation_logs": current_logs,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        response = supabase_client.table("blogs").update(update_data).eq("id", blog_id).execute()
        
        if not response.data:
            logger.error(f"Failed to update blog {blog_id} image data")
            
    except Exception as e:
        logger.error(f"Error updating blog image: {e}")

def get_current_generation_logs(blog_id: str) -> List[Dict]:
    """Get current generation logs for the blog"""
    try:
        response = supabase_client.table("blogs").select("generation_logs").eq("id", blog_id).execute()
        if response.data and response.data[0].get("generation_logs"):
            return response.data[0]["generation_logs"]
        return []
    except Exception as e:
        logger.error(f"Error fetching generation logs: {e}")
        return []

def get_current_seo_meta(blog_id: str) -> Dict:
    """Get current SEO metadata for the blog"""
    try:
        response = supabase_client.table("blogs").select("seo_meta").eq("id", blog_id).execute()
        if response.data and response.data[0].get("seo_meta"):
            return response.data[0]["seo_meta"]
        return {}
    except Exception as e:
        logger.error(f"Error fetching SEO metadata: {e}")
        return {}
