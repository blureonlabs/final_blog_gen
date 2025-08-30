from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from core.auth import get_current_user
from core.supabase_client import supabase_client
from services.image_generation_service import ImageGenerationService
from models.blog import BlogStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/images", tags=["image-generation"])

# Initialize image generation service
image_service = ImageGenerationService()

@router.get("/styles")
async def get_available_styles():
    """Get available image generation styles"""
    try:
        styles = image_service.get_available_styles()
        return {
            "success": True,
            "styles": styles,
            "count": len(styles)
        }
    except Exception as e:
        logger.error(f"Error getting styles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/aspect-ratios")
async def get_available_aspect_ratios():
    """Get available image aspect ratios"""
    try:
        ratios = image_service.get_available_aspect_ratios()
        return {
            "success": True,
            "aspect_ratios": ratios,
            "count": len(ratios)
        }
    except Exception as e:
        logger.error(f"Error getting aspect ratios: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/qualities")
async def get_available_qualities():
    """Get available image quality levels"""
    try:
        qualities = image_service.get_available_qualities()
        return {
            "success": True,
            "qualities": qualities,
            "count": len(qualities)
        }
    except Exception as e:
        logger.error(f"Error getting qualities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate")
async def generate_images(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """
    Generate images for a blog post
    
    Request body:
    - blog_id: UUID of the blog
    - title: Blog title
    - content: Blog content
    - seo_meta: SEO metadata (optional)
    - num_images: Number of images to generate (1-4)
    - style: Image style
    - aspect_ratio: Image aspect ratio
    - quality: Image quality level
    """
    try:
        # Validate required fields
        required_fields = ["blog_id", "title", "content"]
        for field in required_fields:
            if field not in request:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        blog_id = request["blog_id"]
        title = request["title"]
        content = request["content"]
        seo_meta = request.get("seo_meta", {})
        num_images = min(request.get("num_images", 1), 4)  # Cap at 4
        style = request.get("style", "photographic")
        aspect_ratio = request.get("aspect_ratio", "16:9")
        quality = request.get("quality", "standard")
        
        # Validate blog ownership
        blog_response = supabase_client.table("blogs").select("id, project_id").eq("id", blog_id).execute()
        if not blog_response.data:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        blog_data = blog_response.data[0]
        project_response = supabase_client.table("projects").select("user_id").eq("id", blog_data["project_id"]).execute()
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project_data = project_response.data[0]
        if project_data["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get user's Fal AI API key
        api_key_response = supabase_client.table("api_keys").select("api_key").eq("user_id", current_user["id"]).eq("service", "fal").eq("is_active", True).execute()
        
        if not api_key_response.data:
            raise HTTPException(status_code=400, detail="Fal AI API key not found. Please add your Fal AI API key in settings.")
        
        fal_api_key = api_key_response.data[0]["api_key"]
        
        # Set API key for the service
        image_service.set_fal_api_key(fal_api_key)
        
        # Update blog status to image generating
        supabase_client.table("blogs").update({
            "status": BlogStatus.IMAGE_GENERATING.value,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", blog_id).execute()
        
        # Generate images
        result = await image_service.generate_blog_images(
            blog_id=blog_id,
            project_id=blog_data["project_id"],
            title=title,
            content=content,
            seo_meta=seo_meta,
            num_images=num_images,
            style=style,
            aspect_ratio=aspect_ratio,
            quality=quality
        )
        
        if result["success"]:
            # Store images in the images table
            for img in result["images"]:
                # Generate alt text for the image
                alt_text = f"Image {img.get('image_number', 1)} for {title}"
                
                # Insert image record
                image_data = {
                    "project_id": blog_data["project_id"],
                    "blog_id": blog_id,
                    "prompt": img.get("prompt", ""),
                    "alt_text": alt_text,
                    "image_number": img.get("image_number", 1),
                    "s3_url": img["url"],  # Store the generated image URL
                    "status": "generated",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                supabase_client.table("images").insert(image_data).execute()
            
            # Update blog status to ready
            supabase_client.table("blogs").update({
                "status": BlogStatus.READY.value,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", blog_id).execute()
            
            # Log the successful generation
            supabase_client.table("logs").insert({
                "user_id": current_user["id"],
                "project_id": blog_data["project_id"],
                "blog_id": blog_id,
                "level": "info",
                "category": "image_generation",
                "message": f"Generated {len(result['images'])} images successfully",
                "metadata": {
                    "images_count": len(result['images']),
                    "style": style,
                    "aspect_ratio": aspect_ratio,
                    "quality": quality
                }
            }).execute()
            
            return {
                "success": True,
                "message": f"Generated {len(result['images'])} images successfully",
                "blog_id": blog_id,
                "project_id": blog_data["project_id"],
                "total_generated": len(result['images']),
                "requested_count": num_images,
                "images_stored": True
            }
        else:
            # Update blog status to failed
            supabase_client.table("blogs").update({
                "status": BlogStatus.FAILED.value,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", blog_id).execute()
            
            # Log the failure
            supabase_client.table("logs").insert({
                "user_id": current_user["id"],
                "project_id": blog_data["project_id"],
                "blog_id": blog_id,
                "level": "error",
                "category": "image_generation",
                "message": f"Image generation failed: {result.get('error', 'Unknown error')}",
                "metadata": {
                    "error": result.get("error", "Unknown error"),
                    "style": style,
                    "aspect_ratio": aspect_ratio,
                    "quality": quality
                }
            }).execute()
            
            raise HTTPException(status_code=500, detail=f"Image generation failed: {result.get('error', 'Unknown error')}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in image generation endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-placeholder")
async def generate_placeholder_image(
    request: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """Generate a placeholder image for testing purposes"""
    try:
        title = request.get("title", "Blog Title")
        style = request.get("style", "photographic")
        
        placeholder_url = image_service.generate_placeholder_image(title, style)
        
        return {
            "success": True,
            "placeholder_url": placeholder_url,
            "title": title,
            "style": style
        }
        
    except Exception as e:
        logger.error(f"Error generating placeholder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate-api-key")
async def validate_fal_api_key(
    request: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """Validate a Fal AI API key"""
    try:
        api_key = request.get("api_key")
        if not api_key:
            raise HTTPException(status_code=400, detail="API key is required")
        
        # Set the API key temporarily for validation
        image_service.set_fal_api_key(api_key)
        
        # Validate the key
        is_valid = await image_service.validate_api_key(api_key)
        
        return {
            "success": True,
            "is_valid": is_valid,
            "message": "API key is valid" if is_valid else "API key is invalid"
        }
        
    except Exception as e:
        logger.error(f"Error validating API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/blog/{blog_id}")
async def get_blog_images(
    blog_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get images for a specific blog"""
    try:
        # Validate blog ownership
        blog_response = supabase_client.table("blogs").select("id, project_id, seo_meta").eq("id", blog_id).execute()
        if not blog_response.data:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        blog_data = blog_response.data[0]
        project_response = supabase_client.table("projects").select("user_id").eq("id", blog_data["project_id"]).execute()
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project_data = project_response.data[0]
        if project_data["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get images from the images table
        images_response = supabase_client.table("images").select("*").eq("blog_id", blog_id).order("image_number").execute()
        
        images = []
        if images_response.data:
            for img in images_response.data:
                images.append({
                    "id": img["id"],
                    "type": "featured" if img["image_number"] == 1 else "additional",
                    "url": img["s3_url"],
                    "alt_text": img["alt_text"],
                    "prompt": img["prompt"],
                    "image_number": img["image_number"],
                    "status": img["status"],
                    "wordpress_media_id": img.get("wordpress_media_id"),
                    "wordpress_media_url": img.get("wordpress_media_url"),
                    "created_at": img["created_at"],
                    "updated_at": img["updated_at"]
                })
        
        return {
            "success": True,
            "blog_id": blog_id,
            "images": images,
            "total_images": len(images),
            "has_featured_image": bool(featured_image)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting blog images: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/blog/{blog_id}/image/{image_index}")
async def delete_blog_image(
    blog_id: str,
    image_index: int,
    current_user: Dict = Depends(get_current_user)
):
    """Delete a specific image from a blog"""
    try:
        # Validate blog ownership
        blog_response = supabase_client.table("blogs").select("id, project_id, seo_meta").eq("id", blog_id).execute()
        if not blog_response.data:
            raise HTTPException(status_code=404, detail="Blog not found")
        
        blog_data = blog_response.data[0]
        project_response = supabase_client.table("projects").select("user_id").eq("id", blog_data["project_id"]).execute()
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project_data = project_response.data[0]
        if project_data["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get current SEO meta
        seo_meta = blog_data.get("seo_meta", {})
        
        if image_index == 0:
            # Delete featured image
            if "featured_image" in seo_meta:
                del seo_meta["featured_image"]
                message = "Featured image deleted"
        else:
            # Delete additional image
            additional_images = seo_meta.get("additional_images", [])
            if 0 <= image_index - 1 < len(additional_images):
                deleted_image = additional_images.pop(image_index - 1)
                message = f"Additional image {image_index} deleted"
            else:
                raise HTTPException(status_code=404, detail="Image not found")
        
        # Update blog
        supabase_client.table("blogs").update({
            "seo_meta": seo_meta,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", blog_id).execute()
        
        # Log the deletion
        supabase_client.table("logs").insert({
            "user_id": current_user["id"],
            "project_id": blog_data["project_id"],
            "blog_id": blog_id,
            "level": "info",
            "category": "image_management",
            "message": message,
            "metadata": {"image_index": image_index}
        }).execute()
        
        return {
            "success": True,
            "message": message,
            "blog_id": blog_id,
            "remaining_images": len(seo_meta.get("featured_image", {})) + len(seo_meta.get("additional_images", []))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting blog image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_image_generation_stats(
    current_user: Dict = Depends(get_current_user)
):
    """Get image generation statistics for the current user"""
    try:
        # Get user's projects
        projects_response = supabase_client.table("projects").select("id, name").eq("user_id", current_user["id"]).execute()
        
        if not projects_response.data:
            return {
                "success": True,
                "stats": {
                    "total_projects": 0,
                    "total_blogs": 0,
                    "total_images": 0,
                    "blogs_with_images": 0,
                    "success_rate": 0.0
                }
            }
        
        project_ids = [p["id"] for p in projects_response.data]
        
        # Get blogs for user's projects
        blogs_response = supabase_client.table("blogs").select("id, project_id, status").in_("project_id", project_ids).execute()
        
        # Get images for user's blogs
        blog_ids = [b["id"] for b in blogs_response.data] if blogs_response.data else []
        
        if blog_ids:
            images_response = supabase_client.table("images").select("id, blog_id, status").in_("blog_id", blog_ids).execute()
        else:
            images_response = {"data": []}
        
        # Calculate statistics
        total_projects = len(projects_response.data)
        total_blogs = len(blogs_response.data) if blogs_response.data else 0
        total_images = len(images_response.data) if images_response.data else 0
        
        # Count blogs with images
        blogs_with_images = len(set(img["blog_id"] for img in images_response.data)) if images_response.data else 0
        
        # Calculate success rate
        successful_images = len([img for img in images_response.data if img.get("status") == "generated"]) if images_response.data else 0
        success_rate = (successful_images / total_images * 100) if total_images > 0 else 0.0
        
        # Get recent image generation activity
        recent_images = []
        if images_response.data:
            recent_images_response = supabase_client.table("images").select("id, blog_id, created_at, status").in_("blog_id", blog_ids).order("created_at", desc=True).limit(5).execute()
            if recent_images_response.data:
                recent_images = [
                    {
                        "id": img["id"],
                        "blog_id": img["blog_id"],
                        "created_at": img["created_at"],
                        "status": img["status"]
                    }
                    for img in recent_images_response.data
                ]
        
        return {
            "success": True,
            "stats": {
                "total_projects": total_projects,
                "total_blogs": total_blogs,
                "total_images": total_images,
                "blogs_with_images": blogs_with_images,
                "success_rate": round(success_rate, 2),
                "recent_activity": recent_images
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting image generation stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
