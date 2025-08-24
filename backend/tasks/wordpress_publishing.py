from celery import shared_task
from typing import Dict, List, Any
import logging
import requests
from datetime import datetime

from core.supabase_client import supabase_client
from models.blog import BlogStatus

logger = logging.getLogger(__name__)

@shared_task(bind=True, name="publish_to_wordpress")
def publish_to_wordpress_task(self, blog_id: str, wordpress_account_id: str, 
                             publish_status: str = "draft"):
    """
    Publish blog to WordPress
    
    Args:
        blog_id: Blog UUID as string
        wordpress_account_id: WordPress account UUID as string
        publish_status: Publish status (draft or publish)
    """
    try:
        logger.info(f"Starting WordPress publishing for blog {blog_id}")
        
        # Get blog data
        blog_data = get_blog_data(blog_id)
        if not blog_data:
            logger.error(f"Blog {blog_id} not found")
            return
        
        # Get WordPress account data
        wp_account = get_wordpress_account(wordpress_account_id)
        if not wp_account:
            logger.error(f"WordPress account {wordpress_account_id} not found")
            return
        
        # Update status to publishing
        update_blog_status(blog_id, BlogStatus.PUBLISHING)
        
        # Prepare post data for WordPress
        post_data = prepare_wordpress_post(blog_data, publish_status)
        
        # Publish to WordPress
        wp_response = publish_post_to_wordpress(wp_account, post_data)
        
        if wp_response["success"]:
            # Update blog with WordPress data
            update_blog_wordpress_data(blog_id, wp_response["data"])
            
            # Update status to published
            update_blog_status(blog_id, BlogStatus.PUBLISHED)
            
            logger.info(f"WordPress publishing completed for blog {blog_id}")
            
            return {
                "blog_id": blog_id,
                "status": "published",
                "wordpress_url": wp_response["data"]["link"],
                "wordpress_post_id": wp_response["data"]["id"]
            }
        else:
            # Handle publishing failure
            error_message = wp_response.get("error", "Unknown WordPress publishing error")
            update_blog_status(blog_id, BlogStatus.FAILED, error_message)
            
            logger.error(f"WordPress publishing failed for blog {blog_id}: {error_message}")
            
            return {
                "blog_id": blog_id,
                "status": "failed",
                "error": error_message
            }
        
    except Exception as e:
        logger.error(f"Error in WordPress publishing for blog {blog_id}: {e}")
        update_blog_status(blog_id, BlogStatus.FAILED, str(e))
        raise

def prepare_wordpress_post(blog_data: Dict, publish_status: str) -> Dict:
    """Prepare blog data for WordPress API"""
    try:
        # Extract blog content and metadata
        title = blog_data.get("title", "Untitled Blog Post")
        content = blog_data.get("content", "")
        seo_meta = blog_data.get("seo_meta", {})
        
        # Prepare WordPress post data
        post_data = {
            "title": title,
            "content": content,
            "status": publish_status,
            "format": "standard"
        }
        
        # Add excerpt if available
        if seo_meta.get("meta_description"):
            post_data["excerpt"] = seo_meta["meta_description"]
        
        # Add categories and tags
        if seo_meta.get("tags"):
            post_data["tags"] = seo_meta["tags"]
        
        # Add featured image if available
        if seo_meta.get("featured_image", {}).get("url"):
            post_data["featured_media"] = seo_meta["featured_image"]["url"]
        
        # Add custom fields for SEO
        if seo_meta.get("main_keyword"):
            post_data["meta"] = {
                "focus_keyword": seo_meta["main_keyword"],
                "seo_score": seo_meta.get("seo_score", 0)
            }
        
        return post_data
        
    except Exception as e:
        logger.error(f"Error preparing WordPress post: {e}")
        return {}

