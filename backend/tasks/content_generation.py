import asyncio
import logging
from typing import List, Dict, Any
from uuid import uuid4
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from core.ai_client import ai_client
from core.supabase_client import supabase_client
from models.blog import BlogStatus
from lib.text_cleaner import TextCleaner

logger = logging.getLogger(__name__)

async def generate_blogs_task(
    project_id: str,
    prompt: str,
    num_blogs: int,
    ai_model: str = "openai",
    ai_model_version: str = None,
    user_id: str = None,
    batch_size: int = 5
):
    """
    Main task for generating multiple blogs
    
    This function:
    1. Generates blogs in batches to avoid overwhelming the AI APIs
    2. Stores each generated blog in the database
    3. Updates project status and logs progress
    4. Handles errors gracefully and continues with remaining blogs
    """
    supabase = supabase_client
    
    try:
        logger.info(f"Starting blog generation for project {project_id}: {num_blogs} blogs using {ai_model}")
        
        # Update project status to in_progress
        await supabase.table("projects").update({
            "status": "in_progress",
            "updated_at": "now()"
        }).eq("id", project_id).execute()
        
        # Log start of generation
        await supabase.table("activity_logs").insert({
            "user_id": user_id,
            "action": f"Started generating {num_blogs} blogs using {ai_model}",
            "level": "info",
            "category": "generation",
            "timestamp": "now()",
            "metadata": {
                "details": {
                    "project_id": project_id,
                    "ai_model": ai_model,
                    "num_blogs": num_blogs
                }
            }
        }).execute()
        
        # Generate blogs in batches
        blogs_generated = 0
        failed_blogs = 0
        
        for batch_start in range(0, num_blogs, batch_size):
            batch_end = min(batch_start + batch_size, num_blogs)
            batch_size_actual = batch_end - batch_start
            
            logger.info(f"Processing batch {batch_start//batch_size + 1}: blogs {batch_start + 1}-{batch_end}")
            
            # Generate batch of blogs
            batch_blogs = await _generate_batch(
                project_id=project_id,
                prompt=prompt,
                batch_size=batch_size_actual,
                ai_model=ai_model,
                ai_model_version=ai_model_version,
                batch_number=batch_start//batch_size + 1
            )
            
            # Store batch results
            for blog_result in batch_blogs:
                if blog_result["success"]:
                    blogs_generated += 1
                    await _store_blog(project_id, blog_result["blog_data"], supabase)
                else:
                    failed_blogs += 1
                    await _log_error(project_id, blog_result["error"], supabase, user_id)
            
            # Update progress
            progress = int((blogs_generated / num_blogs) * 100)
            await _update_project_progress(project_id, blogs_generated, num_blogs, progress, supabase, user_id)
            
            # Small delay between batches to avoid rate limiting
            if batch_end < num_blogs:
                await asyncio.sleep(2)
        
        # Final status update - status is now managed by the blog generation service
        # We only log completion, the service will set status to "partial" if all blogs generated
        
        # Log completion
        await supabase.table("activity_logs").insert({
            "user_id": user_id,
            "action": f"Blog generation completed: {blogs_generated} successful, {failed_blogs} failed",
            "level": "info",
            "category": "generation",
            "timestamp": "now()",
            "metadata": {
                "details": {
                    "project_id": project_id,
                    "blogs_generated": blogs_generated,
                    "failed_blogs": failed_blogs,
                    "total_requested": num_blogs
                }
            }
        }).execute()
        
        # Final status update to ensure project status is correct
        try:
            if blogs_generated >= num_blogs:
                # All blogs generated - ensure status is set to partial
                await supabase.table("projects").update({
                    "status": "partial",
                    "updated_at": "now()"
                }).eq("id", project_id).execute()
                logger.info(f"📊 Final project status update: set to 'partial' - all {blogs_generated} blogs generated")
            elif blogs_generated > 0:
                # Some blogs generated - ensure status is in_progress
                await supabase.table("projects").update({
                    "status": "in_progress",
                    "updated_at": "now()"
                }).eq("id", project_id).execute()
                logger.info(f"📊 Final project status update: set to 'in_progress' - {blogs_generated}/{num_blogs} blogs generated")
            else:
                # No blogs generated - set status to failed
                await supabase.table("projects").update({
                    "status": "failed",
                    "updated_at": "now()"
                }).eq("id", project_id).execute()
                logger.info(f"📊 Final project status update: set to 'failed' - no blogs generated")
        except Exception as status_error:
            logger.warning(f"⚠️ Could not update final project status: {status_error}")
        
        logger.info(f"Blog generation completed for project {project_id}: {blogs_generated}/{num_blogs} successful")
        
        return {
            "success": True,
            "blogs_generated": blogs_generated,
            "failed_blogs": failed_blogs,
            "total_requested": num_blogs
        }
        
    except Exception as e:
        logger.error(f"Error in blog generation task for project {project_id}: {e}")
        
        # Update project status to failed
        await supabase.table("projects").update({
            "status": "failed",
            "updated_at": "now()"
        }).eq("id", project_id).execute()
        
        # Log error
        await supabase.table("activity_logs").insert({
            "user_id": user_id,
            "action": f"Blog generation failed: {str(e)}",
            "level": "error",
            "category": "generation",
            "timestamp": "now()",
            "metadata": {
                "details": {
                    "project_id": project_id,
                    "error": str(e),
                    "ai_model": ai_model
                }
            }
        }).execute()
        
        return {
            "success": False,
            "error": str(e),
            "blogs_generated": 0,
            "failed_blogs": num_blogs
        }

