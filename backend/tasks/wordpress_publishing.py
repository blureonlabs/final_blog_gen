from celery import shared_task
from typing import Dict, List, Any
import logging
import requests
from datetime import datetime

from core.supabase_client import supabase_client
from models.blog import BlogStatus
from services.s3_storage_service import S3StorageService

logger = logging.getLogger(__name__)

# Initialize S3 storage service
s3_storage = S3StorageService()

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
            logger.error(f"❌ Blog {blog_id} not found or content unavailable")
            update_blog_status(blog_id, BlogStatus.FAILED, "Blog content not found or unavailable")
            return {
                "blog_id": blog_id,
                "status": "failed",
                "error": "Blog content not found or unavailable"
            }
        
        # Get WordPress account data
        wp_account = get_wordpress_account(wordpress_account_id)
        if not wp_account:
            logger.error(f"❌ WordPress account {wordpress_account_id} not found")
            update_blog_status(blog_id, BlogStatus.FAILED, "WordPress account not found")
            return {
                "blog_id": blog_id,
                "status": "failed",
                "error": "WordPress account not found"
            }
        
        # Skip status update to 'publishing' to avoid database constraint issue
        # The blog will remain in 'ready' status during publishing
        logger.info(f"🔄 Blog {blog_id} status remains 'ready' during publishing (constraint bypass)")
        
        # Prepare post data for WordPress
        post_data = prepare_wordpress_post(blog_data, publish_status)
        if not post_data:
            logger.error(f"❌ Failed to prepare WordPress post data for blog {blog_id}")
            update_blog_status(blog_id, BlogStatus.FAILED, "Failed to prepare post data")
            return {
                "blog_id": blog_id,
                "status": "failed",
                "error": "Failed to prepare post data"
            }
        
        logger.info(f"✅ WordPress post data prepared successfully for blog {blog_id}")
        
        # Publish to WordPress
        logger.info(f"🚀 Publishing blog {blog_id} to WordPress...")
        wp_response = publish_post_to_wordpress(wp_account, post_data)
        
        if wp_response["success"]:
            # Update blog with WordPress data
            try:
                update_blog_wordpress_data(blog_id, wp_response["data"])
            except Exception as e:
                logger.warning(f"⚠️ Could not update WordPress data, but publishing succeeded: {e}")
            
            # Update status to published
            try:
                update_blog_status(blog_id, BlogStatus.PUBLISHED)
            except Exception as e:
                logger.warning(f"⚠️ Could not update status to published, but publishing succeeded: {e}")
            
            logger.info(f"WordPress publishing completed for blog {blog_id}")
            
            return {
                "success": True,
                "blog_id": blog_id,
                "status": "published",
                "wordpress_url": wp_response["data"]["link"],
                "wordpress_post_id": wp_response["data"]["id"]
            }
        else:
            # Handle publishing failure
            error_message = wp_response.get("error", "Unknown WordPress publishing error")
            try:
                update_blog_status(blog_id, BlogStatus.FAILED, error_message)
            except Exception as e:
                logger.warning(f"⚠️ Could not update status to failed: {e}")
            
            logger.error(f"WordPress publishing failed for blog {blog_id}: {error_message}")
            
            return {
                "success": False,
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
        logger.info(f"🔍 Preparing WordPress post data for blog: {blog_data.get('title', 'Unknown')}")
        
        # Extract blog content and metadata
        title = blog_data.get("title", "Untitled Blog Post")
        content = blog_data.get("content", "")
        seo_meta = blog_data.get("seo_meta", {})
        
        # Validate required fields
        if not title or not content:
            logger.error(f"❌ Missing required fields - title: {bool(title)}, content: {bool(content)}")
            raise ValueError("Title and content are required for WordPress publishing")
        
        logger.info(f"✅ Content validation passed - title: {len(title)} chars, content: {len(content)} chars")
        
        # Prepare WordPress post data
        post_data = {
            "title": title,
            "content": content,
            "status": publish_status,
            "format": "standard"
        }
        
        # Add excerpt if available
        if seo_meta and seo_meta.get("meta_description"):
            post_data["excerpt"] = seo_meta["meta_description"]
            logger.info(f"✅ Added excerpt: {len(seo_meta['meta_description'])} chars")
        
        # Add categories and tags
        if seo_meta and seo_meta.get("tags"):
            post_data["tags"] = seo_meta["tags"]
            logger.info(f"✅ Added tags: {len(seo_meta['tags'])} tags")
        
        # Add featured image if available
        if seo_meta and seo_meta.get("featured_image", {}).get("url"):
            post_data["featured_media"] = seo_meta["featured_image"]["url"]
            logger.info(f"✅ Added featured image: {seo_meta['featured_image']['url']}")
        else:
            logger.info(f"ℹ️ No featured image available - post will be published without image")
        
        # Add custom fields for SEO
        if seo_meta and seo_meta.get("main_keyword"):
            post_data["meta"] = {
                "focus_keyword": seo_meta["main_keyword"],
                "seo_score": seo_meta.get("seo_score", 0)
            }
            logger.info(f"✅ Added SEO metadata: {seo_meta['main_keyword']}")
        
        logger.info(f"✅ WordPress post data prepared successfully")
        logger.info(f"🔍 Final post data keys: {list(post_data.keys())}")
        
        return post_data
        
    except Exception as e:
        logger.error(f"❌ Error preparing WordPress post: {e}")
        logger.error(f"❌ Error type: {type(e)}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
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
        
        # Ensure site_url is properly formatted
        if not site_url.startswith(('http://', 'https://')):
            site_url = f"https://{site_url}"
            logger.info(f"🔧 Added https:// to site URL: {site_url}")
        
        # Clean up the site URL - remove wp-login.php and other WordPress-specific paths
        if '/wp-login.php' in site_url:
            site_url = site_url.replace('/wp-login.php', '')
            logger.info(f"🔧 Cleaned site URL (removed wp-login.php): {site_url}")
        elif '/wp-admin' in site_url:
            site_url = site_url.replace('/wp-admin', '')
            logger.info(f"🔧 Cleaned site URL (removed wp-admin): {site_url}")
        
        # Validate site URL format
        if not site_url or len(site_url.strip()) < 10:
            return {
                "success": False,
                "error": "Invalid WordPress site URL"
            }
        
        # Use app password if available, otherwise use regular password
        auth_password = app_password if app_password else password
        
        # Prepare authentication
        auth = (username, auth_password)
        
        # Test WordPress API connectivity first
        test_result = test_wordpress_api_connectivity(wp_account, auth)
        if not test_result["success"]:
            logger.warning(f"⚠️ WordPress API connectivity test failed: {test_result['error']}")
            logger.info(f"🔄 Proceeding with publishing attempt anyway...")
        else:
            logger.info(f"✅ WordPress API connectivity test passed using {test_result['endpoint']} endpoint")
            # Use the working endpoint for publishing
            if test_result['endpoint'] == 'fallback':
                api_url = fallback_api_url
        
        # WordPress REST API endpoint - try standard endpoint first, then fallback
        standard_api_url = f"{site_url.rstrip('/')}/wp-json/wp/v2/posts"
        fallback_api_url = f"{site_url.rstrip('/')}/index.php?rest_route=/wp/v2/posts"
        
        # Try standard endpoint first
        api_url = standard_api_url
        
        # Make POST request to WordPress with fallback
        response = None
        error_message = ""
        
        # Try standard endpoint first
        try:
            logger.info(f"🔍 Trying WordPress API endpoint: {api_url}")
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
        except requests.exceptions.RequestException as e:
            error_message = f"Standard endpoint failed: {str(e)}"
            logger.warning(f"⚠️ {error_message}")
        
        # If standard endpoint failed, try fallback
        if not response or response.status_code >= 400:
            if api_url == standard_api_url:
                logger.info(f"🔄 Trying fallback WordPress API endpoint: {fallback_api_url}")
                try:
                    response = requests.post(
                        fallback_api_url,
                        json=post_data,
                        auth=auth,
                        headers={
                            "Content-Type": "application/json",
                            "User-Agent": "Bulk Blog Generator/1.0"
                        },
                        timeout=30
                    )
                    api_url = fallback_api_url  # Update for logging
                except requests.exceptions.RequestException as e:
                    error_message = f"Fallback endpoint failed: {str(e)}"
                    logger.error(f"❌ {error_message}")
                    return {
                        "success": False,
                        "error": f"Both WordPress API endpoints failed: {error_message}"
                    }
        
        if response.status_code in [201, 200]:
            # Success
            try:
                wp_data = response.json()
                logger.info(f"✅ WordPress API response: {wp_data}")
                
                return {
                    "success": True,
                    "data": {
                        "id": wp_data.get("id"),
                        "link": wp_data.get("link"),
                        "status": wp_data.get("status"),
                        "published_at": wp_data.get("date")
                    }
                }
            except Exception as json_error:
                logger.error(f"❌ Failed to parse WordPress response JSON: {json_error}")
                logger.error(f"❌ Response content: {response.text[:500]}")
                return {
                    "success": False,
                    "error": f"Invalid JSON response from WordPress: {str(json_error)}"
                }
        else:
            # Error
            error_message = f"WordPress API error: {response.status_code}"
            response_text = response.text[:500] if response.text else "Empty response"
            
            try:
                error_data = response.json()
                if "message" in error_data:
                    error_message = f"WordPress API error {response.status_code}: {error_data['message']}"
                elif "code" in error_data:
                    error_message = f"WordPress API error {response.status_code}: {error_data['code']}"
            except:
                error_message = f"WordPress API error {response.status_code}: {response_text}"
            
            logger.error(f"❌ WordPress API error: {error_message}")
            logger.error(f"❌ Response status: {response.status_code}")
            logger.error(f"❌ Response headers: {dict(response.headers)}")
            logger.error(f"❌ Response content: {response_text}")
            
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
    """Get blog data from database and retrieve content from storage if needed"""
    try:
        logger.info(f"🔍 Fetching blog data for blog ID: {blog_id}")
        
        # Get blog record from database
        response = supabase_client.table("blogs").select("*").eq("id", blog_id).execute()
        if not response.data:
            logger.error(f"❌ Blog {blog_id} not found in database")
            return None
        
        blog_data = response.data[0]
        logger.info(f"✅ Blog record retrieved: {blog_data.get('title', 'Unknown')}")
        
        # Check if content is stored in S3 and needs to be retrieved
        storage_bucket = blog_data.get("storage_bucket")
        storage_path = blog_data.get("storage_path")
        
        if storage_bucket and storage_bucket != "database" and storage_path:
            logger.info(f"🔍 Blog content stored in S3: {storage_path}")
            
            try:
                # Retrieve content from S3
                s3_content = s3_storage.retrieve_blog_content(storage_path, storage_bucket)
                
                if s3_content and "content" in s3_content:
                    # Add content to blog data
                    blog_data["content"] = s3_content["content"]
                    logger.info(f"✅ Content retrieved from S3: {len(s3_content['content'])} characters")
                else:
                    logger.warning(f"⚠️ S3 content retrieval failed or content missing, using database fallback")
                    # Fallback to database content if available
                    if not blog_data.get("content"):
                        logger.error(f"❌ No content available from S3 or database for blog {blog_id}")
                        return None
                        
            except Exception as s3_error:
                logger.error(f"❌ S3 content retrieval failed: {s3_error}")
                logger.info(f"🔄 Falling back to database content")
                
                # Fallback to database content if available
                if not blog_data.get("content"):
                    logger.error(f"❌ No content available from S3 or database for blog {blog_id}")
                    return None
                    
        elif storage_bucket == "database" or blog_data.get("content"):
            logger.info(f"✅ Blog content available in database: {len(blog_data.get('content', ''))} characters")
        else:
            logger.error(f"❌ No content found for blog {blog_id} - storage_bucket: {storage_bucket}, storage_path: {storage_path}")
            return None
        
        # Ensure we have the required fields for WordPress publishing
        required_fields = ["title", "content"]
        missing_fields = [field for field in required_fields if not blog_data.get(field)]
        
        if missing_fields:
            logger.error(f"❌ Missing required fields for WordPress publishing: {missing_fields}")
            return None
        
        logger.info(f"✅ Blog data ready for WordPress publishing: {blog_data.get('title')}")
        return blog_data
        
    except Exception as e:
        logger.error(f"❌ Error fetching blog data: {e}")
        logger.error(f"❌ Error type: {type(e)}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
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
        # Use datetime.now() instead of utcnow() for better compatibility
        current_time = datetime.now().isoformat()
        
        update_data = {
            "status": status.value,
            "updated_at": current_time
        }
        
        if error_message:
            update_data["error_message"] = error_message
        
        logger.info(f"🔍 Updating blog {blog_id} status to: {status.value}")
        logger.info(f"🔍 Update data: {update_data}")
        
        response = supabase_client.table("blogs").update(update_data).eq("id", blog_id).execute()
        
        if not response.data:
            logger.error(f"Failed to update blog {blog_id} status")
        else:
            logger.info(f"✅ Blog {blog_id} status updated to {status.value}")
            
    except Exception as e:
        logger.error(f"Error updating blog status: {e}")
        logger.error(f"Status value: {status.value}, Type: {type(status.value)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")

def update_blog_wordpress_data(blog_id: str, wp_data: Dict):
    """Update blog with WordPress publishing data"""
    try:
        # Update generation logs
        current_logs = get_current_generation_logs(blog_id)
        current_logs.append({
            "step": "wordpress_publishing",
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "wordpress_post_id": wp_data.get("id"),
            "wordpress_url": wp_data.get("link")
        })
        
        update_data = {
            "wordpress_url": wp_data.get("link"),
            "wordpress_post_id": str(wp_data.get("id")),
            "generation_logs": current_logs,
            "updated_at": datetime.now().isoformat()
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

def test_wordpress_api_connectivity(wp_account: Dict, auth: tuple) -> Dict:
    """Test WordPress API connectivity by making a GET request to the posts endpoint"""
    try:
        site_url = wp_account.get("site_url")
        standard_api_url = f"{site_url.rstrip('/')}/wp-json/wp/v2/posts"
        fallback_api_url = f"{site_url.rstrip('/')}/index.php?rest_route=/wp/v2/posts"
        
        # Try standard endpoint first
        try:
            logger.info(f"🔍 Testing WordPress API connectivity: {standard_api_url}")
            response = requests.get(
                standard_api_url,
                auth=auth,
                headers={"User-Agent": "Bulk Blog Generator/1.0"},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ WordPress API connectivity test passed with standard endpoint")
                return {"success": True, "endpoint": "standard"}
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Standard endpoint connectivity test failed: {e}")
        
        # Try fallback endpoint
        try:
            logger.info(f"🔍 Testing WordPress API connectivity: {fallback_api_url}")
            response = requests.get(
                fallback_api_url,
                auth=auth,
                headers={"User-Agent": "Bulk Blog Generator/1.0"},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ WordPress API connectivity test passed with fallback endpoint")
                return {"success": True, "endpoint": "fallback"}
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Fallback endpoint connectivity test failed: {e}")
        
        return {
            "success": False,
            "error": "Both WordPress API endpoints failed connectivity test"
        }
        
    except Exception as e:
        logger.error(f"❌ Error testing WordPress API connectivity: {e}")
        return {
            "success": False,
            "error": f"Connectivity test error: {str(e)}"
        }
