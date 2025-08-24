from celery import shared_task
from typing import Dict, List, Any
import logging
import asyncio
from uuid import UUID
import json
from datetime import datetime

from core.supabase_client import supabase_client
from core.ai_client import ai_client
from models.blog import BlogStatus, BlogCreate, BlogUpdate
from tasks.seo_optimization import optimize_seo_task
from tasks.blog_formatting import format_blog_task
from tasks.image_generation import generate_image_task

logger = logging.getLogger(__name__)

@shared_task(bind=True, name="generate_blogs_for_project")
def generate_blogs_for_project(self, project_id: str, prompt: str, num_blogs: int, 
                              ai_model: str = "openai", batch_size: int = 5):
    """
    Main task to generate multiple blogs for a project
    
    Args:
        project_id: Project UUID as string
        prompt: Blog generation prompt
        num_blogs: Number of blogs to generate
        ai_model: AI model to use (openai or gemini)
        batch_size: Number of blogs to generate in parallel
    """
    try:
        logger.info(f"Starting blog generation for project {project_id}: {num_blogs} blogs")
        
        # Update project status to running
        update_project_status(project_id, "running")
        
        # Generate blogs in batches
        blogs_created = 0
        blogs_failed = 0
        
        for batch_start in range(0, num_blogs, batch_size):
            batch_end = min(batch_start + batch_size, num_blogs)
            batch_size_actual = batch_end - batch_start
            
            logger.info(f"Processing batch {batch_start//batch_size + 1}: blogs {batch_start+1}-{batch_end}")
            
            # Create batch of blog records
            batch_blogs = create_batch_blogs(project_id, prompt, ai_model, batch_size_actual)
            
            # Process each blog in the batch
            for blog_data in batch_blogs:
                try:
                    # Generate content for this blog
                    blog_result = generate_single_blog.delay(
                        blog_data["id"], 
                        prompt, 
                        ai_model,
                        blog_data["blog_number"]
                    )
                    
                    blogs_created += 1
                    logger.info(f"Blog {blog_data['id']} queued for generation")
                    
                except Exception as e:
                    logger.error(f"Failed to queue blog generation: {e}")
                    blogs_failed += 1
                    update_blog_status(blog_data["id"], BlogStatus.FAILED, str(e))
            
            # Update progress
            update_project_progress(project_id, blogs_created, num_blogs)
            
            # Small delay between batches to avoid overwhelming the system
            if batch_end < num_blogs:
                import time
                time.sleep(2)
        
        # Update project status
        if blogs_failed == 0:
            update_project_status(project_id, "completed")
        elif blogs_created > 0:
            update_project_status(project_id, "partially_completed")
        else:
            update_project_status(project_id, "failed")
        
        logger.info(f"Blog generation completed: {blogs_created} created, {blogs_failed} failed")
        
        return {
            "project_id": project_id,
            "blogs_created": blogs_created,
            "blogs_failed": blogs_failed,
            "total_requested": num_blogs
        }
        
    except Exception as e:
        logger.error(f"Error in generate_blogs_for_project: {e}")
        update_project_status(project_id, "failed")
        raise

@shared_task(bind=True, name="generate_single_blog")
def generate_single_blog(self, blog_id: str, prompt: str, ai_model: str, blog_number: int):
    """
    Generate content for a single blog
    
    Args:
        blog_id: Blog UUID as string
        prompt: Blog generation prompt
        ai_model: AI model to use
        blog_number: Sequential number of this blog in the project
    """
    try:
        logger.info(f"Generating blog {blog_id} (blog #{blog_number})")
        
        # Update blog status to generating
        update_blog_status(blog_id, BlogStatus.GENERATING)
        
        # Create unique prompt for this blog
        unique_prompt = create_unique_prompt(prompt, blog_number)
        
        # Generate initial content
        content_result = asyncio.run(
            ai_client.generate_blog_draft(unique_prompt, ai_model)
        )
        
        # Extract title and content
        content = content_result["content"]
        title = extract_title_from_content(content)
        content_without_title = remove_title_from_content(content)
        
        # Update blog with generated content
        update_blog_content(blog_id, title, content_without_title, content_result)
        
        # Update blog status to SEO optimizing
        update_blog_status(blog_id, BlogStatus.SEO_OPTIMIZING)
        
        # Chain to SEO optimization task
        seo_result = optimize_seo_task.delay(blog_id)
        
        logger.info(f"Blog {blog_id} content generated, queued for SEO optimization")
        
        return {
            "blog_id": blog_id,
            "status": "content_generated",
            "title": title,
            "content_length": len(content_without_title),
            "ai_model": ai_model,
            "seo_task_id": seo_result.id
        }
        
    except Exception as e:
        logger.error(f"Error generating blog {blog_id}: {e}")
        update_blog_status(blog_id, BlogStatus.FAILED, str(e))
        raise