async def generate_blogs_multithreaded_task(
    project_id: str,
    prompt: str,
    num_blogs: int,
    ai_model: str = "openai",
    ai_model_version: str = None,
    user_id: str = None,
    max_concurrent_blogs: int = 5
):
    """
    Multi-threaded task for generating multiple blogs concurrently
    
    This function:
    1. Uses ThreadPoolExecutor to generate multiple blogs simultaneously
    2. Processes blogs as they complete instead of waiting for each one
    3. Provides better performance for large numbers of blogs
    4. Maintains rate limiting and error handling
    """
    supabase = supabase_client
    
    try:
        logger.info(f"🚀 Starting multi-threaded blog generation for project {project_id}: {num_blogs} blogs using {ai_model}")
        logger.info(f"🔀 Max concurrent blogs: {max_concurrent_blogs}")
        
        # Update project status to in_progress
        await supabase.table("projects").update({
            "status": "in_progress",
            "updated_at": "now()"
        }).eq("id", project_id).execute()
        
        # Log start of generation
        await supabase.table("activity_logs").insert({
            "user_id": user_id,
            "action": f"Started multi-threaded generation of {num_blogs} blogs using {ai_model}",
            "level": "info",
            "category": "generation",
            "timestamp": "now()",
            "metadata": {
                "details": {
                    "project_id": project_id,
                    "ai_model": ai_model,
                    "num_blogs": num_blogs,
                    "max_concurrent": max_concurrent_blogs,
                    "generation_method": "multithreaded"
                }
            }
        }).execute()
        
        # Create thread pool for concurrent blog generation
        with ThreadPoolExecutor(max_workers=max_concurrent_blogs) as executor:
            # Submit all blog generation tasks
            future_to_blog = {}
            for blog_number in range(1, num_blogs + 1):
                future = executor.submit(
                    _generate_single_blog_sync,
                    project_id,
                    prompt,
                    blog_number,
                    ai_model,
                    ai_model_version,
                    user_id
                )
                future_to_blog[future] = blog_number
            
            # Process completed blogs as they finish
            blogs_generated = 0
            failed_blogs = 0
            completed_blogs = []
            
            for future in as_completed(future_to_blog):
                blog_number = future_to_blog[future]
                try:
                    result = future.result(timeout=300)  # 5 minute timeout per blog
                    
                    if result and result.get("success"):
                        blogs_generated += 1
                        completed_blogs.append(result["blog_data"])
                        logger.info(f"✅ Blog {blog_number} generated successfully")
                        
                        # Update progress
                        progress = int((blogs_generated / num_blogs) * 100)
                        await _update_project_progress(project_id, blogs_generated, num_blogs, progress, supabase, user_id)
                        
                    else:
                        failed_blogs += 1
                        error_msg = result.get("error", "Unknown error") if result else "No result returned"
                        await _log_error(project_id, error_msg, supabase, user_id)
                        logger.error(f"❌ Blog {blog_number} generation failed: {error_msg}")
                        
                except Exception as e:
                    failed_blogs += 1
                    error_msg = f"Exception in blog {blog_number}: {str(e)}"
                    await _log_error(project_id, error_msg, supabase, user_id)
                    logger.error(f"❌ Blog {blog_number} generation exception: {e}")
                    continue
        
        # Final status update - status is now managed by the blog generation service
        # We only log completion, the service will set status to "partial" if all blogs generated
        
        # Log completion
        await supabase.table("activity_logs").insert({
            "user_id": user_id,
            "action": f"Multi-threaded blog generation completed: {blogs_generated} successful, {failed_blogs} failed",
            "level": "info",
            "category": "generation",
            "timestamp": "now()",
            "metadata": {
                "details": {
                    "project_id": project_id,
                    "blogs_generated": blogs_generated,
                    "failed_blogs": failed_blogs,
                    "total_requested": num_blogs,
                    "generation_method": "multithreaded",
                    "max_concurrent": max_concurrent_blogs
                }
            }
        }).execute()
        
        # Final status update to ensure project status is correct
        try:
            if blogs_generated >= num_blogs:
                # All blogs generated - ensure status is set to partial
                await supabase.table("projects").update({
                    "status": "partial",
                    "updated_at": "now()"
                }).eq("id", project_id).execute()
                logger.info(f"📊 Final project status update: set to 'partial' - all {blogs_generated} blogs generated")
            elif blogs_generated > 0:
                # Some blogs generated - ensure status is in_progress
                await supabase.table("projects").update({
                    "status": "in_progress",
                    "updated_at": "now()"
                }).eq("id", project_id).execute()
                logger.info(f"📊 Final project status update: set to 'in_progress' - {blogs_generated}/{num_blogs} blogs generated")
            else:
                # No blogs generated - set status to failed
                await supabase.table("projects").update({
                    "status": "failed",
                    "updated_at": "now()"
                }).eq("id", project_id).execute()
                logger.info(f"📊 Final project status update: set to 'failed' - no blogs generated")
        except Exception as status_error:
            logger.warning(f"⚠️ Could not update final project status: {status_error}")
        
        logger.info(f"🎉 Multi-threaded blog generation completed for project {project_id}: {blogs_generated}/{num_blogs} successful")
        
        return {
            "success": True,
            "blogs_generated": blogs_generated,
            "failed_blogs": failed_blogs,
            "total_requested": num_blogs,
            "generation_method": "multithreaded"
        }
        
    except Exception as e:
        logger.error(f"❌ Error in multi-threaded blog generation task for project {project_id}: {e}")
        
        # Update project status to failed
        await supabase.table("projects").update({
            "status": "failed",
            "updated_at": "now()"
        }).eq("id", project_id).execute()
        
        # Log error
        await supabase.table("activity_logs").insert({
            "user_id": user_id,
            "action": f"Multi-threaded blog generation failed: {str(e)}",
            "level": "error",
            "category": "generation",
            "timestamp": "now()",
            "metadata": {
                "details": {
                    "project_id": project_id,
                    "error": str(e),
                    "ai_model": ai_model,
                    "generation_method": "multithreaded"
                }
            }
        }).execute()
        
        return {
            "success": False,
            "error": str(e),
            "blogs_generated": 0,
            "failed_blogs": num_blogs,
            "generation_method": "multithreaded"
        }

