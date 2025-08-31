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
async def publish_to_wordpress_task(self, blog_id: str, wordpress_account_id: str, 
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
        post_data = await prepare_wordpress_post(blog_data, publish_status)
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
            
            # Update publishing status using the new is_published column
            try:
                # Keep status as 'ready' for generation workflow, but mark as published
                update_blog_publishing_status(blog_id, True)
                
                # Get project_id from blog to update project status
                try:
                    blog_response = supabase_client.table("blogs").select("project_id").eq("id", blog_id).execute()
                    if blog_response.data and blog_response.data[0].get("project_id"):
                        project_id = blog_response.data[0]["project_id"]
                        # Check and update project status based on publishing progress
                        check_and_update_project_status(project_id)
                except Exception as project_status_error:
                    logger.warning(f"⚠️ Could not update project status: {project_status_error}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Could not update publishing status, but publishing succeeded: {e}")
            
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

async def prepare_wordpress_post(blog_data: Dict, publish_status: str) -> Dict:
    """Prepare blog data for WordPress API"""
    try:
        logger.info(f"🔍 Preparing WordPress post data for blog: {blog_data.get('title', 'Unknown')}")
        
        # Extract blog content and metadata
        title = blog_data.get("title", "Untitled Blog Post")
        content = blog_data.get("content", "")
        seo_meta = blog_data.get("seo_meta", {})
        blog_id = blog_data.get("id")
        
        # Validate required fields
        if not title or not content:
            logger.error(f"❌ Missing required fields - title: {bool(title)}, content: {bool(content)}")
            raise ValueError("Title and content are required for WordPress publishing")
        
        logger.info(f"✅ Content validation passed - title: {len(title)} chars, content: {len(content)} chars")
        
        # Replace image placeholders with WordPress URLs if available
        # Skip if we're already using stored processed content
        if blog_id and blog_data.get("content_source") != "stored_processed":
            try:
                from services.image_placeholder_processor import ImagePlaceholderProcessor
                
                image_processor = ImagePlaceholderProcessor()
                wordpress_urls = await image_processor.get_wordpress_image_urls_for_blog(blog_id)
                
                if wordpress_urls:
                    logger.info(f"🖼️ Found {len(wordpress_urls)} WordPress images, replacing placeholders in content")
                    original_content = content
                    content = image_processor.replace_placeholders_with_wordpress_urls(content, wordpress_urls)
                    
                    if content != original_content:
                        logger.info(f"✅ Successfully replaced image placeholders in content")
                        logger.info(f"📊 Content length changed from {len(original_content)} to {len(content)} characters")
                        
                        # Store the processed content in processed_content column for future use
                        try:
                            await store_processed_content(blog_id, content, original_content)
                            logger.info(f"💾 Stored processed content for future use")
                            
                            # Add a log entry to generation_logs to track the processing
                            try:
                                current_logs = get_current_generation_logs(blog_id)
                                current_logs.append({
                                    "step": "content_processing",
                                    "timestamp": datetime.now().isoformat(),
                                    "status": "success",
                                    "action": "image_placeholder_replacement",
                                    "content_modified": True,
                                    "images_replaced": True,
                                    "processing_summary": f"Processed content: {len(original_content)} → {len(content)} characters"
                                })
                                
                                # Update generation_logs
                                supabase_client.table("blogs").update({
                                    "generation_logs": current_logs
                                }).eq("id", blog_id).execute()
                                
                                logger.info(f"📝 Added processing log entry to generation_logs")
                            except Exception as log_error:
                                logger.warning(f"⚠️ Could not add processing log entry: {log_error}")
                                
                        except Exception as store_error:
                            logger.warning(f"⚠️ Could not store processed content: {store_error}")
                    else:
                        logger.info(f"ℹ️ No image placeholders found in content or no replacements made")
                else:
                    logger.info(f"ℹ️ No WordPress images found for blog {blog_id}, content will be published as-is")
                    
            except Exception as e:
                logger.warning(f"⚠️ Could not process image placeholders: {e}, content will be published as-is")
        elif blog_data.get("content_source") == "stored_processed":
            logger.info(f"🖼️ Using stored processed content - skipping image replacement")
        else:
            logger.info(f"ℹ️ No blog_id available - skipping image processing")
        
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
        
        # WordPress REST API endpoint - try standard endpoint first, then fallback
        standard_api_url = f"{site_url.rstrip('/')}/wp-json/wp/v2/posts"
        fallback_api_url = f"{site_url.rstrip('/')}/index.php?rest_route=/wp/v2/posts"
        
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
        
        # Check if we have stored processed content (with images already replaced)
        stored_processed_content = get_stored_processed_content(blog_id)
        if stored_processed_content:
            logger.info(f"🖼️ Using stored processed content (with images already replaced)")
            blog_data["content"] = stored_processed_content
            blog_data["content_source"] = "stored_processed"
        else:
            logger.info(f"📝 Using original content (images will be replaced during publishing)")
            blog_data["content_source"] = "original"
        
        # Ensure we have the required fields for WordPress publishing
        required_fields = ["title", "content"]
        missing_fields = [field for field in required_fields if not blog_data.get(field)]
        
        if missing_fields:
            logger.error(f"❌ Missing required fields for WordPress publishing: {missing_fields}")
            return None
        
        logger.info(f"✅ Blog data ready for WordPress publishing: {blog_data.get('title')}")
        logger.info(f"📊 Content processing status: {blog_data.get('content_source')}, Length: {len(blog_data.get('content', ''))} characters")
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

def update_blog_publishing_status(blog_id: str, is_published: bool):
    """Update blog publishing status using the new is_published column"""
    try:
        logger.info(f"🔄 Updating blog {blog_id} publishing status to: {is_published}")
        update_data = {
            "is_published": is_published,
            "updated_at": datetime.now().isoformat()
        }
        
        logger.info(f"📝 Update data: {update_data}")
        response = supabase_client.table("blogs").update(update_data).eq("id", blog_id).execute()
        
        if response.data:
            logger.info(f"✅ Successfully updated blog {blog_id} publishing status to {is_published}")
            logger.info(f"📊 Response data: {response.data}")
        else:
            logger.error(f"❌ Failed to update blog {blog_id} publishing status - no response data")
            
    except Exception as e:
        logger.error(f"❌ Error updating blog publishing status: {e}")
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

async def store_processed_content(blog_id: str, processed_content: str, original_content: str):
    """Store processed content in processed_content column for future use"""
    try:
        logger.info(f"💾 Storing processed content for blog {blog_id}")
        
        # Update the blog record with processed content
        update_data = {
            "processed_content": processed_content,
            "updated_at": datetime.now().isoformat()
        }
        
        response = supabase_client.table("blogs").update(update_data).eq("id", blog_id).execute()
        
        if response.data:
            logger.info(f"✅ Processed content stored successfully for blog {blog_id}")
        else:
            logger.error(f"❌ Failed to store processed content for blog {blog_id}")
            
    except Exception as e:
        logger.error(f"❌ Error storing processed content: {e}")
        raise

def get_stored_processed_content(blog_id: str) -> str:
    """Get stored processed content from processed_content column if available"""
    try:
        response = supabase_client.table("blogs").select("processed_content").eq("id", blog_id).execute()
        if response.data and response.data[0].get("processed_content"):
            processed_content = response.data[0]["processed_content"]
            logger.info(f"✅ Found stored processed content for blog {blog_id}")
            return processed_content
        
        logger.info(f"ℹ️ No stored processed content found for blog {blog_id}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error retrieving stored processed content: {e}")
        return None

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
                
                if blog_result and blog_result.get("success") == True:
                    blogs_published += 1
                else:
                    blogs_failed += 1
                    
            except Exception as e:
                logger.error(f"Error publishing blog {blog['id']}: {e}")
                blogs_failed += 1
        
        logger.info(f"Bulk WordPress publishing completed: {blogs_published} published, {blogs_failed} failed")
        
        # Check and update project status after bulk publishing
        try:
            check_and_update_project_status(project_id)
        except Exception as project_status_error:
            logger.warning(f"⚠️ Could not update project status after bulk publishing: {project_status_error}")
        
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

def check_and_update_project_status(project_id: str):
    """Check project status based on blog generation and publishing progress and update accordingly"""
    try:
        logger.info(f"🔍 Checking project status for project {project_id}")
        
        # Get project details
        project_response = supabase_client.table("projects").select("num_blogs, completed_blogs, status").eq("id", project_id).execute()
        if not project_response.data:
            logger.warning(f"⚠️ Project {project_id} not found")
            return
        
        project = project_response.data[0]
        num_blogs = project.get("num_blogs", 0)
        completed_blogs = project.get("completed_blogs", 0)
        current_status = project.get("status", "unknown")
        
        # Count blogs by status in database
        blogs_response = supabase_client.table("blogs").select("id, status, is_published").eq("project_id", project_id).execute()
        total_blogs_in_db = len(blogs_response.data) if blogs_response.data else 0
        
        # Count blogs by status using the new is_published column
        published_blogs = 0
        generated_blogs = 0
        
        if blogs_response.data:
            for blog in blogs_response.data:
                blog_status = blog.get("status", "unknown")
                is_published = blog.get("is_published", False)
                
                if blog_status in ["completed", "ready"]:
                    generated_blogs += 1
                    if is_published:
                        published_blogs += 1
                elif blog_status in ["generating", "draft"]:
                    generated_blogs += 1
        
        logger.info(f"📊 Project {project_id}: {generated_blogs}/{num_blogs} blogs generated, {published_blogs} published, current status: {current_status}")
        
        # Determine correct status based on blog generation and publishing progress
        new_status = None
        status_reason = ""
        
        if num_blogs == 0:
            new_status = "ready"
            status_reason = "No blogs requested"
        elif generated_blogs >= num_blogs and published_blogs >= num_blogs:
            new_status = "completed"
            status_reason = f"All {generated_blogs}/{num_blogs} blogs generated and published"
        elif generated_blogs >= num_blogs:
            new_status = "partial"
            status_reason = f"All {generated_blogs}/{num_blogs} blogs generated but only {published_blogs} published"
        elif generated_blogs > 0:
            # Check if any blogs are currently being generated
            any_generating = False
            if blogs_response.data:
                for blog in blogs_response.data:
                    if blog.get("status") == "generating":
                        any_generating = True
                        break
            
            if any_generating:
                new_status = "in_progress"
                status_reason = f"{generated_blogs}/{num_blogs} blogs generated, some currently generating"
            else:
                new_status = "partial"
                status_reason = f"{generated_blogs}/{num_blogs} blogs generated"
        else:
            # Check if project was ever started (has blogs with failed status or was in progress)
            failed_blogs = 0
            if blogs_response.data:
                for blog in blogs_response.data:
                    if blog.get("status") == "failed":
                        failed_blogs += 1
            
            # If there are failed blogs or current status indicates it was started, mark as failed
            if failed_blogs > 0 or current_status in ["in_progress", "failed"]:
                new_status = "failed"
                status_reason = f"No blogs generated - generation failed ({failed_blogs} failed attempts)"
            else:
                new_status = "ready"
                status_reason = "No blogs generated - project not yet started"
        
        # Update project if status needs to change
        if new_status != current_status:
            try:
                # Update both status and completed_blogs count
                update_data = {
                    "status": new_status,
                    "completed_blogs": generated_blogs,
                    "updated_at": datetime.now().isoformat()
                }
                
                supabase_client.table("projects").update(update_data).eq("id", project_id).execute()
                logger.info(f"🎯 Project {project_id} status updated: {current_status} → {new_status} - {status_reason}")
            except Exception as e:
                logger.error(f"❌ Failed to update project status: {e}")
        else:
            logger.info(f"ℹ️ Project {project_id} status already correct: {current_status}")
            
            # Still update completed_blogs count if it's wrong
            if completed_blogs != generated_blogs:
                try:
                    supabase_client.table("projects").update({
                        "completed_blogs": generated_blogs,
                        "updated_at": datetime.now().isoformat()
                    }).eq("id", project_id).execute()
                    logger.info(f"📊 Project {project_id} completed_blogs count updated: {completed_blogs} → {generated_blogs}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not update completed_blogs count: {e}")
                
    except Exception as e:
        logger.error(f"❌ Error checking/updating project status for {project_id}: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