def create_unique_prompt(base_prompt: str, blog_number: int) -> str:
    """Create a unique prompt for each blog to avoid duplicate content"""
    variations = [
        f"Create a unique perspective on: {base_prompt}",
        f"Write about {base_prompt} from a different angle",
        f"Explore {base_prompt} with fresh insights",
        f"Present {base_prompt} in an innovative way",
        f"Discuss {base_prompt} with a new approach"
    ]
    
    variation = variations[blog_number % len(variations)]
    return f"{variation}. This should be blog post #{blog_number + 1} in a series."

def extract_title_from_content(content: str) -> str:
    """Extract title from the first line of content"""
    lines = content.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            # Remove markdown formatting
            title = line.replace('#', '').replace('*', '').replace('**', '').strip()
            if len(title) > 10:  # Ensure it's a reasonable title
                return title[:100]  # Limit title length
    
    return "Untitled Blog Post"

def remove_title_from_content(content: str) -> str:
    """Remove the title line from content"""
    lines = content.strip().split('\n')
    # Skip empty lines and title lines
    content_lines = []
    title_found = False
    
    for line in lines:
        line = line.strip()
        if line and not title_found:
            # Skip the first non-empty line (title)
            title_found = True
            continue
        content_lines.append(line)
    
    return '\n'.join(content_lines).strip()

def create_batch_blogs(project_id: str, prompt: str, ai_model: str, batch_size: int) -> List[Dict]:
    """Create blog records in the database for a batch"""
    try:
        blogs_data = []
        
        for i in range(batch_size):
            blog_data = {
                "project_id": project_id,
                "prompt": prompt,
                "ai_model": ai_model,
                "status": BlogStatus.DRAFT,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Insert blog into database
            response = supabase_client.table("blogs").insert(blog_data).execute()
            
            if response.data:
                blog_id = response.data[0]["id"]
                blogs_data.append({
                    "id": blog_id,
                    "blog_number": i
                })
                logger.info(f"Created blog record {blog_id}")
            else:
                logger.error(f"Failed to create blog record in batch")
        
        return blogs_data
        
    except Exception as e:
        logger.error(f"Error creating batch blogs: {e}")
        raise

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

def update_blog_content(blog_id: str, title: str, content: str, ai_result: Dict):
    """Update blog with generated content"""
    try:
        update_data = {
            "title": title,
            "content": content,
            "ai_model_version": ai_result.get("model_version"),
            "generation_logs": [{
                "step": "content_generation",
                "timestamp": datetime.utcnow().isoformat(),
                "ai_model": ai_result.get("model"),
                "tokens_used": ai_result.get("tokens_used"),
                "status": "success"
            }],
            "updated_at": datetime.utcnow().isoformat()
        }
        
        response = supabase_client.table("blogs").update(update_data).eq("id", blog_id).execute()
        
        if not response.data:
            logger.error(f"Failed to update blog {blog_id} content")
            
    except Exception as e:
        logger.error(f"Error updating blog content: {e}")

def update_project_status(project_id: str, status: str):
    """Update project status in database"""
    try:
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        response = supabase_client.table("projects").update(update_data).eq("id", project_id).execute()
        
        if not response.data:
            logger.error(f"Failed to update project {project_id} status")
            
    except Exception as e:
        logger.error(f"Error updating project status: {e}")

def update_project_progress(project_id: str, blogs_created: int, total_blogs: int):
    """Update project progress in database"""
    try:
        progress = int((blogs_created / total_blogs) * 100)
        
        update_data = {
            "progress": progress,
            "blogs_generated": blogs_created,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        response = supabase_client.table("projects").update(update_data).eq("id", project_id).execute()
        
        if not response.data:
            logger.error(f"Failed to update project {project_id} progress")
            
    except Exception as e:
        logger.error(f"Error updating project progress: {e}")