def _generate_single_blog_sync(
    project_id: str,
    prompt: str,
    blog_number: int,
    ai_model: str,
    ai_model_version: str = None,
    user_id: str = None
) -> Dict[str, Any]:
    """
    Synchronous version of single blog generation for thread pool executor
    """
    try:
        logger.info(f"🔀 Thread {threading.current_thread().name} generating blog {blog_number}")
        
        # Create a new event loop for this thread if it doesn't have one
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async generation in the thread's event loop
        if loop.is_running():
            # If loop is already running, we need to use asyncio.run_coroutine_threadsafe
            future = asyncio.run_coroutine_threadsafe(
                _generate_single_blog_async(project_id, prompt, blog_number, ai_model, ai_model_version, user_id),
                loop
            )
            return future.result(timeout=300)  # 5 minute timeout
        else:
            # If loop is not running, we can run it directly
            return loop.run_until_complete(
                _generate_single_blog_async(project_id, prompt, blog_number, ai_model, ai_model_version, user_id)
            )
            
    except Exception as e:
        logger.error(f"❌ Thread {threading.current_thread().name} failed to generate blog {blog_number}: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def _generate_single_blog_async(
    project_id: str,
    prompt: str,
    blog_number: int,
    ai_model: str,
    ai_model_version: str = None,
    user_id: str = None
) -> Dict[str, Any]:
    """
    Async version of single blog generation
    """
    try:
        logger.info(f"📝 Generating blog {blog_number} using {ai_model}")
        
        # Generate single blog using the AI client
        blog_data = await ai_client.generate_blog_draft(
            prompt=prompt,
            ai_model=ai_model,
            ai_model_version=ai_model_version
        )
        
        if blog_data:
            # Store in database
            blog_id = await _store_blog(project_id, blog_data, supabase_client)
            
            return {
                "success": True,
                "blog_id": blog_id,
                "blog_data": blog_data
            }
        else:
            return {
                "success": False,
                "error": "AI client returned no data"
            }
            
    except Exception as e:
        logger.error(f"❌ Error generating blog {blog_number}: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def _generate_batch(
    project_id: str,
    prompt: str,
    batch_size: int,
    ai_model: str,
    ai_model_version: str = None,
    batch_number: int = 1
) -> List[Dict[str, Any]]:
    """
    Generate a batch of blogs using the AI client
    """
    batch_results = []
    
    try:
        # Generate multiple blogs using the AI client
        blogs_data = await ai_client.generate_multiple_blogs(
            prompt=prompt,
            num_blogs=batch_size,
            ai_model=ai_model,
            ai_model_version=ai_model_version
        )
        
        for i, blog_data in enumerate(blogs_data):
            try:
                # Add batch information to blog data
                blog_data["batch_number"] = batch_number
                blog_data["blog_number"] = i + 1
                
                batch_results.append({
                    "success": True,
                    "blog_data": blog_data
                })
                
            except Exception as e:
                logger.error(f"Error processing blog {i + 1} in batch {batch_number}: {e}")
                batch_results.append({
                    "success": False,
                    "error": str(e)
                })
        
        # If AI client didn't return expected number of blogs, mark missing ones as failed
        while len(batch_results) < batch_size:
            batch_results.append({
                "success": False,
                "error": "AI client returned fewer blogs than requested"
            })
        
    except Exception as e:
        logger.error(f"Error generating batch {batch_number}: {e}")
        # Mark all blogs in this batch as failed
        for i in range(batch_size):
            batch_results.append({
                "success": False,
                "error": str(e)
            })
    
    return batch_results