def publish_post_to_wordpress(wp_account: Dict, post_data: Dict) -> Dict:
    """Publish post to WordPress using REST API"""
    try:
        # Extract WordPress credentials
        site_url = wp_account.get("site_url")
        username = wp_account.get("username")
        password = wp_account.get("password")
        app_password = wp_account.get("app_password")
        
        if not all([site_url, username, password]):
            return {
                "success": False,
                "error": "Missing WordPress credentials"
            }
        
        # Use app password if available, otherwise use regular password
        auth_password = app_password if app_password else password
        
        # Prepare authentication
        auth = (username, auth_password)
        
        # WordPress REST API endpoint
        api_url = f"{site_url.rstrip('/')}/wp-json/wp/v2/posts"
        
        # Make POST request to WordPress
        response = requests.post(
            api_url,
            json=post_data,
            auth=auth,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Bulk Blog Generator/1.0"
            },
            timeout=30
        )
        
        if response.status_code in [201, 200]:
            # Success
            wp_data = response.json()
            
            return {
                "success": True,
                "data": {
                    "id": wp_data.get("id"),
                    "link": wp_data.get("link"),
                    "status": wp_data.get("status"),
                    "published_at": wp_data.get("date")
                }
            }
        else:
            # Error
            error_message = f"WordPress API error: {response.status_code}"
            try:
                error_data = response.json()
                if "message" in error_data:
                    error_message = error_data["message"]
            except:
                pass
            
            return {
                "success": False,
                "error": error_message
            }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"WordPress API request error: {e}")
        return {
            "success": False,
            "error": f"Network error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error publishing to WordPress: {e}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }

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

def get_wordpress_account(wordpress_account_id: str) -> Dict[str, Any]:
    """Get WordPress account data from database"""
    try:
        response = supabase_client.table("wordpress_accounts").select("*").eq("id", wordpress_account_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Error fetching WordPress account: {e}")
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

def update_blog_wordpress_data(blog_id: str, wp_data: Dict):
    """Update blog with WordPress publishing data"""
    try:
        # Update generation logs
        current_logs = get_current_generation_logs(blog_id)
        current_logs.append({
            "step": "wordpress_publishing",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
            "wordpress_post_id": wp_data.get("id"),
            "wordpress_url": wp_data.get("link")
        })
        
        update_data = {
            "wordpress_url": wp_data.get("link"),
            "wordpress_post_id": str(wp_data.get("id")),
            "generation_logs": current_logs,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        response = supabase_client.table("blogs").update(update_data).eq("id", blog_id).execute()
        
        if not response.data:
            logger.error(f"Failed to update blog {blog_id} WordPress data")
            
    except Exception as e:
        logger.error(f"Error updating blog WordPress data: {e}")

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

@shared_task(bind=True, name="bulk_publish_to_wordpress")
def bulk_publish_to_wordpress_task(self, project_id: str, wordpress_account_id: str, 
                                  publish_status: str = "draft"):
    """
    Bulk publish all ready blogs from a project to WordPress
    
    Args:
        project_id: Project UUID as string
        wordpress_account_id: WordPress account UUID as string
        publish_status: Publish status (draft or publish)
    """
    try:
        logger.info(f"Starting bulk WordPress publishing for project {project_id}")
        
        # Get all ready blogs from the project
        ready_blogs = get_ready_blogs_from_project(project_id)
        
        if not ready_blogs:
            logger.info(f"No ready blogs found for project {project_id}")
            return {
                "project_id": project_id,
                "blogs_published": 0,
                "blogs_failed": 0,
                "message": "No ready blogs to publish"
            }
        
        # Publish each blog
        blogs_published = 0
        blogs_failed = 0
        
        for blog in ready_blogs:
            try:
                # Publish individual blog
                result = publish_to_wordpress_task.delay(
                    blog["id"], 
                    wordpress_account_id, 
                    publish_status
                )
                
                # Wait for result (in production, you might want to handle this asynchronously)
                blog_result = result.get(timeout=60)
                
                if blog_result and blog_result.get("status") == "published":
                    blogs_published += 1
                else:
                    blogs_failed += 1
                    
            except Exception as e:
                logger.error(f"Error publishing blog {blog['id']}: {e}")
                blogs_failed += 1
        
        logger.info(f"Bulk WordPress publishing completed: {blogs_published} published, {blogs_failed} failed")
        
        return {
            "project_id": project_id,
            "blogs_published": blogs_published,
            "blogs_failed": blogs_failed,
            "total_blogs": len(ready_blogs)
        }
        
    except Exception as e:
        logger.error(f"Error in bulk WordPress publishing: {e}")
        raise

def get_ready_blogs_from_project(project_id: str) -> List[Dict]:
    """Get all blogs with 'ready' status from a project"""
    try:
        response = supabase_client.table("blogs").select("*").eq("project_id", project_id).eq("status", "ready").execute()
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Error fetching ready blogs: {e}")
        return []