async def _store_blog(project_id: str, blog_data: Dict[str, Any], supabase) -> str:
    """
    Store a generated blog in the database
    """
    try:
        # Clean the blog content, title, and prompt using TextCleaner
        cleaned_title = TextCleaner.clean_title(blog_data.get("title", ""))
        cleaned_content = TextCleaner.clean_blog_content(blog_data.get("content", ""))
        cleaned_prompt = TextCleaner.clean_prompt(blog_data.get("prompt", ""))
        
        # Create blog record
        blog_record = {
            "id": str(uuid4()),
            "project_id": project_id,
            "title": cleaned_title,
            "content": cleaned_content,
            "prompt": cleaned_prompt,
            "ai_model": blog_data.get("model_provider", "unknown"),
            "ai_model_version": blog_data.get("model", ""),
            "status": BlogStatus.DRAFT,
            "seo_meta": {
                "generation_model": blog_data.get("model_provider"),
                "model_version": blog_data.get("model"),
                "tokens_used": blog_data.get("tokens_used", 0),
                "batch_number": blog_data.get("batch_number"),
                "blog_number": blog_data.get("blog_number"),
                "generated_at": time.time()
            },
            "generation_logs": [
                {
                    "timestamp": time.time(),
                    "message": "Blog generated successfully",
                    "status": "success"
                }
            ]
        }
        
        # Insert into database
        result = await supabase.table("blogs").insert(blog_record).execute()
        
        if result.data:
            logger.info(f"Blog stored successfully: {blog_record['id']}")
            return blog_record['id']
        else:
            logger.error(f"Failed to store blog: {result.error}")
            raise Exception(f"Database error: {result.error}")
            
    except Exception as e:
        logger.error(f"Error storing blog: {e}")
        raise

async def _log_error(project_id: str, error_message: str, supabase, user_id: str = None):
    """
    Log an error during blog generation
    """
    if user_id:
        try:
            await supabase.table("activity_logs").insert({
                "user_id": user_id,
                "action": f"Blog generation error: {error_message}",
                "level": "error",
                "category": "generation",
                "timestamp": "now()",
                "metadata": {
                    "details": {
                        "project_id": project_id,
                        "error_message": error_message
                    }
                }
            }).execute()
        except Exception as e:
            logger.error(f"Error logging error message: {e}")

async def _update_project_progress(
    project_id: str, 
    blogs_generated: int, 
    total_blogs: int, 
    progress: int, 
    supabase,
    user_id: str = None
):
    """
    Update project progress in the database
    """
    try:
        # Update project with current progress
        await supabase.table("projects").update({
            "status": "in_progress",
            "updated_at": "now()"
        }).eq("id", project_id).execute()
        
        # Log progress update
        if user_id:
            await supabase.table("activity_logs").insert({
                "user_id": user_id,
                "action": f"Progress: {blogs_generated}/{total_blogs} blogs generated ({progress}%)",
                "level": "info",
                "category": "generation",
                "timestamp": "now()",
                "metadata": {
                    "details": {
                        "project_id": project_id,
                        "blogs_generated": blogs_generated,
                        "total_blogs": total_blogs,
                        "progress_percentage": progress
                    }
                }
            }).execute()
        
    except Exception as e:
        logger.error(f"Error updating project progress: {e}")

async def generate_single_blog(
    project_id: str,
    prompt: str,
    ai_model: str = "openai",
    ai_model_version: str = None
) -> Dict[str, Any]:
    """
    Generate a single blog (useful for testing or individual blog generation)
    """
    try:
        # Generate single blog
        blog_data = await ai_client.generate_blog_draft(
            prompt=prompt,
            ai_model=ai_model,
            ai_model_version=ai_model_version
        )
        
        # Store in database
        supabase = supabase_client
        blog_id = await _store_blog(project_id, blog_data, supabase)
        
        return {
            "success": True,
            "blog_id": blog_id,
            "blog_data": blog_data
        }
        
    except Exception as e:
        logger.error(f"Error generating single blog: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def retry_failed_blog(blog_id: str) -> Dict[str, Any]:
    """
    Retry generation for a failed blog
    """
    try:
        supabase = supabase_client
        
        # Get the failed blog
        blog_response = supabase.table("blogs").select("*").eq("id", blog_id).execute()
        
        if not blog_response.data:
            return {"success": False, "error": "Blog not found"}
        
        blog = blog_response.data[0]
        
        # Retry generation with same parameters
        blog_data = await ai_client.generate_blog_draft(
            prompt=blog["prompt"],
            ai_model=blog["ai_model"],
            ai_model_version=blog.get("ai_model_version")
        )
        
        # Update existing blog record
        update_data = {
            "title": blog_data.get("title", ""),
            "content": blog_data.get("content", ""),
            "status": BlogStatus.DRAFT,
            "updated_at": "now()",
            "error_message": None,
            "generation_logs": blog.get("generation_logs", []) + [
                {
                    "timestamp": time.time(),
                    "message": "Blog regenerated after failure",
                    "status": "success"
                }
            ]
        }
        
        result = supabase.table("blogs").update(update_data).eq("id", blog_id).execute()
        
        if result.data:
            return {
                "success": True,
                "blog_id": blog_id,
                "message": "Blog regenerated successfully"
            }
        else:
            return {
                "success": False,
                "error": "Failed to update blog record"
            }
            
    except Exception as e:
        logger.error(f"Error retrying failed blog {blog_id}: {e}")
        return {
            "success": False,
            "error": str(e)
        }
